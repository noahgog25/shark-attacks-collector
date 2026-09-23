import pandas as pd

from src.analyze import build_hotspots, build_seasonality


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