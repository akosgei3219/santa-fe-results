"""
Read-only FluentCRM audit for santafehalfmarathon.com.

Pulls, via FluentCRM's REST API (Settings -> REST API key, scoped to
FluentCRM only — not your WordPress password):

    - every email campaign (broadcast) with status, schedule time, and the
      send-from address it will actually use
    - a check of the key campaign dates (July 7 sent? Aug 18 / Sept 15
      scheduled?)
    - subscriber totals vs. the expected list size (1,067)
    - tags and lists with their subscriber counts

Credentials come from the environment so they never land in a file or a
chat log:

    PowerShell:  $env:FLUENTCRM_USER = "..." ; $env:FLUENTCRM_KEY = "..."
    bash:        export FLUENTCRM_USER=...    ; export FLUENTCRM_KEY=...

Then:

    python fluentcrm_audit.py                 # human-readable report
    python fluentcrm_audit.py --json          # raw JSON, for digging deeper

Only the Python standard library is used. The script only issues GET
requests — it cannot change anything in FluentCRM. Delete the API key in
wp-admin (FluentCRM -> Settings -> REST API) when the audit is done.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_SITE = "https://santafehalfmarathon.com"
EXPECTED_SUBSCRIBERS = 1067
# The three sends the audit is verifying: did July 7 go out, and are the
# Aug 18 / Sept 15 broadcasts actually scheduled?
KEY_DATES = ["2026-07-07", "2026-08-18", "2026-09-15"]

# Statuses FluentCRM uses for campaigns. Anything else is shown as-is.
SENT_STATUSES = {"archived", "sent"}
SUBSCRIBER_STATUSES = ["subscribed", "pending", "unsubscribed", "bounced", "complained"]


class AuditError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------
def _get_json(site: str, path: str, user: str, key: str,
              params: dict | None = None, timeout: int = 20) -> dict:
    url = site.rstrip("/") + "/wp-json/fluent-crm/v2/" + path.lstrip("/")
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    token = base64.b64encode(f"{user}:{key}".encode()).decode()
    req = urllib.request.Request(url, headers={"Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise AuditError(
                "401 from FluentCRM — the key pair was rejected. Re-check "
                "FLUENTCRM_USER / FLUENTCRM_KEY against the key you made in "
                "FluentCRM -> Settings -> REST API."
            ) from e
        body = e.read().decode(errors="replace")[:300]
        raise AuditError(f"HTTP {e.code} from {url.split('?')[0]}: {body}") from e
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise AuditError(f"request to {url.split('?')[0]} failed: {e}") from e


def _unwrap(payload: dict, key: str) -> tuple[list, int | None]:
    """FluentCRM wraps collections either as {key: [...]} or as a Laravel
    paginator {key: {"data": [...], "total": N}}. Return (rows, total)."""
    node = payload.get(key, payload)
    if isinstance(node, list):
        return node, None
    if isinstance(node, dict):
        return node.get("data") or [], node.get("total")
    return [], None


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------
def fetch_campaigns(site: str, user: str, key: str) -> list[dict]:
    campaigns, page = [], 1
    while True:
        payload = _get_json(site, "campaigns", user, key,
                            {"page": page, "per_page": 50})
        rows, total = _unwrap(payload, "campaigns")
        campaigns.extend(rows)
        if not rows or total is None or len(campaigns) >= total:
            break
        page += 1
    return campaigns


def fetch_subscriber_totals(site: str, user: str, key: str) -> dict:
    """Overall total, plus a per-status breakdown when the API honors the
    status filter (older FluentCRM builds ignore it — then we skip it)."""
    payload = _get_json(site, "subscribers", user, key, {"per_page": 1})
    _, overall = _unwrap(payload, "subscribers")
    by_status = {}
    for status in SUBSCRIBER_STATUSES:
        payload = _get_json(site, "subscribers", user, key,
                            {"per_page": 1, "statuses[]": status})
        _, count = _unwrap(payload, "subscribers")
        by_status[status] = count
    # If every status "filter" returned the overall total, the filter was
    # ignored and the breakdown is meaningless.
    if overall is not None and list(by_status.values()).count(overall) > 1:
        by_status = {}
    return {"total": overall, "by_status": by_status}


def fetch_taxonomy(site: str, user: str, key: str, kind: str) -> list[dict]:
    """kind is 'tags' or 'lists'."""
    payload = _get_json(site, kind, user, key, {"per_page": 200})
    rows, _ = _unwrap(payload, kind)
    return rows


# ---------------------------------------------------------------------------
# Shaping
# ---------------------------------------------------------------------------
def summarize_campaign(c: dict) -> dict:
    mailer = (c.get("settings") or {}).get("mailer_settings") or {}
    if mailer.get("is_custom") in (True, "yes", 1, "1") and mailer.get("from_email"):
        sender = f"{mailer.get('from_name', '')} <{mailer['from_email']}>".strip()
    else:
        sender = "(site default sender)"
    return {
        "id": c.get("id"),
        "title": c.get("title") or c.get("email_subject") or "(untitled)",
        "subject": c.get("email_subject") or "",
        "status": c.get("status") or "(unknown)",
        "scheduled_at": c.get("scheduled_at") or "",
        "created_at": c.get("created_at") or "",
        "updated_at": c.get("updated_at") or "",
        "recipients": c.get("recipients_count"),
        "from": sender,
    }


def _campaign_date(c: dict) -> str:
    """Best date to identify a campaign by: schedule time, else last update."""
    return (c["scheduled_at"] or c["updated_at"] or c["created_at"] or "")[:10]


def check_key_dates(campaigns: list[dict], key_dates: list[str]) -> list[str]:
    lines = []
    for day in key_dates:
        hits = [c for c in campaigns if _campaign_date(c) == day]
        if not hits:
            lines.append(f"{day}: NO campaign found on this date — needs a look.")
            continue
        for c in hits:
            if c["status"] in SENT_STATUSES:
                verdict = "SENT"
            elif c["status"] == "scheduled":
                verdict = f"scheduled for {c['scheduled_at']}"
            else:
                verdict = f"status is '{c['status']}' — NOT sent, NOT scheduled"
            lines.append(f"{day}: \"{c['title']}\" — {verdict} (from: {c['from']})")
    return lines


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def format_report(campaigns: list[dict], subs: dict, tags: list[dict],
                  lists: list[dict], expected: int, key_dates: list[str]) -> str:
    out = ["FluentCRM audit", "=" * 60, ""]

    out.append(f"Key dates ({', '.join(key_dates)})")
    out.append("-" * 60)
    out.extend(check_key_dates(campaigns, key_dates) or ["(no campaigns at all)"])
    out.append("")

    out.append(f"All campaigns ({len(campaigns)})")
    out.append("-" * 60)
    for c in sorted(campaigns, key=_campaign_date, reverse=True):
        when = c["scheduled_at"] or f"updated {c['updated_at']}"
        recip = f", {c['recipients']} recipients" if c["recipients"] else ""
        out.append(f"[{c['status']:>9}] {c['title']}")
        out.append(f"            {when}{recip} — from: {c['from']}")
    if not campaigns:
        out.append("(none)")
    out.append("")

    out.append("Subscribers")
    out.append("-" * 60)
    total = subs.get("total")
    if total is None:
        out.append("total: (API did not return a count)")
    else:
        diff = total - expected
        note = "matches" if diff == 0 else f"{diff:+d} vs. the {expected} list"
        out.append(f"total: {total}  ({note})")
    for status, count in (subs.get("by_status") or {}).items():
        out.append(f"  {status:>12}: {count}")
    out.append("")

    for label, rows in (("Lists", lists), ("Tags", tags)):
        out.append(f"{label} ({len(rows)})")
        out.append("-" * 60)
        for r in rows:
            count = r.get("subscribersCount", r.get("totalCount", "?"))
            out.append(f"  {r.get('title', r.get('slug', '?'))}: {count} subscribers")
        if not rows:
            out.append("  (none)")
        out.append("")

    return "\n".join(out)


# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--site", default=os.environ.get("FLUENTCRM_SITE_URL", DEFAULT_SITE),
                    help=f"WordPress site URL (default {DEFAULT_SITE})")
    ap.add_argument("--expect", type=int, default=EXPECTED_SUBSCRIBERS,
                    help=f"expected subscriber count (default {EXPECTED_SUBSCRIBERS})")
    ap.add_argument("--key-dates", nargs="*", default=KEY_DATES, metavar="YYYY-MM-DD",
                    help="campaign dates to verify")
    ap.add_argument("--json", action="store_true",
                    help="dump raw data as JSON instead of the report")
    args = ap.parse_args(argv)

    user = os.environ.get("FLUENTCRM_USER", "")
    key = os.environ.get("FLUENTCRM_KEY", "")
    if not (user and key):
        print("Set FLUENTCRM_USER and FLUENTCRM_KEY first (FluentCRM -> Settings\n"
              "-> REST API -> Add New Key), e.g.:\n\n"
              '  PowerShell:  $env:FLUENTCRM_USER = "..." ; $env:FLUENTCRM_KEY = "..."\n'
              "  bash:        export FLUENTCRM_USER=...   ; export FLUENTCRM_KEY=...\n",
              file=sys.stderr)
        return 2

    try:
        campaigns = [summarize_campaign(c) for c in fetch_campaigns(args.site, user, key)]
        subs = fetch_subscriber_totals(args.site, user, key)
        tags = fetch_taxonomy(args.site, user, key, "tags")
        lists = fetch_taxonomy(args.site, user, key, "lists")
    except AuditError as e:
        print(f"audit failed: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"campaigns": campaigns, "subscribers": subs,
                          "tags": tags, "lists": lists}, indent=2))
    else:
        print(format_report(campaigns, subs, tags, lists, args.expect, args.key_dates))
        print("Done. Remember to delete the 'Claude audit' key in\n"
              "FluentCRM -> Settings -> REST API now that you're finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
