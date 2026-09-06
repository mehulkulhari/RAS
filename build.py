#!/usr/bin/env python3
"""Build the RAS practice site.

    python build.py            ->  writes docs/

Substitutes bank.json into app_template.html's __BANK__ placeholder, wraps the
result in a complete HTML document, and writes the small handful of files a
static host needs. The output in docs/ is the whole website; docs/index.html
also opens fine by double-clicking it.
"""
import hashlib, json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
# GitHub Pages publishes straight from this folder: repo Settings -> Pages ->
# Deploy from a branch -> main / docs. No Actions, no second branch.
SITE = os.path.join(HERE, "docs")

TITLE = "RAS Prelims Drill Room"
DESC  = ("5,395 practice questions for the RAS Prelims 2026, across 111 chapters "
         "in 12 subjects, with full-length mocks scored the way RPSC scores them.")

# The two PDF folders are named by subject: RASNotes_<CODE>_... and RAS2026_<CODE>_...
PDF_SETS = [("Handwritten Notes", "RASNotes_", "notes", "Handwritten notes"),
            ("Question Bank",     "RAS2026_",  "bank",  "Question bank")]

def collect_pdfs():
    """Map subject code -> [{kind, file, href, mb}], plus the list of files to copy."""
    docs, files = {}, []
    for folder, prefix, slug, label in PDF_SETS:
        src = os.path.join(HERE, folder)
        if not os.path.isdir(src):
            continue
        for name in sorted(os.listdir(src)):
            if not (name.startswith(prefix) and name.lower().endswith(".pdf")):
                continue
            code = name[len(prefix):len(prefix) + 2]
            path = os.path.join(src, name)
            docs.setdefault(code, []).append({
                "kind": label,
                "file": name,
                "href": f"pdf/{slug}/{name}",
                "mb": f"{os.path.getsize(path) / 1e6:.1f}",
            })
            files.append((path, os.path.join(SITE, "pdf", slug, name)))
    order = [label for *_, label in PDF_SETS]        # notes before question bank
    for code in docs:
        docs[code].sort(key=lambda d: order.index(d["kind"]))
    return docs, files

tpl  = open(os.path.join(HERE, "app_template.html"), encoding="utf-8").read()
bank = json.load(open(os.path.join(HERE, "bank.json"), encoding="utf-8"))
docs, pdf_files = collect_pdfs()

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

# ~34 MB of PDFs: only copy the ones that actually changed, so a rebuild stays quick
copied = 0
for src, dst in pdf_files:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if (not os.path.exists(dst)
            or os.path.getsize(dst) != os.path.getsize(src)
            or os.path.getmtime(dst) < os.path.getmtime(src)):
        shutil.copy2(src, dst)
        copied += 1

# GitHub Pages runs Jekyll otherwise, which strips files it does not recognise
open(os.path.join(SITE, ".nojekyll"), "w").close()

n = sum(len(c["questions"]) for s in bank["subjects"] for c in s["chapters"])
mb = sum(os.path.getsize(os.path.join(r, f))
         for r, _, fs in os.walk(SITE) for f in fs) / 1e6
print(f"built {SITE}{os.sep}  —  {n} questions, index.html {os.path.getsize(index)/1e6:.2f} MB, "
      f"{len(pdf_files)} PDFs ({copied} copied), site {mb:.1f} MB, cache {ver}")
