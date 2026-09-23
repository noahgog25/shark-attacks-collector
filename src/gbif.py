"""Client minimal de l'API officielle GBIF.

GBIF fournit des occurrences publiees, pas une estimation d'abondance. Les
observations de juveniles peuvent aider a reperer des zones candidates de
nurserie, mais ne constituent pas une preuve de reproduction.

Usage:
    python -m src.gbif "Carcharodon carcharias" --limit 100
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

GBIF_API = "https://api.gbif.org/v1"
ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = ROOT / "data" / "reference"


def _get_json(path: str, params: dict[str, str | int]) -> dict:
    query = urlencode(params)
    request = Request(
        f"{GBIF_API}{path}?{query}",
        headers={"Accept": "application/json", "User-Agent": "shark-attacks-collector/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def resolve_species(scientific_name: str) -> dict:
    """Resout un nom scientifique via le backbone taxonomique GBIF."""
    result = _get_json("/species/match", {"name": scientific_name})
    if not result.get("usageKey"):
        raise ValueError(f"Espece non resolue par GBIF : {scientific_name}")
    return result


def normalize_occurrences(match: dict, response: dict, retrieved_at: str) -> pd.DataFrame:
    """Normalise les champs utiles des occurrences GBIF."""
    rows = []
    for occurrence in response.get("results", []):
        latitude = occurrence.get("decimalLatitude")
        longitude = occurrence.get("decimalLongitude")
        if latitude is None or longitude is None:
            continue
        gbif_id = occurrence.get("key")
        rows.append(
            {
                "source": "gbif",
                "source_record_id": gbif_id,
                "species": occurrence.get("species") or match.get("scientificName"),
                "scientific_name": occurrence.get("scientificName"),
                "observed_at": occurrence.get("eventDate"),
                "latitude": latitude,
                "longitude": longitude,
                "country": occurrence.get("country"),
                "locality": occurrence.get("locality"),
                "life_stage": occurrence.get("lifeStage"),
                "basis_of_record": occurrence.get("basisOfRecord"),
                "coordinate_uncertainty_m": occurrence.get("coordinateUncertaintyInMeters"),
                "dataset_name": occurrence.get("datasetName"),
                "license": occurrence.get("license"),
                "source_url": f"https://www.gbif.org/occurrence/{gbif_id}" if gbif_id else None,
                "retrieved_at": retrieved_at,
            }
        )
    return pd.DataFrame(rows)


def fetch_occurrences(scientific_name: str, limit: int = 100) -> tuple[pd.DataFrame, dict]:
    """Recupere les occurrences georeferencees d'une espece via GBIF."""
    if not 1 <= limit <= 300:
        raise ValueError("La limite GBIF doit etre comprise entre 1 et 300")
    match = resolve_species(scientific_name)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    response = _get_json(
        "/occurrence/search",
        {"taxonKey": match["usageKey"], "hasCoordinate": "true", "limit": limit},
    )
    return normalize_occurrences(match, response, retrieved_at), match


def save_occurrences(scientific_name: str, limit: int = 100, output_dir: Path = REFERENCE_DIR) -> Path:
    """Sauvegarde le JSON brut et le CSV normalise avec provenance."""
    match = resolve_species(scientific_name)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    response = _get_json(
        "/occurrence/search",
        {"taxonKey": match["usageKey"], "hasCoordinate": "true", "limit": limit},
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", scientific_name.lower()).strip("_")
    raw_path = output_dir / f"gbif_{slug}.json"
    csv_path = output_dir / f"gbif_{slug}_occurrences.csv"
    raw_path.write_text(json.dumps({"match": match, "response": response}, indent=2), encoding="utf-8")
    normalize_occurrences(match, response, retrieved_at).to_csv(csv_path, index=False)
    return csv_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importer des occurrences de requins depuis GBIF")
    parser.add_argument("scientific_name", help="Nom scientifique, par exemple Carcharodon carcharias")
    parser.add_argument("--limit", type=int, default=100, help="Nombre maximal d'occurrences (1-300)")
    args = parser.parse_args()
    print(f"Occurrences GBIF sauvegardees dans : {save_occurrences(args.scientific_name, args.limit)}")