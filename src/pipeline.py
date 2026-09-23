"""
Pipeline batch complet.

    Source raw canonique (data/raw) -> Collecteur -> Raw (data/raw)
        -> Validation (5 regles) -> Curated (data/curated) + Rejected (data/rejected)
        -> Rapport (reports/interpretation) + Visualisations (reports/images)

Idempotence : le fichier curated et le fichier rejected sont entierement
remplaces a chaque execution (pas d'ajout), donc rejouer le pipeline sur la
meme source ne cree jamais de doublons dans les sorties. Seule la zone raw
accumule une nouvelle preuve de collecte horodatee a chaque run.

Usage :
    python -m src.pipeline [chemin_source_csv]
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collect import collect, sha256_file
from src.analyze import write_analysis_reports
from src.profile import write_profile
from src.validate import run_quality_rules
from src.transform import transform
from src.visualize import plot_attacks_per_year, plot_incident_dashboard

ROOT = Path(__file__).resolve().parent.parent
CURATED_PATH = ROOT / "data" / "curated" / "shark_attacks_curated.csv"
REJECTED_PATH = ROOT / "data" / "rejected" / "rejected_rows.csv"
REPORTS_DIR = ROOT / "reports"
REPORT_PATH = REPORTS_DIR / "interpretation" / "run_report.json"
REPORT_DATA_DIR = REPORTS_DIR / "data"
PROFILE_PATH = REPORTS_DIR / "interpretation" / "source_profile.json"


def run(source_path: str | None = None) -> dict:
    debut = time.perf_counter()

    raw_path = collect(source_path)
    df = pd.read_csv(raw_path)
    profile_path = write_profile(df, PROFILE_PATH)

    accepted, rejected, quality = run_quality_rules(df)
    curated = transform(accepted)

    CURATED_PATH.parent.mkdir(parents=True, exist_ok=True)
    REJECTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    curated.to_csv(CURATED_PATH, index=False)
    rejected.to_csv(REJECTED_PATH, index=False)

    graphique = plot_attacks_per_year()
    dashboard = plot_incident_dashboard()
    analyses = write_analysis_reports(CURATED_PATH, REPORT_DATA_DIR)

    rapport = {
        "pipeline": "shark-attacks-collector",
        "executed_at": pd.Timestamp.now("UTC").isoformat(),
        "source_file": raw_path.name,
        "source_sha256": sha256_file(raw_path),
        "source_size_bytes": raw_path.stat().st_size,
        "contract_version": "1.0",
        "input_rows": quality.input_rows,
        "accepted_rows": quality.accepted_rows,
        "rejected_rows": quality.rejected_rows,
        "duplicates_removed": quality.duplicates_removed,
        "failures_by_rule": quality.failures_by_rule,
        "quality_status": "PASS_WITH_WARNINGS" if quality.rejected_rows else "PASS",
        "duration_seconds": round(time.perf_counter() - debut, 2),
        "outputs": {
            "curated": str(CURATED_PATH.relative_to(ROOT)),
            "rejected": str(REJECTED_PATH.relative_to(ROOT)),
            "visualisation": str(graphique.relative_to(ROOT)),
            "dashboard": str(dashboard.relative_to(ROOT)),
            "hotspots": str(Path(analyses["hotspots"]).relative_to(ROOT)),
            "seasonality": str(Path(analyses["seasonality"]).relative_to(ROOT)),
            "profile": str(profile_path.relative_to(ROOT)),
        },
    }
    REPORT_PATH.write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")
    return rapport


if __name__ == "__main__":
    source_arg = sys.argv[1] if len(sys.argv) > 1 else None
    resultat = run(source_arg)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
