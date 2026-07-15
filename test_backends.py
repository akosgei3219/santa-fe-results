"""Offline unit tests for the registration backends (pytest, no network).

Mocks urllib so no real Airtable/RunSignup/RaceRoster calls are made. Validates
both the outgoing request (URL / params / headers) and the normalized Runner
returned, plus the factory and its error paths.

    pytest test_backends.py
"""
import io
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request

import pytest

import backends

HERE = pathlib.Path(__file__).parent
REGISTRATIONS = HERE / "registrations.json"


@pytest.fixture
def fake_http(monkeypatch):
    """Install a canned urlopen response; returns a dict capturing the request."""
    captured = {}

    def install(canned):
        def _open(req, timeout=15):
            captured["url"] = req.full_url
            captured["headers"] = dict(req.header_items())
            return io.BytesIO(json.dumps(canned).encode())
        monkeypatch.setattr(urllib.request, "urlopen", _open)
        return captured

    return install


# --- _http_get_json error mapping ---

def test_http_get_json_http_error(monkeypatch):
    def _open(req, timeout=15):
        raise urllib.error.HTTPError(req.full_url, 503, "boom", {},
                                     io.BytesIO(b"upstream down"))
    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(backends.BackendError, match="HTTP 503"):
        backends._http_get_json("https://example.com/api?x=1")


def test_http_get_json_network_error(monkeypatch):
    def _open(req, timeout=15):
        raise urllib.error.URLError("no route to host")
    monkeypatch.setattr(urllib.request, "urlopen", _open)
    with pytest.raises(backends.BackendError, match="failed"):
        backends._http_get_json("https://example.com/api")


def test_http_get_json_bad_json(monkeypatch):
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=15: io.BytesIO(b"<html>not json"))
    with pytest.raises(backends.BackendError):
        backends._http_get_json("https://example.com/api")


# --- JSON backend (real file) ---

def test_json_lookup_by_bib():
    b = backends.JsonBackend(REGISTRATIONS)
    r = b.lookup(bib=101, email=None)
    assert r and r["name"] == "Akosgei"
    assert r["packet_picked_up"] is False


def test_json_lookup_by_email_case_insensitive():
    b = backends.JsonBackend(REGISTRATIONS)
    r = b.lookup(bib=None, email="MARIA.LOPEZ@example.com")
    assert r and r["name"] == "Maria Lopez"
    assert r["packet_picked_up"] is True


def test_json_lookup_miss():
    assert backends.JsonBackend(REGISTRATIONS).lookup(bib=999, email=None) is None


def test_json_missing_file():
    b = backends.JsonBackend(HERE / "no_such_file.json")
    with pytest.raises(backends.BackendError, match="not found"):
        b.lookup(bib=101, email=None)


def test_json_corrupt_file(tmp_path):
    bad = tmp_path / "registrations.json"
    bad.write_text("{not valid json")
    with pytest.raises(backends.BackendError, match="not valid JSON"):
        backends.JsonBackend(bad).lookup(bib=101, email=None)


# --- Airtable: check formula + normalization ---

def test_airtable_bib_lookup(fake_http):
    canned = {"records": [{"id": "rec1", "fields": {
        "Name": "Maria Lopez", "Bib": 244, "Email": "maria@example.com",
        "Wave": "Corral B", "Status": "confirmed", "PacketPickedUp": True}}]}
    captured = fake_http(canned)
    b = backends.AirtableBackend("tok", "appXXX", "Registrations")
    r = b.lookup(bib=244, email=None)
    assert "filterByFormula" in captured["url"]
    assert "244" in captured["url"]
    assert captured["headers"].get("Authorization") == "Bearer tok"
    assert r["name"] == "Maria Lopez" and r["wave"] == "Corral B"
    assert r["packet_picked_up"] is True


def test_airtable_email_formula(fake_http):
    captured = fake_http({"records": []})
    b = backends.AirtableBackend("tok", "appXXX", "Registrations")
    assert b.lookup(bib=None, email="a@b.com") is None
    assert "LOWER" in captured["url"]


def test_airtable_email_quote_escaped(fake_http):
    captured = fake_http({"records": []})
    b = backends.AirtableBackend("tok", "appXXX", "Registrations")
    b.lookup(bib=None, email="o'brien@example.com")
    # single quote must be escaped so it can't break out of the formula string
    assert r"\'" in urllib.parse.unquote(captured["url"])


def test_airtable_field_map_override(fake_http):
    canned = {"records": [{"fields": {
        "Runner": "Ana", "BibNo": 7, "Wave": "A", "Status": "confirmed",
        "PacketPickedUp": False}}]}
    fake_http(canned)
    b = backends.AirtableBackend("tok", "appXXX", "Registrations",
                                 field_map={"name": "Runner", "bib": "BibNo"})
    r = b.lookup(bib=7, email=None)
    assert r["name"] == "Ana" and r["bib"] == 7


