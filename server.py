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
    "date": dt.date(2026, 9, 20),  # Sunday - half marathon race day
    "distance_miles": 13.1,
    "cutoff": "3:30 (3 hours 30 minutes)",
    "start_line": "La Tienda Plaza, Eldorado (7 Caliente Rd) - point-to-point via Old Las Vegas Hwy",
    "finish_line": "Railyard Park (740 Cerrillos Rd)",
    "base_elevation_ft": 6992,   # Official: La Tienda at Eldorado start elevation
    "high_point_ft": 7330,       # Woods Loop, ~mile 4 (highest point)
    "finish_elevation_ft": 6956, # Railyard finish (net-downhill course)
    "start_time": "07:30 MDT",
    "packet_pickup": (
        "Expo & packet pickup at Old Warehouse 21 (next to Railyard Park): "
        "Fri 12-5pm and Sat 10am-5pm. Race-morning pickup 5:45-7:10am at the "
        "Eldorado start."
    ),
    # Eldorado / La Tienda Plaza start coordinates (for the weather forecast).
    "latitude": 35.5236,
    "longitude": -105.9319,
}

# Approximate per-mile elevations interpolated from the official published
# anchors (start 6,992 ft; high point 7,330 ft near mile 4; finish 6,956 ft;
# net-downhill, USATF-certified 13.109 mi). Drop a real course.gpx to replace.
COURSE_PROFILE_FT = [
    6992, 7080, 7180, 7280, 7330, 7250, 7160, 7090,
    7040, 7010, 6995, 6980, 6968, 6956,
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
            f"per {units}. At 7,000 ft, run the first few miles a touch slower and "
            f"make it up on the downhill back to the Railyard."
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
            f"Race-day forecast: low {lo:.0f}F at the 7am gun, high {hi:.0f}F, "
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
        f"{r['name']}\n"
        f"Date: {r['date'].isoformat()}  Start: {r['start_time']}\n"
        f"Distance: {r['distance_miles']} miles\n"
        f"Start: {r['start_line']}\n"
        f"Finish: {r['finish_line']}\n"
        f"Base elevation: {r['base_elevation_ft']} ft\n"
        f"Packet pickup: {r['packet_pickup']}"
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
        f"crisp early air at the Plaza start and the finish at Railyard Park, and "
        f"remind them to respect the altitude. Talk like a local runner who's "
        f"happy they're here."
    )


# ---- Live results widget: a JSON endpoint + an embeddable HTML page --------
# These ride on the same Streamable HTTP app, so `python server.py http` serves
# both the MCP endpoint (/mcp) and the widget (/leaderboard, /leaderboard.json).
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse

_CORS = {"Access-Control-Allow-Origin": "*"}


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
    html = (pathlib.Path(__file__).with_name("course_chart.html")).read_text()
    return HTMLResponse(html, headers=_CORS)


@mcp.custom_route("/leaderboard", methods=["GET"])
async def leaderboard_page(request: Request):
    """Serve the embeddable widget HTML."""
    html = (pathlib.Path(__file__).with_name("leaderboard.html")).read_text()
    return HTMLResponse(html, headers=_CORS)


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
