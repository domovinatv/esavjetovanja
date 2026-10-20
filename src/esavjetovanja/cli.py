"""Naredbeni redak: `esavjetovanja <naredba> ...`."""

from __future__ import annotations

import argparse
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="esavjetovanja", description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="korijen za podatke (default: data)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scrape", help="preuzmi savjetovanje (tekst, komentare, dokumente)")
    s.add_argument("ids", nargs="+", type=int, help="ID savjetovanja, npr. 10346 iz /Econ/10346")
    s.add_argument("--channel", default="chrome",
                   help="Playwright kanal: chrome, msedge ili 'bundled' za Playwrightov Chromium")
    s.add_argument("--headed", action="store_true", help="prikaži browser")
    s.add_argument("--no-documents", action="store_true", help="ne preuzimaj .docx/.pdf priloge")

    r = sub.add_parser("report", help="generiraj Markdown izvještaj za preuzeto savjetovanje")
    r.add_argument("ids", nargs="+", type=int)

    args = parser.parse_args(argv)

    if args.cmd == "scrape":
        from .scrape import scrape_consultation
        for cid in args.ids:
            scrape_consultation(
                cid, args.data_dir,
                channel=None if args.channel == "bundled" else args.channel,
                headless=not args.headed,
                documents=not args.no_documents,
            )
    elif args.cmd == "report":
        from .report import write_report
        for cid in args.ids:
            print(write_report(args.data_dir / "savjetovanja" / str(cid)))


if __name__ == "__main__":
    main()
