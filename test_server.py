"""Offline tests for the MCP server's tool/resource/prompt layer (pytest).

Everything network- or backend-shaped is monkeypatched, so these run with no
network and no live MCP client. The FastMCP decorators return the original
functions, so tools are called directly. The widget HTTP routes are exercised
through Starlette's TestClient on the same app `python server.py http` serves.

    pytest test_server.py
"""
import datetime as dt
import io
import json
import sys
import urllib.error
import urllib.request

import pytest
from starlette.testclient import TestClient

import backends
import course
import results
import server


# --- pace_calculator ---

def test_pace_hms():
    out = server.pace_calculator("1:45:00")
    assert out["pace_per_unit"] == "8:01 / mi"
    assert "8:01" in out["summary"]


def test_pace_mmss():
    out = server.pace_calculator("45:30")
    # 2730 s / 13.1 mi = 208.4 s/mi -> 3:28
    assert out["pace_per_unit"] == "3:28 / mi"


def test_pace_km():
    out = server.pace_calculator("1:45:00", units="km")
    # 6300 s / 21.08 km -> 4:59
    assert out["pace_per_unit"] == "4:59 / km"


@pytest.mark.parametrize("bad", ["1:2:3:4", "90"])
def test_pace_wrong_part_count(bad):
    with pytest.raises(ValueError, match="target_finish"):
        server.pace_calculator(bad)


def test_pace_non_numeric():
    with pytest.raises(ValueError):
        server.pace_calculator("about two hours")


# --- days_until_race ---

def test_days_until_building(monkeypatch):
    monkeypatch.setitem(server.RACE, "date", dt.date.today() + dt.timedelta(days=30))
    out = server.days_until_race()
    assert out["days_until"] == 30 and "still building" in out["note"]


def test_days_until_taper(monkeypatch):
    monkeypatch.setitem(server.RACE, "date", dt.date.today() + dt.timedelta(days=5))
    out = server.days_until_race()
    assert out["days_until"] == 5 and "taper" in out["note"]


def test_days_until_race_day(monkeypatch):
    monkeypatch.setitem(server.RACE, "date", dt.date.today())
    out = server.days_until_race()
    assert out["days_until"] == 0 and "race day" in out["note"].lower()


def test_days_until_past(monkeypatch):
    monkeypatch.setitem(server.RACE, "date", dt.date.today() - dt.timedelta(days=3))
    out = server.days_until_race()
    assert out["days_until"] == -3 and "3 days ago" in out["note"]


# --- altitude_advice ---

@pytest.mark.parametrize("from_ft,tier", [
    (0, "big jump"),        # sea level: gain 6992
    (1992, "big jump"),     # gain exactly 5000
    (4992, "noticeable"),   # gain exactly 2000
    (5000, "minimal"),      # gain 1992
    (7000, "minimal"),
])
def test_altitude_tiers(from_ft, tier):
    out = server.altitude_advice(coming_from_elevation_ft=from_ft)
    assert out["adjustment"] == tier
    assert out["elevation_gain_ft"] == server.RACE["base_elevation_ft"] - from_ft


# --- race_day_weather ---

def _weather_response(dates):
    n = len(dates)
    return {"daily": {
        "time": dates,
        "temperature_2m_max": [75.0] * n,
        "temperature_2m_min": [48.0] * n,
        "precipitation_probability_max": [10.0] * n,
        "windspeed_10m_max": [12.0] * n,
    }}


def test_weather_ok(monkeypatch):
    target = server.RACE["date"].isoformat()
    body = json.dumps(_weather_response(["2000-01-01", target])).encode()
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda url, timeout=15: io.BytesIO(body))
    out = server.race_day_weather()
    assert out["status"] == "ok"
    assert out["high_f"] == 75.0 and out["low_f"] == 48.0
    assert "forecast" in out["summary"].lower()


def test_weather_out_of_range(monkeypatch):
    body = json.dumps(_weather_response(["2000-01-01"])).encode()
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda url, timeout=15: io.BytesIO(body))
    out = server.race_day_weather()
    assert out["status"] == "out_of_range"


def test_weather_network_down(monkeypatch):
    def _fail(url, timeout=15):
        raise urllib.error.URLError("no network")
    monkeypatch.setattr(urllib.request, "urlopen", _fail)
    out = server.race_day_weather()
    assert out["status"] == "unavailable" and "no network" in out["reason"]


# --- lookup_registration ---

class FakeBackend:
    def __init__(self, runner=None, error=None):
        self.runner, self.error = runner, error

    def lookup(self, bib, email):
        if self.error:
            raise self.error
        return self.runner


@pytest.fixture
def use_backend(monkeypatch):
    def install(backend):
        monkeypatch.setattr(server, "get_backend", lambda: backend)
    return install


def test_registration_requires_exactly_one_arg():
    with pytest.raises(ValueError, match="exactly one"):
        server.lookup_registration()
    with pytest.raises(ValueError, match="exactly one"):
        server.lookup_registration(bib=101, email="a@b.com")


