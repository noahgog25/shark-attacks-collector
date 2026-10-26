from datetime import date
from urllib.error import URLError

import pandas as pd

from src.enrich.http import RequestStats
from src.enrich.service import (
    _gbif_nearby_counts,
    enrich_frames,
    grid_cell,
    incident_hash,
    nearby_cells,
)


def _incident_rows():
    curated = pd.DataFrame(
        {
            "date_complete": ["2020-01-03", "2020-01-05", "2020-01-01"],
            "annee": [2020, 2020, 2020],
            "pays": ["AUSTRALIA", "AUSTRALIA", "AUSTRALIA"],
            "zone": ["Queensland"] * 3,
            "localite": ["Brisbane"] * 3,
            "activite": ["Surfing"] * 3,
            "type_attaque": ["Unprovoked", "Unprovoked", "Unprovoked"],
            "sexe": ["M", "F", "M"],
            "age": [30, 20, 40],
            "tranche_age": ["30-39", "20-29", "40-49"],
        }
    )
    geocoded = curated.copy()
    geocoded["latitude"] = [-27.5, -27.5, -27.5]
    geocoded["longitude"] = [153.0, 153.0, 153.0]
    geocoded["geocode_status"] = "geocoded"
    return curated, geocoded


def _oisst_fixture():
    dates = list(pd.date_range("1982-01-01", "1982-01-31", freq="D"))
    dates += [pd.Timestamp("2020-01-03"), pd.Timestamp("2020-01-05")]
    return pd.DataFrame({"date": [value.date() for value in dates], "sst": 25.0, "anom": 0.0})


def test_grid_lookup_uses_nearest_ocean_cell_after_land_nan():
    curated, geocoded = _incident_rows()
    called_cells = []

    def fake_oisst(latitude, longitude, _stats):
        called_cells.append((latitude, longitude))
        if (latitude, longitude) == grid_cell(-27.5, 153.0):
            return pd.DataFrame(
                {"date": [date(2020, 1, 3)], "sst": [float("nan")], "anom": [float("nan")]}
            )
        return _oisst_fixture()

    def fake_era5(latitude, longitude, start, end, _stats):
        daily = pd.date_range(start, end, freq="D")
        return pd.DataFrame(
            {
                "date": daily.date,
                "air_tmax_c": 25.0,
                "precip_mm": 1.0,
                "wind_max_kmh": 10.0,
            }
        )

    enriched, report = enrich_frames(
        curated,
        geocoded,
        oisst_stats=RequestStats(),
        era5_stats=RequestStats(),
        oisst_fetcher=fake_oisst,
        era5_fetcher=fake_era5,
    )

    assert len(enriched) == 2
    assert enriched["sst_c"].notna().all()
    assert enriched["hemisphere"].eq("S").all()
    assert enriched["env_status"].eq("OK").all()
    assert report["excluded_by_filter"]["exact_date_not_january_first"]["excluded_rows"] == 1
    assert called_cells[0] == grid_cell(-27.5, 153.0)
    assert len(called_cells) == len(set(called_cells))
    assert max(((cell[0] - -27.5) ** 2 + (cell[1] - 153.0) ** 2) ** 0.5 for cell in called_cells[1:]) < 0.5


def test_api_failure_is_recorded_without_raising():
    curated, geocoded = _incident_rows()

    def unavailable(*_args):
        raise URLError("offline")

    enriched, report = enrich_frames(
        curated,
        geocoded,
        oisst_stats=RequestStats(failures=1),
        era5_stats=RequestStats(failures=1),
        oisst_fetcher=unavailable,
        era5_fetcher=unavailable,
    )

    assert enriched["env_status"].eq("API_FAIL").all()
    assert report["status"] == "WARN"
    assert report["failures"] == 2


def test_incident_hash_ignores_sensitive_name_column():
    row = pd.Series(
        {
            "date_complete": "2020-01-03",
            "annee": 2020,
            "pays": "AUSTRALIA",
            "zone": "Queensland",
            "localite": "Brisbane",
            "activite": "Surfing",
            "type_attaque": "Unprovoked",
            "sexe": "M",
            "age": 30,
            "tranche_age": "30-39",
            "name": "Sensitive name not included in output",
        }
    )

    assert incident_hash(row) == incident_hash({key: value for key, value in row.items() if key != "name"})


def test_oisst_cells_use_dataset_centres_and_wrap_at_the_dateline():
    assert grid_cell(-27.5, 153.0) == (-27.375, 153.125)
    cells = nearby_cells(0.0, 179.9)
    assert any(longitude < -179.5 for _, longitude in cells)
    assert all(
        ((latitude - grid_cell(0.0, 179.9)[0]) ** 2
         + min(abs(longitude - grid_cell(0.0, 179.9)[1]), 360 - abs(longitude - grid_cell(0.0, 179.9)[1])) ** 2) ** 0.5 < 0.5
        for latitude, longitude in cells
    )


def test_h4_only_counts_gbif_occurrences_from_2025_and_2026():
    attacks = pd.DataFrame(
        {
            "date": [date(2025, 3, 1), date(2024, 3, 1)],
            "latitude": [0.0, 0.0],
            "longitude": [0.0, 0.0],
        }
    )
    occurrences = pd.DataFrame(
        {
            "observed_at": ["2026-01-01", "2024-01-01"],
            "latitude": [0.1, 0.1],
            "longitude": [0.1, 0.1],
        }
    )

    counts = _gbif_nearby_counts(attacks, occurrences)

    assert counts.tolist() == [1, 0]
