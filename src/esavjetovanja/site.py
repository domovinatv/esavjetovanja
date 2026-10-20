"""Statična stranica za jedno savjetovanje: tekst, komentari i LLM analiza na jednom mjestu."""

from __future__ import annotations

import json
import shutil
from importlib import resources
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from .analysis import latest_snapshot

_KEEP_ATTRS = {"colspan", "rowspan", "href"}


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def clean_html(html: str) -> str:
    """Makni inline stilove i Wordove ostatke, zadrži strukturu (odlomci, liste, tablice)."""
    soup = BeautifulSoup(html, "html.parser")
    first = soup.find(lambda t: isinstance(t, Tag))
    if first is not None and (first.name in {"h1", "h2", "h3", "h4", "h5", "h6"}
                              or "section-title" in first.get("class", [])):
        first.decompose()
    for el in soup.find_all(True):
        el.attrs = {k: v for k, v in el.attrs.items() if k in _KEEP_ATTRS}
        if el.name in {"span", "font"}:
            el.unwrap()
    for el in soup.find_all(["p", "li", "td"]):
        if not el.get_text(strip=True) and not el.find(["img", "table"]):
            el.decompose()
    return str(soup).strip()


def build_data(folder: Path) -> dict:
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    sections = _read_jsonl(folder / "sections.jsonl")
    comments = _read_jsonl(folder / "comments.jsonl")

    snapshot = analysis = synthesis = None
    if snap_dir := latest_snapshot(folder):
        snapshot = json.loads((snap_dir / "snapshot.json").read_text(encoding="utf-8"))
        analysis = {r["section_id"]: r for r in _read_jsonl(snap_dir / "analiza.jsonl")}
        if (snap_dir / "dokument.json").exists():
            synthesis = json.loads((snap_dir / "dokument.json").read_text(encoding="utf-8"))

    by_section: dict[int, list[dict]] = {}
    for c in comments:
        by_section.setdefault(c["section_id"], []).append({
            k: c[k] for k in ("id", "author", "type", "datetime", "text", "likes", "dislikes")
        })

    return {
        "meta": {k: meta[k] for k in ("id", "url", "title", "opened", "closed", "report_expected",
                                      "totals", "scraped_at", "documents")},
        "snapshot": snapshot,
        "synthesis": synthesis,
        "sections": [
            {
                "id": s["id"],
                "order": s["order"],
                "level": s["level"],
                "heading": s["heading"],
                "path": s["heading_path"],
                "html": clean_html(s["html"]),
                "chars": len(s["text"]),
                "comments": by_section.get(s["id"], []),
                "analysis": (analysis or {}).get(s["id"]),
            }
            for s in sorted(sections, key=lambda s: s["order"])
        ],
    }


def build_site(folder: Path, out: Path) -> Path:
    data = build_data(folder)
    template = resources.files("esavjetovanja").joinpath("templates/index.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = template.replace("__TITLE__", data["meta"]["title"]).replace("__DATA__", payload)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    docs_out = out / "dokumenti"
    docs_out.mkdir(exist_ok=True)
    for doc in data["meta"]["documents"]:
        shutil.copy2(folder / doc["file"], docs_out / Path(doc["file"]).name)
    return out / "index.html"
