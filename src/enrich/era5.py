"""Open-Meteo Archive (ERA5) daily weather client."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

from src.enrich.http import RequestStats, request_text

ARCHIVE_API = "https://archive-api.open-meteo.com/v1/archive"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "external" / "era5"
DAILY_FIELDS = ("temperature_2m_max", "precipitation_sum", "wind_speed_10m_max")


def build_archive_url(
    latitude: float, longitude: float, start_date: str, end_date: str
) -> str:
    params = {
        "latitude": f"{latitude:.5f}",
        "longitude": f"{longitude:.5f}",
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join(DAILY_FIELDS),
        "timezone": "auto",
        "wind_speed_unit": "kmh",
    }
    return f"{ARCHIVE_API}?{urlencode(params)}"


def normalize_json(body: str) -> pd.DataFrame:
    """Convert Open-Meteo daily response into a typed date-indexed frame."""
    response = json.loads(body)
    daily = response.get("daily")
    if not isinstance(daily, dict) or "time" not in daily:
        raise ValueError("Réponse ERA5 sans série journalière.")

    frame = pd.DataFrame({"date": pd.to_datetime(daily["time"], errors="coerce").date})
    for source_name, target_name in (
        ("temperature_2m_max", "air_tmax_c"),
        ("precipitation_sum", "precip_mm"),
        ("wind_speed_10m_max", "wind_max_kmh"),
    ):
        values = daily.get(source_name)
        if values is None or len(values) != len(frame):
            raise ValueError(f"Série ERA5 absente ou incomplète : {source_name}")
        frame[target_name] = pd.to_numeric(pd.Series(values), errors="coerce")
    return frame.dropna(subset=["date"]).reset_index(drop=True)


def fetch_daily(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    stats: RequestStats,
    *,
    cache_dir: Path = CACHE_DIR,
) -> pd.DataFrame:
    """Fetch daily weather once for a place and requested date range."""
    url = build_archive_url(latitude, longitude, start_date, end_date)
    return normalize_json(request_text(url, cache_dir, stats))
