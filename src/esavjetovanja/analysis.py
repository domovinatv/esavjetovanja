"""Snapshot LLM analize: spajanje dijelova, izračun ukupnih ocjena, metapodaci.

Snapshot živi u data/savjetovanja/<id>/analize/<datum>_<model>/:
  dijelovi/*.jsonl   sirovi izlaz modela, jedan objekt po dijelu dokumenta
  dokument.json      sinteza cijelog dokumenta (piše model)
  analiza.jsonl      spojeno i provjereno, s izračunatom ukupnom ocjenom
  snapshot.json      model, vrijeme, broj komentara, otisak teksta, prosjeci
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

CRITERIA = ["konkretnost", "mjerljivost", "utemeljenost", "provedivost", "jasnoca"]
METHOD_VERSION = 1


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def overall(scores: dict) -> int | None:
    values = [v for k in CRITERIA if isinstance(v := scores.get(k), (int, float))]
    return round(sum(values) / len(values)) if values else None


def text_fingerprint(sections: list[dict]) -> str:
    h = hashlib.sha256()
    for s in sorted(sections, key=lambda s: s["order"]):
        h.update(f"{s['heading']}\n{s['text']}\n".encode())
    return h.hexdigest()[:16]


def latest_snapshot(folder: Path) -> Path | None:
    root = folder / "analize"
    snaps = sorted(p for p in root.iterdir() if (p / "snapshot.json").exists()) if root.exists() else []
    return snaps[-1] if snaps else None


def merge_snapshot(folder: Path, snapshot_dir: Path, *, model: str, created_at: str) -> dict:
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    sections = _read_jsonl(folder / "sections.jsonl")
    comments = _read_jsonl(folder / "comments.jsonl")
    order = {s["id"]: s["order"] for s in sections}
    comment_ids = {c["id"] for c in comments}

    rows: dict[int, dict] = {}
    for part in sorted((snapshot_dir / "dijelovi").glob("*.jsonl")):
        for row in _read_jsonl(part):
            rows[row["section_id"]] = row

    problems = []
    if missing := sorted(set(order) - set(rows)):
        problems.append(f"bez analize: {missing}")
    if unknown := sorted(set(rows) - set(order)):
        problems.append(f"nepoznati dijelovi: {unknown}")
    analysed_comments = {c["comment_id"] for r in rows.values() for c in r.get("komentari", [])}
    if missing_c := comment_ids - analysed_comments:
        problems.append(f"komentari bez analize: {len(missing_c)}")

    merged = []
    for sid in sorted(rows, key=lambda s: order.get(s, 10**9)):
        row = rows[sid]
        row["ukupno"] = overall(row.get("ocjene") or {})
        merged.append(row)
    with (snapshot_dir / "analiza.jsonl").open("w", encoding="utf-8") as f:
        for row in merged:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    scored = [r for r in merged if r["ukupno"] is not None]
    weights = {s["id"]: max(len(s["text"]), 1) for s in sections}
    snapshot = {
        "savjetovanje": meta["id"],
        "model": model,
        "metodologija": METHOD_VERSION,
        "izradjeno": created_at,
        "podaci_preuzeti": meta["scraped_at"],
        "komentara": len(comments),
        "dijelova": len(sections),
        "otisak_teksta": text_fingerprint(sections),
        "prosjek": {
            "ukupno": round(sum(r["ukupno"] for r in scored) / len(scored)) if scored else None,
            # težinski prosjek po duljini teksta: dugi dijelovi više utječu
            "ukupno_tezinski": round(
                sum(r["ukupno"] * weights[r["section_id"]] for r in scored)
                / sum(weights[r["section_id"]] for r in scored)
            ) if scored else None,
            **{
                k: round(sum(vals) / len(vals)) if (vals := [
                    r["ocjene"][k] for r in scored if isinstance(r["ocjene"].get(k), (int, float))
                ]) else None
                for k in CRITERIA
            },
        },
        "problemi": problems,
    }
    (snapshot_dir / "snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return snapshot
