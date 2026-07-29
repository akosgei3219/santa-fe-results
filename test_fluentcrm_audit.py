"""Offline tests for fluentcrm_audit.py — no network, no credentials."""

import fluentcrm_audit as fa


def _campaign(**over):
    base = {
        "id": 7,
        "title": "Race week reminders",
        "email_subject": "See you Sunday!",
        "status": "scheduled",
        "scheduled_at": "2026-08-18 09:00:00",
        "created_at": "2026-07-01 12:00:00",
        "updated_at": "2026-07-02 12:00:00",
        "recipients_count": 1067,
        "settings": {"mailer_settings": {
            "is_custom": "yes",
            "from_name": "Santa Fe Half",
            "from_email": "hello@santafehalfmarathon.com",
        }},
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# _unwrap tolerates both response envelopes FluentCRM uses
# ---------------------------------------------------------------------------
def test_unwrap_bare_list():
    rows, total = fa._unwrap({"tags": [{"title": "VIP"}]}, "tags")
    assert rows == [{"title": "VIP"}]
    assert total is None


def test_unwrap_paginator():
    payload = {"subscribers": {"data": [{"id": 1}], "total": 1067, "current_page": 1}}
    rows, total = fa._unwrap(payload, "subscribers")
    assert rows == [{"id": 1}]
    assert total == 1067


def test_unwrap_missing_key():
    assert fa._unwrap({}, "campaigns") == ([], None)


# ---------------------------------------------------------------------------
# summarize_campaign
# ---------------------------------------------------------------------------
def test_summarize_custom_sender():
    s = fa.summarize_campaign(_campaign())
    assert s["from"] == "Santa Fe Half <hello@santafehalfmarathon.com>"
    assert s["status"] == "scheduled"
    assert s["recipients"] == 1067


def test_summarize_default_sender_and_missing_fields():
    s = fa.summarize_campaign({"id": 1, "email_subject": "Hi"})
    assert s["from"] == "(site default sender)"
    assert s["title"] == "Hi"  # falls back to subject
    assert s["status"] == "(unknown)"


# ---------------------------------------------------------------------------
# key-date verdicts — the July 7 / Aug 18 / Sept 15 questions
# ---------------------------------------------------------------------------
def test_key_dates_sent_scheduled_and_missing():
    campaigns = [fa.summarize_campaign(c) for c in [
        _campaign(status="archived", scheduled_at="2026-07-07 08:00:00",
                  title="July newsletter"),
        _campaign(status="scheduled", scheduled_at="2026-08-18 09:00:00"),
        _campaign(status="draft", scheduled_at="2026-09-15 09:00:00",
                  title="September blast"),
    ]]
    lines = fa.check_key_dates(campaigns, ["2026-07-07", "2026-08-18",
                                           "2026-09-15", "2026-10-01"])
    assert "SENT" in lines[0]
    assert "scheduled for 2026-08-18 09:00:00" in lines[1]
    assert "NOT sent, NOT scheduled" in lines[2]
    assert lines[3].startswith("2026-10-01: NO campaign found")


def test_key_date_uses_updated_at_when_never_scheduled():
    c = fa.summarize_campaign(_campaign(status="draft", scheduled_at=None,
                                        updated_at="2026-07-07 10:00:00"))
    assert fa._campaign_date(c) == "2026-07-07"


# ---------------------------------------------------------------------------
# report formatting
# ---------------------------------------------------------------------------
def test_format_report_subscriber_diff_and_sections():
    campaigns = [fa.summarize_campaign(_campaign())]
    subs = {"total": 1060, "by_status": {"subscribed": 1055, "bounced": 5}}
    report = fa.format_report(campaigns, subs,
                              tags=[{"title": "2026 runners", "subscribersCount": 900}],
                              lists=[], expected=1067, key_dates=["2026-08-18"])
    assert "total: 1060  (-7 vs. the 1067 list)" in report
    assert "2026 runners: 900 subscribers" in report
    assert "scheduled for 2026-08-18 09:00:00" in report
    assert "Lists (0)" in report


def test_format_report_exact_match():
    report = fa.format_report([], {"total": 1067, "by_status": {}},
                              [], [], expected=1067, key_dates=[])
    assert "total: 1067  (matches)" in report


# ---------------------------------------------------------------------------
# main() refuses to run without credentials (and never touches the network)
# ---------------------------------------------------------------------------
def test_main_requires_env(monkeypatch, capsys):
    monkeypatch.delenv("FLUENTCRM_USER", raising=False)
    monkeypatch.delenv("FLUENTCRM_KEY", raising=False)
    assert fa.main([]) == 2
    assert "FLUENTCRM_USER" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# HTTP layer, with urlopen mocked — still no real network
# ---------------------------------------------------------------------------
import io
import json
import urllib.error


class _FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _serve(monkeypatch, handler):
    """Route fa's urlopen through handler(url, request)."""
    def fake_urlopen(req, timeout=0):
        return handler(req.full_url, req)
    monkeypatch.setattr(fa.urllib.request, "urlopen", fake_urlopen)


def test_get_json_sends_scoped_basic_auth(monkeypatch):
    seen = {}

    def handler(url, req):
        seen["url"] = url
        seen["auth"] = req.get_header("Authorization")
        return _FakeResponse({"ok": True})

    _serve(monkeypatch, handler)
    out = fa._get_json("https://example.com/", "tags", "user-a", "key-b", {"per_page": 5})
    assert out == {"ok": True}
    assert seen["url"] == "https://example.com/wp-json/fluent-crm/v2/tags?per_page=5"
    import base64
    assert seen["auth"] == "Basic " + base64.b64encode(b"user-a:key-b").decode()


def _http_error(url, code, body=b""):
    return urllib.error.HTTPError(url, code, "err", {}, io.BytesIO(body))


def test_get_json_401_explains_bad_key(monkeypatch):
    _serve(monkeypatch, lambda url, req: (_ for _ in ()).throw(_http_error(url, 401)))
    try:
        fa._get_json("https://example.com", "tags", "u", "k")
        assert False, "expected AuditError"
    except fa.AuditError as e:
        assert "key pair was rejected" in str(e)


def test_get_json_other_http_error_includes_body(monkeypatch):
    _serve(monkeypatch, lambda url, req: (_ for _ in ()).throw(_http_error(url, 500, b"boom")))
    try:
        fa._get_json("https://example.com", "tags", "u", "k")
        assert False, "expected AuditError"
    except fa.AuditError as e:
        assert "HTTP 500" in str(e) and "boom" in str(e)


def test_get_json_network_failure(monkeypatch):
    _serve(monkeypatch, lambda url, req: (_ for _ in ()).throw(urllib.error.URLError("down")))
    try:
        fa._get_json("https://example.com", "tags", "u", "k")
        assert False, "expected AuditError"
    except fa.AuditError as e:
        assert "failed" in str(e)


# ---------------------------------------------------------------------------
# fetchers
# ---------------------------------------------------------------------------
def test_fetch_campaigns_paginates(monkeypatch):
    def handler(url, req):
        if "page=1" in url:
            return _FakeResponse({"campaigns": {"data": [{"id": 1}, {"id": 2}], "total": 3}})
        return _FakeResponse({"campaigns": {"data": [{"id": 3}], "total": 3}})

    _serve(monkeypatch, handler)
    got = fa.fetch_campaigns("https://example.com", "u", "k")
    assert [c["id"] for c in got] == [1, 2, 3]


def test_fetch_campaigns_bare_list_single_page(monkeypatch):
    _serve(monkeypatch, lambda url, req: _FakeResponse({"campaigns": [{"id": 9}]}))
    assert fa.fetch_campaigns("https://example.com", "u", "k") == [{"id": 9}]


def test_fetch_subscriber_totals_with_working_filter(monkeypatch):
    def handler(url, req):
        if "statuses" not in url:
            return _FakeResponse({"subscribers": {"data": [], "total": 1067}})
        for status, n in [("subscribed", 1000), ("pending", 30), ("unsubscribed", 20),
                          ("bounced", 12), ("complained", 5)]:
            if status in url:
                return _FakeResponse({"subscribers": {"data": [], "total": n}})
        raise AssertionError(url)

    _serve(monkeypatch, handler)
    subs = fa.fetch_subscriber_totals("https://example.com", "u", "k")
    assert subs["total"] == 1067
    assert subs["by_status"]["subscribed"] == 1000


def test_fetch_subscriber_totals_ignored_filter_drops_breakdown(monkeypatch):
    _serve(monkeypatch, lambda url, req: _FakeResponse(
        {"subscribers": {"data": [], "total": 1067}}))
    subs = fa.fetch_subscriber_totals("https://example.com", "u", "k")
    assert subs["total"] == 1067
    assert subs["by_status"] == {}


def test_fetch_taxonomy(monkeypatch):
    _serve(monkeypatch, lambda url, req: _FakeResponse(
        {"tags": [{"title": "VIP", "subscribersCount": 12}]}))
    assert fa.fetch_taxonomy("https://example.com", "u", "k", "tags")[0]["title"] == "VIP"


# ---------------------------------------------------------------------------
# main() success and failure paths (fetchers stubbed)
# ---------------------------------------------------------------------------
def _with_creds(monkeypatch):
    monkeypatch.setenv("FLUENTCRM_USER", "u")
    monkeypatch.setenv("FLUENTCRM_KEY", "k")


def test_main_report_path(monkeypatch, capsys):
    _with_creds(monkeypatch)
    monkeypatch.setattr(fa, "fetch_campaigns", lambda *a: [_campaign()])
    monkeypatch.setattr(fa, "fetch_subscriber_totals",
                        lambda *a: {"total": None, "by_status": {}})
    monkeypatch.setattr(fa, "fetch_taxonomy", lambda *a: [])
    assert fa.main([]) == 0
    out = capsys.readouterr().out
    assert "FluentCRM audit" in out
    assert "(API did not return a count)" in out
    assert "delete the 'Claude audit' key" in out


def test_main_json_path(monkeypatch, capsys):
    _with_creds(monkeypatch)
    monkeypatch.setattr(fa, "fetch_campaigns", lambda *a: [_campaign()])
    monkeypatch.setattr(fa, "fetch_subscriber_totals",
                        lambda *a: {"total": 1067, "by_status": {}})
    monkeypatch.setattr(fa, "fetch_taxonomy", lambda *a: [])
    assert fa.main(["--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["subscribers"]["total"] == 1067
    assert data["campaigns"][0]["status"] == "scheduled"


def test_main_audit_error(monkeypatch, capsys):
    _with_creds(monkeypatch)
    monkeypatch.setattr(fa, "fetch_campaigns",
                        lambda *a: (_ for _ in ()).throw(fa.AuditError("nope")))
    assert fa.main([]) == 1
    assert "audit failed: nope" in capsys.readouterr().err
