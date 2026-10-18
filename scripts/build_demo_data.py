"""Generate reproducible, non-personal sample data and expected outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.transform import transform
from src.validate import run_quality_rules

SAMPLES_DIR = ROOT / "data" / "samples"


def build_sample_data() -> tuple[Path, Path, Path]:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    countries = ["USA", "AUSTRALIA", "SOUTH AFRICA", "BRAZIL"]
    areas = ["Florida", "Queensland", "Western Cape", "Pernambuco"]
    locations = ["Miami", "Brisbane", "Cape Town", "Recife"]
    activities = ["Surfing", "Swimming", "Fishing", "Diving"]
    rows = []
    for index in range(120):
        month = index % 12 + 1
        rows.append(
            {
                "date": f"{2010 + index % 16}-{month:02d}-15",
                "year": 2010 + index % 16,
                "type": "Unprovoked" if index % 5 else "Provoked",
                "country": countries[index % len(countries)],
                "area": areas[index % len(areas)],
                "location": locations[index % len(locations)],
                "activity": activities[index % len(activities)],
                "name": f"Synthetic record {index + 1:03d}",
                "sex": "M" if index % 2 else "F",
                "age": "250" if index == 116 else str(18 + index % 63),
            }
        )

    rows[117]["country"] = ""
    rows[118]["year"] = 999
    rows[119]["type"] = "Synthetic invalid type"
    rows.append(rows[0].copy())

    raw_path = SAMPLES_DIR / "sample_source.csv"
    curated_path = SAMPLES_DIR / "sample_curated.csv"
    rejected_path = SAMPLES_DIR / "sample_rejected.csv"
    raw = pd.DataFrame(rows)
    raw.to_csv(raw_path, index=False)
    accepted, rejected, _ = run_quality_rules(raw)
    transform(accepted).to_csv(curated_path, index=False)
    rejected.to_csv(rejected_path, index=False)
    return raw_path, curated_path, rejected_path


if __name__ == "__main__":
    for path in build_sample_data():
        print(path.relative_to(ROOT))