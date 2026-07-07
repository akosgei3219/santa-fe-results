"""
Public race-results lookup for the Santa Fe Half Marathon MCP server.

Unlike registration data (which RunSignup gates behind an API key + the race's
`can_use_registration_api` flag), the RunSignup *results* endpoint is public for
races that publish results. This module queries it and normalizes a runner's
finish into a simple dict. It powers the `lookup_result` tool and works today
for past editions; on race day it returns live results as they post.

Endpoint:
    GET https://runsignup.com/rest/race/{race_id}/results/get-results
        ?event_id={event_id}&format=json

Only the Python standard library is used.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional

# Half Marathon event IDs by year for race 83604 (from the RunSignup race API).
# 2026 will have results once the race is run.
HALF_MARATHON_EVENTS = {
    2023: 681853,
    2025: 904960,
    2026: 1056101,
}
DEFAULT_RACE_ID = 83604


class ResultsError(RuntimeError):
    pass


def _get_json(url: str, timeout: int = 15) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise ResultsError(f"HTTP {e.code} from results API") from e
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise ResultsError(f"results request failed: {e}") from e


def parse_result_row(row: dict) -> dict:
    """Normalize one RunSignup result row into a simple finish record."""
    name = " ".join(x for x in [row.get("first_name"), row.get("last_name")] if x)
    # RunSignup gives chip_time when chip-timed, else clock_time.
    finish = row.get("chip_time") or row.get("clock_time") or ""
    return {
        "name": name or "(unknown)",
        "bib": row.get("bib"),
        "place": row.get("place"),
        "gender": row.get("gender"),
        "age": row.get("age"),
        "finish_time": finish,
        "pace_per_mile": row.get("pace"),
    }


def find_result(bib: int, event_id: int, race_id: int = DEFAULT_RACE_ID,
                fetch=_get_json) -> Optional[dict]:
    """Look up one runner's result by bib within a results set.

    `fetch` is injectable so this is unit-testable without network access.
    Pages through the results set until the bib is found (bounded).
    """
    page = 1
    while page <= 50:  # safety bound; a half marathon fits well within this
        params = urllib.parse.urlencode({
            "event_id": event_id,
            "format": "json",
            "results_per_page": 1000,
            "page": page,
        })
        url = (f"https://runsignup.com/rest/race/{race_id}/results/"
               f"get-results?{params}")
        data = fetch(url)
        sets = data.get("individual_results_sets", [])
        if not sets:
            return None
        rows = sets[0].get("results", [])
        if not rows:
            return None
        for row in rows:
            if str(row.get("bib")) == str(bib):
                return parse_result_row(row)
        if len(rows) < 1000:
            return None  # last page reached, not found
        page += 1
    return None


def top_results(event_id: int, n: int = 10, race_id: int = DEFAULT_RACE_ID,
                fetch=_get_json) -> list[dict]:
    """Return the top-N finishers (by place) for a results set, normalized.

    `fetch` is injectable for testing. Reads the first results page (results are
    returned in place order), trims to n.
    """
    params = urllib.parse.urlencode({
        "event_id": event_id, "format": "json",
        "results_per_page": max(1, n), "page": 1,
    })
    url = (f"https://runsignup.com/rest/race/{race_id}/results/"
           f"get-results?{params}")
    data = fetch(url)
    sets = data.get("individual_results_sets", [])
    if not sets:
        return []
    rows = sets[0].get("results", [])[:n]
    return [parse_result_row(r) for r in rows]
