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
