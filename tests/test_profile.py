import pandas as pd

from src.profile import build_profile


def test_build_profile_recense_structure_manquants_et_doublons():
    df = pd.DataFrame({"country": ["FRANCE", None], "year": [2020, 2020]})

    profile = build_profile(df)

    assert profile["rows"] == 2
    assert profile["columns"] == 2
    assert profile["missing_rate"]["country"] == 0.5
    assert profile["duplicate_rows"] == 0
    assert profile["categorical_top_values"]["country"]["<NA>"] == 1