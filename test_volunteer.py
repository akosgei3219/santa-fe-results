"""Tests for the POST /volunteer sign-up endpoint."""
import json

import pytest
from starlette.testclient import TestClient

import server

GOOD = {"name": "Maria Lopez", "email": "maria@example.com", "role": "aid station"}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for key in ("RECAPTCHA_SECRET", "SMTP_HOST", "VOLUNTEER_TO",
                "VOLUNTEER_RATE_LIMIT", "VOLUNTEER_RATE_WINDOW"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("VOLUNTEERS_FILE", str(tmp_path / "volunteers.json"))
    server._RATE_STORE.clear()
    yield
    server._RATE_STORE.clear()


@pytest.fixture
def client():
    return TestClient(server.mcp.streamable_http_app())


def saved(tmp_path):
    path = tmp_path / "volunteers.json"
    return json.loads(path.read_text()) if path.exists() else []


def test_signup_saved(client, tmp_path):
    resp = client.post("/volunteer", json=GOOD)
    assert resp.status_code == 201
    assert resp.json() == {"status": "ok", "saved": True}
    assert resp.headers["access-control-allow-origin"] == "*"
    rows = saved(tmp_path)
    assert len(rows) == 1
    assert rows[0]["name"] == "Maria Lopez"
    assert rows[0]["role"] == "aid station"
    assert rows[0]["race_year"] == server.RACE["date"].year


def test_role_defaults_to_general_and_is_case_insensitive(client, tmp_path):
    assert client.post("/volunteer", json={**GOOD, "role": ""}).status_code == 201
    assert client.post("/volunteer", json={**GOOD, "role": "Finish Line"}).status_code == 201
    assert [r["role"] for r in saved(tmp_path)] == ["general", "finish line"]


def test_preflight_allows_cross_site_post(client):
    resp = client.options("/volunteer")
    assert resp.status_code == 204
    assert "POST" in resp.headers["access-control-allow-methods"]
    assert "Content-Type" in resp.headers["access-control-allow-headers"]


@pytest.mark.parametrize("body,reason", [
    ({"email": "a@b.co"}, "name and email are required"),
    ({"name": "A"}, "name and email are required"),
    ({"name": "A", "email": "not-an-email"}, "email address looks invalid"),
    ({"name": "A", "email": "a@b.co", "role": "mayor"}, "unknown role"),
])
def test_validation(client, tmp_path, body, reason):
    resp = client.post("/volunteer", json=body)
    assert resp.status_code == 400
    assert reason in resp.json()["reason"]
    assert saved(tmp_path) == []


def test_invalid_json(client):
    resp = client.post("/volunteer", content=b"{nope", headers={"content-type": "application/json"})
    assert resp.status_code == 400


def test_honeypot_blocks_and_saves_nothing(client, tmp_path):
    resp = client.post("/volunteer", json={**GOOD, "website": "http://spam"})
    assert resp.status_code == 400
    assert saved(tmp_path) == []


def test_long_fields_are_truncated(client, tmp_path):
    client.post("/volunteer", json={**GOOD, "notes": "x" * 5000})
    assert len(saved(tmp_path)[0]["notes"]) == 1000


def test_rate_limit(client, monkeypatch, tmp_path):
    monkeypatch.setenv("VOLUNTEER_RATE_LIMIT", "2")
    assert client.post("/volunteer", json=GOOD).status_code == 201
    assert client.post("/volunteer", json=GOOD).status_code == 201
    resp = client.post("/volunteer", json=GOOD)
    assert resp.status_code == 429
    assert int(resp.headers["retry-after"]) > 0
    assert len(saved(tmp_path)) == 2


def test_rate_limit_window_expires(monkeypatch):
    monkeypatch.setenv("VOLUNTEER_RATE_LIMIT", "1")
    monkeypatch.setenv("VOLUNTEER_RATE_WINDOW", "60")
    assert server.check_rate_limit("9.9.9.9", now=1000)[0]
    assert not server.check_rate_limit("9.9.9.9", now=1030)[0]
    assert server.check_rate_limit("9.9.9.9", now=1061)[0]


def test_rate_limit_uses_forwarded_ip(client, monkeypatch):
    monkeypatch.setenv("VOLUNTEER_RATE_LIMIT", "1")
    h1 = {"x-forwarded-for": "1.1.1.1, 10.0.0.1"}
    h2 = {"x-forwarded-for": "2.2.2.2"}
    assert client.post("/volunteer", json=GOOD, headers=h1).status_code == 201
    assert client.post("/volunteer", json=GOOD, headers=h2).status_code == 201
    assert client.post("/volunteer", json=GOOD, headers=h1).status_code == 429


# --- reCAPTCHA: must be checked BEFORE anything is saved ---

def test_recaptcha_required_when_configured(client, monkeypatch, tmp_path):
    monkeypatch.setenv("RECAPTCHA_SECRET", "s")
    resp = client.post("/volunteer", json=GOOD)
    assert resp.status_code == 400
    assert resp.json()["reason"] == "recaptcha token required"
    assert saved(tmp_path) == []


@pytest.mark.parametrize("reply,ok", [
    ({"success": True, "score": 0.9, "action": "volunteer"}, True),
    ({"success": False}, False),
    ({"success": True, "score": 0.1, "action": "volunteer"}, False),
    ({"success": True, "score": 0.9, "action": "login"}, False),
])
def test_recaptcha_outcomes(client, monkeypatch, tmp_path, reply, ok):
    monkeypatch.setenv("RECAPTCHA_SECRET", "s")
    monkeypatch.setattr(server, "verify_recaptcha", lambda token: reply)
    resp = client.post("/volunteer", json={**GOOD, "recaptcha_token": "t"})
    assert (resp.status_code == 201) is ok
    assert len(saved(tmp_path)) == (1 if ok else 0)


def test_recaptcha_network_error_fails_closed(client, monkeypatch, tmp_path):
    monkeypatch.setenv("RECAPTCHA_SECRET", "s")

    def boom(token):
        raise OSError("down")
    monkeypatch.setattr(server, "verify_recaptcha", boom)
    resp = client.post("/volunteer", json={**GOOD, "recaptcha_token": "t"})
    assert resp.status_code == 400
    assert saved(tmp_path) == []


def test_verify_recaptcha_requires_secret(monkeypatch):
    with pytest.raises(RuntimeError):
        server.verify_recaptcha("t")


# --- coordinator email ---

class FakeSMTP:
    sent = []

    def __init__(self, host, port, timeout):
        self.host, self.port = host, port

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self):
        pass

    def login(self, u, p):
        pass

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)


