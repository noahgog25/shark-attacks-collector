import json
from pathlib import Path

import pytest
import pandas as pd

from src import collect as collect_module
from src import pipeline as pipeline_module


def test_collect_conserve_un_snapshot_horodate_sans_modifier_la_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    source = tmp_path / "source.csv"
    source.write_bytes(b"country,year\nUSA,2020\n")
    raw_dir = tmp_path / "raw"
    monkeypatch.setattr(collect_module, "RAW_DIR", raw_dir)

    first_snapshot = collect_module.collect(source)
    second_snapshot = collect_module.collect(source)

    assert first_snapshot != second_snapshot
    assert first_snapshot.name.startswith("source_")
    assert first_snapshot.read_bytes() == source.read_bytes()
    assert second_snapshot.read_bytes() == source.read_bytes()
    assert source.read_bytes() == b"country,year\nUSA,2020\n"


def test_collect_signale_une_source_absente(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        collect_module.collect(tmp_path / "missing.csv")


def test_collect_utilise_lechantillon_si_la_source_par_defaut_est_absente(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    sample = tmp_path / "sample.csv"
    sample.write_text("country,year,type,age\nUSA,2020,Unprovoked,30\n", encoding="utf-8")
    monkeypatch.setattr(collect_module, "DEFAULT_SOURCE", tmp_path / "private.csv")
    monkeypatch.setattr(collect_module, "SAMPLE_SOURCE", sample)
    monkeypatch.setattr(collect_module, "RAW_DIR", tmp_path / "raw")

    snapshot = collect_module.collect()

    assert snapshot.read_text(encoding="utf-8") == sample.read_text(encoding="utf-8")


def test_pipeline_documente_incident_source_absente_et_reprend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    report_path = tmp_path / "run_report.json"
    source = tmp_path / "valid.csv"
    pd.DataFrame(
        {
            "date": ["2020-01-01"],
            "year": [2020],
            "type": ["Unprovoked"],
            "country": ["USA"],
            "area": ["Florida"],
            "location": ["Miami"],
            "activity": ["Surfing"],
            "name": ["Synthetic Person"],
            "sex": ["M"],
            "age": ["30"],
        }
    ).to_csv(source, index=False)
    monkeypatch.setattr(pipeline_module, "REPORT_PATH", report_path)
    monkeypatch.setattr(pipeline_module, "ROOT", tmp_path)
    monkeypatch.setattr(
        pipeline_module,
        "collect",
        lambda _path=None: (_ for _ in ()).throw(FileNotFoundError("source indisponible")),
    )

    with pytest.raises(FileNotFoundError):
        pipeline_module.run("missing.csv")

    failed_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert failed_report["status"] == "FAIL"
    assert failed_report["error_type"] == "FileNotFoundError"
    failed_run_id = failed_report["run_id"]

    monkeypatch.setattr(pipeline_module, "collect", lambda _path=None: source)
    monkeypatch.setattr(pipeline_module, "PROFILE_PATH", tmp_path / "profile.json")
    monkeypatch.setattr(pipeline_module, "CURATED_PATH", tmp_path / "curated.csv")
    monkeypatch.setattr(pipeline_module, "REJECTED_PATH", tmp_path / "rejected.csv")
    monkeypatch.setattr(pipeline_module, "REPORT_DATA_DIR", tmp_path / "reports-data")
    monkeypatch.setattr(
        pipeline_module, "plot_attacks_per_year", lambda: tmp_path / "year.png"
    )
    monkeypatch.setattr(
        pipeline_module, "plot_incident_dashboard", lambda: tmp_path / "dashboard.png"
    )
    monkeypatch.setattr(
        pipeline_module,
        "write_analysis_reports",
        lambda *_args: {
            "hotspots": tmp_path / "hotspots.csv",
            "seasonality": tmp_path / "seasonality.csv",
        },
    )

    result = pipeline_module.run("valid.csv")

    assert result["status"] == "PASS"
    assert result["run_id"] != failed_run_id
    assert result["input_rows"] == 1
    assert result["newest_record_date"] == "2020-01-01"
    assert result["data_age_days"] is not None