def test_registration_found(use_backend):
    use_backend(FakeBackend(runner={
        "name": "Maria Lopez", "bib": 244, "wave": "Corral B",
        "status": "confirmed", "packet_picked_up": True}))
    out = server.lookup_registration(bib=244)
    assert out["status"] == "found"
    assert out["packet"] == "picked up"
    assert "Maria Lopez" in out["summary"]


def test_registration_not_found(use_backend):
    use_backend(FakeBackend(runner=None))
    out = server.lookup_registration(email="nobody@example.com")
    assert out["status"] == "not_found"
    assert out["query"] == "nobody@example.com"


def test_registration_backend_error(use_backend):
    use_backend(FakeBackend(error=backends.BackendError("backend down")))
    out = server.lookup_registration(bib=1)
    assert out["status"] == "error" and "backend down" in out["reason"]


def test_registration_default_backend_reads_local_json(monkeypatch):
    monkeypatch.delenv("REGISTRATION_BACKEND", raising=False)
    monkeypatch.setattr(server, "_BACKEND", None)  # force a fresh build
    out = server.lookup_registration(bib=101)
    assert out["status"] == "found" and out["name"] == "Akosgei"


# --- lookup_result ---

FINISH = {"name": "Evan Gaynor", "bib": 204, "place": 1, "gender": "M",
          "age": 37, "finish_time": "1:13:12", "pace_per_mile": "5:37"}


def test_lookup_result_found(monkeypatch):
    monkeypatch.setattr(results, "find_result", lambda bib, event_id: dict(FINISH))
    out = server.lookup_result(bib=204, year=2025)
    assert out["status"] == "found" and out["place"] == 1
    assert "1:13:12" in out["summary"]


def test_lookup_result_not_found(monkeypatch):
    monkeypatch.setattr(results, "find_result", lambda bib, event_id: None)
    out = server.lookup_result(bib=9999, year=2025)
    assert out["status"] == "not_found" and out["bib"] == 9999


def test_lookup_result_unknown_year():
    out = server.lookup_result(bib=204, year=1999)
    assert out["status"] == "error" and "1999" in out["reason"]


def test_lookup_result_api_error(monkeypatch):
    def _fail(bib, event_id):
        raise results.ResultsError("HTTP 500 from results API")
    monkeypatch.setattr(results, "find_result", _fail)
    out = server.lookup_result(bib=204, year=2025)
    assert out["status"] == "error" and "HTTP 500" in out["reason"]


# --- results_leaderboard ---

def test_leaderboard_ok(monkeypatch):
    monkeypatch.setattr(results, "top_results", lambda event_id, n: [dict(FINISH)] * n)
    out = server.results_leaderboard(year=2025, top_n=3)
    assert out["status"] == "ok" and out["count"] == 3


@pytest.mark.parametrize("requested,clamped", [(0, 1), (-5, 1), (500, 50), (10, 10)])
def test_leaderboard_clamps_top_n(monkeypatch, requested, clamped):
    seen = {}

    def fake(event_id, n):
        seen["n"] = n
        return []
    monkeypatch.setattr(results, "top_results", fake)
    server.results_leaderboard(year=2025, top_n=requested)
    assert seen["n"] == clamped


def test_leaderboard_unknown_year():
    assert server.results_leaderboard(year=1999)["status"] == "error"


def test_leaderboard_api_error(monkeypatch):
    def _fail(event_id, n):
        raise results.ResultsError("boom")
    monkeypatch.setattr(results, "top_results", _fail)
    out = server.results_leaderboard(year=2025)
    assert out["status"] == "error" and out["reason"] == "boom"


# --- course_elevation ---

PROFILE = {"distance_miles": 13.11, "per_mile_elevation_ft": [6992, 7080],
           "total_gain_ft": 500, "total_loss_ft": 540,
           "min_elevation_ft": 6956, "max_elevation_ft": 7330, "point_count": 42}


def test_course_elevation_real_gpx(monkeypatch):
    monkeypatch.setattr(course, "load_course", lambda: dict(PROFILE))
    out = server.course_elevation()
    assert out["status"] == "ok" and out["source"] == "course.gpx"
    assert out["distance_miles"] == 13.11


def test_course_elevation_placeholder(monkeypatch):
    monkeypatch.setattr(course, "load_course", lambda: None)
    out = server.course_elevation()
    assert out["status"] == "ok" and "placeholder" in out["source"]
    assert out["per_mile_elevation_ft"] == server.COURSE_PROFILE_FT


def test_course_elevation_error(monkeypatch):
    def _fail():
        raise course.CourseError("invalid GPX XML")
    monkeypatch.setattr(course, "load_course", _fail)
    out = server.course_elevation()
    assert out["status"] == "error" and "invalid GPX" in out["reason"]


# --- race_photos tool ---

def test_photos_no_year():
    out = server.race_photos()
    assert out["status"] == "ok"
    assert "requested_year" not in out
    assert out["runsignup"]["by_year"]["2025"].startswith("https://")


def test_photos_known_year():
    out = server.race_photos(year=2025)
    assert out["requested_year"] == 2025
    assert out["requested_album"].startswith("https://")


