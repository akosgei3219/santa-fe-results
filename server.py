"""
Santa Fe Half Marathon - an example MCP server.

Demonstrates the three MCP primitives:
    TOOLS      : callable functions the model invokes to compute or act
    RESOURCES  : readable data the model/host can pull in as context
    PROMPTS    : reusable templates the server offers

Runs over the stdio transport (client launches this file as a subprocess and
talks JSON-RPC 2.0 over stdin/stdout). Never print() to stdout - it corrupts
the JSON-RPC stream. Logs go to stderr.

    python server.py
"""

from __future__ import annotations

import sys
import json
import pathlib
import datetime as dt
import urllib.request
import urllib.error
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

import os
# Bind address/port for HTTP transport. Defaults to localhost:8000 for local dev;
# in a container set MCP_HOST=0.0.0.0 so the port is reachable from outside.
mcp = FastMCP(
    "santa-fe-half-marathon",
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8000")),
)


def log(msg: str) -> None:
    """Log to stderr. stdout is reserved for the JSON-RPC stream on stdio."""
    print(f"[santa-fe-mcp] {msg}", file=sys.stderr, flush=True)


RACE = {
    "name": "Capitol Ford Santa Fe International Half Marathon",
    "edition": "6th annual",
    "date": dt.date(2027, 9, 19),  # Sunday - Half Marathon & 3-Amigos Relay
    "distance_miles": 13.1,
    "cutoff": "4:30 from the 7:30 AM start - course support ends 12:00 PM",
    "start_line": "Romero Park, Agua Fria Village - Half Marathon & 3-Amigos Relay start",
    "finish_line": "Reunity Resources Farm, Santa Fe River corridor",
    "course_note": (
        "First ~4.9 miles on streets, then the car-free Santa Fe River Trail. "
        "GPS-measured; not USATF-certified for this course yet."
    ),
    "base_elevation_ft": 6640,   # Romero Park start
    "low_point_ft": 6567,        # near Agua Fria Village, ~mile 4
    "high_point_ft": 6883,       # mile 9 turnaround (highest point)
    "finish_elevation_ft": 6590, # Reunity Resources Farm
    "total_climb_ft": 651,
    "start_time": "07:30 MDT",
    "schedule": [
        "Sat Sept 18, 2027: 5K, 10K and Kids Fun Dash",
        "Sun Sept 19, 2027: Half Marathon and 3-Amigos Relay (7:30 AM start)",
    ],
    "packet_pickup": (
        "Reunity Resources Farm, all events: Fri Sept 17 10am-6pm and Sat Sept 18 "
        "10am-5pm. 5K and 10K bibs are mailed about a week before race day "
        "(collect shirts at Reunity). Sunday race-morning pickup (Half & Relay) "
        "is for emergencies only, 6-7am."
    ),
    "registration_url": "https://runsignup.com/Race/Register/?raceId=89412",
    # Romero Park start coordinates (for the weather forecast).
    "latitude": 35.6592,
    "longitude": -106.0290,
}

# Approximate per-mile elevations interpolated from the published 2026 course
# anchors (start ~6,640 ft; low 6,567 ft near mile 4; high point 6,883 ft at the
# mile 9 turnaround; finish ~6,590 ft). Drop a real course.gpx to replace.
COURSE_PROFILE_FT = [
    6640, 6620, 6600, 6580, 6567, 6630, 6690, 6760,
    6830, 6883, 6800, 6720, 6650, 6590,
]

REGISTRATIONS_FILE = pathlib.Path(__file__).with_name("registrations.json")

# Registration data source. Defaults to the local JSON file; set the
# REGISTRATION_BACKEND env var to 'airtable', 'runsignup', or 'raceroster'
# (see backends.py and .env.example) to point at a real platform. Built once
# at startup; misconfiguration surfaces the first time the tool is called.
import backends
import results
import course
import photos
_BACKEND = None

def get_backend():
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = backends.build_backend(REGISTRATIONS_FILE)
        log(f"registration backend: {type(_BACKEND).__name__}")
    return _BACKEND


