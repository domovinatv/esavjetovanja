# Portal e-Savjetovanja, LLM analiza i deploy (2026-10-20)

Bilješke iz prve sesije: što bi sljedeći prolaz morao ponovno otkriti.

## Portal

- esavjetovanja.gov.hr je **Blazor Server** (SignalR websocket). `curl` vrati
  praznu ljusku; nema JSON API-ja ni izvoza. Jedini put je pravi browser
  (Playwright, `channel="chrome"`; Playwrightov bundled Chromium na ovom stroju
  nije bio instaliran).
- Komentari se pojave tek nakon klika na `#section-<id>`; povratak gumbom
  „Natrag na savjetovanje". Komentari su paginirani Syncfusion pagerom
  (`.e-next:not(.e-disable)`); na 10346 nijedan dio nije imao više od jedne stranice,
  pa paginacija **nije stvarno testirana**.
- Glavni dokument se preuzima kao `data:` URL download (Playwright `expect_download`
  radi), ostali kroz „Ostali dokumenti" → `fluent-button[title='Preuzmi dokument']`.
- CSS klasa `section-heading-level-N` je **netočna** (gotovo sve je 1). Razina se
  čita iz prvog elementa u `.section-content`: `h1..h6`, a `p.section-title` = 0.
- Prijava (NIAS) ne otkriva dodatne podatke, samo radnje: Dodaj komentar,
  like/dislike, Istraživanja (prazno), Obavijesti. Prijavljen korisnik dobije
  **OIB u URL-u** naslovne stranice; paziti da ne završi u logovima/datotekama.
- Katalog: ~9 330 savjetovanja, tablica bez linkova. Korisnik **ne želi** katalog;
  fokus je samo 10346.

## Zamka u scraperu

`scrape --no-documents` prepiše `meta.json` s praznim `documents`, iako .docx
datoteke ostaju na disku. Prije commita uvijek puni scrape (ili popraviti da
zadrži stari popis).

## Analiza (snapshot 2026-10-20_claude-opus-5-5)

- Ulaz je razrezan na 4 skupine poglavlja (A: naslov–2, B: 3, C: 4, D: 5–7 +
  pojmovnik), svaka ~50–100k znakova; 4 Opus agenta, effort high, ~500k
  subagent tokena ukupno, 4,5–10,5 min po agentu. Upute i shema: vidi
  `analiza/METODOLOGIJA.md`; prompt agenta je bio u scratchpadu, shema je
  dokumentirana kroz polja u `analiza.jsonl`.
- `dokument.json` (sinteza) napisao je glavni model ručno iz spojenih rezultata.
- Rezultat: 44/100 težinski, mjerljivost 19, provedivost 25, jasnoća 65.

## Deploy

- Cloudflare Worker `esavjetovanje`, samo static assets iz `site/`, custom domain
  `esavjetovanje.domovina.ai`. Zona domovina.ai je na računu **D.O.M.**
  (`account_id` u `wrangler.jsonc`); bez njega wrangler pita za račun i padne.
- `site/` je u `.gitignore`; gradi se `uv run esavjetovanja site 10346`.

## Otvoreno

- Postupak za novi snapshot: re-scrape, analizirati samo nove komentare /
  promijenjene dijelove (usporedba `otisak_teksta`), diff prema prethodnom
  snapshotu, prikaz povijesti na stranici.
- Pomoć korisniku u pisanju vlastitih komentara (popis `gdje_komentirati`).
- Prompt za agente premjestiti u repo (`analiza/prompt.md`) radi ponovljivosti.
