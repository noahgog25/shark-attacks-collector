"""Join local incident and geocoding data with NOAA OISST and ERA5."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from urllib.error import HTTPError, URLError

from src.analysis.environment import (
    build_sensitivity_results,
    build_hypothesis_results,
    local_climatology,
    monthly_sst_summary,
    prepare_eligible_population,
)
from src.enrich.era5 import CACHE_DIR as ERA5_CACHE_DIR
from src.enrich.era5 import fetch_daily as fetch_era5
from src.enrich.http import RequestStats
from src.enrich.oisst import CACHE_DIR as OISST_CACHE_DIR
from src.enrich.oisst import fetch_cell as fetch_oisst_cell

LOGGER = logging.getLogger(__name__)
CURATED_COLUMNS = (
    "date_complete",
    "annee",
    "pays",
    "zone",
    "localite",
    "activite",
    "type_attaque",
    "sexe",
    "age",
    "tranche_age",
)
OISST_FIRST_DATE = date(1982, 1, 1)
OISST_LAST_DATE = date(2023, 12, 31)
ERA5_FIRST_DATE = date(1940, 1, 1)


def incident_hash(row: pd.Series | dict) -> str:
    """Create a stable incident identifier without using the sensitive name field."""
    values = {}
    for column in CURATED_COLUMNS:
        value = row.get(column)
        if value is None or pd.isna(value):
            values[column] = None
        elif isinstance(value, (pd.Timestamp, datetime, date)):
            values[column] = pd.Timestamp(value).date().isoformat()
        elif column in {"annee", "age"} and pd.notna(value):
            number = pd.to_numeric(value, errors="coerce")
            values[column] = int(number) if pd.notna(number) else None
        else:
            values[column] = str(value).strip()
    payload = json.dumps(values, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def grid_cell(latitude: float, longitude: float) -> tuple[float, float]:
    latitude_index = round((latitude + 89.875) / 0.25)
    longitude_index = round((longitude + 179.875) / 0.25)
    grid_latitude = max(-89.875, min(89.875, -89.875 + latitude_index * 0.25))
    grid_longitude = max(-179.875, min(179.875, -179.875 + longitude_index * 0.25))
    return round(grid_latitude, 3), round(grid_longitude, 3)


def nearby_cells(latitude: float, longitude: float) -> list[tuple[float, float]]:
    """Return unique 0.25-degree neighbours strictly inside 0.5 degrees."""
    center_lat, center_lon = grid_cell(latitude, longitude)
    center_lat_index = round((center_lat + 89.875) / 0.25)
    center_lon_index = round((center_lon + 179.875) / 0.25)
    cells = []
    for lat_step in range(-2, 3):
        for lon_step in range(-2, 3):
            distance = math.hypot(lat_step * 0.25, lon_step * 0.25)
            latitude_index = center_lat_index + lat_step
            if (lat_step or lon_step) and distance < 0.5 and 0 <= latitude_index < 720:
                cells.append(
                    (
                        round(-89.875 + latitude_index * 0.25, 3),
                        round(-179.875 + (center_lon_index + lon_step) % 1440 * 0.25, 3),
                    )
                )
    return sorted(
        cells,
        key=lambda cell: math.hypot(
            cell[0] - center_lat,
            min(abs(cell[1] - center_lon), 360 - abs(cell[1] - center_lon)),
        ),
    )


def _finite_mean(values: list[float]) -> float | None:
    finite = [float(value) for value in values if value is not None and np.isfinite(value)]
    return float(np.mean(finite)) if finite else None


def _mean_for_dates(series: pd.DataFrame, dates: list[date], column: str) -> float | None:
    if not dates or series.empty:
        return None
    series_dates = pd.to_datetime(series["date"], errors="coerce").dt.date
    values = series.loc[series_dates.isin(dates), column].dropna().tolist()
    return _finite_mean(values)


def _previous_three_day_total(series: pd.DataFrame, incident_date: date) -> float | None:
    prior_dates = [incident_date - timedelta(days=offset) for offset in (3, 2, 1)]
    series_dates = pd.to_datetime(series["date"], errors="coerce").dt.date
    values = series.loc[series_dates.isin(prior_dates), "precip_mm"].dropna()
    return float(values.sum()) if len(values) == 3 else None


def _control_dates(
    incident_date: date, rng: random.Random, count: int = 10
) -> list[date]:
    first_day = date(incident_date.year, 1, 1)
    last_day = date(incident_date.year, 12, 31)
    available_days = (last_day - first_day).days
    excluded_day = (incident_date - first_day).days
    choices = [offset for offset in range(available_days + 1) if offset != excluded_day]
    selected = rng.sample(choices, min(count, len(choices)))
    return [first_day + timedelta(days=offset) for offset in selected]


def _normalise_geo(curated: pd.DataFrame, geocoded: pd.DataFrame) -> pd.DataFrame:
    if "latitude" not in geocoded or "longitude" not in geocoded:
        raise ValueError("Le fichier géocodé doit contenir latitude et longitude.")
    incidents = curated.copy()
    locations = geocoded.copy()
    incidents["incident_id"] = incidents.apply(incident_hash, axis=1)
    locations["incident_id"] = locations.apply(incident_hash, axis=1)
    location_columns = [
        column
        for column in ("incident_id", "latitude", "longitude", "geocode_type", "geocode_status")
        if column in locations.columns
    ]
    locations = locations[location_columns].drop_duplicates("incident_id", keep="last")
    merged = incidents.merge(locations, on="incident_id", how="left")
    merged["date"] = pd.to_datetime(merged["date_complete"], errors="coerce").dt.date
    return merged


def _lookup_ocean_cell(
    latitude: float,
    longitude: float,
    incident_date: date,
    stats: RequestStats,
    cell_cache: dict[tuple[float, float], pd.DataFrame | Exception],
    oisst_fetcher: Callable,
) -> tuple[
    tuple[float, float] | None,
    pd.DataFrame | None,
    float | None,
    float | None,
    float | None,
    str | None,
]:
    for cell in [grid_cell(latitude, longitude), *nearby_cells(latitude, longitude)]:
        if cell not in cell_cache:
            try:
                cell_cache[cell] = oisst_fetcher(cell[0], cell[1], stats)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
                cell_cache[cell] = error
                LOGGER.warning("NOAA OISST request failed at cell %s: %s", cell, error)
        series = cell_cache[cell]
        if isinstance(series, Exception):
            return None, None, None, None, None, "API_FAIL"
        dated = series.loc[series["date"] == incident_date]
        if dated.empty:
            continue
        value = pd.to_numeric(dated["sst"], errors="coerce").dropna()
        if value.empty:
            continue
        local = local_climatology(series)
        climate_row = local.loc[local["date"].dt.date == incident_date]
        climate = (
            float(climate_row.iloc[0]["sst_clim_c"])
            if not climate_row.empty and pd.notna(climate_row.iloc[0]["sst_clim_c"])
            else None
        )
        anomaly = float(value.iloc[0] - climate) if climate is not None else None
        return cell, local, float(value.iloc[0]), climate, anomaly, None
    return None, None, None, None, None, "NO_OCEAN_CELL"


def enrich_frames(
    curated: pd.DataFrame,
    geocoded: pd.DataFrame,
    *,
    oisst_stats: RequestStats | None = None,
    era5_stats: RequestStats | None = None,
    oisst_fetcher: Callable = fetch_oisst_cell,
    era5_fetcher: Callable = fetch_era5,
    gbif_occurrences: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Enrich joined incidents while keeping API failures visible per row."""
    oisst_stats = oisst_stats or RequestStats()
    era5_stats = era5_stats or RequestStats()
    joined = _normalise_geo(curated, geocoded)
    eligible, eligibility = prepare_eligible_population(joined.rename(columns={"date": "date"}))
    eligible_ids = set(eligible["incident_id"])
    frame = joined.loc[joined["incident_id"].isin(eligible_ids)].copy()

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.date
    frame["hemisphere"] = frame["latitude"].map(
        lambda value: "S" if pd.notna(value) and float(value) < 0 else "N"
    )
    if "geocode_type" in frame.columns:
        frame["geocode_precision"] = frame["geocode_type"].fillna(
            "centre_de_localite_approximatif"
        )
    else:
        frame["geocode_precision"] = "centre_de_localite_approximatif"
    frame["env_status"] = "OK"
    cell_cache: dict[tuple[float, float], pd.DataFrame | Exception] = {}
    cell_for_incident: dict[str, tuple[tuple[float, float], pd.DataFrame] | None] = {}

    current_date = datetime.now(timezone.utc).date()
    weather_cache: dict[tuple[float, float], pd.DataFrame | Exception] = {}
    for _, row in frame.iterrows():
        incident_id = row["incident_id"]
        incident_date = row["date"]
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
        cell_for_incident[incident_id] = None
        if incident_date < OISST_FIRST_DATE:
            frame.loc[frame["incident_id"] == incident_id, "env_status"] = "PRE_1982"
        elif incident_date > OISST_LAST_DATE:
            frame.loc[frame["incident_id"] == incident_id, "env_status"] = "OUTSIDE_OISST_WINDOW"
        else:
            cell, series, sst, climate, anomaly, failure_status = _lookup_ocean_cell(
                latitude, longitude, incident_date, oisst_stats, cell_cache, oisst_fetcher
            )
            if cell is not None and series is not None:
                cell_for_incident[incident_id] = (cell, series)
                frame.loc[frame["incident_id"] == incident_id, "sst_c"] = sst
                frame.loc[frame["incident_id"] == incident_id, "sst_clim_c"] = climate
                frame.loc[frame["incident_id"] == incident_id, "sst_anom_c"] = (
                    anomaly
                )
                noaa_anomaly = pd.to_numeric(
                    series.loc[series["date"] == incident_date, "anom"], errors="coerce"
                ).dropna()
                frame.loc[frame["incident_id"] == incident_id, "sst_anom_noaa_c"] = (
                    float(noaa_anomaly.iloc[0]) if not noaa_anomaly.empty else None
                )
                frame.loc[frame["incident_id"] == incident_id, "env_status"] = "OK"
            else:
                frame.loc[frame["incident_id"] == incident_id, "env_status"] = failure_status

        if incident_date >= ERA5_FIRST_DATE and incident_date <= current_date:
            place_key = (round(latitude, 3), round(longitude, 3))
            if place_key not in weather_cache:
                place_rows = frame.loc[
                    (frame["latitude"].round(3) == place_key[0])
                    & (frame["longitude"].round(3) == place_key[1])
                    & frame["date"].notna()
                ]
                place_dates = place_rows["date"].tolist()
                start = max(ERA5_FIRST_DATE, min(place_dates))
                end = min(current_date, max(place_dates))
                start = date(start.year, 1, 1)
                end = date(end.year, 12, 31) if end < current_date else current_date
                try:
                    weather_cache[place_key] = era5_fetcher(
                        latitude,
                        longitude,
                        start.isoformat(),
                        end.isoformat(),
                        era5_stats,
                    )
                except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
                    weather_cache[place_key] = error
                    LOGGER.warning("Open-Meteo Archive request failed at place %s: %s", place_key, error)
            weather = weather_cache[place_key]
            if isinstance(weather, Exception):
                frame.loc[frame["incident_id"] == incident_id, "env_status"] = "API_FAIL"
            else:
                event = weather.loc[weather["date"] == incident_date]
                if not event.empty:
                    for column in ("air_tmax_c", "precip_mm", "wind_max_kmh"):
                        frame.loc[frame["incident_id"] == incident_id, column] = event.iloc[0][column]
                    frame.loc[frame["incident_id"] == incident_id, "precip_3d_mm"] = (
                        _previous_three_day_total(weather, incident_date)
                    )

    control_rng = random.Random(20261027)
    for _, row in frame.iterrows():
        incident_id = row["incident_id"]
        incident_date = row["date"]
        controls = _control_dates(incident_date, control_rng)
        cell_entry = cell_for_incident.get(incident_id)
        if cell_entry is not None:
            _, series = cell_entry
            frame.loc[frame["incident_id"] == incident_id, "sst_control_mean_c"] = _mean_for_dates(
                series, controls, "sst"
            )
        place_key = (round(float(row["latitude"]), 3), round(float(row["longitude"]), 3))
        weather = weather_cache.get(place_key)
        if isinstance(weather, pd.DataFrame):
            for source_column, target_column in (
                ("air_tmax_c", "air_tmax_control_mean_c"),
                ("precip_mm", "precip_control_mean_mm"),
                ("wind_max_kmh", "wind_control_mean_kmh"),
            ):
                frame.loc[frame["incident_id"] == incident_id, target_column] = _mean_for_dates(
                    weather, controls, source_column
                )
            frame.loc[
                frame["incident_id"] == incident_id, "precip_3d_control_mean_mm"
            ] = _finite_mean(
                [
                    _previous_three_day_total(weather, control_date)
                    for control_date in controls
                ]
            )

    frame["gbif_2025_2026_within_100km"] = _gbif_nearby_counts(frame, gbif_occurrences)
    output_columns = [
        "incident_id",
        "date",
        "latitude",
        "longitude",
        "geocode_precision",
        "hemisphere",
        "sst_c",
        "sst_clim_c",
        "sst_anom_c",
        "sst_anom_noaa_c",
        "sst_control_mean_c",
        "air_tmax_c",
        "air_tmax_control_mean_c",
        "precip_mm",
        "precip_control_mean_mm",
        "wind_max_kmh",
        "wind_control_mean_kmh",
        "precip_3d_mm",
        "precip_3d_control_mean_mm",
        "gbif_2025_2026_within_100km",
        "env_status",
        "pays",
        "type_attaque",
    ]
    for column in output_columns:
        if column not in frame.columns:
            frame[column] = np.nan
    enriched = frame.loc[:, output_columns].sort_values("incident_id").reset_index(drop=True)
    failures = int(enriched["env_status"].eq("API_FAIL").sum())
    report = {
        "status": "WARN" if failures or enriched.empty or enriched["env_status"].eq("NO_OCEAN_CELL").any() else "PASS",
        "api_calls": oisst_stats.api_calls + era5_stats.api_calls,
        "cache_hits": oisst_stats.cache_hits + era5_stats.cache_hits,
        "failures": oisst_stats.failures + era5_stats.failures,
        "retries": oisst_stats.retries + era5_stats.retries,
        "oisst": oisst_stats.as_dict(),
        "era5": era5_stats.as_dict(),
        "lines_enriched": int(enriched["env_status"].eq("OK").sum()),
        "lines_excluded": len(curated) - len(enriched),
        "excluded_by_filter": eligibility["filters"],
        "oisst_eligible_rows": eligibility["oisst_rows"],
        "era5_eligible_rows": eligibility["era5_rows"],
        "duration_seconds": 0.0,
    }
    return enriched, report


