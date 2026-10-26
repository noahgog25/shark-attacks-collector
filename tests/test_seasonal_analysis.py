import json
from pathlib import Path

import pandas as pd

from src.seasonal_analysis import analyze_seasonality, write_seasonal_outputs


def _curated_seasonality() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date_complete": [
                "2020-01-01",
                "2020-01-01",
                "2020-01-01",
                "2020-01-01",
                "2020-07-10",
                "2020-07-11",
                "date invalide",
            ],
            "activite": [
                "Surfing",
                "Surfing",
                "Surfing",
                "Surfing",
                "Swimming",
                "Swimming",
                "Inconnue",
            ],
        }
    )


def test_analyze_seasonality_exposes_january_first_sensitivity():
    summary, distribution = analyze_seasonality(_curated_seasonality())

    assert summary["dated_incidents"] == 6
    assert summary["missing_or_invalid_dates"] == 1
    assert summary["january_first_dates"] == 4
    assert summary["peak_month_all_dates"] == 1
    assert summary["peak_month_excluding_january_first"] == 7
    assert summary["activity_month_cramers_v"] == 1.0
    assert summary["activity_month_cramers_v_excluding_january_first"] == 0.0
    assert len(distribution) == 36
    assert set(distribution["activite"]) == {
        "Surfing",
        "Swimming",
        "Autres",
    }


def test_write_seasonal_outputs_creates_csv_json_figure_and_interpretation(tmp_path: Path):
    curated_path = tmp_path / "curated.csv"
    _curated_seasonality().to_csv(curated_path, index=False)

    outputs = write_seasonal_outputs(
        curated_path,
        tmp_path / "data",
        tmp_path / "images",
        tmp_path / "interpretation",
    )

    assert all(path.exists() for path in outputs.values())
    distribution = pd.read_csv(outputs["distribution"])
    summary = json.loads(outputs["summary"].read_text(encoding="utf-8"))
    interpretation = outputs["interpretation"].read_text(encoding="utf-8")
    assert len(distribution) == 36
    assert summary["peak_month_excluding_january_first"] == 7
    assert "sensibilite, pas une correction" in interpretation
    assert outputs["figure"].stat().st_size > 0
