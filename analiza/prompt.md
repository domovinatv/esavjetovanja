# Prompt za analizu dijelova dokumenta (metodologija v1)

Ovaj prompt dobiva svaki agent koji analizira jednu skupinu dijelova jednog
savjetovanja. Varijable u `{vitičastim}` zagradama popunjava onaj tko pokreće
analizu. Pravila ocjenjivanja su u [METODOLOGIJA.md](METODOLOGIJA.md); ovdje su
samo upute za rad i oblik izlaza.

---

Analiziraš dio javnog savjetovanja s portala e-Savjetovanja:
**{naslov}** (ID {id}, {url}).

Radni direktorij: `{repo}`.

## Ulaz

- `data/savjetovanja/{id}/sections.jsonl`: dijelovi dokumenta. Tvoji su dijelovi
  s `order` od **{od}** do **{do}** (uključivo).
- `data/savjetovanja/{id}/comments.jsonl`: komentari; tvoji su oni čiji je
  `section_id` u tvojim dijelovima.
- `analiza/METODOLOGIJA.md`: kriteriji, sidra ljestvice 0–100, vrste dijelova i
  komentara. Pročitaj je prije ocjenjivanja i drži se je.

Čitaj ciljano: dijelove i komentare izvuci kratkom Python skriptom
(`python3 -I`) filtriranom po `order` / `section_id`, polje `text`, ne `html`.
Ne čitaj cijele datoteke i ne čitaj isti dio dvaput. Ako ti treba kontekst iz
ostatka dokumenta (npr. tablica mjera, financijski okvir), pogledaj samo
naslove (`heading`) i po potrebi jedan kratak isječak.

{kontekst}

## Izlaz

Zapiši **jedan JSON objekt po retku** za svaki svoj dio (i one bez teksta) u
`data/savjetovanja/{id}/analize/{snapshot}/dijelovi/{skupina}.jsonl`. Piši
postupno (dopisuj nakon svakih nekoliko dijelova), da rad ne propadne ako stane.

```json
{
  "section_id": 123,
  "vrsta": "mjera",
  "sazetak": "1–3 rečenice jednostavnim jezikom: što ovaj dio stvarno kaže.",
  "kljucne_tvrdnje": ["konkretne tvrdnje iz teksta, s brojkama gdje postoje"],
  "obveze": [{"sto": "...", "tko": "nositelj ili null", "do_kada": "rok ili null", "iznos": "iznos ili null"}],
  "ocjene": {"konkretnost": 0, "mjerljivost": 0, "utemeljenost": 0, "provedivost": 0, "jasnoca": 0},
  "obrazlozenje": "2–4 rečenice zašto takve ocjene, uz pozivanje na tekst.",
  "slabosti": ["što nedostaje da bi tekst bio provediv i provjerljiv"],
  "otvorena_pitanja": ["pitanja koja bi nositelj trebao odgovoriti"],
  "komentari": [{
    "comment_id": "id iz comments.jsonl",
    "vrsta": "kritika | prijedlog_izmjene | podrska | pitanje | ostalo",
    "tema": "kratko, 2–6 riječi",
    "sazetak": "1–2 rečenice",
    "utemeljenost": 0,
    "ocjena_modela": "2–3 rečenice: drži li primjedba vodu u odnosu na tekst i što bi prihvaćanje promijenilo."
  }],
  "komentari_sinteza": "1–2 rečenice o svim komentarima na taj dio, ili null ako ih nema."
}
```

Pravila:

- `obveze` samo ako ih tekst stvarno navodi; ništa ne izmišljaj. Nepoznato je `null`.
- Kriterij koji za vrstu dijela nema smisla je `null` (npr. pojmovnik, sadržaj,
  kratice, naslov bez teksta: sve `null`). Ukupnu ocjenu **ne računaš** ti.
- Svaki komentar s tvojih dijelova mora se pojaviti točno jednom.
- Ocjenjuješ sadržaj primjedbe, ne autora; ne nagađaš tko stoji iza komentara.
- Hrvatski standardni jezik, bez praznih fraza. Brojke i nazive prepiši točno.
- Na kraju provjeri: `python3 -I -c` koji učita tvoju datoteku, potvrdi da je
  svaki redak valjan JSON, da su pokriveni svi tvoji `section_id` i svi komentari.

Na kraju vrati kratko izvješće (do 15 redaka): broj dijelova, raspon ocjena,
tri najslabija i tri najjača dijela s razlogom, te 3–5 mjesta gdje bi novi
komentar građana najviše pomogao (section_id + zašto).
