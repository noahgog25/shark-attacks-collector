from pathlib import Path

import pandas as pd

from src.viz.environment_charts import write_environment_charts


def test_environment_charts_write_all_five_figures_with_fixture_data(tmp_path: Path):
    enriched_path = tmp_path / "enriched.csv"
    hypotheses_path = tmp_path / "hypotheses.csv"
    monthly_path = tmp_path / "monthly.csv"
    pd.DataFrame(
        {
            "incident_id": ["a", "b", "c"],
            "date": ["2020-01-03", "2020-01-05", "2020-07-02"],
            "latitude": [-20, -20, 25],
            "pays": ["AUSTRALIA", "AUSTRALIA", "USA"],
            "sst_c": [25.0, 27.0, 22.0],
            "sst_anom_c": [1.0, -0.5, 0.3],
            "sst_control_mean_c": [24.0, 26.0, 22.0],
            "air_tmax_c": [31.0, 29.0, 26.0],
            "air_tmax_control_mean_c": [28.0, 28.0, 27.0],
        }
    ).to_csv(enriched_path, index=False)
    pd.DataFrame(
        {
            "hypothesis_id": ["H1", "H2", "H3", "H4", "H5"],
            "test": ["Mann–Whitney"] * 5,
            "result": ["n=3; médiane=1.0"] * 5,
            "status": ["Non concluante (échantillon ou données insuffisants)"] * 5,
            "n_incident": [3] * 5,
        }
    ).to_csv(hypotheses_path, index=False)
    pd.DataFrame(
        {
            "pays": ["AUSTRALIA", "AUSTRALIA", "USA"],
            "hemisphere": ["S", "S", "N"],
            "season_month": [1, 7, 7],
            "attacks": [1, 1, 1],
            "mean_sst_c": [27.0, 20.0, 22.0],
            "spearman_month_sst": [-1.0, -1.0, None],
        }
    ).to_csv(monthly_path, index=False)

    outputs = write_environment_charts(
        enriched_path,
        hypotheses_path,
        monthly_path,
        tmp_path / "images",
    )

    assert set(outputs) == {
        "sst_controls",
        "sst_anomaly",
        "monthly_sst",
        "air_controls",
        "hypotheses",
    }
    assert all(path.exists() and path.stat().st_size > 0 for path in outputs.values())


def test_environment_charts_show_insufficient_data_without_outputs(tmp_path: Path):
    outputs = write_environment_charts(
        tmp_path / "missing-enriched.csv",
        tmp_path / "missing-hypotheses.csv",
        tmp_path / "missing-monthly.csv",
        tmp_path / "images",
    )

    assert all(path.exists() and path.stat().st_size > 0 for path in outputs.values())
