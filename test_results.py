"""Offline test for results parsing using the REAL RunSignup response shape."""
import results

# Trimmed real payload captured from the public 2025 results (event 904960).
REAL = {"individual_results_sets":[{"results":[
    {"result_id":196841754,"place":1,"bib":204,"first_name":"Evan",
     "last_name":"Gaynor","gender":"M","age":37,"clock_time":"1:13:12",
     "chip_time":"","pace":"5:37"},
    {"result_id":196841755,"place":2,"bib":190,"first_name":"Paul",
     "last_name":"LeFrancois","gender":"M","age":35,"clock_time":"1:19:44",
     "chip_time":"","pace":"6:07"},
]}]}

def fake_fetch(url):
    return REAL

def test_found_by_bib():
    r = results.find_result(204, event_id=904960, fetch=fake_fetch)
    assert r["name"] == "Evan Gaynor", r
    assert r["place"] == 1 and r["finish_time"] == "1:13:12"
    assert r["pace_per_mile"] == "5:37"
    print("PASS test_found_by_bib")

def test_chip_time_preferred():
    payload = {"individual_results_sets":[{"results":[
        {"bib":300,"first_name":"A","last_name":"B","place":5,
         "clock_time":"2:00:00","chip_time":"1:58:30","pace":"9:03"}]}]}
    r = results.find_result(300, 904960, fetch=lambda u: payload)
    assert r["finish_time"] == "1:58:30", r  # chip beats clock
    print("PASS test_chip_time_preferred")

def test_not_found():
    assert results.find_result(9999, 904960, fetch=fake_fetch) is None
    print("PASS test_not_found")

def test_empty_set():
    assert results.find_result(1, 904960, fetch=lambda u: {"individual_results_sets":[]}) is None
    print("PASS test_empty_set")

for n,f in list(globals().items()):
    if n.startswith("test_"): f()
print("\nALL RESULTS TESTS PASSED")

def test_top_results():
    payload = {"individual_results_sets":[{"results":[
        {"place":1,"bib":204,"first_name":"Evan","last_name":"Gaynor","gender":"M","age":37,"clock_time":"1:13:12","chip_time":"","pace":"5:37"},
        {"place":2,"bib":190,"first_name":"Paul","last_name":"LeFrancois","gender":"M","age":35,"clock_time":"1:19:44","chip_time":"","pace":"6:07"},
        {"place":3,"bib":245,"first_name":"Fernando","last_name":"Carpio Morales","gender":"M","age":30,"clock_time":"1:27:35","chip_time":"","pace":"6:43"},
    ]}]}
    top = results.top_results(904960, n=2, fetch=lambda u: payload)
    assert len(top) == 2 and top[0]["name"] == "Evan Gaynor" and top[0]["place"] == 1
    print("PASS test_top_results")

test_top_results()
print("top_results OK")
