# Santa Fe International Half Marathon — Site & Systems Audit (v2)
**Date:** July 14, 2026 · **Race day:** Sunday, September 20, 2026 (~10 weeks out)
**Scope:** santafehalfmarathon.com (WordPress + Elementor on HostGator), live results infrastructure, social channels
**Supersedes:** July 11 audit — this version reflects all fixes completed since, each re-verified against the live site today.

---

## Part 1 — Race-Day Infrastructure: ALL GREEN ✅

| System | Status | Evidence |
|---|---|---|
| Results server (Render) | ✅ Healthy | `santa-fe-results.onrender.com` serving /leaderboard, /leaderboard.json, /result.json, /course, /mcp |
| Redundant services | ✅ Cleaned up | `-tl65` and `santa-fe-half-marathon` deleted; blueprints disconnected |
| Homepage Live Results embed | ✅ Live | `#results` section with lazy-loaded leaderboard iframe (confirmed in served HTML today) |
| Nav links (EN + ES) | ✅ Live | Desktop "Finish line / Live Results" in Plan dropdown; "Live Results / Resultados" in mobile drawer |
| Footer social links | ✅ Fixed | facebook.com/RunSantaFe + instagram.com/runsantafe sitewide |
| GitHub → Render pipeline | ✅ In sync | Local folder = GitHub main = deployed (verified byte-identical) |
| 2026 results mapping | ✅ Ready | RunSignUp event 1056101 wired; leaderboard auto-fills on race day |
| Race-week reminder | ✅ Scheduled | Sept 14: upgrade Render tier + re-verify endpoints (push + email) |
| Facebook announcement | ✅ Published | "10 weeks" post live with year-one finish-line photo |

**Open infrastructure items:**
- Race week (Sept 14 reminder set): upgrade Render to a paid tier so the leaderboard never cold-starts on race morning.
- Optional housekeeping: delete the failed `santa-fe-results-board` static site in Render (inert, no cost).
- Facebook post photo swap to the race-timer photo is still pending — the 15.6 MB file exceeds the Drive transfer limit; drop `sfi-half-marathon-01.jpg` into the connected folder and I can finish it.

---

## Part 2 — SEO Fixes Completed Since Last Audit ✅

Every critical finding from the July 11 audit is now resolved and was re-verified against the live, anonymously-fetched HTML today:

**1. SportsEvent structured data — FIXED ✅**
The homepage now carries full `SportsEvent` JSON-LD: name, startDate `2026-09-20T07:30:00-06:00`, Santa Fe Railyard Park location, registration offer (RunSignUp), organizer, and subEvents for the 3-Amigos Relay, 4K Fitness, and Kids 1K Dash. Google can now show event rich results with the race date. Recommended follow-up: run it through Google's Rich Results Test once and submit the homepage for recrawl in Search Console.

**2. Interior pages orphaned (no nav) — FIXED ✅**
All five key interior pages now have the branded sticky header + 4-column footer, modeled on runsedona.com's structure and typographically matched to the homepage (Oswald display / Inter body, gold-on-obsidian):
- /contact-us/ ✅ (header, footer, Oswald fonts — verified live today)
- /course-map/ ✅
- /event-schedule/ ✅
- /lodging-travel/ ✅
- /packet-pickup/ ✅
Every page now links to Races, Course Map, Schedule, Packet Pickup, Lodging, Live Results, Contact, and a gold Register pill.

**3. Registration links inconsistent — FIXED ✅**
All RaceRoster links (two different event IDs plus bare links, 9 total) replaced sitewide with the canonical `runsignup.com/Race/Register/?raceId=83604`. Verified today: zero `raceroster.com` references remain on the homepage or any of the five interior pages.

**4. www subdomain — NOT A DEFECT (finding withdrawn) ✅**
The July 11 report flagged www as unresolvable; that was a false negative from the audit sandbox (it couldn't do DNS lookups). Verified from your PC: www.santafehalfmarathon.com resolves via HostGator nameservers and 301-redirects to the apex with a valid certificate. Nothing to fix.

---

## Part 3 — Quick Wins: COMPLETED July 14 ✅

All five high-impact quick wins from the earlier audit are now done and verified in the live HTML:

1. **Homepage title — FIXED ✅** Now `Santa Fe International Half Marathon | Sept 20, 2026 Race` (57 chars, was ~90 with duplication). Verified live.
2. **Meta descriptions — FIXED ✅** Custom 140–146 char descriptions written in AIOSEO for /contact-us/, /event-schedule/, and /lodging-travel/, replacing the 250+ char auto-dumps. All three verified live.
3. **Homepage deep links — FIXED ✅** Six bilingual (EN/ES) deep links added to homepage sections: Course → /course-map/, Schedule → /event-schedule/, Perks → /packet-pickup/, Lodging → /lodging-travel/, Charity → /charity-information/, FAQ → /contact-us/. The internal-linking loop is now closed in both directions.
4. **Hero image — FIXED ✅** Descriptive alt text added ("Runners climbing toward sunrise over the Sangre de Cristo Mountains…"). The lazy-load conflict flagged earlier was already resolved — the hero carries only `fetchpriority="high"`.
5. **Image alts — FIXED ✅** All three course-map images (route map, elevation profile, mile-by-mile blueprint) and all four lodging images (travel hero + three partner-hotel logos, set at the media-library level so they're fixed sitewide). Both pages now serve zero empty alts.

### 🟠 Remaining minor item

- **og:type is "article" on every page** (homepage should be "website"), and every page shares the same logo og:image. Cosmetic for social shares; no ranking impact.

## Part 4 — Longer-term Opportunities

### 🟡 Nice-to-haves

- **Bilingual content:** no hreflang; Spanish lives inside the H1 via toggle spans. Long term: a real `/es/` page with hreflang tags.
- Server returns **406 to non-browser user agents** (mod_security UA rule) — breaks third-party SEO tools.
- **robots.txt blocks GPTBot and CCBot** — invisible to AI answer engines where "half marathons in Santa Fe" queries increasingly happen. Reconsider.
- Post-race: mirror top-10 finisher names/times as HTML text on the page (iframe content doesn't rank for your domain).
- Publish occasional news posts (elite field, charity totals) for fresh-content signal.
- Working well, leave alone: one H1 per page, clean heading nesting, self-referential canonicals, true 404s, healthy 22-page sitemap.

---

## What's left (all optional)

1. og:type / og:image cleanup for nicer social-share cards
2. hreflang / Spanish strategy (bigger project, post-race is fine)
3. Occasional news posts for fresh-content signal
4. Post-race: mirror top-10 finishers as HTML text on the results page

---

*Method: infrastructure verified directly (Render endpoints, GitHub sync, scheduled reminders); site findings from live, anonymously-fetched HTML of the homepage and all five interior pages on July 14, 2026. All Elementor saves confirmed persisted (isChanged = false) and re-checked in the served HTML.*
