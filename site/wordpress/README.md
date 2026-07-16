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
| `01-promo-bar.html` | Pecos Trail Inn 15% banner (auto-hides after Sept 22) |
| `02-hero-countdown.html` | Hero + live countdown + register CTAs |
| `03-stat-strip.html` | 13.109 mi / 7:30 AM / net −36′ / 3:30 facts row |
| `04-race-info.html` | Start, finish, packet-pickup cards |
| `05-course-chart.html` | Elevation profile with hover + data table |
| `06-live-results.html` | Results section (leaderboard-ready) |
| `07-photos.html` | Photo cards + album links |
| `08-where-to-stay.html` | Pecos Trail Inn offer + code (auto-hides after Sept 22) |
| `08b-vendor-expo.html` | Vendor booths: flat $300 fee, informational day chips |
| `09-altitude.html` | Three altitude tips |
| `10-register-band.html` | Bottom register call-to-action |

## After inserting: replace 3 image URLs

Upload to **Media → Add New**: `../assets/sfi-half-marathon-04.jpg`,
`../assets/sfi-half-marathon-06.jpg`, and the Pecos Trail Inn logo. Copy each
file's URL from the Media Library, then in the Elementor HTML widgets replace:

- `IMAGE_URL_FINISH` (2 spots: hero block + photos block) → finish-line photo URL
- `IMAGE_URL_COMMUNITY` (photos block) → community photo URL
- `LOGO_URL_PECOS` (where-to-stay block) → hotel logo URL

Until replaced, the page still looks intentional: the hero shows a dark
gradient, and the photo cards / logo panel hide themselves.

## Vendor form + confirmation email

The vendor section shows the **flat $300 fee** (one price, both expo days —
there are no per-day tiers). The Friday/Saturday chips are purely
informational, and the copy tells applicants their day checkboxes don't
change the price. Two placeholders to wire up on your side:

- `VENDOR_FORM_URL` in `08b-vendor-expo.html` (and the imported template) →
  link to your WordPress vendor application page/form. In that form, remove
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
