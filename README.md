# RAS Prelims 2026 — Practice site

5,395 questions across 111 chapters in 12 subjects, full-length mocks scored the way
RPSC scores them, chapter fact sheets, and the handwritten class notes split into one
PDF per chapter. One page, no framework, no server. Works offline once loaded.

## The website

`docs/` **is** the website. GitHub Pages publishes it straight from that folder, so the
public URL is:

    https://<your-github-username>.github.io/<repo-name>/

Anyone with that link can open it — no account, no sign-in. `DEPLOY.md` has the one-time
setup and how to push an update.

## Files

| File | What it is |
|---|---|
| `app_template.html` | **The source.** All the HTML, CSS and JavaScript. Two placeholders, `__BANK__` and `__DOCS__`. |
| `bank.json` | **The data.** 5,395 questions, 3.5 MB. |
| `sw_template.js` | The offline cache. `__VER__` is filled in per build. |
| `assets/` | Icons — the tab favicon, the home-screen icons, the maskable Android one. |
| `Handwritten Notes/` | The 12 source PDFs, one per subject. `build.py` cuts these into per-chapter files. |
| `Question Bank/` | Not used by the site — the practice questions come from `bank.json`. Kept as reference. |
| `build.py` | Assembles all of the above into `docs/`. |
| `docs/` | **The built site.** Everything a host needs and nothing it does not. |

## Rebuilding

    python build.py

Needs `pypdf` — `pip install pypdf` — to cut the notes into chapters. That step reads
every page of every notes PDF, so a full build takes a couple of minutes; chapter files
already present and newer than their source are left alone, so later builds are quick.

Edit `app_template.html` to change how it looks or behaves, `bank.json` to change
questions, or replace a PDF in `Handwritten Notes/` to update notes — then run the
script. It rewrites `docs/`.

Commit and push afterwards, or the live site keeps serving the old build.

## Data shape

```jsonc
{
  "meta": { "title": "...", "exam_date": "2026-12-06", "built": "..." },
  "subjects": [{
    "code": "RH",                       // 2-letter subject code
    "subject": "Rajasthan History, Art & Culture",
    "chapters": [{
      "code": "RH01",                   // chapter code, sorts naturally
      "title": "Pre-historic and Proto-historic Sites of Rajasthan",
      "factsheet": ["one-line must-know fact", "..."],
      "questions": [{
        "q":    "question stem; a newline escape is a real line break for statement types",
        "opts": ["A", "B", "C", "D"],   // always exactly four
        "ans":  1,                      // 0-based index into opts
        "exp":  "why the answer is right, plus one adjacent fact",
        "diff": "E",                    // E easy | M moderate | H hard
        "type": "direct",               // direct|statement|match|negative|order|ar
        "pyq":  "RAS Pre 2021",         // or null
        "repeat": true,                 // optional: asked in 2+ papers
        "tags": ["Ahar", "Chalcolithic"],
        "id":   1                       // unique across the whole bank
      }]
    }]
  }]
}
```

To add a question, append an object to any chapter's `questions` array and rerun
`build.py`. `id` only needs to be unique — the app uses it as the key for saved
progress, so avoid renumbering existing questions or you will orphan saved answers.

## How the notes are split

Each file in `Handwritten Notes/` covers a whole subject, but the Notes tab lists
chapters, because a chapter is what someone actually sits down to read.

`build.py` finds where each chapter starts by looking for the page whose text begins
with the chapter's code — the notes are typeset with `RH01` as the heading of the page
that opens that chapter — and writes pages up to the next chapter's start as
`docs/pdf/RH/RH01.pdf`. All 111 chapters are found this way; if one ever isn't, the
build says so by name and skips it rather than producing a wrong file.

Splitting rather than linking to `#page=` matters on a phone: most mobile PDF viewers
ignore page anchors, and a chapter file is ~400 KB against ~3 MB for a whole subject.
The cost is that each chapter re-embeds the notes' fonts, so the split set is about 1.4x
the size of the originals on disk. Nobody downloads more than one chapter at a time,
so that trade is worth it.

## How the app is put together

`app_template.html` reads top to bottom:

1. **`<style>`** — design tokens first (`:root`, then the two dark-theme blocks), then
   components, then the phone layout. Type is IBM Plex: Serif for question stems, Sans
   for the interface, Mono for numbers, codes and the timer.
2. **Markup** — masthead, a left rail for the subject/chapter tree, and one `#view`
   container that every screen renders into.
3. **`<script>`** — plain JavaScript, no dependencies:
   - `BANK` and `DOCS` — the injected data. `CH` indexes chapters by code, `ALLQ`
     flattens every question.
   - `store` — `{ seen: { questionId: 1|0 }, mock: {...} }`. `1` correct, `0` wrong.
   - `SCREENS` — one render function per tab, each rebuilding `#view` from scratch.
     No virtual DOM, no diffing.
   - `WEIGHT` — the real RAS subject weightage, averaged over the 2013–2024 papers.
     `composeMock()` draws a 150-question paper against it, so every mock has the same
     subject mix as the actual exam.
   - Marking is RPSC's: 200/150 marks a question, minus one third of that for a wrong answer.
   - `--mh` is set from the masthead's measured height, because on a phone it wraps to
     two rows and the chapter drawer has to start below whatever height that turns out to be.

## Keyboard shortcuts (practice mode)

`1`–`4` pick an option · `Enter` or `→` next · `←` previous

## Notes

- **Progress is per-device.** It lives in `localStorage` under `ras2026.v1`, so the phone
  and the laptop each keep their own. Clearing site data resets it. There is no account
  and no server — which is the same reason anyone can open the link without signing in.
- **The site is public.** Anyone with the URL can read every question and download every
  PDF. Don't put anything in it you would not hand to a stranger.
- **It works offline.** A service worker caches the page and its fonts on the first visit,
  so afterwards it opens with no signal and costs no data. The chapter PDFs are deliberately
  left out of that cache — 51 MB is too much to put on someone's phone without asking — so
  reading notes needs a connection, while the questions do not.
- An update reaches a phone on the *second* launch after you push: the first fetches the
  new version in the background, the next one runs it.
