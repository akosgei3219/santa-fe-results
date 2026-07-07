"""Offline tests for the GPX course parser (no network)."""
import math
import course

GPX = open("sample_course.gpx").read()

def test_parse():
    pts = course.parse_gpx(GPX)
    assert len(pts) == 8, len(pts)
    assert pts[0]["lat"] == 35.5236 and pts[0]["ele"] == 2103.0
    print("PASS test_parse")

def test_haversine_known():
    # ~1 degree of latitude ~= 69 miles
    d = course.haversine_mi(35.0, -105.0, 36.0, -105.0)
    assert 68 < d < 70, d
    print(f"PASS test_haversine_known ({d:.1f} mi)")

def test_build_profile():
    prof = course.build_profile(course.parse_gpx(GPX))
    # Eldorado->Railyard straight-ish line ~ 10-11 mi for this synthetic set
    assert prof["distance_miles"] > 5, prof
    assert len(prof["per_mile_elevation_ft"]) == int(math.floor(prof["distance_miles"])) + 1
    # elevations converted m->ft (2103 m ~ 6900 ft)
    assert 6800 < prof["per_mile_elevation_ft"][0] < 7000, prof["per_mile_elevation_ft"][0]
    assert prof["total_gain_ft"] > 0 and prof["total_loss_ft"] > 0
    assert prof["max_elevation_ft"] >= prof["min_elevation_ft"]
    print("PASS test_build_profile", {k: prof[k] for k in
          ("distance_miles","total_gain_ft","total_loss_ft","min_elevation_ft","max_elevation_ft")})

def test_missing_elevation_fill():
    # strip elevations, fill via a fake Open-Meteo response
    pts = course.parse_gpx(GPX)
    for p in pts: p["ele"] = None
    def fake(url):
        n = url.count("%2C") + url.count(",")  # rough count of points in batch
        return {"elevation": [2100.0]*len(pts)}
    filled = course.fetch_missing_elevations(pts, fetch=fake)
    assert all(p["ele"] == 2100.0 for p in filled)
    print("PASS test_missing_elevation_fill")

def test_load_course_absent(tmpname="does_not_exist.gpx"):
    import pathlib
    assert course.load_course(pathlib.Path(tmpname)) is None
    print("PASS test_load_course_absent")

for n,f in list(globals().items()):
    if n.startswith("test_"): f()
print("\nALL COURSE TESTS PASSED")
