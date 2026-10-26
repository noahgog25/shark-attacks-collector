import pandas as pd

from src.analyze import (
    build_hotspots,
    build_monthly_date_sensitivity,
    build_seasonality,
)


def test_hotspots_compte_et_classe_les_incidents():
    curated = pd.DataFrame(
        {
            "pays": ["AUSTRALIA", "AUSTRALIA", "USA"],
            "zone": ["South Australia", "South Australia", "Florida"],
            "localite": ["Adelaide", "Adelaide", "Miami"],
        }
    )

    result = build_hotspots(curated)

    assert result.iloc[0]["localite"] == "Adelaide"
    assert result.iloc[0]["incidents_declares"] == 2
    assert result.iloc[0]["rang"] == 1


def test_saisonnalite_ignore_les_dates_invalides():
    curated = pd.DataFrame({"date_complete": ["2023-01-05", "2023-01-01", "date invalide"]})

    result = build_seasonality(curated)

    assert result.to_dict("records") == [{"mois": 1, "incidents_declares": 2}]


def test_sensitivity_mensuelle_affiche_toutes_les_dates_et_sans_1er_janvier():
    curated = pd.DataFrame(
        {
            "date_complete": [
                "2020-01-01",
                "2021-01-01",
                "2022-01-15",
                "2022-07-10",
                "date invalide",
            ]
        }
    )

    result = build_monthly_date_sensitivity(curated)

    january = result.loc[result["mois"].eq(1)].iloc[0]
    july = result.loc[result["mois"].eq(7)].iloc[0]
    assert january["toutes_les_dates"] == 3
    assert january["sans_1_janvier"] == 1
    assert july["toutes_les_dates"] == july["sans_1_janvier"] == 1