"""
Pipeline batch complet.

    Source raw canonique (data/raw) -> Collecteur -> Raw (data/raw)
        -> Validation (5 regles) -> Curated (data/curated) + Rejected (data/rejected)
        -> Rapport (reports/interpretation) + Visualisations (reports/images)

Idempotence : les fichiers curated et rejected sont entierement remplaces
a chaque execution. Chaque run conserve une copie brute horodatee distincte.

Usage :
    python -m src.pipeline [chemin_source_csv]
"""

from __future__ import annotations

import json
import logging
import sys
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.collect import collect, sha256_file
from src.analyze import write_analysis_reports
from src.profile import write_profile
from src.validate import run_quality_rules
from src.transform import transform
from src.visualize import plot_attacks_per_year, plot_incident_dashboard
from src.enrich.service import run_enrichment
from src.viz.environment_charts import write_environment_charts

ROOT = Path(__file__).resolve().parent.parent
CURATED_PATH = ROOT / "data" / "curated" / "shark_attacks_curated.csv"
REJECTED_PATH = ROOT / "data" / "rejected" / "rejected_rows.csv"
REPORTS_DIR = ROOT / "reports"
REPORT_PATH = REPORTS_DIR / "interpretation" / "run_report.json"
REPORT_DATA_DIR = REPORTS_DIR / "data"
PROFILE_PATH = REPORTS_DIR / "interpretation" / "source_profile.json"
ENRICHED_PATH = ROOT / "data" / "curated" / "attacks_enriched.csv"
GEOCODED_PATH = REPORT_DATA_DIR / "attacks_with_coordinates.csv"
GBIF_DIR = ROOT / "data" / "reference"
LOGGER = logging.getLogger("shark_attacks_pipeline")


