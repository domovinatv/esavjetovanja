"""Preuzimanje jednog savjetovanja s esavjetovanja.gov.hr.

Portal je Blazor Server aplikacija: HTML koji vrati server je prazna ljuska, a
sadržaj stiže preko SignalR websocketa. Zato stranicu renderiramo u pravom
browseru (Playwright) i čitamo DOM. Komentari se vide tek kad se klikne na
pojedini dio dokumenta, pa scraper klika svaki dio koji ima komentare.

Rezultat za savjetovanje <id> ide u data/savjetovanja/<id>/:
  meta.json        naslov, datumi, ukupni brojevi, popis dokumenata
  sections.jsonl   svi dijelovi dokumenta (tekst, HTML, putanja naslova, brojači)
  comments.jsonl   svi komentari s autorom, vrstom, datumom, tekstom i reakcijama
  documents/       dokument savjetovanja i ostali priloženi dokumenti
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import Page, sync_playwright

BASE_URL = "https://esavjetovanja.gov.hr"

_COUNT_PATTERNS = {
    "general": r"Opći komentari:\s*(\d+)",
    "addition": r"Nadopuna teksta:\s*(\d+)",
    "total": r"Ukupno komentara:\s*(\d+)",
}
_TOTAL_PATTERNS = {
    "comments": r"Ukupno komentara:\s*(\d+)",
    "general": r"Ukupno općih komentara:\s*(\d+)",
    "addition": r"Ukupno nadopuna teksta:\s*(\d+)",
}
_DATE_PATTERNS = {
    "opened": r"Datum otvaranja:\s*([\d.]+)",
    "closed": r"Datum zatvaranja:\s*([\d.]+)",
    "report_expected": r"Očekivana objava izvješća:\s*([\d.]+)",
}


def _text(el: Tag | None) -> str:
    if el is None:
        return ""
    text = el.get_text("\n", strip=False)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def _hr_date(value: str) -> str | None:
    """'16.10.2026' -> '2026-10-16', '16.10.2026 18:46' -> '2026-10-16T18:46'."""
    value = value.strip().rstrip(".")
    for fmt, out in (("%d.%m.%Y %H:%M", "%Y-%m-%dT%H:%M"), ("%d.%m.%Y", "%Y-%m-%d")):
        try:
            return datetime.strptime(value, fmt).strftime(out)
        except ValueError:
            pass
    return None


def _counts(text: str, patterns: dict[str, str]) -> dict[str, int]:
    out = {}
    for key, pattern in patterns.items():
        m = re.search(pattern, text)
        out[key] = int(m.group(1)) if m else 0
    return out


def _wait_for_app(page: Page) -> None:
    page.wait_for_selector(".document-sections .document-section", timeout=60_000)
    page.wait_for_timeout(1000)


def _parse_header(soup: BeautifulSoup) -> dict:
    title_el = soup.select_one(".eConTitle h2")
    dates_text = _text(soup.select_one(".eConTitle .dates-row"))
    stats_text = _text(soup.select_one(".eConTitle .statistics-row"))
    return {
        "title": _text(title_el),
        **{k: _hr_date(m.group(1)) if (m := re.search(p, dates_text)) else None
           for k, p in _DATE_PATTERNS.items()},
        "totals": _counts(stats_text, _TOTAL_PATTERNS),
    }


def _split_heading(content: Tag | None) -> tuple[int | None, str, str]:
    """Vrati (razina, naslov, tekst bez naslova). Razina 0 je naslov cijelog dokumenta."""
    if content is None:
        return None, "", ""
    first = content.find(lambda t: isinstance(t, Tag))
    if first is None:
        return None, "", _text(content)
    if m := re.fullmatch(r"h([1-6])", first.name):
        level = int(m.group(1))
    elif "section-title" in first.get("class", []):
        level = 0
    else:
        return None, "", _text(content)
    heading = _text(first)
    body = _text(content).removeprefix(heading).strip()
    return level, heading, body


def _parse_sections(soup: BeautifulSoup) -> list[dict]:
    sections = []
    heading_path: dict[int, str] = {}
    for el in soup.select(".document-sections > .document-section"):
        content = el.select_one(".section-content")
        level, heading, body = _split_heading(content)
        if level is not None:
            heading_path = {k: v for k, v in heading_path.items() if k < level}
            heading_path[level] = heading
        sections.append({
            "id": int(el["id"].removeprefix("section-")),
            "order": int(el.get("data-order", 0)),
            "level": level,
            "heading": heading,
            # Putanja bez naslova dokumenta (razina 0), npr. ["4. ...", "4.3. ...", "4.3.1. ..."]
            "heading_path": [heading_path[k] for k in sorted(heading_path) if k > 0] or [heading],
            "text": body,
            "html": content.decode_contents() if content else "",
            "comment_counts": _counts(_text(el.select_one(".comment-stats")), _COUNT_PATTERNS),
        })
    return sections


def _parse_comments(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    comments = []
    for item in soup.select(".slice-detail-view .comment-item"):
        classes = item.get("class", [])
        counts = [int(c.get_text(strip=True) or 0) for c in item.select(".comment-counts .count")]
        popularity = _text(item.select_one(".popularity-stat"))
        text_el = item.select_one(".comment-text")
        # Sve što nije zaglavlje, tekst ni statistika (npr. odgovor nositelja nakon zatvaranja)
        extra = [
            {"class": " ".join(child.get("class", [])), "text": _text(child)}
            for child in item.find_all(recursive=False)
            if isinstance(child, Tag)
            and not {"comment-header", "comment-text", "comment-stats"} & set(child.get("class", []))
        ]
        comments.append({
            "author": _text(item.select_one(".comment-author-name")),
            "type": _text(item.select_one(".comment-type-badge")),
            "type_class": next((c for c in classes if c != "comment-item"), None),
            "datetime": _hr_date(_text(item.select_one(".comment-date"))),
            "text": _text(text_el),
            "html": text_el.decode_contents() if text_el else "",
            "likes": counts[0] if len(counts) > 0 else None,
            "dislikes": counts[1] if len(counts) > 1 else None,
            "popularity": int(m.group(0)) if (m := re.search(r"-?\d+", popularity)) else None,
            "extra": extra,
        })
    return comments


def _comments_for_section(page: Page, section_id: int) -> list[dict]:
    page.locator(f"#section-{section_id}").click()
    page.wait_for_selector(".slice-detail-view .comment-item", timeout=30_000)
    page.wait_for_timeout(500)
    comments: list[dict] = []
    while True:
        comments.extend(_parse_comments(page.content()))
        next_btn = page.locator(".slice-detail-view .e-pager .e-next:not(.e-disable)")
        if next_btn.count() == 0:
            break
        first_before = page.locator(".slice-detail-view .comment-item").first.inner_text()
        next_btn.first.click()
        page.wait_for_function(
            "prev => document.querySelector('.slice-detail-view .comment-item')?.innerText !== prev",
            arg=first_before, timeout=15_000,
        )
        page.wait_for_timeout(300)
    page.get_by_role("button", name="Natrag na savjetovanje").first.click()
    _wait_for_app(page)
    return comments


def _safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip() or "dokument"


def _download_documents(page: Page, out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    docs = []

    with page.expect_download(timeout=60_000) as dl_info:
        page.get_by_text("Preuzmi dokument savjetovanja").first.click()
    dl = dl_info.value
    name = _safe_name(dl.suggested_filename)
    dl.save_as(out_dir / name)
    docs.append({"name": dl.suggested_filename, "file": f"documents/{name}", "kind": "Glavni dokument"})

    page.get_by_text("Ostali dokumenti").first.click()
    page.wait_for_timeout(1500)
    items = page.locator(".documents-list .document-item")
    for i in range(items.count()):
        item = items.nth(i)
        label = item.locator(".document-name").inner_text().strip()
        meta = item.locator(".document-meta").inner_text().strip() if item.locator(".document-meta").count() else ""
        with page.expect_download(timeout=60_000) as dl_info:
            item.locator("fluent-button[title='Preuzmi dokument']").click()
        dl = dl_info.value
        name = _safe_name(dl.suggested_filename or label)
        dl.save_as(out_dir / name)
        docs.append({"name": label, "file": f"documents/{name}", "kind": meta})
    return docs


def _comment_id(c: dict) -> str:
    key = f"{c['section_id']}|{c['author']}|{c['datetime']}|{c['text']}"
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def scrape_consultation(
    consultation_id: int,
    data_dir: Path,
    *,
    channel: str | None = "chrome",
    headless: bool = True,
    documents: bool = True,
    log=print,
) -> Path:
    url = f"{BASE_URL}/Econ/{consultation_id}"
    out = data_dir / "savjetovanja" / str(consultation_id)
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=headless)
        context = browser.new_context(accept_downloads=True, locale="hr-HR")
        page = context.new_page()
        log(f"Otvaram {url}")
        page.goto(url, wait_until="networkidle")
        _wait_for_app(page)

        soup = BeautifulSoup(page.content(), "html.parser")
        header = _parse_header(soup)
        sections = _parse_sections(soup)
        log(f"{header['title']}\n  dijelova: {len(sections)}, komentara prema portalu: {header['totals']['comments']}")

        comments: list[dict] = []
        by_id = {s["id"]: s for s in sections}
        with_comments = [s for s in sections if s["comment_counts"]["total"] > 0]
        for n, section in enumerate(with_comments, 1):
            rows = _comments_for_section(page, section["id"])
            expected = section["comment_counts"]["total"]
            flag = "" if len(rows) == expected else f"  (!) očekivano {expected}"
            log(f"  [{n}/{len(with_comments)}] dio {section['id']}: {len(rows)} komentara{flag}")
            for c in rows:
                c["section_id"] = section["id"]
                c["section_order"] = section["order"]
                c["section_heading_path"] = by_id[section["id"]]["heading_path"]
                c["id"] = _comment_id(c)
                comments.append(c)

        docs = []
        if documents:
            log("Preuzimam dokumente")
            docs = _download_documents(page, out / "documents")
        browser.close()

    comments.sort(key=lambda c: (c["section_order"], c["datetime"] or ""))
    meta = {
        "id": consultation_id,
        "url": url,
        **header,
        "sections": len(sections),
        "comments_scraped": len(comments),
        "documents": docs,
        "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_jsonl(out / "sections.jsonl", sections)
    _write_jsonl(out / "comments.jsonl", comments)

    if len(comments) != header["totals"]["comments"]:
        log(f"UPOZORENJE: preuzeto {len(comments)} komentara, portal kaže {header['totals']['comments']}")
    log(f"Spremljeno u {out}")
    return out
