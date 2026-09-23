import pandas as pd

from src.geocode import location_query


def test_location_query_prefere_la_localite_et_ignore_inconnu():
    row = pd.Series({"localite": "Miami", "zone": "Florida", "pays": "USA"})

    assert location_query(row) == "Miami, Florida, USA"


def test_location_query_fait_un_fallback_sur_le_pays():
    row = pd.Series({"localite": "Inconnu", "zone": "", "pays": "USA"})

    assert location_query(row) == "USA"