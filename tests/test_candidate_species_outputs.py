from pathlib import Path

import pandas as pd

from src.csv_comparison_visualize import write_candidate_species_outputs


def test_write_candidate_species_outputs_cree_pie_table_et_interpretation(tmp_path: Path):
    summary_path = tmp_path / "summary.csv"
    pd.DataFrame(
        {
            "species": ["Species A", "Species B"],
            "attaques_proximite_forte_25km": [10, 2],
            "attaques_proximite_regionale_100km": [20, 5],
            "occurrences_juvéniles_proches": [3, 1],
        }
    ).to_csv(summary_path, index=False)

    outputs = write_candidate_species_outputs(
        summary_path,
        tmp_path / "pie.png",
        tmp_path / "table.csv",
        tmp_path / "interpretation.md",
    )

    assert all(path.exists() for path in outputs.values())
    table = pd.read_csv(outputs["table"])
    assert table.iloc[0]["espece_candidate"] == "Species A"
    assert table.iloc[0]["part_des_proximités_100_km_pct"] == 80.0