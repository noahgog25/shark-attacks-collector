from pathlib import Path

import pandas as pd

from src.csv_comparison_visualize import plot_csv_comparison


def test_plot_csv_comparison_uses_the_two_csv_files(tmp_path: Path):
    proximity_path = tmp_path / "proximity.csv"
    summary_path = tmp_path / "summary.csv"
    output_path = tmp_path / "comparison.png"
    pd.DataFrame(
        {
            "species": ["Species A", "Species A", "Species B"],
            "nearest_distance_km": [10, 80, 200],
            "distance_band": ["proximite_forte", "proximite_regionale", "pas_de_proximite_100km"],
        }
    ).to_csv(proximity_path, index=False)
    pd.DataFrame(
        {
            "species": ["Species A", "Species B"],
            "attaques_proximite_forte_25km": [1, 0],
            "attaques_proximite_regionale_100km": [2, 0],
            "occurrences_juvéniles_proches": [1, 0],
        }
    ).to_csv(summary_path, index=False)

    result = plot_csv_comparison(proximity_path, summary_path, output_path)

    assert result == output_path
    assert output_path.exists()