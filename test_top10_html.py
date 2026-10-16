"""Tests for the top-10 HTML mirror generator."""

import pytest

import results
import top10_html


ROWS = [
    {"name": "Evan Gaynor", "bib": 204, "place": 1, "gender": "M", "age": 37,
     "finish_time": "1:13:12", "pace_per_mile": "5:37"},
    {"name": "Ana <O'Brien> & Co", "bib": 190, "place": 2, "gender": "F", "age": 29,
     "finish_time": "1:19:40", "pace_per_mile": "6:05"},
]


def test_render_contains_names_times_and_year():
    out = top10_html.render_top10(2026, ROWS)
    assert "2026 Santa Fe International Half Marathon" in out
    assert "Evan Gaynor" in out and "1:13:12" in out and "5:37/mi" in out
    assert f"Results/{results.DEFAULT_RACE_ID}" in out


def test_render_escapes_html():
    out = top10_html.render_top10(2026, ROWS)
    assert "Ana &lt;O&#x27;Brien&gt; &amp; Co" in out
    assert "<O'Brien>" not in out


def test_render_is_script_free():
    assert "<script" not in top10_html.render_top10(2026, ROWS).lower()


def test_main_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(results, "top_results", lambda event_id, n: list(ROWS))
    out = tmp_path / "top10.html"
    assert top10_html.main(["--year", "2026", "-o", str(out)]) == 0
    text = out.read_text()
    assert "Top 10 Finishers" in text and "Evan Gaynor" in text


def test_main_stdout(capsys, monkeypatch):
    monkeypatch.setattr(results, "top_results", lambda event_id, n: list(ROWS))
    assert top10_html.main(["--year", "2025"]) == 0
    assert "2025 Santa Fe International Half Marathon" in capsys.readouterr().out


def test_main_fetch_error(capsys, monkeypatch):
    def boom(event_id, n):
        raise results.ResultsError("feed down")
    monkeypatch.setattr(results, "top_results", boom)
    assert top10_html.main(["--year", "2026"]) == 1
    assert "feed down" in capsys.readouterr().err


def test_main_empty_results(capsys, monkeypatch):
    monkeypatch.setattr(results, "top_results", lambda event_id, n: [])
    assert top10_html.main(["--year", "2026"]) == 1
    assert "no results posted" in capsys.readouterr().err


def test_main_rejects_unknown_year():
    with pytest.raises(SystemExit):
        top10_html.main(["--year", "1999"])
