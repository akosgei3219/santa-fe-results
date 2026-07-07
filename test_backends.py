"""Offline unit tests for the registration backends.

Mocks urllib so no real Airtable/RunSignup/RaceRoster calls are made. Validates
both the outgoing request (URL / params) and the normalized Runner returned.
"""
import io
import json
import pathlib
import urllib.request
import backends

CAPTURED = {}

def fake_urlopen(canned: dict):
    def _open(req, timeout=15):
        CAPTURED["url"] = req.full_url
        CAPTURED["headers"] = dict(req.header_items())
        return io.BytesIO(json.dumps(canned).encode())
    return _open

def run(name, fn):
    try:
        fn(); print(f"PASS  {name}")
    except AssertionError as e:
        print(f"FAIL  {name}: {e}"); raise

# --- JSON backend (real file) ---
def test_json():
    b = backends.JsonBackend(pathlib.Path("registrations.json"))
    r = b.lookup(bib=101, email=None)
    assert r and r["name"] == "Akosgei", r
    assert r["packet_picked_up"] is False
    assert b.lookup(bib=999, email=None) is None

# --- Airtable: check formula + normalization ---
def test_airtable():
    canned = {"records": [{"id": "rec1", "fields": {
        "Name": "Maria Lopez", "Bib": 244, "Email": "maria@example.com",
        "Wave": "Corral B", "Status": "confirmed", "PacketPickedUp": True}}]}
    urllib.request.urlopen = fake_urlopen(canned)
    b = backends.AirtableBackend("tok", "appXXX", "Registrations")
    r = b.lookup(bib=244, email=None)
    assert "filterByFormula" in CAPTURED["url"], CAPTURED["url"]
    assert "244" in CAPTURED["url"]
    assert CAPTURED["headers"].get("Authorization") == "Bearer tok"
    assert r["name"] == "Maria Lopez" and r["wave"] == "Corral B"
    assert r["packet_picked_up"] is True

def test_airtable_email_formula():
    urllib.request.urlopen = fake_urlopen({"records": []})
    b = backends.AirtableBackend("tok", "appXXX", "Registrations")
    assert b.lookup(bib=None, email="a@b.com") is None
    assert "LOWER" in CAPTURED["url"]

# --- RunSignup: check search params + normalization ---
def test_runsignup():
    canned = {"participants": [{
        "user": {"first_name": "Margie", "last_name": "Stephens",
                 "email": "margie@example.com"},
        "bib_num": "1201", "status": "active", "corral_name": "Wave 2",
        "checkedin": True}]}
    urllib.request.urlopen = fake_urlopen(canned)
    b = backends.RunSignupBackend("k", "s", "12345", "678")
    r = b.lookup(bib=1201, email=None)
    assert "search_bib=1201" in CAPTURED["url"], CAPTURED["url"]
    assert "format=json" in CAPTURED["url"]
    assert r["name"] == "Margie Stephens" and r["bib"] == 1201
    assert r["wave"] == "Wave 2" and r["status"] == "active"
    assert r["packet_picked_up"] is True

def test_runsignup_email_search():
    urllib.request.urlopen = fake_urlopen({"participants": []})
    b = backends.RunSignupBackend("k", "s", "12345", "678")
    assert b.lookup(bib=None, email="x@y.com") is None
    assert "search_email=x%40y.com" in CAPTURED["url"], CAPTURED["url"]

# --- RaceRoster: envelope + normalization ---
def test_raceroster():
    canned = {"data": [
        {"bib": 501, "first_name": "Devon", "last_name": "Yazzie",
         "email": "devon@example.com", "wave": "Corral C",
         "status": "confirmed", "checked_in": False}]}
    urllib.request.urlopen = fake_urlopen(canned)
    b = backends.RaceRosterBackend("https://example.com/participants", "rrtok")
    r = b.lookup(bib=None, email="devon@example.com")
    assert CAPTURED["headers"].get("Authorization") == "Bearer rrtok"
    assert r["name"] == "Devon Yazzie" and r["bib"] == 501
    assert r["packet_picked_up"] is False

# --- Factory + error handling ---
def test_factory_and_errors():
    import os
    os.environ["REGISTRATION_BACKEND"] = "json"
    assert isinstance(backends.build_backend(pathlib.Path("registrations.json")),
                      backends.JsonBackend)
    os.environ["REGISTRATION_BACKEND"] = "airtable"
    try:
        backends.build_backend(pathlib.Path("registrations.json"))
        assert False, "expected BackendError for missing Airtable config"
    except backends.BackendError:
        pass
    os.environ["REGISTRATION_BACKEND"] = "json"

for n, f in list(globals().items()):
    if n.startswith("test_"):
        run(n, f)
print("\nALL BACKEND TESTS PASSED")