# ========================= TOOLS =========================

@mcp.tool()
def pace_calculator(target_finish: str, units: Literal["mi", "km"] = "mi") -> dict:
    """Compute the average pace needed to hit a target half-marathon finish time.

    Args:
        target_finish: Goal time as "H:MM:SS" or "MM:SS" (e.g. "1:45:00").
        units: Return pace per mile ("mi") or per kilometre ("km").
    """
    parts = [int(p) for p in target_finish.split(":")]
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h, m, s = 0, parts[0], parts[1]
    else:
        raise ValueError('target_finish must look like "H:MM:SS" or "MM:SS"')

    total_seconds = h * 3600 + m * 60 + s
    distance = RACE["distance_miles"] if units == "mi" else RACE["distance_miles"] * 1.60934
    pace_seconds = total_seconds / distance
    pace_min, pace_sec = divmod(round(pace_seconds), 60)
    return {
        "target_finish": target_finish,
        "pace_per_unit": f"{pace_min}:{pace_sec:02d} / {units}",
        "summary": (
            f"To finish in {target_finish} you need about {pace_min}:{pace_sec:02d} "
            f"per {units}. At altitude, stay patient on the climb from mile 4 to the "
            f"mile 9 turnaround and make it up on the run back down the River Trail."
        ),
    }


@mcp.tool()
def days_until_race() -> dict:
    """How many days until race day, counted from today."""
    today = dt.date.today()
    delta = (RACE["date"] - today).days
    if delta > 0:
        phase = "taper week" if delta <= 7 else "still building"
        note = f"{delta} days out - {phase}."
    elif delta == 0:
        note = "It's race day. Go get it."
    else:
        note = f"Race was {abs(delta)} days ago. Nice work - recover well."
    return {"race_date": RACE["date"].isoformat(), "days_until": delta, "note": note}


@mcp.tool()
def altitude_advice(coming_from_elevation_ft: int = 0) -> dict:
    """Practical altitude guidance based on where a runner is traveling from.

    Args:
        coming_from_elevation_ft: The runner's home elevation in feet.
    """
    gain = RACE["base_elevation_ft"] - coming_from_elevation_ft
    if gain >= 5000:
        tier = "big jump"
        advice = (
            "The altitude here is no joke - 7,000 ft hits different from sea level. "
            "Get in 2-3 days early if you can, hydrate hard all week, and don't "
            "chase your flat-course PR on the climbs."
        )
    elif gain >= 2000:
        tier = "noticeable"
        advice = (
            "You'll feel the thin air a bit. Keep a water bottle glued to your hand "
            "for a few days beforehand and ease off the pace on the hills."
        )
    else:
        tier = "minimal"
        advice = "You're already used to elevation - just hydrate and enjoy it."
    return {"elevation_gain_ft": gain, "adjustment": tier, "advice": advice}


@mcp.tool()
def race_day_weather() -> dict:
    """Live forecast for race day at the Santa Fe start line.

    Calls the free Open-Meteo API (no key). If race day is outside the ~16-day
    forecast window, or the network is unreachable, returns a clear status
    instead of raising.
    """
    target = RACE["date"].isoformat()
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={RACE['latitude']}&longitude={RACE['longitude']}"
        "&daily=temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,windspeed_10m_max"
        "&temperature_unit=fahrenheit&windspeed_unit=mph"
        "&timezone=America%2FDenver&forecast_days=16"
    )
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"status": "unavailable", "reason": str(e), "race_date": target}

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    if target not in dates:
        return {
            "status": "out_of_range",
            "race_date": target,
            "note": (
                "Race day is beyond the forecast window right now. Check back "
                "within about two weeks of the race for a real forecast."
            ),
        }

    i = dates.index(target)
    hi = daily["temperature_2m_max"][i]
    lo = daily["temperature_2m_min"][i]
    rain = daily["precipitation_probability_max"][i]
    wind = daily["windspeed_10m_max"][i]
    return {
        "status": "ok",
        "race_date": target,
        "high_f": hi,
        "low_f": lo,
        "precip_chance_pct": rain,
        "max_wind_mph": wind,
        "summary": (
            f"Race-day forecast: low {lo:.0f}F around the 7:30am start, high {hi:.0f}F, "
            f"{rain:.0f}% chance of rain, wind up to {wind:.0f} mph. Mornings up "
            f"here are crisp - dress for the start, not the finish."
        ),
    }


