# Drugo AI savjetovanje (10347) i inkrementalni snapshot (2026-11-02)

## Savjetovanja

Oba je otvorio MPUDT, oba traju 16.10.–15.11.2026., a izvješće se očekuje 16.12.2026.:

- **10346**: Nacionalni plan za razvoj UI do 2032.
- **10347**: Akcijski plan za provedbu NPUI do 2028. Ima 49 dijelova (33 mjere), oko 195k znakova.

Staro savjetovanje 8742 (obrazac za zakon o provedbi AI Acta, prosinac 2024.) je zatvoreno.

ID se nađe filtrom na naslovnoj stranici portala: polje `fluent-text-field[placeholder='Unesite tekst']`
i gumb „Filtriraj”. Redci tablice nemaju `<a>`; URL se dobije klikom na `.EconTitle`. Playwrightov
`click()` na gumb ne prolazi jer ga prekriva `filter-row-only`, pa klik ide kroz JS (`el.click()`).

## Inkrementalni snapshot (10346)

Od 20.10. su stigla 6 nova komentara (79 → 85), a `otisak_teksta` je ostao isti. Postupak:

1. Puni scrape (ne `--no-documents`), zatim usporedba `comments.jsonl` s `git show HEAD:` verzijom
   po `id`.
2. Kopirati `dijelovi/` i `dokument.json` iz prethodnog snapshota u novu mapu, dopisati analizu samo
   novih komentara u odgovarajuće retke i osvježiti `komentari_sinteza`.
3. `esavjetovanja merge <id> <snapshot> --base <prethodni>`. U `snapshot.json` se upiše `osnova`.

Stranica uspoređuje zadnja dva snapshota: komentar kojeg nema u analizi prethodnog snapshota dobiva
oznaku „novo” i filtar „Novi komentari”. U kartici ocjene piše razlika u broju komentara, u otisku
teksta i u ocjeni.

Komentar koji je samo poveznica na vanjski dokument (Google Docs) dobiva `utemeljenost: null`, a
predložak tada prikazuje „—”.

## Analiza 10347

Prompt je u `analiza/prompt.md`, zajedno s varijablama. Pokrenuta su 4 Opus agenta (`effort: medium`),
skupine po `order`: A 1–18, B 19–29, C 30–39, D 40–49, svaka oko 41–56k znakova. Agent C i agent D
potrošili su oko 93–96k tokena i 8 poziva alata, za otprilike 3 minute, što je bitno manje nego na
10346 (`effort: high`, oko 125k tokena po agentu).

## Stranica

- `/` je popis savjetovanja (`templates/landing.html`), a `/<id>/` je stranica pojedinog savjetovanja.
- Stari linkovi iz vremena kad je na `/` bilo samo 10346 i dalje rade: `/#s<id>` JS preusmjerava na
  `/10346/#s<id>`, a `/dokumenti/*` preusmjerava `_redirects` (301).
- `site` briše cijeli `site/` prije gradnje.

## Otvoreno

- Oba savjetovanja zatvaraju se 15.11.2026. Prije toga treba ih još jednom preuzeti
  (`scrape 10346 10347`), jer komentari obično stižu pred zatvaranje. Za 10346 zatim slijedi
  inkrementalni snapshot (postupak gore); za 10347 isto, s prvim snapshotom kao `--base`.
- Nalaze agenata za 10347 provjerio sam samo uzorkom: mjera 12 (10 naspram 5 mil.) i mjera 3
  (15,99 mil. za BrAIn naspram 8,8 mil.) odgovaraju tekstu. Ostale tvrdnje iz
  `dokument.json` / `gdje_komentirati` treba provjeriti u izvorniku prije nego što se citiraju
  u komentaru na portalu.
- Pomoć u pisanju komentara za mjesta iz `gdje_komentirati` (oba dokumenta). Komentari na
  portal idu samo stručni; tako je dogovoreno na sjednici Savjeta MOST-a 2.11.
- Komentar Velibora Božića na 10346 je samo poveznica na Google Doc, pa nije ocijenjen.
- Na `/` ostaje i stari `/dokumenti/*` iz prijašnjeg deploya (vraća 200, a ne 301 iz
  `_redirects`); nije štetno.

## Vezani dokumenti

- [2026-10-20-portal-analiza-deploy.md](2026-10-20-portal-analiza-deploy.md): portal, prva analiza, deploy
