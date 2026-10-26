"""NOAA OISST v2.1 point-series client over ERDDAP griddap."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from urllib.parse import quote

import pandas as pd

from src.enrich.http import RequestStats, request_text

ERDDAP_ROOT = "https://coastwatch.pfeg.noaa.gov/erddap"
DATASET_ID = "ncdcOisst21Agg_LonPM180"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "external" / "oisst"
START_DATE = "1982-01-01"
END_DATE = "2023-12-31"


def build_griddap_url(
    latitude: float,
    longitude: float,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
) -> str:
    """Build a single-cell daily request for SST and anomaly time series."""
    def midday_utc(value: str) -> str:
        return value if "T" in value else f"{value}T12:00:00Z"

    start_time = midday_utc(start_date)
    end_time = midday_utc(end_date)
    fields = []
    for variable in ("sst", "anom"):
        fields.append(
            f"{variable}[({start_time}):1:({end_time})][(0.0)][({latitude:.3f})][({longitude:.3f})]"
        )
    query = ",".join(fields)
    return f"{ERDDAP_ROOT}/griddap/{DATASET_ID}.csv?{quote(query, safe='[],():.-,')}"


def normalize_csv(body: str) -> pd.DataFrame:
    """Parse ERDDAP CSV, discarding metadata/unit rows and null grid values."""
    frame = pd.read_csv(StringIO(body), comment="#")
    frame.columns = [str(column).strip().lower() for column in frame.columns]
    required = {"time", "sst", "anom"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Colonnes NOAA manquantes : {sorted(missing)}")

    frame["date"] = pd.to_datetime(
        frame["time"], errors="coerce", utc=True, format="ISO8601"
    ).dt.date
    for column in ("sst", "anom"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=["date", "sst"]).loc[:, ["date", "sst", "anom"]].reset_index(drop=True)


def fetch_cell(
    latitude: float,
    longitude: float,
    stats: RequestStats,
    *,
    cache_dir: Path = CACHE_DIR,
    start_date: str = START_DATE,
    end_date: str = END_DATE,
) -> pd.DataFrame:
    """Fetch the daily 1982–2023 SST series for one unique grid cell."""
    url = build_griddap_url(latitude, longitude, start_date, end_date)
    body = request_text(url, cache_dir, stats)
    return normalize_csv(body)
