"""Offline tests for results parsing using the REAL RunSignup response shape.

    pytest test_results.py
"""
import io
import json
import urllib.error
import urllib.request
from urllib.parse import urlparse, parse_qs

import pytest

import results

# Trimmed real payload captured from the public 2025 results (event 904960).
REAL = {"individual_results_sets": [{"results": [
    {"result_id": 196841754, "place": 1, "bib": 204, "first_name": "Evan",
     "last_name": "Gaynor", "gender": "M", "age": 37, "clock_time": "1:13:12",
     "chip_time": "", "pace": "5:37"},
    {"result_id": 196841755, "place": 2, "bib": 190, "first_name": "Paul",
     "last_name": "LeFrancois", "gender": "M", "age": 35, "clock_time": "1:19:44",
     "chip_time": "", "pace": "6:07"},
]}]}


def fake_fetch(url):
    return REAL


def page_of(url):
    return int(parse_qs(urlparse(url).query)["page"][0])


def make_row(bib, place):
    return {"place": place, "bib": bib, "first_name": "R", "last_name": f"unner{bib}",
            "clock_time": "2:00:00", "chip_time": "", "pace": "9:00"}


# --- _get_json error mapping ---

def test_get_json_success(monkeypatch):
    body = json.dumps({"ok": True}).encode()
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda url, timeout=15: io.BytesIO(body))
    assert results._get_json("https://example.com/api") == {"ok": True}


def test_get_json_http_error(monkeypatch):
    def _fail(url, timeout=15):
        raise urllib.error.HTTPError(url, 500, "err", {}, io.BytesIO(b""))
    monkeypatch.setattr(urllib.request, "urlopen", _fail)
    with pytest.raises(results.ResultsError, match="HTTP 500"):
        results._get_json("https://example.com/api")


def test_get_json_network_error(monkeypatch):
    def _fail(url, timeout=15):
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(urllib.request, "urlopen", _fail)
    with pytest.raises(results.ResultsError, match="request failed"):
        results._get_json("https://example.com/api")


# --- find_result ---

def test_found_by_bib():
    r = results.find_result(204, event_id=904960, fetch=fake_fetch)
    assert r["name"] == "Evan Gaynor"
    assert r["place"] == 1 and r["finish_time"] == "1:13:12"
    assert r["pace_per_mile"] == "5:37"


def test_chip_time_preferred():
    payload = {"individual_results_sets": [{"results": [
        {"bib": 300, "first_name": "A", "last_name": "B", "place": 5,
         "clock_time": "2:00:00", "chip_time": "1:58:30", "pace": "9:03"}]}]}
    r = results.find_result(300, 904960, fetch=lambda u: payload)
    assert r["finish_time"] == "1:58:30"  # chip beats clock


def test_not_found():
    assert results.find_result(9999, 904960, fetch=fake_fetch) is None


def test_empty_set():
    assert results.find_result(1, 904960,
                               fetch=lambda u: {"individual_results_sets": []}) is None


def test_empty_rows():
    payload = {"individual_results_sets": [{"results": []}]}
    assert results.find_result(1, 904960, fetch=lambda u: payload) is None


def test_finds_bib_on_second_page():
    # page 1 is full (1000 rows), so the search must continue to page 2
    def fetch(url):
        if page_of(url) == 1:
            rows = [make_row(i, i) for i in range(1, 1001)]
        else:
            rows = [make_row(5555, 1001)]
        return {"individual_results_sets": [{"results": rows}]}

    r = results.find_result(5555, 904960, fetch=fetch)
    assert r is not None and r["place"] == 1001


def test_not_found_stops_at_partial_page():
    # a page with < 1000 rows is the last one; no further pages are fetched
    calls = []

    def fetch(url):
        calls.append(page_of(url))
        return {"individual_results_sets": [{"results": [make_row(1, 1)]}]}

    assert results.find_result(9999, 904960, fetch=fetch) is None
    assert calls == [1]


def test_page_safety_bound():
    # every page comes back full and never contains the bib: must stop at 50
    calls = []

    def fetch(url):
        calls.append(page_of(url))
        rows = [make_row(i, i) for i in range(1, 1001)]
        return {"individual_results_sets": [{"results": rows}]}

    assert results.find_result(999999, 904960, fetch=fetch) is None
    assert len(calls) == 50


# --- parse_result_row ---

def test_parse_row_fallbacks():
    r = results.parse_result_row({"clock_time": "2:10:00"})
    assert r["name"] == "(unknown)"
    assert r["finish_time"] == "2:10:00"  # clock used when no chip time


# --- top_results ---

def test_top_results():
    payload = {"individual_results_sets": [{"results": [
        {"place": 1, "bib": 204, "first_name": "Evan", "last_name": "Gaynor",
         "gender": "M", "age": 37, "clock_time": "1:13:12", "chip_time": "", "pace": "5:37"},
        {"place": 2, "bib": 190, "first_name": "Paul", "last_name": "LeFrancois",
         "gender": "M", "age": 35, "clock_time": "1:19:44", "chip_time": "", "pace": "6:07"},
        {"place": 3, "bib": 245, "first_name": "Fernando", "last_name": "Carpio Morales",
         "gender": "M", "age": 30, "clock_time": "1:27:35", "chip_time": "", "pace": "6:43"},
    ]}]}
    top = results.top_results(904960, n=2, fetch=lambda u: payload)
    assert len(top) == 2
    assert top[0]["name"] == "Evan Gaynor" and top[0]["place"] == 1


def test_top_results_empty_set():
    assert results.top_results(904960, n=5,
                               fetch=lambda u: {"individual_results_sets": []}) == []


def test_top_results_requests_at_least_one():
    captured = {}

    def fetch(url):
        captured.update(parse_qs(urlparse(url).query))
        return {"individual_results_sets": []}

    results.top_results(904960, n=0, fetch=fetch)
    assert captured["results_per_page"] == ["1"]