def test_email_sent_when_configured(client, monkeypatch):
    FakeSMTP.sent = []
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("VOLUNTEER_TO", "coordinator@example.com")
    monkeypatch.setattr(server.smtplib, "SMTP", FakeSMTP)
    assert client.post("/volunteer", json=GOOD).status_code == 201
    msg = FakeSMTP.sent[0]
    assert msg["To"] == "coordinator@example.com"
    assert msg["Reply-To"] == "maria@example.com"
    assert "aid station" in msg["Subject"]


def test_no_email_without_recipient(client, monkeypatch):
    FakeSMTP.sent = []
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(server.smtplib, "SMTP", FakeSMTP)
    assert client.post("/volunteer", json=GOOD).status_code == 201
    assert FakeSMTP.sent == []


def test_email_failure_still_saves(client, monkeypatch, tmp_path):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("VOLUNTEER_TO", "c@example.com")

    def broken(*a, **k):
        raise OSError("smtp down")
    monkeypatch.setattr(server.smtplib, "SMTP", broken)
    assert client.post("/volunteer", json=GOOD).status_code == 201
    assert len(saved(tmp_path)) == 1


# --- 2027 race info ---

def test_race_info_is_2027():
    text = server.race_info()
    assert server.RACE["date"].isoformat() == "2027-09-19"
    assert "Reunity" in text and "Romero Park" in text
    assert "raceId=89412" in text
    assert "10K" in text
