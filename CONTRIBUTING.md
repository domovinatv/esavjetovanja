# Doprinos

Hvala što želiš pomoći.

## Prijava problema

Otvori issue i navedi ID savjetovanja, naredbu koju si pokrenuo i ispis
greške. Portal se povremeno mijenja, pa scraper može prestati raditi kad se
promijeni struktura stranice. Takve prijave su najkorisnije.

## Razvoj

```bash
uv sync
uv run esavjetovanja scrape <id> --headed   # vidi što browser radi
```

Kod je u `src/esavjetovanja/`:

- `scrape.py` otvara savjetovanje u Playwrightu i čita DOM
- `report.py` izrađuje Markdown izvještaj iz preuzetih JSONL datoteka
- `cli.py` je naredbeni redak

Ako mijenjaš selektore, provjeri da broj preuzetih komentara i dalje odgovara
broju koji navodi portal (scraper ispiše upozorenje ako ne odgovara).

## Dodavanje savjetovanja u repozitorij

Pokreni `scrape` i `report` za savjetovanje, dodaj redak u tablicu u
`README.md` i otvori pull request s mapom `data/savjetovanja/<id>/`.
