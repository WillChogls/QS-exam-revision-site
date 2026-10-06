# SQA Revision

Personal revision site for SQA National 5, Higher and Advanced Higher: past
papers by level → subject → year → paper, coursework guidance, search, and a
placeholder AI tutor chat panel.

Styled with the "Exam Paper" theme in `static/css/style.css`, with light and dark
modes. Templates use semantic HTML with stable classes/IDs (`.paper-list`,
`.paper-card`, `#chat-panel`, `#chat-messages`, `#search-form`, …) that the CSS
targets.

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python seed.py          # builds revision.db from data/sqa_papers.json (wipes it if it exists)
flask --app app run     # http://127.0.0.1:5000
```

On macOS port 5000 may be taken by AirPlay Receiver; use `flask --app app run --port 5050`.

## Data

`data/sqa_papers.json` holds metadata for every subject in SQA's past paper
finder (N5, Higher, Advanced Higher, 2022–2026). Only metadata is stored; every
question paper, marking instruction, audio file and coursework document links
to sqa.org.uk.

- `python scrape_sqa.py` refreshes the JSON from sqa.org.uk (~190 requests, ~2 min).
  Run it when SQA publishes a new year, then `python seed.py`.
- `python seed.py` rebuilds `revision.db` from the JSON offline. It sorts each
  file into an exam paper, an extra for a paper (answer booklet, audio,
  transcript, map, data sheet), or a coursework document, and matches marking
  instructions to papers by name.

Known gaps: 71 papers have no marking instructions. Most are Gaelic-medium
papers (SQA publishes none separately) or 2026 papers not yet released. SQA
publishes no coursework deadlines or guidance text; the `coursework.description`
and `deadline` columns are there for you to fill in by hand.

### Updating the papers

The scrape never runs automatically, and the site makes no requests to SQA
while it's running. Run the scrape manually:

- once a year, in the autumn, when SQA publishes the new year's papers
- again later if that year's marking instructions weren't out yet

```sh
source .venv/bin/activate
python scrape_sqa.py    # rewrites data/sqa_papers.json (~2 min)
python seed.py          # rebuilds revision.db from it
git add data/sqa_papers.json && git commit -m "Update SQA papers"
```

`seed.py` prints how many papers still have no marking instructions. A drop
in that number means newly released MIs were picked up.

## Layout

```
app.py                       app factory, blueprint registration
models.py                    schema, LEVELS, query helpers
scrape_sqa.py                SQA past paper finder -> data/sqa_papers.json
seed.py                      data/sqa_papers.json -> revision.db
routes/browse.py             /, /<level>/, /<level>/<subject>/, /<level>/<subject>/<year>/, /paper/<id>
routes/coursework.py         /<level>/<subject>/coursework
routes/search.py             /search?level=&subject=&year=
templates/base.html          shared layout
templates/partials/          breadcrumbs, paper_card, chat_panel, settings_panel
static/css/style.css         "Exam Paper" theme; colour tokens on :root, dark overrides on [data-theme="dark"]
static/js/chat.js            chat panel behaviour
static/js/theme.js           Settings panel and light/dark switching
```

## Appearance

The Settings button in the header opens a panel with three options:
**System default**, **Light** and **Dark**. The choice is saved in
`localStorage` under `theme` (`"light"` or `"dark"`; no key means follow the
device). An inline script in `base.html` applies it before the page paints.
If storage is blocked, the choice still applies until you leave the page.

Fonts (Newsreader, IBM Plex Sans, IBM Plex Mono) load from Google Fonts. This is
the site's only external request; offline, the system fallback fonts are used.

## Chat panel

UI only, with no AI and no network requests. `getReply(message, context)` in
`static/js/chat.js` returns `"AI tutor coming soon."`. It is async, so it can be
replaced with a `fetch()` to a backend endpoint. `context` is
`{ level, subject, year, paper, paperId, question }` (`question` is `null` when
the question number box is blank), read from `data-*` attributes on `#chat-panel`. Chat history is
in memory only and clears on reload.
