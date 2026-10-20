# Metodologija analize (verzija 1)

Analizu radi jezični model (LLM) i ona je **mišljenje modela u jednom trenutku**,
a ne službena ocjena. Svaki snapshot bilježi model, datum, broj komentara i
otisak (hash) teksta dokumenta, tako da se analize mogu ponoviti, usporediti
kroz vrijeme i osporiti.

## Jedinica analize

Jedinica je **dio dokumenta** onako kako ga portal e-Savjetovanja dijeli
(naslov + tekst ispod njega, do sljedećeg naslova). Na te dijelove se vežu i
komentari na portalu.

## Što model radi za svaki dio

1. **Sažetak** jednostavnim jezikom: što ovaj dio stvarno kaže, u 1–3 rečenice.
2. **Vrsta dijela**: `uvod`, `analiza_stanja`, `vizija`, `cilj`, `prioritet`,
   `mjera`, `pokazatelji`, `podrucje_primjene`, `financije`, `upravljanje`,
   `pojmovnik`, `pomocni` (sadržaj, kratice).
3. **Obveze**: konkretna obećanja iz teksta (što, tko, do kada, koliko novca),
   samo ako ih tekst stvarno navodi.
4. **Ocjene 0–100** po kriterijima ispod. Kriterij koji za tu vrstu dijela nema
   smisla dobiva `null` (npr. analiza stanja ne mora imati rokove).
5. **Slabosti** i **otvorena pitanja**: što nedostaje da bi tekst bio provediv i
   provjerljiv.
6. **Komentari**: za svaki komentar vrsta, tema, kratki sažetak, procjena
   koliko je primjedba utemeljena u odnosu na tekst (0–100) i kratko
   obrazloženje modela.

## Kriteriji

| Kriterij | Pitanje |
|---|---|
| `konkretnost` | Govori li tekst što će se točno napraviti, ili samo smjer i namjeru? |
| `mjerljivost` | Postoje li pokazatelji, polazne i ciljne vrijednosti po kojima se može provjeriti uspjeh? |
| `utemeljenost` | Jesu li tvrdnje potkrijepljene podacima, izvorima, analizom? |
| `provedivost` | Jesu li navedeni nositelj, rok, sredstva i redoslijed; je li to realno? |
| `jasnoca` | Može li ga razumjeti obrazovan čitatelj koji nije stručnjak, bez praznih fraza? |

**Ukupna ocjena** je aritmetička sredina kriterija koji nisu `null`,
zaokružena na cijeli broj. Računa je kod, ne model.

### Sidra ljestvice

| Raspon | Značenje |
|---|---|
| 0–20 | deklarativno: fraze bez sadržaja koji se može provjeriti |
| 21–40 | opći smjer, pokoji konkretan element |
| 41–60 | djelomično konkretno: neki nositelji, rokovi ili brojke, ali s rupama |
| 61–80 | konkretno: većina elemenata postoji, preostale rupe su manje |
| 81–100 | operativno: može se provesti i provjeriti bez dodatnih pretpostavki |

Ocjena opisuje **tekst**, ne temu ni namjeru. Strateški dokument je
po prirodi općenitiji od akcijskog plana; to je uračunato kroz `null` za
kriterije koji ne pripadaju vrsti dijela, ne kroz blaže ocjenjivanje.

## Vrste komentara

`kritika`, `prijedlog_izmjene` (nadopuna teksta), `podrska`, `pitanje`, `ostalo`.

Model ocjenjuje **sadržaj** primjedbe, ne autora. Ne nagađa tko stoji iza
komentara, ni kako je komentar nastao.

## Ograničenja

- Model može pogrešno razumjeti tekst ili propustiti kontekst izvan dokumenta.
- Ocjene između dijelova nisu savršeno usporedive; služe za orijentaciju, ne za rang listu.
- Analiza se ne ažurira sama: novi komentari znače novi snapshot.