@mcp.tool()
def lookup_registration(bib: Optional[int] = None, email: Optional[str] = None) -> dict:
    """Look up a runner's registration by bib number or email.

    Pass exactly one of bib or email. Returns registration status, wave, and
    packet-pickup state. The data source is pluggable (local JSON by default;
    Airtable / RunSignup / RaceRoster via REGISTRATION_BACKEND) but this tool's
    interface to the model is identical regardless of backend.
    """
    if (bib is None) == (email is None):
        raise ValueError("Provide exactly one of bib or email.")

    try:
        runner = get_backend().lookup(bib, email)
    except backends.BackendError as e:
        return {"status": "error", "reason": str(e)}

    if runner is None:
        key = f"bib {bib}" if bib is not None else email
        return {"status": "not_found", "query": key,
                "note": "No registration matches that. Double-check the bib or email."}

    picked = "picked up" if runner["packet_picked_up"] else "not yet picked up"
    wave = runner.get("wave") or "(no wave)"
    return {
        "status": "found",
        "name": runner["name"],
        "bib": runner.get("bib"),
        "wave": runner.get("wave", ""),
        "registration_status": runner.get("status", ""),
        "packet": picked,
        "summary": (
            f"{runner['name']} - bib #{runner.get('bib')}, {wave} wave, "
            f"{runner.get('status','')}. Packet {picked}."
        ),
    }


@mcp.tool()
def lookup_result(bib: int, year: int = 2025) -> dict:
    """Look up a runner's Half Marathon finish (place, time, pace) by bib.

    Uses RunSignup's PUBLIC results API - no API key needed, works today for
    past editions and returns live results on race day. `year` selects the
    edition (2023, 2025, or 2026 once results post).

    Args:
        bib: The runner's bib number.
        year: Race year to look in. Defaults to 2025 (most recent completed).
    """
    event_id = results.HALF_MARATHON_EVENTS.get(year)
    if event_id is None:
        return {"status": "error",
                "reason": f"no Half Marathon results known for {year}; "
                          f"try one of {sorted(results.HALF_MARATHON_EVENTS)}"}
    try:
        r = results.find_result(bib, event_id)
    except results.ResultsError as e:
        return {"status": "error", "reason": str(e)}
    if r is None:
        return {"status": "not_found", "bib": bib, "year": year,
                "note": f"No {year} half-marathon result for bib #{bib}."}
    return {
        "status": "found",
        "year": year,
        **r,
        "summary": (
            f"{r['name']} (bib #{r['bib']}) finished {r['finish_time']} - "
            f"place {r['place']}, {r['pace_per_mile']}/mi in the {year} half."
        ),
    }


@mcp.tool()
def course_elevation() -> dict:
    """Course elevation profile: per-mile elevations plus total gain/loss.

    Uses the real course if a `course.gpx` file is present next to the server;
    otherwise returns the illustrative built-in profile and says so.
    """
    try:
        prof = course.load_course()
    except course.CourseError as e:
        return {"status": "error", "reason": str(e)}
    if prof is not None:
        return {"status": "ok", "source": "course.gpx", **prof}
    # fallback: illustrative built-in list
    return {
        "status": "ok",
        "source": "placeholder (add course.gpx for the real profile)",
        "per_mile_elevation_ft": COURSE_PROFILE_FT,
        "note": "Illustrative elevations, not the surveyed course.",
    }