def run(source_path: str | None = None, enrich: bool = False) -> dict:
    debut = time.perf_counter()
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%S%fZ")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rapport = {
        "pipeline": "shark-attacks-collector",
        "run_id": run_id,
        "executed_at": started_at.isoformat(),
        "status": "RUNNING",
        "contract_version": "1.0",
    }
    LOGGER.info("run_id=%s event=started source=%s", run_id, source_path or "default")

    try:
        raw_path = collect(source_path)
        rapport.update(
            {
                "source_file": raw_path.name,
                "source_sha256": sha256_file(raw_path),
                "source_size_bytes": raw_path.stat().st_size,
            }
        )
        LOGGER.info("run_id=%s event=source_copied file=%s", run_id, raw_path.name)
        df = pd.read_csv(raw_path)
        if df.empty:
            raise ValueError("La source CSV ne contient aucune observation.")
        required_columns = {"country", "year", "type", "age"}
        missing_columns = sorted(required_columns.difference(df.columns))
        if missing_columns:
            raise ValueError(f"Colonnes requises absentes : {', '.join(missing_columns)}")

        profile_path = write_profile(df, PROFILE_PATH)
        accepted, rejected, quality = run_quality_rules(df)
        curated = transform(accepted)

        CURATED_PATH.parent.mkdir(parents=True, exist_ok=True)
        REJECTED_PATH.parent.mkdir(parents=True, exist_ok=True)
        curated.to_csv(CURATED_PATH, index=False)
        rejected.to_csv(REJECTED_PATH, index=False)
        LOGGER.info(
            "run_id=%s event=quality_complete input=%d accepted=%d rejected=%d duplicates=%d",
            run_id,
            quality.input_rows,
            quality.accepted_rows,
            quality.rejected_rows,
            quality.duplicates_removed,
        )

        graphique = plot_attacks_per_year()
        dashboard = plot_incident_dashboard()
        analyses = write_analysis_reports(CURATED_PATH, REPORT_DATA_DIR)
        valid_dates = pd.to_datetime(curated["date_complete"], errors="coerce").dropna()
        newest_record_date = valid_dates.max() if not valid_dates.empty else None
        data_age_days = (
            (started_at.date() - newest_record_date.date()).days
            if newest_record_date is not None
            else None
        )

        rapport.update(
            {
                "status": "PASS",
                "source_file": raw_path.name,
                "source_sha256": sha256_file(raw_path),
                "source_size_bytes": raw_path.stat().st_size,
                "source_mtime_utc": datetime.fromtimestamp(
                    raw_path.stat().st_mtime, timezone.utc
                ).isoformat(),
                "input_rows": quality.input_rows,
                "accepted_rows": quality.accepted_rows,
                "rejected_rows": quality.rejected_rows,
                "duplicates_removed": quality.duplicates_removed,
                "failures_by_rule": quality.failures_by_rule,
                "quality_status": (
                    "PASS_WITH_WARNINGS"
                    if quality.rejected_rows or quality.duplicates_removed
                    else "PASS"
                ),
                "warnings": [
                    warning
                    for warning in (
                        f"{quality.rejected_rows} ligne(s) rejetee(s)"
                        if quality.rejected_rows
                        else None,
                        f"{quality.duplicates_removed} doublon(s) supprime(s)"
                        if quality.duplicates_removed
                        else None,
                    )
                    if warning is not None
                ],
                "enrichment": {
                    "status": "NOT_REQUESTED",
                    "api_calls": 0,
                    "cache_hits": 0,
                    "failures": 0,
                    "lines_enriched": 0,
                    "lines_excluded": 0,
                    "duration_seconds": 0.0,
                },
                "newest_record_date": (
                    newest_record_date.date().isoformat()
                    if newest_record_date is not None
                    else None
                ),
                "data_age_days": data_age_days,
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
        )
        if enrich:
            environment_report = run_enrichment(
                CURATED_PATH,
                GEOCODED_PATH,
                ENRICHED_PATH,
                gbif_dir=GBIF_DIR,
                analysis_dir=REPORT_DATA_DIR,
            )
            rapport["enrichment"] = environment_report
            rapport["outputs"]["environmental_enrichment"] = str(
                ENRICHED_PATH.relative_to(ROOT)
            )
            rapport["outputs"]["environment_hypotheses"] = str(
                Path(environment_report["hypotheses_output"]).relative_to(ROOT)
            )
            for output_key, report_key in (
                ("environment_monthly_sst", "monthly_sst_output"),
                ("environment_sensitivities", "sensitivities_output"),
            ):
                if environment_report.get(report_key):
                    rapport["outputs"][output_key] = str(
                        Path(environment_report[report_key]).relative_to(ROOT)
                    )
            charts = write_environment_charts(
                ENRICHED_PATH,
                REPORT_DATA_DIR / "environment_hypotheses.csv",
                REPORT_DATA_DIR / "environment_monthly_sst.csv",
                REPORTS_DIR / "images",
            )
            environment_report["charts"] = {
                name: str(path.relative_to(ROOT)) for name, path in charts.items()
            }
            rapport["outputs"]["environment_charts"] = environment_report["charts"]
            if environment_report["status"] == "WARN":
                rapport["warnings"].append(
                    "Enrichissement environnemental partiel; consulter la section enrichment."
                )
        LOGGER.info(
            "run_id=%s event=completed status=%s quality_status=%s enrichment_status=%s",
            run_id,
            rapport["status"],
            rapport["quality_status"],
            rapport["enrichment"]["status"],
        )
    except Exception as error:
        rapport.update(
            {
                "status": "FAIL",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "duration_seconds": round(time.perf_counter() - debut, 2),
            }
        )
        REPORT_PATH.write_text(
            json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        LOGGER.exception("run_id=%s event=failed", run_id)
        raise

    REPORT_PATH.write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding="utf-8")
    return rapport


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Exécuter le pipeline Shark Attacks Collector")
    parser.add_argument("source", nargs="?", help="Chemin du CSV source facultatif")
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Activer les enrichissements environnementaux optionnels",
    )
    arguments = parser.parse_args()
    resultat = run(arguments.source, enrich=arguments.enrich)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
