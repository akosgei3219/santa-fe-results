# Putting the live leaderboard on santafehalfmarathon.com

Your site is a **custom static HTML site** (hand-coded, hosted as files on
HostGator — not WordPress/Elementor). So embedding is a direct HTML edit, which
is actually the simplest case. Two pieces:

1. **Results server** → deploy on Render (see `DEPLOY.md`). You get a URL like
   `https://santa-fe-half-marathon.onrender.com`. Verify by opening `…/leaderboard`.
2. **Your site** → paste one `<section>` into the page's HTML and re-upload.

## Add the section

1. In HostGator **cPanel → File Manager**, go to `public_html` and open the page
   file (likely `index.html`). Edit in place, or download it, edit locally, and
   re-upload.
2. Paste the whole block from `embed_static_site.html` where you want results —
   a natural spot is right after your "Course Profile" section.
3. Replace `RACE_HOST` in the iframe `src` with your Render host, e.g.
   `santa-fe-half-marathon.onrender.com`.
4. Save (or upload). Refresh the site — the "Live Results" section appears,
   already styled with your `--nm-gold` / `--card-bg` / `--border-gray` /
   `--text-muted` variables so it matches the rest of the page.

Optionally add a nav link to it — your header already uses in-page anchors, so
a link to `#results` will jump to the new section.

## Notes

- **HTTPS:** your site and the Render URL are both HTTPS, so no mixed-content
  warning. Don't use an `http://` iframe src.
- **Caching:** static files can sit behind HostGator/Cloudflare caching. If you
  don't see the section after uploading, hard-refresh (Ctrl/Cmd+Shift+R) or purge
  the CDN. The leaderboard itself refreshes inside the iframe, so results never
  go stale from page caching.
- **Height:** the section uses a responsive frame (`padding-top:78%`). If it
  looks too tall/short in your layout, nudge that percentage.

## What only you can do

Deploying the server (host account), pointing any subdomain DNS, entering the
RunSignup secret, and editing/uploading the site file are steps that need your
accounts and credentials. Everything else — the server, the styled section,
the brand match — is ready.
