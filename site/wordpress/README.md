# WordPress + Elementor package

The same Santa Fe Half Marathon site, packaged for WordPress with Elementor.
Two ways to use it — pick one:

## Option A — import the whole page (fastest)

1. WordPress admin → **Templates → Saved Templates → Import Templates**
   (with Elementor installed; on some versions it's Templates → Add New →
   Import). Upload `elementor-template.json`.
2. Create a page (e.g. "Home") → **Edit with Elementor** → click the gray
   folder icon → **My Templates** → insert "Santa Fe Half Marathon — Home".
3. For a full-bleed page, set the page's layout to **Elementor Canvas**
   (Page Settings ⚙ → Page Layout) — otherwise the theme's own header/footer
   wrap the sections, which also works fine.

## Option B — paste individual sections

Each file in `blocks/` is a self-contained section (styles + markup + script,
all scoped so nothing leaks into your theme). In Elementor, drag in an
**HTML** widget and paste a block's entire file contents. They also work in a
Gutenberg **Custom HTML** block. Use any subset, in any order:

| Block | What it is |
|---|---|
| `00-header.html` | Sticky header matching the site-wide menu spec: logo → `/`, five dropdowns (Races / Course / Race Weekend / Results & Awards / About) with real page URLs, Register CTA → RunSignup #83604 |
| `01-promo-bar.html` | Pecos Trail Inn 15% banner (auto-hides after Sept 22) |
| `02-hero-countdown.html` | Hero + live countdown + register CTAs |
| `03-stat-strip.html` | 13.109 mi / 7:30 AM / net −36′ / 3:30 facts row |
| `03b-whats-new.html` | What's New This Year (2026): YouthWorks finish-line food, Tricia Downing returns, live results, champions wall, Nuckolls Brewing post-race celebrations |
| `04-race-info.html` | Start, finish, packet-pickup cards |
| `04b-schedule.html` | Three-day Schedule of Events (expo Fri/Sat + race-day timeline) |
| `05-course-chart.html` | Elevation profile with hover + data table |
| `06-live-results.html` | Results section (leaderboard-ready) |
| `06b-champions.html` | Past Champions cards — derived live from RunSignup results (top man + woman per year), hidden until results load |
| `06c-ambassador.html` | Meet Tricia Downing — Wheelchair Division Athlete Ambassador feature (photo + bio + Expo speaker note) |
| `07-photos.html` | Photo cards + album links |
| `08-where-to-stay.html` | Pecos Trail Inn offer + code (auto-hides after Sept 22) |
| `08b-vendor-expo.html` | Vendor booths: flat $300 fee, informational day chips |
| `09-altitude.html` | Three altitude tips |
| `09b-faq.html` | Ten-question FAQ accordion (lodging item auto-hides after Sept 22) |
| `09c-partners.html` | Partners strip: Capitol Ford (title) + Pecos Trail Inn (lodging) |
| `10-register-band.html` | Bottom register call-to-action |
| `11-footer.html` | Three-column footer + copyright bar (for Canvas pages with no theme footer) |

## After inserting: images

All images need **no setup** — the hero, Photos, Where to Stay, and
partners blocks hotlink them from the static-site CDN
(`santa-fe-results-board.onrender.com/assets/…`), which is always warm and
serves them with day-long caching. That includes both sponsor logos
(Capitol Ford and Pecos Trail Inn). Everything works the moment the
template is imported. To serve images from your own WordPress instead
(recommended eventually: your hosting, your CDN), upload the files from
`../assets/` to the Media Library and swap the `onrender.com/assets` URLs
in those blocks.

The ambassador photo still falls back to its Google Drive original until
`tricia-downing.webp`/`.jpg` land in `../assets/`.

## Vendor form + confirmation email

The vendor section shows the **flat $300 fee** (one price, both expo days —
there are no per-day tiers). The Friday/Saturday chips are purely
informational, and the copy tells applicants their day checkboxes don't
change the price. Two placeholders to wire up on your side:

- The "Apply for a booth" button in `08b-vendor-expo.html` (and the imported
  template) currently links to https://santafehalfmarathon.com — swap in a
  dedicated vendor application page URL when one exists. In that form, remove
  any per-day pricing fields and keep the day checkboxes as plain,
  non-pricing inputs.
- `vendor-confirmation-email.md` → the automated confirmation email copy for
  your form plugin's notification settings, rewritten for the flat $300 setup.

## Menu anchors

Sections keep their ids, so WordPress menu items can use custom links:
`/#race`, `/#course`, `/#results`, `/#photos`, `/#stay`, `/#vendors`.
(Remove the Stay menu item after Sept 22 — the section hides itself then.)

## Race-day leaderboard

In `06-live-results.html` (or that section's HTML widget), set:

```js
var RESULTS_HOST = "your-results-host.onrender.com";
```

once the results server from this repo is deployed (see `../../DEPLOY.md`).
Leave it `""` and the section shows official RunSignup results links instead.

## Regenerating

These files are hand-maintained copies of the static site's sections
(`../index.html`). If you change content there, mirror it here.
