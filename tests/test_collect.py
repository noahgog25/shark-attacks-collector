from pathlib import Path

import pytest

from src import collect as collect_module


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