"""
Pluggable registration backends for the Santa Fe Half Marathon MCP server.

Every backend implements one method:

    lookup(bib: int | None, email: str | None) -> Optional[Runner]

where Runner is a normalized dict the server understands, regardless of which
platform it came from:

    {
        "name": str,
        "bib": int | None,
        "wave": str,
        "status": str,          # e.g. "confirmed", "active", "waitlist"
        "packet_picked_up": bool,
    }

Return None if no runner matches. This is the seam that makes the MCP tool
backend-agnostic: swap the backend and the tool's interface to the model does
not change at all.

Backends included:
    - JsonBackend       : local registrations.json (default; no network)
    - AirtableBackend   : Airtable REST API (filterByFormula)
    - RunSignupBackend  : RunSignup REST API (search_bib / search_email)
    - RaceRosterBackend : adapter for a RaceRoster participants endpoint

Only the Python standard library is used, so there is no extra dependency.
Select a backend with the REGISTRATION_BACKEND env var (see build_backend()).
"""

from __future__ import annotations

import os
import json
import pathlib
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional, Callable

Runner = dict


class BackendError(RuntimeError):
    """Raised when a backend is misconfigured or the upstream call fails hard."""


def _http_get_json(url: str, headers: Optional[dict] = None, timeout: int = 15) -> dict:
    """GET a URL and parse JSON. Raises BackendError on network/parse failure."""
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise BackendError(f"HTTP {e.code} from {url.split('?')[0]}: {body}") from e
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise BackendError(f"request to {url.split('?')[0]} failed: {e}") from e


# ---------------------------------------------------------------------------
# JSON (default) — reads the local registrations.json file. No network.
# ---------------------------------------------------------------------------
class JsonBackend:
    def __init__(self, path: pathlib.Path):
        self.path = pathlib.Path(path)

    def lookup(self, bib: Optional[int], email: Optional[str]) -> Optional[Runner]:
        try:
            runners = json.loads(self.path.read_text())
        except FileNotFoundError:
            raise BackendError(f"registration file not found: {self.path}")
        except ValueError as e:
            raise BackendError(f"registration file is not valid JSON ({self.path}): {e}")
        for r in runners:
            if (bib is not None and r.get("bib") == bib) or (
                email is not None and str(r.get("email", "")).lower() == email.lower()
            ):
                return {
                    "name": r["name"],
                    "bib": r.get("bib"),
                    "wave": r.get("wave", ""),
                    "status": r.get("status", ""),
                    "packet_picked_up": bool(r.get("packet_picked_up", False)),
                }
        return None


# ---------------------------------------------------------------------------
# Airtable — one row per runner in a base/table you own.
# Field names are configurable so this fits whatever your columns are called.
# ---------------------------------------------------------------------------
class AirtableBackend:
    def __init__(self, token: str, base_id: str, table: str,
                 field_map: Optional[dict] = None):
        if not (token and base_id and table):
            raise BackendError("Airtable needs AIRTABLE_TOKEN, AIRTABLE_BASE_ID, AIRTABLE_TABLE")
        self.token = token
        self.base_id = base_id
        self.table = table
        # Map normalized keys -> your Airtable column names.
        self.f = {
            "name": "Name", "bib": "Bib", "email": "Email",
            "wave": "Wave", "status": "Status", "packet": "PacketPickedUp",
        }
        if field_map:
            self.f.update(field_map)

    def lookup(self, bib: Optional[int], email: Optional[str]) -> Optional[Runner]:
        # Build an Airtable filterByFormula matching bib or email.
        if bib is not None:
            formula = f"{{{self.f['bib']}}}={bib}"
        else:
            safe = str(email).replace("'", r"\'")
            formula = f"LOWER({{{self.f['email']}}})=LOWER('{safe}')"
        query = urllib.parse.urlencode({"filterByFormula": formula, "maxRecords": 1})
        url = (f"https://api.airtable.com/v0/{self.base_id}/"
               f"{urllib.parse.quote(self.table)}?{query}")
        data = _http_get_json(url, headers={"Authorization": f"Bearer {self.token}"})
        records = data.get("records", [])
        if not records:
            return None
        fields = records[0].get("fields", {})
        return {
            "name": fields.get(self.f["name"], ""),
            "bib": fields.get(self.f["bib"]),
            "wave": fields.get(self.f["wave"], ""),
            "status": fields.get(self.f["status"], ""),
            "packet_picked_up": bool(fields.get(self.f["packet"], False)),
        }


