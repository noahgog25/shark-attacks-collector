import json

import pandas as pd

from src import pipeline as pipeline_module
from src.enrich.service import run_enrichment


def test_pipeline_records_optional_enrichment_warning_without_failing(tmp_path, monkeypatch):
    source = tmp_path / "source.csv"
    pd.DataFrame(
        {
            "date": ["2020-01-02"],
            "year": [2020],
            "type": ["Unprovoked"],
            "country": ["USA"],
            "area": ["Florida"],
            "location": ["Miami"],
            "activity": ["Surfing"],
            "sex": ["M"],
            "age": ["30"],
        }
    ).to_csv(source, index=False)
    monkeypatch.setattr(pipeline_module, "ROOT", tmp_path)
    monkeypatch.setattr(pipeline_module, "REPORT_PATH", tmp_path / "run_report.json")
    monkeypatch.setattr(pipeline_module, "PROFILE_PATH", tmp_path / "profile.json")
    monkeypatch.setattr(pipeline_module, "CURATED_PATH", tmp_path / "curated.csv")
    monkeypatch.setattr(pipeline_module, "REJECTED_PATH", tmp_path / "rejected.csv")
    monkeypatch.setattr(pipeline_module, "REPORT_DATA_DIR", tmp_path / "report-data")
    monkeypatch.setattr(pipeline_module, "GEOCODED_PATH", tmp_path / "coordinates.csv")
    monkeypatch.setattr(pipeline_module, "ENRICHED_PATH", tmp_path / "attacks_enriched.csv")
    monkeypatch.setattr(pipeline_module, "GBIF_DIR", tmp_path / "gbif")
    monkeypatch.setattr(
        pipeline_module,
        "write_environment_charts",
        lambda *_args: {"hypotheses": tmp_path / "hypotheses.png"},
    )
    monkeypatch.setattr(pipeline_module, "collect", lambda _path=None: source)
    monkeypatch.setattr(pipeline_module, "plot_attacks_per_year", lambda: tmp_path / "year.png")
    monkeypatch.setattr(pipeline_module, "plot_incident_dashboard", lambda: tmp_path / "dashboard.png")
    monkeypatch.setattr(
        pipeline_module,
        "write_analysis_reports",
        lambda *_args: {
            "hotspots": tmp_path / "hotspots.csv",
            "seasonality": tmp_path / "seasonality.csv",
        },
    )
    monkeypatch.setattr(
        pipeline_module,
        "run_enrichment",
        lambda *_args, **_kwargs: {
            "status": "WARN",
            "api_calls": 0,
            "cache_hits": 0,
            "failures": 2,
            "lines_enriched": 0,
            "lines_excluded": 1,
            "duration_seconds": 0.1,
            "hypotheses_output": str(tmp_path / "report-data" / "environment_hypotheses.csv"),
        },
    )

    report = pipeline_module.run(str(source), enrich=True)
    persisted = json.loads((tmp_path / "run_report.json").read_text(encoding="utf-8"))

    assert report["status"] == "PASS"
    assert report["enrichment"]["status"] == "WARN"
    assert "Enrichissement environnemental partiel" in report["warnings"][0]
    assert persisted["outputs"]["environmental_enrichment"] == "attacks_enriched.csv"


def test_synthetic_sample_enrichment_is_offline_and_reports_insufficient_locations(tmp_path):
    curated_path = tmp_path / "curated.csv"
    geocoded_path = tmp_path / "geocoded.csv"
    output_path = tmp_path / "data" / "curated" / "attacks_enriched.csv"
    analysis_dir = tmp_path / "reports" / "data"
    sample = pd.read_csv("data/samples/sample_curated.csv")
    sample.to_csv(curated_path, index=False)
    pd.DataFrame(columns=[*sample.columns, "latitude", "longitude"]).to_csv(
        geocoded_path, index=False
    )

    report = run_enrichment(
        curated_path,
        geocoded_path,
        output_path,
        gbif_dir=tmp_path / "gbif",
        analysis_dir=analysis_dir,
    )

    assert report["status"] == "WARN"
    assert report["api_calls"] == report["cache_hits"] == 0
    assert report["lines_enriched"] == 0
    assert report["lines_excluded"] == len(sample)
    assert output_path.exists()
    assert (analysis_dir / "environment_hypotheses.csv").exists()
    assert "name" not in pd.read_csv(output_path).columns
