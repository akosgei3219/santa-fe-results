# Santa Fe Half Marathon — example MCP server

A small, runnable Model Context Protocol server that shows all three MCP
primitives in one place, themed around the Santa Fe Half Marathon.

## What's inside

**Tools** (model-invoked, can compute or act):
- `pace_calculator(target_finish, units)` — pace needed to hit a goal time
- `days_until_race()` — countdown to race day
- `altitude_advice(coming_from_elevation_ft)` — practical 7,000 ft guidance
- `race_day_weather()` — **live** forecast from the free Open-Meteo API (no key)
- `lookup_registration(bib | email)` — runner status, wave, packet pickup
- `lookup_result(bib, year)` — **live** finish time/place from public results
- `course_elevation()` — per-mile elevation + total gain/loss from a GPX
- `results_leaderboard(year, top_n)` — top finishers (public results, no key)
- `race_photos(year)` — links to RunSignup galleries + Google Drive + OneDrive albums

**Resources** (readable context the host attaches):
- `race://info` — core logistics (date, start/finish, elevation, packet pickup)
- `race://course-profile` — mile-by-mile elevation table
- `race://photos` — photo album links (RunSignup + Drive + OneDrive)

**Prompt** (reusable template):
- `race_day_pep_talk(runner_name)` — a warm race-morning message

## Run it

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py                 # starts on stdio and waits for a client
```

`python server.py` will look like it hangs — that's correct. On the `stdio`
transport the server waits for a client to speak JSON-RPC over stdin. Ctrl-C to
stop.

Quick end-to-end check without a full client:

```bash
python smoke_test.py             # launches the server and exercises every tool
```

The offline unit tests (no network, no client) run with pytest and also run in
CI on every push and pull request:

```bash
pip install pytest
pytest                           # test_server / test_backends / test_course / test_results
```

## Connect it to a client

Copy the block from `claude_desktop_config.example.json` into your client's MCP
config, replacing the path with the absolute path to `server.py`. In Claude
Desktop that file is `claude_desktop_config.json`; restart the app and the
server's tools appear.

## The two "real" tools

- **`race_day_weather`** makes an actual HTTPS call to Open-Meteo at invocation
  time using only the Python standard library — no API key, no extra dependency.
  If race day is beyond the ~16-day forecast window, or the network is
  unreachable, it returns a clear status object instead of raising, so the model
  can relay that to the runner. (In a locked-down sandbox with no DNS it returns
  `status: "unavailable"` — that's the graceful path working, not a bug.)
- **`lookup_registration`** reads `registrations.json` as a stand-in for a real
  registration database or platform API. Swap the file read for your DB/HTTP
  call and the tool's interface to the model doesn't change at all — that's the
  point of MCP: the client never sees the backend.

## Things worth noticing in the code

- **Never `print()` to stdout.** On stdio, stdout carries the JSON-RPC stream —
  a stray print corrupts it. All logging goes to stderr via `log()`.
- **Docstrings are the API.** The model picks tools by name and docstring, so
  they're written to be descriptive, not decorative.
- **Tools vs. resources.** Computing a pace is a tool (model decides to call it);
  the static race sheet is a resource (host/user attaches it). Same data, but a
  different consent and risk model.
- **Swappable transport.** This runs on stdio. To make it remote you'd switch to
  Streamable HTTP — the tool functions don't change at all.

The `RACE` facts in `server.py` reflect the real 2026 event (race ID 83604,
Sun Sep 20 7:30am, Eldorado -> Railyard). For the real course profile, drop a
`course.gpx` next to `server.py` (see "Course profile from GPX" below).

## Running it remotely (Streamable HTTP)

The same server runs over HTTP with no change to any tool. Pick the transport
with a CLI arg or the `MCP_TRANSPORT` env var (default is `stdio`):

```bash
python server.py http        # serves at http://127.0.0.1:8000/mcp
# or: MCP_TRANSPORT=http python server.py
```

Host and port are set in the `FastMCP(...)` constructor near the top of
`server.py` — set `host="0.0.0.0"` to accept connections from other machines,
and put it behind TLS + auth before exposing it publicly.

Point an HTTP-capable client at it with `remote_config.example.json`. Verify it
end to end with:

```bash
python server.py http &      # start the server
python http_smoke_test.py    # connect over HTTP and call some tools
```

Note: if you're behind a SOCKS proxy, HTTP clients need `pip install httpx[socks]`,
and you'll want `NO_PROXY=127.0.0.1,localhost` so loopback traffic skips the proxy.

### stdio vs. HTTP — when to use which

- **stdio** — the client launches the server as a local subprocess. Best for
  personal/desktop use, IDE plugins, and anything touching local files. Nothing
  hits the network.
- **Streamable HTTP** — the server runs independently and can serve many clients
  at once. This is what you'd deploy to power the marathon site. It costs more to
  operate (hosting, TLS, auth) but scales and is maintained separately from any
  one client.

## Course profile from GPX

Export the course as a `.gpx` and save it as `course.gpx` next to `server.py`.
The `course_elevation` tool and the `race://course-profile` resource then
switch automatically from the illustrative placeholder to the real surveyed
profile: per-mile elevations (feet), total ascent/descent, and min/max. The
parser (`course.py`) uses the haversine formula for distance and only the
standard library. If the GPX has no `<ele>` tags, it fills elevations from the
free Open-Meteo Elevation API (no key); if that call fails it reports a clear
status instead of crashing.

A synthetic `sample_course.gpx` fixture is included for the tests (it is **not**
the real course). Verify parsing, distance, and gain/loss with:

```bash
pytest test_course.py
```

## Live results widget (for the website)

