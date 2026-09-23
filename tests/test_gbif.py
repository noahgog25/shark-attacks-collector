import pandas as pd

from src.gbif import normalize_occurrences


def test_normalize_occurrences_conserve_provenance_et_coordonnees():
    match = {"usageKey": 123, "scientificName": "Carcharodon carcharias"}
    response = {
        "results": [
            {
                "key": 456,
                "species": "Carcharodon carcharias",
                "decimalLatitude": -34.1,
                "decimalLongitude": 18.4,
                "lifeStage": "JUVENILE",
                "country": "South Africa",
            },
            {"key": 457, "decimalLatitude": None, "decimalLongitude": 18.4},
        ]
    }

    result = normalize_occurrences(match, response, "2026-09-23T00:00:00+00:00")

    assert len(result) == 1
    assert result.iloc[0]["source"] == "gbif"
    assert result.iloc[0]["source_record_id"] == 456
    assert result.iloc[0]["life_stage"] == "JUVENILE"
    assert pd.notna(result.iloc[0]["source_url"])