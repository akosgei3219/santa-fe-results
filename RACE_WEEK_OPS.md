# Race-Week Ops — Santa Fe Half Marathon

The tech side of race weekend, in order. Everything here assumes the setup
that's already live: results server + static homepage on Render, widgets
embedded on the site, leaderboard auto-mapped to the 2026 event (1056101).

## The one thing that matters most: keep the server warm

The free Render tier spins the results server down after ~15 minutes idle.
The first request after that takes 30-60 seconds — which on race morning
means a runner typing their bib and staring at a spinner. Two ways to fix
it, pick one:

- **Upgrade (recommended):** Render dashboard → santa-fe-half-marathon →
  upgrade the docker service to the Starter tier. Do it by **Thursday,
  Sept 17** so it's warm through packet pickup, race day, and results
  traffic. Downgrade again the week after. The static site stays free —
  it's CDN-served and never sleeps.
- **Free keep-warm:** point an uptime monitor (UptimeRobot, cron-job.org)
  at `https://santa-fe-half-marathon.onrender.com/leaderboard` every 10
  minutes. Works, but the free tier also has monthly usage limits — the
  paid week is the safer bet for the one weekend that counts.

## T-minus one week (by Sun, Sept 13)

- ⬜ Decide keep-warm approach above; if upgrading, note it on the calendar
- ⬜ Open the live site and hard-refresh: hero, countdown, logos, embed all up
- ⬜ Spot-check `/leaderboard` and `/course` load fast twice in a row
- ⬜ Confirm 2025 results still look right (regression check):
     `/leaderboard.json?year=2025` returns 10 finishers
- ⬜ If registration lookup should be live: RunSignup API key/secret set in
     Render env (see GO_LIVE.md §3) — or consciously skip it, results
     don't need it

## Packet-pickup weekend (Fri Sept 18 – Sat Sept 19)

- ⬜ Server upgraded / keep-warm confirmed running
- ⬜ Check HostGator disk headroom before race-day photo uploads
- ⬜ Dry-run "find my time" once with a 2025 bib so the flow is fresh in
     your head when a runner asks at the expo

## Race morning (Sun, Sept 20 — gun at 7:30 AM)

- ⬜ ~6:00 AM: open `/leaderboard?year=2026` — expect the empty pre-race
     state, not an error (an error means the RunSignup results feed isn't
     up yet; check with timing)
- ⬜ First finishers ~8:35 AM: leaderboard should start filling on its own —
     it reads RunSignup live, nothing to switch on
- ⬜ Spot-check one bib in "Find my time" as soon as results post
- ⬜ If the leaderboard errors mid-race: it self-recovers when the feed
     does; the widget shows a clean message, not a crash. Don't restart
     anything — check RunSignup's results page first to see whether it's
     us or the feed.

## After the race

- ⬜ Keep the server warm through Sunday evening — results traffic peaks
     after the awards, not during the race
- ⬜ Monday: confirm final results match RunSignup's official page
- ⬜ Upload race photos (watch HostGator disk)
- ⬜ Following week: downgrade Render, keep the uptime monitor if you set
     one up (it's free and doubles as a health check year-round)

## If something breaks

- Widget shows "results unavailable": the server can't reach RunSignup.
  Check https://runsignup.com/Race/Results/83604 directly — if that's down,
  it's the feed, not us, and it recovers on its own.
- Whole site down: check https://status.render.com, then the service logs
  in the Render dashboard.
- Photos not loading: they're served from the static site
  (santa-fe-results-board.onrender.com/assets/…) — check that service
  separately; it deploys from the same repo.