def test_airtable_requires_config():
    with pytest.raises(backends.BackendError, match="Airtable needs"):
        backends.AirtableBackend("", "appXXX", "Registrations")


# --- RunSignup: check search params + normalization ---

def test_runsignup_bib_search(fake_http):
    canned = {"participants": [{
        "user": {"first_name": "Margie", "last_name": "Stephens",
                 "email": "margie@example.com"},
        "bib_num": "1201", "status": "active", "corral_name": "Wave 2",
        "checkedin": True}]}
    captured = fake_http(canned)
    b = backends.RunSignupBackend("k", "s", "12345", "678")
    r = b.lookup(bib=1201, email=None)
    assert "search_bib=1201" in captured["url"]
    assert "format=json" in captured["url"]
    assert r["name"] == "Margie Stephens" and r["bib"] == 1201
    assert r["wave"] == "Wave 2" and r["status"] == "active"
    assert r["packet_picked_up"] is True


def test_runsignup_email_search(fake_http):
    captured = fake_http({"participants": []})
    b = backends.RunSignupBackend("k", "s", "12345", "678")
    assert b.lookup(bib=None, email="x@y.com") is None
    assert "search_email=x%40y.com" in captured["url"]


def test_runsignup_requires_config():
    with pytest.raises(backends.BackendError, match="RunSignup needs"):
        backends.RunSignupBackend("k", "", "12345", "678")


# --- RaceRoster: envelope + normalization ---

def test_raceroster_data_envelope(fake_http):
    canned = {"data": [
        {"bib": 501, "first_name": "Devon", "last_name": "Yazzie",
         "email": "devon@example.com", "wave": "Corral C",
         "status": "confirmed", "checked_in": False}]}
    captured = fake_http(canned)
    b = backends.RaceRosterBackend("https://example.com/participants", "rrtok")
    r = b.lookup(bib=None, email="devon@example.com")
    assert captured["headers"].get("Authorization") == "Bearer rrtok"
    assert r["name"] == "Devon Yazzie" and r["bib"] == 501
    assert r["packet_picked_up"] is False


def test_raceroster_bare_list_and_miss(fake_http):
    fake_http([{"bib": 1, "first_name": "A", "last_name": "B",
                "email": "a@b.com"}])
    b = backends.RaceRosterBackend("https://example.com/participants", "rrtok")
    assert b.lookup(bib=999, email=None) is None


def test_raceroster_requires_config():
    with pytest.raises(backends.BackendError, match="RaceRoster needs"):
        backends.RaceRosterBackend("", "rrtok")


# --- Factory: every choice + error paths ---

def test_factory_json_default(monkeypatch):
    monkeypatch.delenv("REGISTRATION_BACKEND", raising=False)
    b = backends.build_backend(REGISTRATIONS)
    assert isinstance(b, backends.JsonBackend)


def test_factory_airtable_missing_config(monkeypatch):
    monkeypatch.setenv("REGISTRATION_BACKEND", "airtable")
    monkeypatch.delenv("AIRTABLE_TOKEN", raising=False)
    with pytest.raises(backends.BackendError):
        backends.build_backend(REGISTRATIONS)


def test_factory_airtable_configured(monkeypatch):
    monkeypatch.setenv("REGISTRATION_BACKEND", "airtable")
    monkeypatch.setenv("AIRTABLE_TOKEN", "t")
    monkeypatch.setenv("AIRTABLE_BASE_ID", "b")
    monkeypatch.setenv("AIRTABLE_TABLE", "Registrations")
    assert isinstance(backends.build_backend(REGISTRATIONS),
                      backends.AirtableBackend)


def test_factory_runsignup_configured(monkeypatch):
    monkeypatch.setenv("REGISTRATION_BACKEND", "runsignup")
    monkeypatch.setenv("RUNSIGNUP_API_KEY", "k")
    monkeypatch.setenv("RUNSIGNUP_API_SECRET", "s")
    monkeypatch.setenv("RUNSIGNUP_RACE_ID", "1")
    monkeypatch.setenv("RUNSIGNUP_EVENT_ID", "2")
    assert isinstance(backends.build_backend(REGISTRATIONS),
                      backends.RunSignupBackend)


def test_factory_raceroster_configured(monkeypatch):
    monkeypatch.setenv("REGISTRATION_BACKEND", "raceroster")
    monkeypatch.setenv("RACEROSTER_PARTICIPANTS_URL", "https://example.com/p")
    monkeypatch.setenv("RACEROSTER_TOKEN", "t")
    assert isinstance(backends.build_backend(REGISTRATIONS),
                      backends.RaceRosterBackend)


def test_factory_unknown_backend(monkeypatch):
    monkeypatch.setenv("REGISTRATION_BACKEND", "carrier-pigeon")
    with pytest.raises(backends.BackendError, match="unknown REGISTRATION_BACKEND"):
        backends.build_backend(REGISTRATIONS)
