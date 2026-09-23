"""Profilage reproductible d'un DataFrame avant validation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_profile(df: pd.DataFrame) -> dict:
    """Construit un profil compact et serialisable de la source brute."""
    missing = df.isna().mean().round(4).to_dict()
    profile = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "missing_rate": missing,
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_summary": json.loads(df.describe(include="number").to_json()),
        "categorical_top_values": {},
    }
    for column in df.select_dtypes(exclude="number").columns:
        profile["categorical_top_values"][column] = {
            str(value): int(count)
            for value, count in df[column].fillna("<NA>").value_counts().head(10).items()
        }
    return profile


def write_profile(df: pd.DataFrame, output_path: Path) -> Path:
    """Ecrit le profil JSON avant toute transformation."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_profile(df), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path