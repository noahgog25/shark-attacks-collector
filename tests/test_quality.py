"""
Tests minimaux des regles de qualite. A completer au fil des iterations
(un cas par regle, cas limites sur les bornes d'age et d'annee...).
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.validate import run_quality_rules
from src.transform import transform


def _ligne(**overrides):
    base = {
        "date": "2023-05-13", "year": 2023.0, "type": "Unprovoked",
        "country": "AUSTRALIA", "area": "South Australia", "location": "Elliston",
        "activity": "Surfing", "name": "Test", "sex": "M", "age": "46",
    }
    base.update(overrides)
    return base


def test_ligne_valide_est_acceptee():
    df = pd.DataFrame([_ligne()])
    accepted, rejected, report = run_quality_rules(df)
    assert len(accepted) == 1
    assert len(rejected) == 0


def test_pays_manquant_est_rejete():
    df = pd.DataFrame([_ligne(country=None)])
    accepted, rejected, report = run_quality_rules(df)
    assert len(accepted) == 0
    assert len(rejected) == 1
    assert report.failures_by_rule["completude_pays"] == 1


def test_annee_hors_bornes_est_rejetee():
    df = pd.DataFrame([_ligne(year=1.0)])
    accepted, rejected, report = run_quality_rules(df)
    assert len(accepted) == 0
    assert report.failures_by_rule["validite_annee"] == 1


def test_type_inconnu_est_rejete():
    df = pd.DataFrame([_ligne(type="Unknown type")])
    accepted, rejected, report = run_quality_rules(df)
    assert len(accepted) == 0
    assert rejected.iloc[0]["_reject_reason"] == "type d'attaque inconnu"
    assert report.failures_by_rule["coherence_type"] == 1


def test_age_hors_domaine_est_corrige_sans_rejeter():
    df = pd.DataFrame([_ligne(age="250")])
    accepted, rejected, report = run_quality_rules(df)
    assert len(accepted) == 1
    assert pd.isna(accepted.iloc[0]["age_clean"])


def test_doublon_est_supprime():
    df = pd.DataFrame([_ligne(), _ligne()])
    accepted, rejected, report = run_quality_rules(df)
    assert len(accepted) == 1
    assert report.duplicates_removed == 1
    assert report.failures_by_rule["unicite"] == 1


def test_rejouer_validation_et_transformation_est_stable():
    df = pd.DataFrame([_ligne(), _ligne()])
    accepted_first, _, _ = run_quality_rules(df)
    accepted_second, _, _ = run_quality_rules(df)

    first = transform(accepted_first)
    second = transform(accepted_second)

    pd.testing.assert_frame_equal(first, second)