def _gbif_nearby_counts(
    attacks: pd.DataFrame, occurrences: pd.DataFrame | None
) -> pd.Series:
    counts = pd.Series(0, index=attacks.index, dtype="int64")
    if occurrences is None or occurrences.empty:
        return counts
    required = {"observed_at", "latitude", "longitude"}
    if not required.issubset(occurrences.columns):
        LOGGER.warning("Skipping H4: local GBIF export lacks required columns.")
        return counts
    gbif = occurrences.copy()
    gbif["observed_at"] = pd.to_datetime(gbif["observed_at"], errors="coerce")
    gbif["latitude"] = pd.to_numeric(gbif["latitude"], errors="coerce")
    gbif["longitude"] = pd.to_numeric(gbif["longitude"], errors="coerce")
    gbif = gbif.loc[
        gbif["observed_at"].dt.year.isin((2025, 2026))
        & gbif["latitude"].between(-90, 90)
        & gbif["longitude"].between(-180, 180)
    ]
    for index, attack in attacks.loc[
        pd.to_datetime(attacks["date"], errors="coerce").dt.year.isin((2025, 2026))
    ].iterrows():
        distance = _haversine_km(
            float(attack["latitude"]),
            float(attack["longitude"]),
            gbif["latitude"].to_numpy(dtype=float),
            gbif["longitude"].to_numpy(dtype=float),
        )
        counts.loc[index] = int((distance <= 100).sum())
    return counts


