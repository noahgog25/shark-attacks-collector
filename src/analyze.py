"""Analyses descriptives des incidents acceptes.

Les sorties de ce module decrivent des incidents declares et non un risque
biologique ou une abondance de requins. Les lieux sans localite exploitable
restent dans les agregations par pays et zone.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_hotspots(curated: pd.DataFrame) -> pd.DataFrame:
    """Retourne les localites avec le plus d'incidents declares."""
    required = {"pays", "zone", "localite"}
    missing = required - set(curated.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes pour les hotspots : {sorted(missing)}")

    work = curated.copy()
    for column in required:
        work[column] = work[column].fillna("Inconnu").astype(str).str.strip()
        work.loc[work[column] == "", column] = "Inconnu"

    hotspots = (
        work.groupby(["pays", "zone", "localite"], dropna=False)
        .size()
        .rename("incidents_declares")
        .reset_index()
        .sort_values(["incidents_declares", "pays", "zone", "localite"], ascending=[False, True, True, True])
        .reset_index(drop=True)
    )
    hotspots.insert(0, "rang", hotspots.index + 1)
    return hotspots


def build_seasonality(curated: pd.DataFrame) -> pd.DataFrame:
    """Compte les incidents declares par mois et saison meteorologique."""
    if "date_complete" not in curated.columns:
        raise ValueError("La colonne date_complete est necessaire pour la saisonnalite")

    dates = pd.to_datetime(curated["date_complete"], errors="coerce")
    months = dates.dropna().dt.month.astype(int)
    result = months.value_counts().rename_axis("mois").rename("incidents_declares").reset_index()
    result["mois"] = result["mois"].astype(int)
    return result.sort_values("mois").reset_index(drop=True)


def write_analysis_reports(curated_path: Path, reports_dir: Path) -> dict[str, str]:
    """Lit le curated et ecrit les deux agregations descriptives."""
    curated = pd.read_csv(curated_path)
    reports_dir.mkdir(parents=True, exist_ok=True)
    hotspots_path = reports_dir / "hotspots_incidents_declares.csv"
    seasonality_path = reports_dir / "saisonnalite_incidents_declares.csv"
    build_hotspots(curated).to_csv(hotspots_path, index=False)
    build_seasonality(curated).to_csv(seasonality_path, index=False)
    return {
        "hotspots": str(hotspots_path),
        "seasonality": str(seasonality_path),
    }