@mcp.tool()
def results_leaderboard(year: int = 2025, top_n: int = 10) -> dict:
    """Top finishers for the Half Marathon (public results, no key required).

    Args:
        year: Race year (2023, 2025, or 2026 once results post).
        top_n: How many finishers to return (1-50).
    """
    top_n = max(1, min(50, top_n))
    event_id = results.HALF_MARATHON_EVENTS.get(year)
    if event_id is None:
        return {"status": "error",
                "reason": f"no results known for {year}; "
                          f"try {sorted(results.HALF_MARATHON_EVENTS)}"}
    try:
        rows = results.top_results(event_id, top_n)
    except results.ResultsError as e:
        return {"status": "error", "reason": str(e)}
    return {"status": "ok", "year": year, "count": len(rows), "leaderboard": rows}


@mcp.tool()
def race_photos(year: Optional[int] = None) -> dict:
    """Where to find race photos - RunSignup galleries and the Drive archive.

    Args:
        year: Optional edition (2025, 2022, 2020) to highlight that album.
    """
    return {"status": "ok", **photos.get_photos(year)}


# ========================= RESOURCES =========================

@mcp.resource("race://info")
def race_info() -> str:
    """Core logistics for the Santa Fe Half Marathon."""
    r = RACE
    return (
        f"{r['name']} ({r['edition']})\n"
        f"Date: {r['date'].isoformat()}  Start: {r['start_time']}\n"
        f"Schedule: {' | '.join(r['schedule'])}\n"
        f"Distance: {r['distance_miles']} miles  Time limit: {r['cutoff']}\n"
        f"Start: {r['start_line']}\n"
        f"Finish: {r['finish_line']}\n"
        f"Course: {r['course_note']}\n"
        f"Elevation: start {r['base_elevation_ft']} ft, high {r['high_point_ft']} ft "
        f"at mile 9, +{r['total_climb_ft']} ft total climb\n"
        f"Packet pickup: {r['packet_pickup']}\n"
        f"Register: {r['registration_url']}"
    )


@mcp.resource("race://course-profile")
def course_profile() -> str:
    """Mile-by-mile elevation profile as simple text.

    Uses the real course.gpx if present, else the illustrative built-in list.
    """
    try:
        prof = course.load_course()
    except course.CourseError:
        prof = None
    if prof is not None:
        header = (f"Real course ({prof['distance_miles']} mi): "
                  f"+{prof['total_gain_ft']} ft / -{prof['total_loss_ft']} ft, "
                  f"low {prof['min_elevation_ft']} / high {prof['max_elevation_ft']} ft")
        elevations = prof["per_mile_elevation_ft"]
    else:
        header = "Illustrative profile (add course.gpx for the surveyed course)"
        elevations = COURSE_PROFILE_FT
    lines = [header, "Mile\tElevation (ft)"]
    for mile, ft in enumerate(elevations):
        lines.append(f"{mile}\t{ft}")
    return "\n".join(lines)


@mcp.resource("race://photos")
def race_photos_resource() -> str:
    """Photo album links (RunSignup galleries + Google Drive archive)."""
    p = photos.get_photos()
    lines = ["Race photos", "", "RunSignup galleries:",
             f"  All: {p['runsignup']['all_albums']}",
             f"  Start line: {p['runsignup']['start_line']}"]
    for y, url in p["runsignup"]["by_year"].items():
        lines.append(f"  {y}: {url}")
    lines += ["", "Google Drive archive:"]
    for name, url in p["google_drive"].items():
        lines.append(f"  {name}: {url}")
    lines += ["", "OneDrive (pro photographer sets):"]
    for name, url in p.get("onedrive", {}).items():
        lines.append(f"  {name}: {url}")
    return "\n".join(lines)


# ========================= PROMPT =========================

@mcp.prompt()
def race_day_pep_talk(runner_name: str = "runner") -> str:
    """A short, warm race-morning message for a runner."""
    return (
        f"Write a short, encouraging race-morning note for {runner_name} running "
        f"the Santa Fe Half Marathon. Keep it warm and neighborly, mention the "
        f"crisp early air at the Romero Park start, the quiet miles along the Santa "
        f"Fe River Trail and the finish at Reunity Resources Farm, and "
        f"remind them to respect the altitude. Talk like a local runner who's "
        f"happy they're here."
    )