Running over HTTP, the server also serves an embeddable leaderboard on the
same app as `/mcp`:

- `GET /leaderboard` — a self-contained HTML widget (auto-refreshes every 30s,
  year + size selectors, loading/empty/error states). Source: `leaderboard.html`.
- `GET /leaderboard.json?year=2025&top_n=10` — the JSON feed it polls, with
  `Access-Control-Allow-Origin: *` so it can be embedded cross-origin.
- `GET /result.json?bib=204&year=2025` — single-runner lookup powering the
  widget's "Find my time" bib search box (same CORS).

Both are backed by the same public RunSignup results API as `lookup_result`, so
no key is required. Embed on the marathon site with an iframe:

```html
<iframe src="https://your-host/leaderboard" width="700" height="560"
        style="border:0" title="Live Leaderboard"></iframe>
```

Or reuse the JSON feed from your own front-end (set `window.LEADERBOARD_URL` to
point the bundled widget at a different origin). Start it with
`python server.py http` and open http://127.0.0.1:8000/leaderboard.

## Live results lookup (`lookup_result`)

Registration data is gated, but RunSignup's **results** API is public for races
that publish results — so `lookup_result(bib, year)` works today with no key.
It returns a runner's finish time (chip time preferred), overall place, pace,
age and gender, normalized in `results.py`. Half Marathon event IDs are mapped
by year (2023 / 2025 / 2026); 2026 returns results once the race is run and
live results as they post on race day.

Parsing is verified against a real captured 2025 response:

```bash
pytest test_results.py
```

## Real registration backends (Airtable / RunSignup / RaceRoster)

`lookup_registration` reads through a pluggable backend defined in `backends.py`.
The default is the local `registrations.json`; switch backends with the
`REGISTRATION_BACKEND` env var. Every backend normalizes its platform's response
into the same shape, so the tool's interface to the model never changes.

Copy `.env.example` to `.env` and fill in the block you need:

- **Airtable** (`REGISTRATION_BACKEND=airtable`) — needs `AIRTABLE_TOKEN`
  (personal access token, scope `data.records:read`), `AIRTABLE_BASE_ID`,
  `AIRTABLE_TABLE`. Looks up one record via `filterByFormula` on your Bib/Email
  column. If your columns are named differently, edit the `field_map` defaults
  in `AirtableBackend`.
- **RunSignup** (`REGISTRATION_BACKEND=runsignup`) — needs `RUNSIGNUP_API_KEY`,
  `RUNSIGNUP_API_SECRET`, `RUNSIGNUP_RACE_ID`, `RUNSIGNUP_EVENT_ID`. Uses the
  API's server-side `search_bib` / `search_email`, so it fetches the one runner
  instead of the whole roster. The real race ID for the Capitol Ford Santa Fe
  International Half Marathon (**83604**) is already filled into the config
  examples. Find your Half Marathon `event_id` in the RunSignup dashboard, or
  call `GET https://api.runsignup.com/rest/race/83604?format=json` with your key
  and read the `event_id` for the half-marathon event. For 2026 the Half
  Marathon `event_id` is **1056101** (already filled into the config examples).

  > **Important:** the race's public API record currently shows
  > `can_use_registration_api: "F"`, meaning participant data isn't exposed
  > over the API yet. The race director must enable API access on the race
  > (RunSignup: Race > Participants > API access) and use an API key with
  > permission before `lookup_registration` returns live runners. Until then
  > the backend will connect but find no participants.
- **RaceRoster** (`REGISTRATION_BACKEND=raceroster`) — needs
  `RACEROSTER_PARTICIPANTS_URL` and `RACEROSTER_TOKEN`. RaceRoster's participant
  API is OAuth-gated and account-specific, so this adapter reads the endpoint
  from env and normalizes common field names; adjust `RaceRosterBackend` to match
  your exact response.

A misconfigured backend returns `{"status": "error", "reason": ...}` to the model
rather than crashing the server.

Run the offline backend tests (mocked HTTP, no real API calls):

```bash
pytest test_backends.py
```

### Gotcha: passing env vars over stdio

On the **stdio** transport the client launches the server with a *sanitized*
environment — variables you export in your shell do **not** reach the server
subprocess. Put backend credentials in the client config's `env` block (see
`claude_desktop_config.example.json`). For the **HTTP** transport you start the
server process yourself, so its normal environment applies (e.g.
`set -a; source .env; set +a; python server.py http`).

## Deploy with Docker

The repo ships a `Dockerfile`, `.dockerignore`, and `docker-compose.yml` so the
HTTP server (MCP endpoint + results widget) runs anywhere with one command.

```bash
docker compose up --build      # builds the image and serves on :8000
# or plain Docker:
docker build -t santa-fe-mcp .
docker run -p 8000:8000 santa-fe-mcp
```

Then open http://localhost:8000/leaderboard (widget) — the MCP endpoint is at
`/mcp`. The image runs `python server.py http` and reads these env vars:

- `MCP_HOST` (default `0.0.0.0` in the image so the port is reachable), `MCP_PORT` (8000)
- `REGISTRATION_BACKEND` and its credentials (see `.env.example`). Pass real
  secrets at runtime — e.g. uncomment `env_file: .env` in `docker-compose.yml`,
  or `docker run --env-file .env ...`. The `.dockerignore` deliberately keeps
  `.env` and `course.gpx` out of the image; mount or inject them at run time.

A `HEALTHCHECK` polls `/leaderboard`, so `docker ps` shows the container's health.
To expose it publicly, put it behind a reverse proxy (Caddy/nginx/Traefik) that
terminates TLS and forwards to port 8000 — don't serve it plaintext on the
internet, especially once real registration credentials are in play.
