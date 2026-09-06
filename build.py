#!/usr/bin/env python3
"""Build the RAS practice site.

    python build.py            ->  writes docs/

Substitutes bank.json into app_template.html's __BANK__ placeholder, wraps the
result in a complete HTML document, and writes the small handful of files a
static host needs. The output in docs/ is the whole website; docs/index.html
also opens fine by double-clicking it.
"""
import hashlib, json, os, re, shutil

from pypdf import PdfReader, PdfWriter

HERE = os.path.dirname(os.path.abspath(__file__))
# GitHub Pages publishes straight from this folder: repo Settings -> Pages ->
# Deploy from a branch -> main / docs. No Actions, no second branch.
SITE = os.path.join(HERE, "docs")

TITLE = "RAS Prelims Drill Room"
DESC  = ("5,395 practice questions for the RAS Prelims 2026, across 111 chapters "
         "in 12 subjects, with full-length mocks scored the way RPSC scores them.")

NOTES_DIR = os.path.join(HERE, "Handwritten Notes")
PDF_OUT   = os.path.join("pdf")          # relative to SITE, and to the page

_norm = lambda t: "".join((t or "").split())   # collapse the letter-spacing the notes are typeset with

def split_notes(bank):
    """Cut each subject's notes PDF into one PDF per chapter.

    The notes are a single file per subject, but the app lists chapters, and a
    chapter is what someone actually wants to read. Page anchors (#page=N) are
    ignored by most phone PDF viewers, so each chapter gets its own file: it
    opens reliably, and it is ~200 KB rather than the ~2.5 MB of a whole subject.

    A chapter starts on the page whose text begins with its code — "RH01..." —
    which is how the notes are typeset. Returns {chapterCode: {href, pages, kb}}.
    """
    if not os.path.isdir(NOTES_DIR):
        return {}, set()

    by_code = {s["code"]: s["chapters"] for s in bank["subjects"]}
    docs, produced = {}, set()

    for name in sorted(os.listdir(NOTES_DIR)):
        if not (name.startswith("RASNotes_") and name.lower().endswith(".pdf")):
            continue
        subject = name[len("RASNotes_"):][:2]
        chapters = [c["code"] for c in by_code.get(subject, [])]
        if not chapters:
            continue

        src = os.path.join(NOTES_DIR, name)
        reader = PdfReader(src)

        starts = {}
        for i, page in enumerate(reader.pages):
            head = _norm(page.extract_text())
            for ch in chapters:
                if ch not in starts and head.startswith(ch):
                    starts[ch] = i
        missing = [c for c in chapters if c not in starts]
        if missing:
            print(f"  ! {subject}: no start page found for {', '.join(missing)} — skipped")

        found = sorted(starts.items(), key=lambda kv: kv[1])
        for n, (ch, first) in enumerate(found):
            last = found[n + 1][1] if n + 1 < len(found) else len(reader.pages)
            rel = f"{PDF_OUT}/{subject}/{ch}.pdf"
            dst = os.path.join(SITE, rel.replace("/", os.sep))
            produced.add(os.path.normpath(dst))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if not (os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src)):
                w = PdfWriter()
                for page in reader.pages[first:last]:
                    w.add_page(page)
                with open(dst, "wb") as fh:
                    w.write(fh)
            docs[ch] = {"href": rel,
                        "pages": last - first,
                        "kb": round(os.path.getsize(dst) / 1024)}
    return docs, produced

tpl  = open(os.path.join(HERE, "app_template.html"), encoding="utf-8").read()
bank = json.load(open(os.path.join(HERE, "bank.json"), encoding="utf-8"))
docs, wanted = split_notes(bank)

# "</" must be escaped or a "</script>" inside any question string would close the tag early
payload = json.dumps(bank, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
# __DOCS__ first, while the template is still small
page = tpl.replace("__DOCS__", json.dumps(docs, ensure_ascii=False)).replace("__BANK__", payload)

# the template is authored as document content; everything through </style> belongs in <head>
cut = page.index("</style>") + len("</style>")
head, body = page[:cut], page[cut:]

doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{DESC}">
<meta name="theme-color" content="#FFFFFF" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#171B24" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="RAS Drill">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:type" content="website">
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="icon" href="icon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
{head}
</head>
<body>
{body}
</body>
</html>
"""

os.makedirs(SITE, exist_ok=True)
index = os.path.join(SITE, "index.html")
open(index, "w", encoding="utf-8").write(doc)

# the cache name has to change whenever the page does, or phones keep serving the old one
ver = hashlib.sha256(doc.encode("utf-8")).hexdigest()[:12]
sw = open(os.path.join(HERE, "sw_template.js"), encoding="utf-8").read().replace("__VER__", ver)
open(os.path.join(SITE, "sw.js"), "w", encoding="utf-8").write(sw)

open(os.path.join(SITE, "manifest.webmanifest"), "w", encoding="utf-8").write(json.dumps({
    "name": TITLE,
    "short_name": "RAS Drill",
    "description": DESC,
    "start_url": ".",
    "scope": ".",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#F5F6F8",
    "theme_color": "#2B3F8F",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        {"src": "icon.svg", "sizes": "any", "type": "image/svg+xml"},
    ],
}, indent=2))

for f in os.listdir(os.path.join(HERE, "assets")):
    shutil.copy2(os.path.join(HERE, "assets", f), os.path.join(SITE, f))

# Drop anything left over from an earlier build — renamed chapters, the old
# question-bank folder — so docs/ only ever holds what this build produced.
# Guarded: with the notes folder missing there is nothing to prune *against*,
# and pruning would silently delete every chapter PDF the site is serving.
pdf_root = os.path.join(SITE, PDF_OUT)
for root, _, files in (os.walk(pdf_root, topdown=False) if wanted else []):
    for f in files:
        path = os.path.normpath(os.path.join(root, f))
        if path not in wanted:
            os.remove(path)
    if not os.listdir(root):
        os.rmdir(root)
if not wanted:
    print("  ! 'Handwritten Notes' not found — left docs/pdf/ untouched")

# GitHub Pages runs Jekyll otherwise, which strips files it does not recognise
open(os.path.join(SITE, ".nojekyll"), "w").close()

n = sum(len(c["questions"]) for s in bank["subjects"] for c in s["chapters"])
mb = sum(os.path.getsize(os.path.join(r, f))
         for r, _, fs in os.walk(SITE) for f in fs) / 1e6
print(f"built {SITE}{os.sep}  —  {n} questions, index.html {os.path.getsize(index)/1e6:.2f} MB, "
      f"{len(docs)} chapter PDFs, site {mb:.1f} MB, cache {ver}")
