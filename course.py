"""
GPX course-profile parsing for the Santa Fe Half Marathon MCP server.

Drop the real course export at `course.gpx` (next to this file) and the
`race://course-profile` resource and `course_elevation` tool will use it
automatically. Without a GPX, callers fall back to the illustrative
COURSE_PROFILE_FT list in server.py.

Pipeline:
    parse GPX trackpoints (lat, lon, ele)
      -> cumulative distance via the haversine formula
      -> resample to one elevation sample per mile
      -> total ascent / descent, min / max

If the GPX has no <ele> data, `fetch_missing_elevations` can fill it from the
free Open-Meteo Elevation API (no key). Only the Python standard library is
used for parsing; the elevation fill is optional and degrades gracefully.
"""

from __future__ import annotations

import json
import math
import pathlib
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional

COURSE_GPX = pathlib.Path(__file__).with_name("course.gpx")
_EARTH_RADIUS_MI = 3958.7613  # miles


class CourseError(RuntimeError):
    pass


def haversine_mi(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance between two lat/lon points, in miles."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * _EARTH_RADIUS_MI * math.asin(math.sqrt(a))


def parse_gpx(text: str) -> list[dict]:
    """Extract ordered trackpoints from GPX XML.

    Returns a list of {"lat","lon","ele"} (ele is meters or None). Handles the
    default GPX namespace by matching on local tag names.
    """
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        raise CourseError(f"invalid GPX XML: {e}") from e

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]  # strip namespace

    points = []
    for el in root.iter():
        if local(el.tag) == "trkpt":
            lat = el.get("lat"); lon = el.get("lon")
            if lat is None or lon is None:
                continue
            ele = None
            for child in el:
                if local(child.tag) == "ele" and child.text:
                    try:
                        ele = float(child.text)
                    except ValueError:
                        ele = None
            points.append({"lat": float(lat), "lon": float(lon), "ele": ele})
    if not points:
        raise CourseError("no <trkpt> points found in GPX")
    return points


def _m_to_ft(m: float) -> float:
    return m * 3.280839895


def build_profile(points: list[dict]) -> dict:
    """Turn trackpoints into a per-mile elevation profile + gain/loss summary.

    Requires elevation on every point (call fetch_missing_elevations first if
    the GPX lacks <ele>). Elevations are returned in feet.
    """
    if any(p["ele"] is None for p in points):
        raise CourseError("some trackpoints have no elevation; fill them first")

    # cumulative distance (miles) at each point
    cum = [0.0]
    for a, b in zip(points, points[1:]):
        cum.append(cum[-1] + haversine_mi(a["lat"], a["lon"], b["lat"], b["lon"]))
    total_mi = cum[-1]

    # per-mile elevation via linear interpolation on cumulative distance
    per_mile = []
    n_marks = int(math.floor(total_mi))
    j = 0
    for mile in range(0, n_marks + 1):
        while j < len(cum) - 1 and cum[j + 1] < mile:
            j += 1
        if cum[j] >= mile or j + 1 >= len(cum):
            ele_m = points[j]["ele"]
        else:
            span = cum[j + 1] - cum[j]
            frac = 0 if span == 0 else (mile - cum[j]) / span
            ele_m = points[j]["ele"] + frac * (points[j + 1]["ele"] - points[j]["ele"])
        per_mile.append(round(_m_to_ft(ele_m)))

    # total ascent / descent over the full track (feet)
    gain = loss = 0.0
    for a, b in zip(points, points[1:]):
        d = b["ele"] - a["ele"]
        if d > 0:
            gain += d
        else:
            loss += -d

    eles_ft = [_m_to_ft(p["ele"]) for p in points]
    return {
        "distance_miles": round(total_mi, 2),
        "per_mile_elevation_ft": per_mile,
        "total_gain_ft": round(_m_to_ft(gain)),
        "total_loss_ft": round(_m_to_ft(loss)),
        "min_elevation_ft": round(min(eles_ft)),
        "max_elevation_ft": round(max(eles_ft)),
        "point_count": len(points),
    }


def fetch_missing_elevations(points: list[dict], fetch=None) -> list[dict]:
    """Fill missing <ele> using the Open-Meteo Elevation API (batches of 100).

    `fetch` is injectable for testing. Network failures raise CourseError.
    """
    if all(p["ele"] is not None for p in points):
        return points

    def _default_fetch(url):
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    fetch = fetch or _default_fetch

    idx_missing = [i for i, p in enumerate(points) if p["ele"] is None]
    for start in range(0, len(idx_missing), 100):
        batch = idx_missing[start:start + 100]
        lats = ",".join(str(points[i]["lat"]) for i in batch)
        lons = ",".join(str(points[i]["lon"]) for i in batch)
        url = ("https://api.open-meteo.com/v1/elevation?"
               + urllib.parse.urlencode({"latitude": lats, "longitude": lons}))
        try:
            data = fetch(url)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            raise CourseError(f"elevation fill failed: {e}") from e
        elevs = data.get("elevation", [])
        for k, i in enumerate(batch):
            if k < len(elevs):
                points[i]["ele"] = float(elevs[k])
    return points


def load_course(path: pathlib.Path = COURSE_GPX, fill_missing: bool = True) -> Optional[dict]:
    """Load and profile course.gpx if it exists. Returns None when absent."""
    if not path.exists():
        return None
    points = parse_gpx(path.read_text())
    if fill_missing:
        points = fetch_missing_elevations(points)
    return build_profile(points)