def test_photos_unknown_year():
    out = server.race_photos(year=1999)
    assert out["requested_album"] == "no RunSignup album for that year"


# --- resources ---

def test_race_info_resource():
    text = server.race_info()
    assert server.RACE["name"] in text
    assert server.RACE["date"].isoformat() in text
    assert "Packet pickup" in text


def test_course_profile_resource_placeholder(monkeypatch):
    monkeypatch.setattr(course, "load_course", lambda: None)
    text = server.course_profile()
    assert "Illustrative profile" in text
    # one line per mile of the built-in table
    assert f"0\t{server.COURSE_PROFILE_FT[0]}" in text


def test_course_profile_resource_real(monkeypatch):
    monkeypatch.setattr(course, "load_course", lambda: dict(PROFILE))
    text = server.course_profile()
    assert text.startswith("Real course (13.11 mi)")
    assert "+500 ft / -540 ft" in text


def test_course_profile_resource_swallows_course_error(monkeypatch):
    def _fail():
        raise course.CourseError("bad gpx")
    monkeypatch.setattr(course, "load_course", _fail)
    assert "Illustrative profile" in server.course_profile()


def test_photos_resource():
    text = server.race_photos_resource()
    assert "RunSignup galleries:" in text
    assert "Google Drive archive:" in text
    assert "OneDrive" in text


# --- prompt ---

def test_pep_talk_prompt():
    text = server.race_day_pep_talk("Jo")
    assert "Jo" in text and "Santa Fe Half Marathon" in text


# --- transport selection ---

def test_transport_default_stdio(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["server.py"])
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    assert server._choose_transport() == "stdio"


@pytest.mark.parametrize("arg", ["http", "HTTP", "streamable-http", "streamable_http"])
def test_transport_http_aliases(monkeypatch, arg):
    monkeypatch.setattr(sys, "argv", ["server.py", arg])
    assert server._choose_transport() == "streamable-http"


def test_transport_from_env(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["server.py"])
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    assert server._choose_transport() == "streamable-http"


def test_transport_unknown_exits(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["server.py", "carrier-pigeon"])
    with pytest.raises(SystemExit):
        server._choose_transport()


# --- widget HTTP routes (same app `python server.py http` serves) ---

@pytest.fixture
def client():
    return TestClient(server.mcp.streamable_http_app())


def test_site_asset_serves_photo(client):
    resp = client.get("/assets/sfi-half-marathon-04.jpg")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.headers["access-control-allow-origin"] == "*"
    assert "max-age" in resp.headers["cache-control"]
    assert len(resp.content) > 1000


def test_site_asset_unknown_name_404(client):
    assert client.get("/assets/nope.jpg").status_code == 404


def test_site_asset_traversal_and_bad_type_404(client):
    assert client.get("/assets/..%2Fserver.py").status_code == 404
    assert client.get("/assets/registrations.json").status_code == 404


def test_leaderboard_json_ok(monkeypatch, client):
    monkeypatch.setattr(results, "top_results", lambda event_id, n: [dict(FINISH)] * n)
    resp = client.get("/leaderboard.json?year=2025&top_n=2")
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "*"
    body = resp.json()
    assert body["status"] == "ok" and body["count"] == 2


def test_leaderboard_json_bad_params(client):
    resp = client.get("/leaderboard.json?year=nope")
    assert resp.status_code == 400
    assert resp.json()["status"] == "error"


def test_leaderboard_json_upstream_error_is_502(client):
    resp = client.get("/leaderboard.json?year=1999")  # unknown year -> error status
    assert resp.status_code == 502


def test_result_json_found(monkeypatch, client):
    monkeypatch.setattr(results, "find_result", lambda bib, event_id: dict(FINISH))
    resp = client.get("/result.json?bib=204&year=2025")
    assert resp.status_code == 200
    assert resp.json()["status"] == "found"


def test_result_json_not_found_is_200(monkeypatch, client):
    monkeypatch.setattr(results, "find_result", lambda bib, event_id: None)
    resp = client.get("/result.json?bib=9999&year=2025")
    assert resp.status_code == 200
    assert resp.json()["status"] == "not_found"


def test_result_json_bad_params(client):
    resp = client.get("/result.json?bib=abc&year=2025")
    assert resp.status_code == 400


def test_result_json_missing_bib(client):
    resp = client.get("/result.json?year=2025")
    assert resp.status_code == 400


def test_result_json_upstream_error_is_502(monkeypatch, client):
    def _fail(bib, event_id):
        raise results.ResultsError("down")
    monkeypatch.setattr(results, "find_result", _fail)
    resp = client.get("/result.json?bib=204&year=2025")
    assert resp.status_code == 502


@pytest.mark.parametrize("path,marker", [
    ("/leaderboard", "<html"),
    ("/course", "<html"),
])
def test_static_pages_served(client, path, marker):
    resp = client.get(path)
    assert resp.status_code == 200
    assert marker in resp.text.lower()
    assert resp.headers["access-control-allow-origin"] == "*"
