# Go-Live Checklist — Santa Fe Half Marathon

Everything built and tested is ready. What's left needs your accounts (deploy,
DNS, file edits) — those are marked ⬜. Done items are ✅.

## What's already done ✅
- ✅ MCP server: 9 tools, 3 resources, 1 prompt — full test suite green
- ✅ Live results leaderboard widget with "Find my time" bib search
- ✅ Course elevation chart (real 6,992 → 7,330 → 6,956 ft, USATF 13.109 mi)
- ✅ Widgets recolored to your brand (--nm-gold / obsidian / turquoise)
- ✅ Real race data wired in (race 83604, event 1056101, official course facts)
- ✅ Photo registry (RunSignup + Drive + OneDrive) + curated Drive gallery
- ✅ Deploy configs: Render, Fly, VPS+Caddy — all validated
- ✅ One paste-block for your static site: combined_embed.html
- ✅ Verified live site is healthy (countdown works, course map loads)
- ✅ Freed disk space (removed /staging/6708)

## Remaining steps (your account) ⬜

### 1. Deploy the results server (~5 min)
- ⬜ Push this folder to a GitHub repo (see GITHUB_SETUP.md)
- ⬜ Render → New → Blueprint → pick the repo (reads render.yaml) → Apply
- ⬜ Note the URL, e.g. https://santa-fe-half-marathon.onrender.com
- ⬜ Open <that URL>/leaderboard to confirm it serves

### 2. Put the widgets on the site (~5 min)
- ⬜ HostGator cPanel → File Manager → public_html
- ⬜ Copy index.html → index-backup.html (one-click revert insurance)
- ⬜ Edit index.html, paste combined_embed.html after the Course Profile section
- ⬜ Replace RACE_HOST (one spot) with your Render host
- ⬜ Save. Hard-refresh the site (Ctrl/Cmd+Shift+R)
- ⬜ Optional: delete the leftover "Save your certified map…" caption line

### 3. (Optional) Turn on live registration lookup
- ⬜ In Render → Environment: REGISTRATION_BACKEND=runsignup + your
     RUNSIGNUP_API_KEY / _SECRET (race_id 83604, event_id 1056101 pre-filled)
- ⬜ Have the race director enable API access on the race
     (Results/leaderboard already work with no key — this is only for the
     registration-status tool.)

## Race-week checklist
- ⬜ Upgrade Render to a paid tier for race weekend so it stays warm (free
     tier sleeps when idle; first hit after idle is slow)
- ⬜ Confirm 2026 results flow: on race day the leaderboard auto-fills
     (event 1056101). Nothing to change — it's already mapped.
- ⬜ Keep an eye on HostGator disk usage before uploading race-day photos

## Reference files
- DEPLOY.md — host-by-host deploy steps
- GITHUB_SETUP.md — first push to a repo
- EMBED_ON_YOUR_SITE.md — static-site embed details
- combined_embed.html — the paste-block (results + course chart)
- README.md — full server documentation
