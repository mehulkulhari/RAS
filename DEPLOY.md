# Putting it online

The site is the `docs/` folder. GitHub Pages serves it directly — free, permanent,
no card, and anyone with the link can open it without signing in.

## One-time setup

**1. Make an empty repo on GitHub.**
Go to <https://github.com/new>. Name it something short — `ras-drill` works, and the
name becomes part of the URL. Set it to **Public** (Pages needs that on a free account).
Do **not** tick "Add a README", "Add .gitignore" or "Choose a license" — the repo has to
start empty, or the first push is rejected.

**2. Push this folder.** Run these here, with `YOU` and `REPO` replaced:

```bash
git remote add origin https://github.com/YOU/REPO.git
git push -u origin main
```

It will ask for a username and password. **The password box wants a Personal Access
Token, not your GitHub password** — GitHub stopped accepting passwords over git in 2021.
Make one at <https://github.com/settings/tokens> → *Generate new token (classic)* → tick
the **repo** scope → copy it, and paste that as the password.

If you would rather not deal with tokens: install [GitHub Desktop](https://desktop.github.com),
choose *Add → Add Existing Repository*, point it at this folder, and press *Publish*.

The push moves roughly 45 MB, so give it a minute.

**3. Turn Pages on.** In the repo: **Settings → Pages**. Under *Build and deployment*
set **Source** to `Deploy from a branch`, **Branch** to `main`, and the folder to
`/docs`. Save.

Wait a minute or two, then open:

    https://YOU.github.io/REPO/

That is the link. Send it to anyone.

## On the phone

Open the link, then *Add to Home Screen* — the Share menu on iPhone, the ⋮ menu on
Android. It gets its own icon and opens without browser chrome, like an app. After the
first visit it loads from the phone itself, so it works with no signal and costs no data.

## Pushing an update

```bash
python build.py
git add -A
git commit -m "update questions"
git push
```

Live in under a minute. Phones pick it up on the *second* launch after that — the first
one fetches the new version in the background, the next one runs it.

## If something goes wrong

**The push is rejected with "updates were rejected".** The GitHub repo was not empty.
Run `git pull --rebase origin main`, then push again.

**Pages says "There isn't a GitHub Pages site here".** Normal for the first few minutes
after the first deploy. Give it five.

**404 on the PDFs.** Check they were committed — `git ls-files docs/pdf` should list 24
files.

**An old version keeps loading on the phone.** That is the offline cache doing its job.
Launch it twice, or pull down to refresh.
