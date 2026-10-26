import json
from pathlib import Path
from urllib.error import URLError

import pandas as pd
import pytest

from src.enrich.era5 import build_archive_url, normalize_json
from src.enrich.http import RequestStats, request_text
from src.enrich.oisst import build_griddap_url, normalize_csv
import src.enrich.http as http


def test_oisst_url_requests_two_variables_for_one_cell():
    url = build_griddap_url(-34.25, 18.5)

    assert url.startswith("https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv?")
    assert "sst[(1982-01-01T12:00:00Z):1:(2023-12-31T12:00:00Z)][(0.0)][(-34.250)][(18.500)]" in url
    assert "anom[(1982-01-01T12:00:00Z):1:(2023-12-31T12:00:00Z)]" in url


def test_normalize_oisst_drops_units_and_land_nan_rows():
    body = (
        "time,latitude,longitude,sst,anom\n"
        "UTC,degrees_north,degrees_east,degree_C,degree_C\n"
        "1982-01-01T12:00:00Z,-34.25,18.5,20.0,0.5\n"
        "1982-01-02T12:00:00Z,-34.25,18.5,NaN,NaN\n"
    )

    result = normalize_csv(body)

    assert result.to_dict("records") == [
        {"date": pd.Timestamp("1982-01-01").date(), "sst": 20.0, "anom": 0.5}
    ]


def test_era5_url_uses_daily_fields_and_kilometres_per_hour():
    url = build_archive_url(-34.25, 18.5, "2020-01-01", "2020-12-31")

    assert "daily=temperature_2m_max%2Cprecipitation_sum%2Cwind_speed_10m_max" in url
    assert "timezone=auto" in url
    assert "wind_speed_unit=kmh" in url


def test_normalize_era5_response():
    body = json.dumps(
        {
            "daily": {
                "time": ["2020-01-01"],
                "temperature_2m_max": [28.2],
                "precipitation_sum": [2.4],
                "wind_speed_10m_max": [16.5],
            }
        }
    )

    result = normalize_json(body)

    assert result.iloc[0].to_dict() == {
        "date": pd.Timestamp("2020-01-01").date(),
        "air_tmax_c": 28.2,
        "precip_mm": 2.4,
        "wind_max_kmh": 16.5,
    }


def test_http_request_caches_responses_by_request_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b"fixture body"

    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return Response()

    monkeypatch.setattr(http, "urlopen", fake_urlopen)
    monkeypatch.setattr(http.time, "sleep", lambda _seconds: None)
    stats = RequestStats()

    assert request_text("https://example.test/data", tmp_path, stats) == "fixture body"
    assert request_text("https://example.test/data", tmp_path, stats) == "fixture body"
    assert len(calls) == 1
    assert stats.as_dict() == {"api_calls": 1, "cache_hits": 1, "failures": 0, "retries": 0}
    assert calls[0][0].get_header("User-agent")


def test_http_request_retries_then_reports_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(http, "urlopen", lambda *_args, **_kwargs: (_ for _ in ()).throw(URLError("offline")))
    monkeypatch.setattr(http.time, "sleep", lambda _seconds: None)
    stats = RequestStats()

    with pytest.raises(URLError):
        request_text("https://example.test/failure", tmp_path, stats, retries=2)

    assert stats.as_dict() == {"api_calls": 2, "cache_hits": 0, "failures": 1, "retries": 1}