# ---- Live results widget: a JSON endpoint + an embeddable HTML page --------
# These ride on the same Streamable HTTP app, so `python server.py http` serves
# both the MCP endpoint (/mcp) and the widget (/leaderboard, /leaderboard.json).
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, Response

_CORS = {"Access-Control-Allow-Origin": "*"}

# Race photos served for the website (the WP template hotlinks these, so the
# page works on import with no manual Media Library steps).
_ASSETS_DIR = (pathlib.Path(__file__).with_name("site") / "assets").resolve()
_ASSET_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".svg": "image/svg+xml", ".webp": "image/webp"}


@mcp.custom_route("/assets/{filename}", methods=["GET"])
async def site_asset(request: Request):
    """Serve a file from site/assets. Unknown names and traversal -> 404."""
    path = (_ASSETS_DIR / request.path_params["filename"]).resolve()
    media = _ASSET_TYPES.get(path.suffix.lower())
    if path.parent != _ASSETS_DIR or media is None or not path.is_file():
        return JSONResponse({"status": "not_found"}, status_code=404, headers=_CORS)
    return Response(path.read_bytes(), media_type=media,
                    headers={**_CORS, "Cache-Control": "public, max-age=86400"})


@mcp.custom_route("/leaderboard.json", methods=["GET"])
async def leaderboard_json(request: Request):
    """JSON feed the widget polls. ?year=2025&top_n=10"""
    try:
        year = int(request.query_params.get("year", "2025"))
        top_n = int(request.query_params.get("top_n", "10"))
    except ValueError:
        return JSONResponse({"status": "error", "reason": "bad params"},
                            status_code=400, headers=_CORS)
    data = results_leaderboard(year=year, top_n=top_n)
    code = 200 if data.get("status") == "ok" else 502
    return JSONResponse(data, status_code=code, headers=_CORS)


@mcp.custom_route("/result.json", methods=["GET"])
async def result_json(request: Request):
    """Single-runner finish lookup for the widget's search box. ?bib=204&year=2025"""
    try:
        bib = int(request.query_params.get("bib", ""))
        year = int(request.query_params.get("year", "2025"))
    except ValueError:
        return JSONResponse({"status": "error", "reason": "bib and year must be numbers"},
                            status_code=400, headers=_CORS)
    data = lookup_result(bib=bib, year=year)
    code = 200 if data.get("status") in ("found", "not_found") else 502
    return JSONResponse(data, status_code=code, headers=_CORS)


@mcp.custom_route("/course", methods=["GET"])
async def course_page(request: Request):
    """Serve the standalone course-elevation chart (static, brand-matched)."""
    html = (pathlib.Path(__file__).with_name("course_chart.html")).read_text(encoding="utf-8")
    return HTMLResponse(html, headers=_CORS)


@mcp.custom_route("/leaderboard", methods=["GET"])
async def leaderboard_page(request: Request):
    """Serve the embeddable widget HTML."""
    html = (pathlib.Path(__file__).with_name("leaderboard.html")).read_text(encoding="utf-8")
    return HTMLResponse(html, headers=_CORS)


# ---- Volunteer sign-up -----------------------------------------------------
# POST /volunteer with JSON {name, email, role, phone?, notes?}. Checks run in
# order: honeypot -> required fields -> rate limit -> reCAPTCHA (only when
# RECAPTCHA_SECRET is set). Only a submission that passes all of them is saved
# and announced. Config lives in env vars (see .env.example); no personal
# addresses are hard-coded here because this repository is public.
import re
import smtplib
import threading
from starlette.concurrency import run_in_threadpool
import urllib.parse
from email.message import EmailMessage

