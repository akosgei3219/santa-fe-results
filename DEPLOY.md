# Deploying the Santa Fe Half Marathon server

The app is one container that serves the results widget (`/leaderboard`) and the
MCP endpoint (`/mcp`) on port 8000. Pick one host below. All three use the same
`Dockerfile`; you only need one config.

The default `REGISTRATION_BACKEND=json` needs no secrets, so you can deploy first
and wire real RunSignup credentials in afterward.

---

## Option A — Render (easiest, recommended to start)

1. Push this folder to a GitHub/GitLab repo.
2. In Render: **New > Blueprint**, pick the repo. It reads `render.yaml`.
3. Click **Apply**. Render builds the image and gives you a URL like
   `https://santa-fe-half-marathon.onrender.com`.
4. Widget: `…/leaderboard`. Health check (`/leaderboard`) is already configured.
5. Custom domain: **Settings > Custom Domains**, add e.g.
   `race.santafehalfmarathon.com`, then add the CNAME Render shows you at your
   DNS provider. TLS is automatic.

Free tier sleeps when idle (first hit after idle is slow). Bump to a paid plan
for race day so it stays warm.

## Option B — Fly.io (global, scales to zero)

1. Install the CLI and sign in: `fly auth login`.
2. From this folder: `fly launch --copy-config --no-deploy` (it reads `fly.toml`;
   accept the app name or change it).
3. `fly deploy`. Your URL: `https://santa-fe-half-marathon.fly.dev`.
4. Custom domain: `fly certs add race.santafehalfmarathon.com`, then add the
   shown records at your DNS provider.

## Option C — Your own VPS (full control)

1. Get a small Linux VPS with Docker installed. Point a DNS **A record**
   (e.g. `race.santafehalfmarathon.com`) at its public IP.
2. Copy this folder to the server. Edit `deploy/Caddyfile` — replace the domain
   with yours.
3. `docker compose -f docker-compose.prod.yml up -d --build`
   Caddy fetches a Let's Encrypt cert automatically and serves HTTPS.

---

## Turning on live registration lookups (optional)

`lookup_registration` returns real runners only once you point it at RunSignup
**and** the race director enables API access (see the backends section in
`README.md`). To configure:

- **Render:** dashboard > Environment. Set `REGISTRATION_BACKEND=runsignup`,
  `RUNSIGNUP_API_KEY`, `RUNSIGNUP_API_SECRET`, `RUNSIGNUP_RACE_ID=83604`,
  `RUNSIGNUP_EVENT_ID=1056101`. Mark the key/secret as secret.
- **Fly:** `fly secrets set REGISTRATION_BACKEND=runsignup RUNSIGNUP_API_KEY=... RUNSIGNUP_API_SECRET=...`
  and `fly deploy`.
- **VPS:** put them in a `.env` file and uncomment `env_file: .env` in
  `docker-compose.prod.yml`.

Results and the leaderboard (`lookup_result`, `/leaderboard`) are public and need
no keys — they work the moment you deploy.

---

## Put it on the website

Once you have an HTTPS URL, embed the live leaderboard on
santafehalfmarathon.com with an iframe:

```html
<iframe src="https://race.santafehalfmarathon.com/leaderboard"
        width="700" height="600" style="border:0"
        title="Live Leaderboard"></iframe>
```

## What only you can do

Creating the host account, adding the domain's DNS records, and entering the
RunSignup secret are steps I can't do for you — they need your accounts and
credentials. Everything else (the image, configs, health checks) is ready to go.
