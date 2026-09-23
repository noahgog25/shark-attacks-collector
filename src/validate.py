"""
Regles de qualite appliquees a la donnee brute avant transformation.

Chaque regle est nommee, isolee, et alimente un compteur d'echecs dans le
rapport d'execution. Quatre regles sont eliminatoires (la ligne part en
zone "rejected"), une seule (le domaine de l'age) est corrective : on vide
la valeur plutot que de perdre toute la ligne pour un age suspect.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

ANNEE_MIN = 1000
ANNEE_MAX = 2026
AGE_MIN = 0
AGE_MAX = 120

TYPES_AUTORISES = {
    "Unprovoked", "Provoked", "Invalid", "Watercraft", "Sea Disaster",
    "Questionable", "Boat", "Unverified", "Unconfirmed", "Under investigation",
}

CLE_UNICITE = ["date", "year", "type", "country", "area", "location", "activity", "name", "sex", "age"]


def _extraire_age(valeur) -> int | None:
    """Extrait le premier nombre entier d'un champ age souvent sale (ex: '28 & 26', '30s')."""
    if pd.isna(valeur):
        return None
    trouve = re.search(r"\d+", str(valeur))
    return int(trouve.group()) if trouve else None


@dataclass
class QualityReport:
    input_rows: int = 0
    accepted_rows: int = 0
    rejected_rows: int = 0
    duplicates_removed: int = 0
    failures_by_rule: dict = field(default_factory=dict)


def run_quality_rules(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, QualityReport]:
    """Applique les 5 regles et retourne (accepte, rejete, rapport)."""
    report = QualityReport(input_rows=len(df))
    work = df.copy()
    work["age_clean"] = work["age"].apply(_extraire_age)
    reasons = pd.Series("", index=work.index)

    # 1. Completude : le pays doit etre renseigne
    r1 = work["country"].isna() | (work["country"].astype(str).str.strip() == "")
    report.failures_by_rule["completude_pays"] = int(r1.sum())
    reasons.loc[r1 & (reasons == "")] = "pays manquant"

    # 2. Validite : l'annee doit etre un entier plausible
    r2 = work["year"].isna() | ~work["year"].between(ANNEE_MIN, ANNEE_MAX)
    report.failures_by_rule["validite_annee"] = int(r2.sum())
    reasons.loc[r2 & (reasons == "")] = "annee invalide"

    # 3. Coherence : le type d'attaque doit appartenir aux valeurs connues
    r3 = ~work["type"].isin(TYPES_AUTORISES)
    report.failures_by_rule["coherence_type"] = int(r3.sum())
    reasons.loc[r3 & (reasons == "")] = "type d'attaque inconnu"

    # 4. Domaine : l'age, si renseigne, doit etre plausible -> corrige, pas eliminatoire
    r4 = work["age_clean"].notna() & ~work["age_clean"].between(AGE_MIN, AGE_MAX)
    report.failures_by_rule["domaine_age_corrige"] = int(r4.sum())
    work.loc[r4, "age_clean"] = None

    work["_reject_reason"] = reasons

    # 5. Unicite : dedoublonnage sur l'ensemble des champs source
    avant = len(work)
    work = work.drop_duplicates(subset=CLE_UNICITE, keep="first")
    report.duplicates_removed = avant - len(work)

    accepted = work[work["_reject_reason"] == ""].drop(columns=["_reject_reason"])
    rejected = work[work["_reject_reason"] != ""]

    report.accepted_rows = len(accepted)
    report.rejected_rows = len(rejected)
    return accepted, rejected, report
