"""Markdown izvještaj iz preuzetog savjetovanja (bez LLM-a, čista statistika i pregled)."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _quote(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def _chapter(comment: dict) -> str:
    path = comment["section_heading_path"]
    return path[0] if path else "(bez naslova)"


def build_report(folder: Path) -> str:
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    sections = {s["id"]: s for s in _read_jsonl(folder / "sections.jsonl")}
    comments = _read_jsonl(folder / "comments.jsonl")

    authors = Counter(c["author"] for c in comments)
    types = Counter(c["type"] for c in comments)
    days = Counter((c["datetime"] or "")[:10] for c in comments)
    chapters = Counter(_chapter(c) for c in comments)

    out = [
        f"# {meta['title']}",
        "",
        f"- Izvor: <{meta['url']}>",
        f"- Otvoreno: {meta['opened']} · zatvaranje: {meta['closed']} · očekivano izvješće: {meta['report_expected']}",
        f"- Preuzeto: {meta['scraped_at']}",
        f"- Dijelova dokumenta: {meta['sections']}",
        f"- Komentara: {len(comments)} (portal navodi {meta['totals']['comments']})",
        "",
        "## Pregled",
        "",
        "| Vrsta | Broj |",
        "|---|---:|",
        *[f"| {t} | {n} |" for t, n in types.most_common()],
        "",
        f"Različitih autora: **{len(authors)}**. "
        f"Najaktivniji autor ima {authors.most_common(1)[0][1] if authors else 0} "
        f"od {len(comments)} komentara ({100 * authors.most_common(1)[0][1] / max(len(comments), 1):.0f} %)."
        if authors else "Nema komentara.",
        "",
        "### Autori",
        "",
        "| Autor | Komentara | Opći | Nadopuna |",
        "|---|---:|---:|---:|",
    ]
    by_author_type: dict[str, Counter] = defaultdict(Counter)
    for c in comments:
        by_author_type[c["author"]][c["type"]] += 1
    for author, n in authors.most_common():
        t = by_author_type[author]
        out.append(f"| {author} | {n} | {t['Opći komentar']} | {t['Nadopuna teksta']} |")

    out += ["", "### Po danima", "", "| Dan | Komentara |", "|---|---:|"]
    out += [f"| {d} | {n} |" for d, n in sorted(days.items())]

    out += ["", "### Po poglavljima", "", "| Poglavlje | Komentara |", "|---|---:|"]
    out += [f"| {ch} | {n} |" for ch, n in chapters.most_common()]

    out += ["", "## Komentari uz tekst", ""]
    by_section: dict[int, list[dict]] = defaultdict(list)
    for c in comments:
        by_section[c["section_id"]].append(c)
    for sid in sorted(by_section, key=lambda s: sections[s]["order"]):
        section = sections[sid]
        crumbs = " › ".join(section["heading_path"])
        out += [f"### {crumbs}", "", f"*Dio {section['order']} (id {sid})*", ""]
        if section["text"]:
            out += ["<details><summary>Izvorni tekst dijela</summary>", "", _quote(section["text"]), "", "</details>", ""]
        for c in by_section[sid]:
            reactions = f" · 👍 {c['likes']} 👎 {c['dislikes']}" if c["likes"] or c["dislikes"] else ""
            out += [f"**{c['type']}** — {c['author']}, {c['datetime']}{reactions}", "", _quote(c["text"]), ""]
    return "\n".join(out).rstrip() + "\n"


def write_report(folder: Path) -> Path:
    path = folder / "README.md"
    path.write_text(build_report(folder), encoding="utf-8")
    return path
