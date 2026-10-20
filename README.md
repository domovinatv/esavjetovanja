# esavjetovanja

Otvoreni alati za preuzimanje, katalog i analizu javnih savjetovanja s portala
[e-Savjetovanja](https://esavjetovanja.gov.hr).

Portal e-Savjetovanja je glavno mjesto na kojem građani, udruge i tvrtke
komentiraju nacrte zakona, strategija i planova prije donošenja. Komentari su
javni, ali ih portal prikazuje tek kad se klikne pojedini dio dokumenta i ne
nudi nikakav izvoz. Zato je teško odgovoriti na jednostavna pitanja: tko je
komentirao, koliko, na koje dijelove teksta i što je predložio.

Ovaj repozitorij preuzima cijelo savjetovanje u otvorene formate (JSONL,
Markdown i izvorni .docx), da se može čitati, pretraživati i analizirati.

## Preuzeta savjetovanja

| ID | Savjetovanje | Otvoreno | Komentara | Izvještaj |
|---|---|---|---:|---|
| [10346](https://esavjetovanja.gov.hr/Econ/10346) | Nacionalni plan za razvoj umjetne inteligencije za razdoblje do 2032. godine | 16.10. – 15.11.2026. | 79 | [pregled](data/savjetovanja/10346/README.md) |

Brojevi vrijede za trenutak preuzimanja (`scraped_at` u `meta.json`). Dok je
savjetovanje otvoreno, komentari i dalje stižu.

## Brzi početak

Potrebni su Python 3.11+, [uv](https://docs.astral.sh/uv/) i Google Chrome.

```bash
git clone https://github.com/domovinatv/esavjetovanja.git
cd esavjetovanja
uv sync

# preuzmi savjetovanje; ID je broj iz URL-a https://esavjetovanja.gov.hr/Econ/10346
uv run esavjetovanja scrape 10346

# izradi Markdown izvještaj: statistika, autori, poglavlja, svi komentari uz izvorni tekst
uv run esavjetovanja report 10346
```

Nemaš Chrome? Koristi Playwrightov Chromium:

```bash
uv run playwright install chromium
uv run esavjetovanja scrape 10346 --channel bundled
```

### Opcije

| Naredba | Opcija | Opis |
|---|---|---|
| `scrape` | `--headed` | prikaži browser dok radi |
| `scrape` | `--no-documents` | ne preuzimaj .docx/.pdf priloge |
| `scrape` | `--channel` | `chrome` (zadano), `msedge` ili `bundled` |
| sve | `--data-dir` | korijen za podatke (zadano `data/`) |

Za prijavu na portal nije potreban račun. Svi podaci koje alat preuzima javno
su vidljivi i bez prijave.

## Format podataka

```
data/savjetovanja/<id>/
├── meta.json        naslov, datumi, ukupni brojevi s portala, popis dokumenata
├── sections.jsonl   dijelovi dokumenta, jedan po retku
├── comments.jsonl   komentari, jedan po retku
├── documents/       dokument savjetovanja i ostali prilozi (.docx)
└── README.md        izvještaj (esavjetovanja report)
```

**`sections.jsonl`**

| Polje | Opis |
|---|---|
| `id` | ID dijela na portalu |
| `order` | redni broj u dokumentu |
| `level` | razina naslova (0 = naslov dokumenta, 1 = poglavlje, 2 = potpoglavlje …) |
| `heading` | naslov dijela |
| `heading_path` | putanja naslova, npr. `["4. …", "4.3. …", "4.3.1. …"]` |
| `text` | tekst dijela bez naslova |
| `html` | izvorni HTML dijela |
| `comment_counts` | `general`, `addition`, `total` prema portalu |

**`comments.jsonl`**

| Polje | Opis |
|---|---|
| `id` | stabilni hash (dio, autor, vrijeme, tekst); portal ne izlaže ID komentara |
| `section_id`, `section_order`, `section_heading_path` | na koji se dio komentar odnosi |
| `author` | autor onako kako ga portal prikazuje |
| `type` | `Opći komentar` ili `Nadopuna teksta` (prijedlog izmjene teksta) |
| `datetime` | vrijeme objave, `YYYY-MM-DDTHH:MM` (lokalno vrijeme portala) |
| `text`, `html` | tekst komentara |
| `likes`, `dislikes`, `popularity` | reakcije korisnika |
| `extra` | ostali blokovi u komentaru, npr. odgovor nositelja nakon zatvaranja |

Na kraju svakog preuzimanja alat usporedi broj preuzetih komentara s brojem
koji navodi portal i upozori ako se razlikuju.

## Kako radi

e-Savjetovanja je [Blazor Server](https://learn.microsoft.com/aspnet/core/blazor/)
aplikacija. HTML koji vrati server je prazna ljuska, a sadržaj stiže preko
websocketa (SignalR). Zato običan HTTP zahtjev ne vrati ništa korisno.

Alat otvara stranicu u headless Chromeu (Playwright), čita sve dijelove
dokumenta, klikne svaki dio koji ima komentare, prođe kroz sve stranice
komentara i vrati se na popis. Dokumente preuzima istim gumbima kojima bi ih
preuzeo i korisnik.

Alat ne zaobilazi nikakvu zaštitu, ne prijavljuje se i radi jedan zahtjev za
drugim, otprilike brzinom kojom bi stranicu pregledavao čovjek.

## Plan

- [x] preuzimanje jednog savjetovanja: tekst, komentari, dokumenti
- [x] Markdown izvještaj po savjetovanju
- [ ] katalog svih savjetovanja (~9 300) s institucijom, stanjem i datumima
- [ ] objavljena izvješća o savjetovanju: prihvaćeni i odbijeni komentari s obrazloženjem
- [ ] analiza: teme, grupiranje sličnih komentara, sažetak po poglavlju, praćenje što je ušlo u konačni tekst

Prijedlozi i pull requestovi su dobrodošli, vidi [CONTRIBUTING.md](CONTRIBUTING.md).

## Napomena o podacima

Komentare portal javno objavljuje zajedno s imenom autora ili nazivom pravne
osobe. Repozitorij ih preuzima u istom obliku radi transparentnosti postupka
savjetovanja. Ako si autor komentara i imaš primjedbu, otvori issue.

Sadržaj dokumenata i komentara pripada izvornim autorima i tijelima javne
vlasti. Ovo nije službeni alat Vlade Republike Hrvatske.

## Licenca

Kod je pod [MIT licencom](LICENSE).