def _haversine_km(latitude: float, longitude: float, latitudes, longitudes) -> np.ndarray:
    radius = 6371.0088
    lat1, lat2 = np.radians(latitude), np.radians(latitudes)
    delta_lat = lat2 - lat1
    delta_lon = np.radians(longitudes) - math.radians(longitude)
    term = np.sin(delta_lat / 2) ** 2 + math.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2) ** 2
    return 2 * radius * np.arcsin(np.sqrt(term))


def run_enrichment(
    curated_path: Path,
    geocoded_path: Path,
    output_path: Path,
    *,
    gbif_dir: Path,
    analysis_dir: Path,
    oisst_stats: RequestStats | None = None,
    era5_stats: RequestStats | None = None,
) -> dict:
    """Load local inputs, execute optional enrichments, and persist the CSV."""
    started = datetime.now(timezone.utc)
    curated = pd.read_csv(curated_path)
    if geocoded_path.exists():
        geocoded = pd.read_csv(geocoded_path)
    else:
        geocoded = pd.DataFrame(columns=[*CURATED_COLUMNS, "latitude", "longitude"])
    occurrences = []
    for path in sorted(gbif_dir.glob("gbif_*_occurrences.csv")):
        occurrences.append(pd.read_csv(path))
    gbif = pd.concat(occurrences, ignore_index=True) if occurrences else None
    enriched, report = enrich_frames(
        curated,
        geocoded,
        oisst_stats=oisst_stats,
        era5_stats=era5_stats,
        gbif_occurrences=gbif,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(output_path, index=False)
    hypothesis_path = analysis_dir / "environment_hypotheses.csv"
    monthly_path = analysis_dir / "environment_monthly_sst.csv"
    sensitivity_path = analysis_dir / "environment_sensitivities.json"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    hypotheses = build_hypothesis_results(enriched)
    hypotheses.to_csv(hypothesis_path, index=False)
    monthly = monthly_sst_summary(enriched)
    monthly.to_csv(monthly_path, index=False)
    sensitivities = build_sensitivity_results(enriched)
    sensitivity_path.write_text(
        json.dumps(sensitivities, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    report["duration_seconds"] = round(
        (datetime.now(timezone.utc) - started).total_seconds(), 2
    )
    report["output"] = str(output_path)
    report["hypotheses_output"] = str(hypothesis_path)
    report["hypotheses"] = hypotheses.to_dict(orient="records")
    report["monthly_sst_output"] = str(monthly_path)
    report["monthly_sst_spearman"] = (
        monthly[
            ["pays", "hemisphere", "spearman_month_sst"]
        ].drop_duplicates().to_dict(orient="records")
    )
    report["sensitivities_output"] = str(sensitivity_path)
    report["sensitivities"] = sensitivities
    report["attribution"] = {
        "oisst": "NOAA OISST v2.1, NOAA NCEI",
        "era5": "Open-Meteo Archive (ERA5); CC BY 4.0",
    }
    return report
