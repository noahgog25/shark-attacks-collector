import pandas as pd

from src.compare_ecology import (
    _build_summary,
    _write_hypotheses,
    compare_attacks_to_species,
    haversine_km,
)


def test_haversine_zero_distance():
    assert haversine_km(10, 20, 10, 20) == 0


def test_compare_attacks_to_species_finds_nearby_occurrence():
    attacks = pd.DataFrame(
        {
            "latitude": [0.0], "longitude": [0.0], "pays": ["TEST"],
            "activite": ["Surfing"], "type_attaque": ["Unprovoked"],
        }
    )
    occurrences = pd.DataFrame(
        {
            "species": ["Species test"], "latitude": [0.1], "longitude": [0.1],
            "source_record_id": [1], "life_stage": ["JUVENILE"],
            "coordinate_uncertainty_m": [10], "source_url": ["https://example.test/1"],
            "observed_at": ["2026-01-01"],
        }
    )

    result = compare_attacks_to_species(attacks, occurrences)

    assert result.iloc[0]["distance_band"] == "proximite_forte"
    assert result.iloc[0]["juvenile_occurrences_within_100km"] == 1


def test_hypotheses_documentent_les_proximités_et_les_limites_temporelles(tmp_path):
    attacks = pd.DataFrame(
        {
            "latitude": [0.0],
            "longitude": [0.0],
            "activite": ["Surfing"],
            "type_attaque": ["Unprovoked"],
        }
    )
    occurrences = pd.DataFrame(
        {
            "species": ["Species test"],
            "latitude": [0.1],
            "longitude": [0.1],
            "source_record_id": [1],
            "life_stage": ["JUVENILE"],
            "coordinate_uncertainty_m": [10],
            "source_url": ["https://example.test/1"],
            "observed_at": ["2026-01-01"],
        }
    )
    proximity = compare_attacks_to_species(attacks, occurrences)
    output_path = tmp_path / "hypotheses.md"

    _write_hypotheses(_build_summary(proximity), proximity, output_path, occurrences)

    report = output_path.read_text(encoding="utf-8")
    assert "1 attaques sur 1" in report
    assert "2026-01-01 a 2026-01-01" in report
    assert "ne permettent pas de conclure a une relation temporelle" in report