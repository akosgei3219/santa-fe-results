# Getting this into a GitHub repo

From inside this folder, on your own machine (needs git + a GitHub account):

```bash
git init
git add .
git commit -m "Santa Fe Half Marathon MCP server"
```

Then create an empty repo on github.com (no README/…gitignore — this folder has
them), copy its URL, and:

```bash
git branch -M main
git remote add origin https://github.com/<you>/santa-fe-half-marathon.git
git push -u origin main
```

That's the repo Render/Fly point at (see DEPLOY.md). `.gitignore` already keeps
`.env`, `course.gpx`, and caches out of the commit, so no secrets get pushed.

Tip: double-check nothing sensitive is staged before the first commit:

```bash
git status            # .env and course.gpx should NOT appear
```