VOLUNTEER_ROLES = {
    "course marshal", "aid station", "packet pickup", "start line",
    "finish line", "relay exchange", "shuttle ambassador", "setup / teardown",
    "kids fun dash", "general",
}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_VOL_LOCK = threading.Lock()
_RATE_STORE: dict[str, list[float]] = {}


def _volunteers_file() -> pathlib.Path:
    """Where sign-ups are stored. Git-ignored; override with VOLUNTEERS_FILE."""
    custom = os.environ.get("VOLUNTEERS_FILE", "").strip()
    return pathlib.Path(custom) if custom else pathlib.Path(__file__).with_name("volunteers.json")


def check_rate_limit(client_ip: str, now: Optional[float] = None) -> tuple[bool, int]:
    """In-memory sliding window per client IP. Returns (allowed, retry_after_s)."""
    try:
        limit = int(os.environ.get("VOLUNTEER_RATE_LIMIT", "10"))
        window = int(os.environ.get("VOLUNTEER_RATE_WINDOW", "3600"))
    except ValueError:
        limit, window = 10, 3600
    now = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
    stamps = [t for t in _RATE_STORE.get(client_ip, []) if t > now - window]
    if len(stamps) >= limit:
        _RATE_STORE[client_ip] = stamps
        return False, max(1, int(stamps[0] + window - now))
    stamps.append(now)
    _RATE_STORE[client_ip] = stamps
    return True, 0


def verify_recaptcha(token: str) -> dict:
    """Verify a reCAPTCHA v3 token with Google and return the parsed reply."""
    secret = os.environ.get("RECAPTCHA_SECRET", "").strip()
    if not secret:
        raise RuntimeError("RECAPTCHA_SECRET not configured")
    data = urllib.parse.urlencode({"secret": secret, "response": token}).encode()
    req = urllib.request.Request("https://www.google.com/recaptcha/api/siteverify", data=data)
    with urllib.request.urlopen(req, timeout=6) as resp:
        return json.loads(resp.read().decode())


def _recaptcha_problem(payload: dict) -> Optional[str]:
    """None if reCAPTCHA passes or is not configured, else a reason string."""
    if not os.environ.get("RECAPTCHA_SECRET", "").strip():
        return None
    token = str(payload.get("recaptcha_token") or "")
    if not token:
        return "recaptcha token required"
    try:
        v = verify_recaptcha(token)
    except Exception as e:  # network or config trouble: fail closed
        log(f"recaptcha verification error: {e}")
        return "recaptcha verification error"
    if not v.get("success"):
        return "recaptcha verification failed"
    score = v.get("score")
    if score is not None and score < float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5")):
        return "recaptcha score too low"
    expected = os.environ.get("RECAPTCHA_ACTION", "volunteer")
    if expected and v.get("action") and v.get("action") != expected:
        return "recaptcha action mismatch"
    return None


def _save_volunteer(entry: dict) -> None:
    path = _volunteers_file()
    with _VOL_LOCK:
        try:
            arr = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        except json.JSONDecodeError:
            arr = []
        if not isinstance(arr, list):
            arr = []
        arr.append(entry)
        path.write_text(json.dumps(arr, indent=2), encoding="utf-8")


def _notify_coordinator(entry: dict) -> None:
    """Email the volunteer coordinator. No-op unless SMTP_HOST and VOLUNTEER_TO are set."""
    host = os.environ.get("SMTP_HOST", "").strip()
    to_addr = os.environ.get("VOLUNTEER_TO", "").strip()
    if not host or not to_addr:
        return
    msg = EmailMessage()
    msg["Subject"] = f"New volunteer: {entry['name']} - {entry['role']}"
    msg["From"] = os.environ.get("VOLUNTEER_FROM", "info@santafehalfmarathon.com")
    msg["To"] = to_addr
    msg["Reply-To"] = entry["email"]
    msg.set_content(
        "New volunteer sign-up:\n\n"
        f"Name: {entry['name']}\nEmail: {entry['email']}\n"
        f"Phone: {entry['phone'] or '-'}\nRole: {entry['role']}\n"
        f"Notes: {entry['notes'] or '-'}\nSubmitted: {entry['created_at']}\n"
    )
    try:
        with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=10) as s:
            if os.environ.get("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes"):
                s.starttls()
            user, pw = os.environ.get("SMTP_USER", ""), os.environ.get("SMTP_PASS", "")
            if user and pw:
                s.login(user, pw)
            s.send_message(msg)
        log(f"volunteer email sent for {entry['role']}")
    except Exception as e:  # the sign-up is already saved; email is best-effort
        log(f"volunteer email failed: {e}")


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


