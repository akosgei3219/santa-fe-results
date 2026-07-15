"""Offline tests for the GPX course parser (pytest, no network).

    pytest test_course.py
"""
import math
import pathlib

import pytest

import course

HERE = pathlib.Path(__file__).parent
GPX = (HERE / "sample_course.gpx").read_text()


# --- parsing ---

def test_parse():
    pts = course.parse_gpx(GPX)
    assert len(pts) == 8
    assert pts[0]["lat"] == 35.5236 and pts[0]["ele"] == 2103.0


def test_parse_invalid_xml():
    with pytest.raises(course.CourseError, match="invalid GPX XML"):
        course.parse_gpx("<gpx><trk>")


def test_parse_no_trackpoints():
    with pytest.raises(course.CourseError, match="no <trkpt>"):
        course.parse_gpx('<gpx xmlns="http://www.topografix.com/GPX/1/1"></gpx>')


def test_parse_skips_trkpt_without_coords():
    gpx = ('<gpx><trk><trkseg>'
           '<trkpt lat="35.5"><ele>2100</ele></trkpt>'
           '<trkpt lat="35.5" lon="-105.9"><ele>2100</ele></trkpt>'
           '</trkseg></trk></gpx>')
    pts = course.parse_gpx(gpx)
    assert len(pts) == 1


def test_parse_unparseable_elevation_becomes_none():
    gpx = ('<gpx><trk><trkseg>'
           '<trkpt lat="35.5" lon="-105.9"><ele>n/a</ele></trkpt>'
           '</trkseg></trk></gpx>')
    pts = course.parse_gpx(gpx)
    assert pts[0]["ele"] is None


# --- geometry / profile ---

def test_haversine_known():
    # ~1 degree of latitude ~= 69 miles
    d = course.haversine_mi(35.0, -105.0, 36.0, -105.0)
    assert 68 < d < 70


def test_build_profile():
    prof = course.build_profile(course.parse_gpx(GPX))
    # Eldorado->Railyard straight-ish line ~ 10-11 mi for this synthetic set
    assert prof["distance_miles"] > 5
    assert len(prof["per_mile_elevation_ft"]) == int(math.floor(prof["distance_miles"])) + 1
    # elevations converted m->ft (2103 m ~ 6900 ft)
    assert 6800 < prof["per_mile_elevation_ft"][0] < 7000
    assert prof["total_gain_ft"] > 0 and prof["total_loss_ft"] > 0
    assert prof["max_elevation_ft"] >= prof["min_elevation_ft"]
    assert prof["point_count"] == 8


def test_build_profile_requires_elevations():
    pts = course.parse_gpx(GPX)
    pts[3]["ele"] = None
    with pytest.raises(course.CourseError, match="no elevation"):
        course.build_profile(pts)


# --- elevation fill ---

def test_missing_elevation_fill():
    pts = course.parse_gpx(GPX)
    for p in pts:
        p["ele"] = None
    filled = course.fetch_missing_elevations(
        pts, fetch=lambda url: {"elevation": [2100.0] * len(pts)})
    assert all(p["ele"] == 2100.0 for p in filled)


def test_fill_noop_when_all_present():
    pts = course.parse_gpx(GPX)

    def explode(url):
        raise AssertionError("no fetch should happen when all elevations exist")

    assert course.fetch_missing_elevations(pts, fetch=explode) is pts


def test_fill_batches_of_100():
    from urllib.parse import urlparse, parse_qs
    pts = [{"lat": 35.0 + i * 1e-4, "lon": -105.0, "ele": None} for i in range(150)]
    calls = []

    def fake(url):
        n = len(parse_qs(urlparse(url).query)["latitude"][0].split(","))
        calls.append(n)
        return {"elevation": [2000.0] * n}

    filled = course.fetch_missing_elevations(pts, fetch=fake)
    assert len(calls) == 2 and calls[0] == 100 and calls[1] == 50
    assert all(p["ele"] == 2000.0 for p in filled)


def test_fill_network_failure_raises_course_error():
    import urllib.error
    pts = [{"lat": 35.0, "lon": -105.0, "ele": None}]

    def fail(url):
        raise urllib.error.URLError("offline")

    with pytest.raises(course.CourseError, match="elevation fill failed"):
        course.fetch_missing_elevations(pts, fetch=fail)


def test_fill_short_response_leaves_gaps():
    pts = [{"lat": 35.0, "lon": -105.0, "ele": None},
           {"lat": 35.1, "lon": -105.0, "ele": None}]
    filled = course.fetch_missing_elevations(pts, fetch=lambda url: {"elevation": [2000.0]})
    assert filled[0]["ele"] == 2000.0 and filled[1]["ele"] is None


# --- load_course ---

def test_load_course_absent():
    assert course.load_course(HERE / "does_not_exist.gpx") is None


def test_load_course_happy_path():
    # sample_course.gpx has elevation on every point, so no network fill runs
    prof = course.load_course(HERE / "sample_course.gpx")
    assert prof is not None
    assert prof["distance_miles"] > 5
    assert prof["point_count"] == 8
