# Race-Week Ops — Santa Fe Half Marathon

The tech side of race weekend, in order.

> **Big simplification (July 2026):** the website's leaderboards no longer go
> through the Render server. Both the homepage Live Results section and the
> Results & Photos page read RunSignup's public results API **directly from
> the visitor's browser** (it's CORS-open, no key needed). There is no server
> to keep warm for the website — if RunSignup is up, results work. The Render
> server still exists and serves `/leaderboard` (standalone page + MCP
> endpoint), but nothing on santafehalfmarathon.com depends on it.

## What that changes

- **Upgrading Render to a paid tier for race week is now optional.** Do it
  only if you share the standalone `santa-fe-results.onrender.com/leaderboard`
  link directly (social posts, timing tent QR code). The website itself is
  unaffected by Render cold starts.
- One soft dependency remains: the Results & Photos page upgrades its card
  photo to `santa-fe-results.onrender.com/assets/sfi-half-marathon-04.webp`
  when that server is awake. If it's asleep, the page falls back to a
  WordPress-hosted photo automatically. Cosmetic only.

## T-minus one week (by Sun, Sept 13)

- ⬜ Open the live site and hard-refresh: hero, countdown, logos, leaderboard all up
- ⬜ Confirm 2025 results render (regression check): the homepage leaderboard
     shows 10 finishers for 2025, and bib search returns a result
- ⬜ Check the Results & Photos page: leaderboard, Past Champions, photo sections
- ⬜ If registration lookup should be live on the MCP server: RunSignup API
     key/secret set in Render env (see GO_LIVE.md §3) — or consciously skip
     it; website results don't need it

## Packet-pickup weekend (Fri Sept 18 – Sat Sept 19)

- ⬜ Check HostGator disk headroom before race-day photo uploads
- ⬜ Dry-run "find my time" once with a 2025 bib so the flow is fresh in
     your head when a runner asks at the expo
- ⬜ Kids 1K Dash is Saturday 3 PM — expect a site-traffic bump Saturday too

## Race morning (Sun, Sept 20 — gun at 7:30 AM)

- ⬜ ~6:00 AM: open the homepage leaderboard on 2026 — expect the clean
     "results haven't posted yet" state, not an error (an error means the
     RunSignup results feed isn't up; check with timing)
- ⬜ First finishers ~8:35 AM: the leaderboard fills on its own — it reads
     RunSignup live and auto-refreshes every 30 seconds; nothing to switch on
- ⬜ Spot-check one bib in "Find my time" as soon as results post
- ⬜ If the leaderboard errors mid-race: it self-recovers when the feed does;
     the widget shows a clean message, not a crash. Don't restart anything —
     check RunSignup's results page first to see whether it's us or the feed.

## After the race

- ⬜ Monday: confirm final results match RunSignup's official page
- ⬜ Upload race photos (watch HostGator disk)
- ⬜ Post-race SEO item from the audit: mirror the top-10 finishers as plain
     HTML text on the Results & Photos page so the results rank for our domain

## If something breaks

- Leaderboard shows "couldn't reach the results feed": the visitor's browser
  can't reach RunSignup. Check https://runsignup.com/Race/Results/83604
  directly — if that's down, it's the feed, not us, and it recovers on its own.
- Website down: that's WordPress/HostGator — wp-admin, HostGator status, or
  their support. Render is not involved.
- Standalone leaderboard page down: check https://status.render.com, then the
  service logs in the Render dashboard. Remember the website doesn't need it.