_VOL_CORS = {**_CORS, "Access-Control-Allow-Methods": "POST, OPTIONS",
             "Access-Control-Allow-Headers": "Content-Type"}


def _vol_error(reason: str, code: int = 400, extra: Optional[dict] = None) -> JSONResponse:
    return JSONResponse({"status": "error", "reason": reason}, status_code=code,
                        headers={**_VOL_CORS, **(extra or {})})


@mcp.custom_route("/volunteer", methods=["OPTIONS"])
async def volunteer_preflight(request: Request):
    """CORS preflight so the form on santafehalfmarathon.com can POST here."""
    return Response(status_code=204, headers=_VOL_CORS)


@mcp.custom_route("/volunteer", methods=["POST"])
async def volunteer_submit(request: Request):
    """Accept a volunteer sign-up: JSON {name, email, role, phone?, notes?}."""
    try:
        payload = await request.json()
    except Exception:
        return _vol_error("invalid JSON")
    if not isinstance(payload, dict):
        return _vol_error("invalid JSON")

    # Honeypot: a hidden field real people never fill in.
    if payload.get("website") or payload.get("hp"):
        log("volunteer submission rejected: honeypot")
        return _vol_error("spam detected")

    def field(key: str, max_len: int) -> str:
        return str(payload.get(key) or "").strip()[:max_len]

    name, email = field("name", 120), field("email", 254)
    phone, notes = field("phone", 40), field("notes", 1000)
    role = field("role", 60).lower() or "general"
    if not name or not email:
        return _vol_error("name and email are required")
    if not _EMAIL_RE.match(email):
        return _vol_error("email address looks invalid")
    if role not in VOLUNTEER_ROLES:
        return _vol_error(f"unknown role; choose one of {sorted(VOLUNTEER_ROLES)}")

    allowed, retry = check_rate_limit(_client_ip(request))
    if not allowed:
        return _vol_error("too many sign-ups from this connection; try again later",
                          429, {"Retry-After": str(retry)})

    problem = _recaptcha_problem(payload)
    if problem:
        log(f"volunteer submission rejected: {problem}")
        return _vol_error(problem)

    entry = {
        "name": name, "email": email, "phone": phone, "role": role, "notes": notes,
        "race_year": RACE["date"].year,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    try:
        _save_volunteer(entry)
    except OSError as e:
        log(f"volunteer save failed: {e}")
        return _vol_error("could not save sign-up", 500)
    await run_in_threadpool(_notify_coordinator, entry)  # SMTP blocks; keep the loop free
    return JSONResponse({"status": "ok", "saved": True}, status_code=201, headers=_VOL_CORS)


def _choose_transport() -> str:
    """Pick transport from CLI arg or MCP_TRANSPORT env var. Default: stdio."""
    import os
    arg = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MCP_TRANSPORT", "stdio")
    arg = arg.lower()
    if arg in ("http", "streamable-http", "streamable_http"):
        return "streamable-http"
    if arg == "stdio":
        return "stdio"
    raise SystemExit(f"unknown transport {arg!r}; use 'stdio' or 'http'")


if __name__ == "__main__":
    transport = _choose_transport()
    if transport == "streamable-http":
        log(f"starting on streamable-http at http://{mcp.settings.host}:{mcp.settings.port}/mcp")
    else:
        log("starting on stdio transport")
    mcp.run(transport=transport)
