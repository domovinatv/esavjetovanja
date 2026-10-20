# esavjetovanja

Otvoreni alati za preuzimanje, katalog i analizu javnih savjetovanja s portala
[e-Savjetovanja](https://esavjetovanja.gov.hr).

Portal e-Savjetovanja je glavno mjesto na kojem građani, udruge i tvrtke
komentiraju nacrte zakona, strategija i planova prije donošenja. Komentari su
javni, ali ih portal prikazuje tek kad se klikne pojedini dio dokumenta i ne
nudi nikakav izvoz. Zato je teško odgovoriti na jednostavna pitanja: tko je
komentirao, koliko, na koje dijelove teksta i što je predložio.

Ovaj repozitorij preuzima cijelo savjetovanje u otvorene formate (JSONL,
Markdown i izvorni .docx), na njega pušta jezični model da ga analizira dio po
dio, i sve to objavljuje kao jednu stranicu koja se može čitati:
**[esavjetovanje.domovina.ai](https://esavjetovanje.domovina.ai)**.

Na stranici je za svaki dio dokumenta:

- sažetak jednostavnim jezikom: što taj dio stvarno kaže
- ocjena 0–100 po pet kriterija (konkretnost, mjerljivost, utemeljenost, provedivost, jasnoća)
- obveze iz teksta (što, tko, do kada, koliko novca), slabosti i otvorena pitanja
- izvorni tekst
- javni komentari, svaki s procjenom modela koliko je primjedba utemeljena

Na vrhu je sinteza cijelog dokumenta, karta dokumenta obojena po ocjenama i
popis mjesta gdje bi novi komentar najviše pomogao.

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

# izgradi stranicu u site/ (uzima zadnji snapshot analize) i objavi je na Cloudflare
uv run esavjetovanja site 10346
npx wrangler deploy
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
├── README.md        izvještaj (esavjetovanja report)
└── analize/
    └── <datum>_<model>/     jedan snapshot analize
        ├── dijelovi/*.jsonl  izlaz modela po skupinama poglavlja
        ├── analiza.jsonl     spojeno, s izračunatom ukupnom ocjenom
        ├── dokument.json     sinteza cijelog dokumenta
        └── snapshot.json     model, vrijeme, broj komentara, otisak teksta, prosjeci
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

## Analiza

Pravila po kojima model ocjenjuje opisana su u
[analiza/METODOLOGIJA.md](analiza/METODOLOGIJA.md): jedinica analize, kriteriji,
sidra ljestvice 0–100 i ograničenja. Ukupnu ocjenu računa kod (prosjek
kriterija), ne model.

Svaka analiza je **snapshot**: zna se koji ju je model izradio, kada, nad
koliko komentara i nad kojom verzijom teksta (otisak `otisak_teksta`). Kad
stignu novi komentari ili se tekst promijeni, radi se novi snapshot, a stari
ostaje u povijesti za usporedbu.

| Snapshot | Model | Komentara | Ocjena |
|---|---|---:|---:|
| [2026-10-20](data/savjetovanja/10346/analize/2026-10-20_claude-opus-5-5/) | claude-opus-5-5 | 79 | 44 |

Ocjene su mišljenje jezičnog modela, ne službena ocjena dokumenta. Mjerodavan
je izvorni tekst na portalu.

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
- [x] LLM analiza po dijelovima dokumenta, snapshot s modelom i vremenom
- [x] stranica esavjetovanje.domovina.ai
- [ ] novi snapshot kad stignu novi komentari, usporedba snapshota
- [ ] objavljeno izvješće o savjetovanju: prihvaćeni i odbijeni komentari s obrazloženjem
- [ ] usporedba nacrta i konačnog teksta: što je od komentara ušlo u dokument

Prijedlozi i pull requestovi su dobrodošli, vidi [CONTRIBUTING.md](CONTRIBUTING.md).

## Napomena o podacima

Komentare portal javno objavljuje zajedno s imenom autora ili nazivom pravne
osobe. Repozitorij ih preuzima u istom obliku radi transparentnosti postupka
savjetovanja. Ako si autor komentara i imaš primjedbu, otvori issue.

Sadržaj dokumenata i komentara pripada izvornim autorima i tijelima javne
vlasti. Ovo nije službeni alat Vlade Republike Hrvatske.

## Licenca

Kod je pod [MIT licencom](LICENSE).