# ---------------------------------------------------------------------------
# RunSignup — REST API. Uses server-side search params so we fetch one runner,
# not the whole roster. Docs: api.runsignup.com/rest/race/:race_id/participants
# ---------------------------------------------------------------------------
class RunSignupBackend:
    def __init__(self, api_key: str, api_secret: str, race_id: str, event_id: str):
        if not (api_key and api_secret and race_id and event_id):
            raise BackendError(
                "RunSignup needs RUNSIGNUP_API_KEY, RUNSIGNUP_API_SECRET, "
                "RUNSIGNUP_RACE_ID, RUNSIGNUP_EVENT_ID"
            )
        self.api_key = api_key
        self.api_secret = api_secret
        self.race_id = race_id
        self.event_id = event_id

    def lookup(self, bib: Optional[int], email: Optional[str]) -> Optional[Runner]:
        params = {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "event_id": self.event_id,
            "format": "json",
            "results_per_page": 1,
            "include_corrals": "T",  # so we can surface a wave/corral
        }
        if bib is not None:
            params["search_bib"] = bib
        else:
            params["search_email"] = email
        url = (f"https://api.runsignup.com/rest/race/{self.race_id}/participants?"
               + urllib.parse.urlencode(params))
        data = _http_get_json(url)
        parts = data.get("participants", []) if isinstance(data, dict) else []
        if not parts:
            return None
        p = parts[0]
        user = p.get("user", {})
        name = " ".join(x for x in [user.get("first_name"), user.get("last_name")] if x)
        corral = p.get("corral_name") or p.get("corral") or ""
        return {
            "name": name or "(unknown)",
            "bib": int(p["bib_num"]) if p.get("bib_num") else None,
            "wave": corral,
            "status": p.get("status", ""),
            # RunSignup exposes check-in via include_checkin_data; treat any
            # checkin record as packet pickup if present.
            "packet_picked_up": bool(p.get("checkedin") or p.get("checkin_data")),
        }


# ---------------------------------------------------------------------------
# RaceRoster — adapter. RaceRoster's participant API is OAuth-gated and the
# exact endpoint/fields depend on your account and API version, so this reads
# them from env rather than hardcoding. Set RACEROSTER_PARTICIPANTS_URL to the
# endpoint that returns your event's participants as JSON, and RACEROSTER_TOKEN
# to a bearer token. Adjust the field names below to match your response.
# ---------------------------------------------------------------------------
class RaceRosterBackend:
    def __init__(self, participants_url: str, token: str):
        if not (participants_url and token):
            raise BackendError(
                "RaceRoster needs RACEROSTER_PARTICIPANTS_URL and RACEROSTER_TOKEN"
            )
        self.url = participants_url
        self.token = token

    def lookup(self, bib: Optional[int], email: Optional[str]) -> Optional[Runner]:
        data = _http_get_json(self.url, headers={"Authorization": f"Bearer {self.token}"})
        # Accept either a bare list or a {"data": [...]} / {"participants": [...]} envelope.
        rows = data if isinstance(data, list) else (
            data.get("data") or data.get("participants") or []
        )
        for row in rows:
            row_bib = row.get("bib") or row.get("bib_number")
            row_email = (row.get("email") or "").lower()
            if (bib is not None and str(row_bib) == str(bib)) or (
                email is not None and row_email == email.lower()
            ):
                first = row.get("first_name") or row.get("firstName") or ""
                last = row.get("last_name") or row.get("lastName") or ""
                return {
                    "name": (f"{first} {last}").strip() or row.get("name", "(unknown)"),
                    "bib": int(row_bib) if row_bib else None,
                    "wave": row.get("wave") or row.get("corral") or "",
                    "status": row.get("status", ""),
                    "packet_picked_up": bool(row.get("checked_in") or row.get("packet_picked_up")),
                }
        return None


# ---------------------------------------------------------------------------
# Factory — choose a backend from environment. Default is the local JSON file.
# ---------------------------------------------------------------------------
def build_backend(json_fallback_path: pathlib.Path) -> "object":
    choice = os.environ.get("REGISTRATION_BACKEND", "json").lower()

    if choice == "json":
        return JsonBackend(json_fallback_path)

    if choice == "airtable":
        return AirtableBackend(
            token=os.environ.get("AIRTABLE_TOKEN", ""),
            base_id=os.environ.get("AIRTABLE_BASE_ID", ""),
            table=os.environ.get("AIRTABLE_TABLE", ""),
        )

    if choice == "runsignup":
        return RunSignupBackend(
            api_key=os.environ.get("RUNSIGNUP_API_KEY", ""),
            api_secret=os.environ.get("RUNSIGNUP_API_SECRET", ""),
            race_id=os.environ.get("RUNSIGNUP_RACE_ID", ""),
            event_id=os.environ.get("RUNSIGNUP_EVENT_ID", ""),
        )

    if choice == "raceroster":
        return RaceRosterBackend(
            participants_url=os.environ.get("RACEROSTER_PARTICIPANTS_URL", ""),
            token=os.environ.get("RACEROSTER_TOKEN", ""),
        )

    raise BackendError(f"unknown REGISTRATION_BACKEND {choice!r}")
