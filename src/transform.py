"""
Transformation de la donnee validee en dataset curated exploitable :
colonnes renommees et typees, pays normalise, tranche d'age calculee.
"""

from __future__ import annotations

import pandas as pd


def _tranche_age(age) -> str | None:
    if age is None or pd.isna(age):
        return None
    age = int(age)
    borne = (age // 10) * 10
    return f"{borne}-{borne + 9}"


def transform(accepted: pd.DataFrame) -> pd.DataFrame:
    df = accepted.copy()

    df["pays"] = df["country"].astype(str).str.strip().str.upper()
    df["date_complete"] = pd.to_datetime(df["date"], errors="coerce", format="%Y-%m-%d")
    df["annee"] = df["year"].astype("Int64")
    df["age"] = df["age_clean"].astype("Int64")
    df["tranche_age"] = df["age"].apply(_tranche_age)
    df["sexe"] = df["sex"].where(df["sex"].isin(["M", "F"]))
    df["activite"] = df["activity"].fillna("Inconnue").astype(str).str.strip()
    df["type_attaque"] = df["type"].astype(str).str.strip()
    df["zone"] = df["area"]
    df["localite"] = df["location"]

    colonnes = [
        "date_complete", "annee", "pays", "zone", "localite",
        "activite", "type_attaque", "sexe", "age", "tranche_age",
    ]
    curated = df[colonnes].sort_values("annee", na_position="last").reset_index(drop=True)
    return curated
