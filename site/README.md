# santafehalfmarathon.com — site source

The full website as a single self-contained page: `index.html` plus the two
photos in `assets/`. No build step, no external scripts or fonts — everything
(styles, countdown, elevation chart, results embed) is inline, so it works
uploaded anywhere static files are served.

## What's on the page

- **Hero** — race name, date, finish-line photo, live countdown to the
  7:30 AM MDT gun on September 20, 2026, and Register CTAs (RunSignup race 83604).
- **Race Info** — start (La Tienda Plaza, Eldorado), finish (Railyard Park),
  packet pickup / expo at Old Warehouse 21, cutoff, start time.
- **Course** — the brand-matched SVG elevation profile (6,992 → 7,330 → 6,956 ft,
  13.109 USATF miles) rendered inline with hover tooltips and an accessible
  mile-by-mile table. No iframe or server needed for this section.
- **Live Results** — shows official-results links by default; flips to the live
  leaderboard iframe when a results host is configured (see below).
- **Photos** — the two repo photos plus links to the RunSignup galleries,
  Google Drive gallery, and the 2025 pro-photo OneDrive album.
- **Altitude tips**, register band, and footer.

## Go-live: one edit

When the results server (this repo, `python server.py http`) is deployed —
e.g. on Render per `../DEPLOY.md` — open `index.html` and set the one config
line near the top of the `<script>` block:

```js
const RESULTS_HOST = "santa-fe-half-marathon.onrender.com";
```

No protocol, no trailing slash. The Results section then swaps its links for
the auto-refreshing leaderboard iframe (with the "Find my time" bib search).
Leave it `""` and the section gracefully shows the official RunSignup results
links instead — the page never looks broken.

## Lodging partner logo

The "Where to Stay" section (Pecos Trail Inn, 15% off with code
`RUNSANTAFE26`, stays Sept 16–22) reserves a white logo panel that stays
hidden until the file exists. To light it up, save the hotel's logo as
`assets/pecos-trail-inn.png` — no HTML edit needed. The promo bar, nav link,
and section all hide themselves automatically after the offer window closes
at end of day Tuesday, Sept 22, 2026 (Mountain time).

## Deploying the page

- **HostGator (current host):** cPanel → File Manager → `public_html`. Back up
  the existing `index.html` (copy to `index-backup.html`), then upload this
  `index.html` and the `assets/` folder. Hard-refresh to bust caching.
- **GitHub Pages (free alternative):** push this `site/` folder to the site
  repo and enable Pages on it; point the domain's DNS at Pages per GitHub docs.

## Editing

All content is plain HTML in `index.html`; brand colors are CSS variables at
the top (`--nm-gold`, `--nm-turquoise`, `--nm-crimson`, obsidian backgrounds).
Race facts match `../server.py` (`RACE` dict) — if the date, start, or course
changes, update both places.
