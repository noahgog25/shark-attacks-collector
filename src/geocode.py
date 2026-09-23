"""Geocodage prudent des lieux d'attaques via Nominatim/OpenStreetMap.

Le geocodage est volontairement optionnel et limite aux lieux les plus
frequents. Les coordonnees obtenues sont celles d'un lieu ou d'une ville,
pas necessairement celles de l'incident exact.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CURATED_PATH = ROOT / "data" / "curated" / "global_shark_attacks-selected-columns.csv"
REFERENCE_DIR = ROOT / "data" / "reference"
OUTPUT_PATH = ROOT / "reports" / "data" / "attacks_with_coordinates.csv"
CACHE_PATH = REFERENCE_DIR / "nominatim_cache.json"
NOMINATIM_API = "https://nominatim.openstreetmap.org/search"


def location_query(row: pd.Series) -> str:
    """Construit une requete du lieu le plus precis disponible."""
    values = []
    for column in ("localite", "zone", "pays"):
        value = str(row.get(column, "")).strip()
        if value and value.lower() not in {"nan", "inconnu"}:
            values.append(value)
    return ", ".join(values)


def _fetch_location(query: str) -> dict | None:
    params = urlencode({"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1})
    request = Request(
        f"{NOMINATIM_API}?{params}",
        headers={
            "Accept": "application/json",
            "User-Agent": "shark-attacks-collector/1.0 (educational project)",
        },
    )
    with urlopen(request, timeout=30) as response:
        results = json.load(response)
    if not results:
        return None
    result = results[0]
    return {
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
        "display_name": result.get("display_name"),
        "geocode_type": result.get("type"),
    }


def enrich_attacks(
    curated_path: Path = CURATED_PATH,
    output_path: Path = OUTPUT_PATH,
    cache_path: Path = CACHE_PATH,
    limit: int = 25,
    delay_seconds: float = 1.1,
) -> Path:
    """Ajoute des coordonnees aux lieux les plus frequents et ecrit un CSV."""
    if limit < 1:
        raise ValueError("La limite doit etre positive")
    df = pd.read_csv(curated_path)
    df["geocoded_query"] = df.apply(location_query, axis=1)
    counts = df.loc[df["geocoded_query"] != "", "geocoded_query"].value_counts().head(limit)

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    retrieved_at = datetime.now(timezone.utc).isoformat()
    for query in counts.index:
        if query in cache:
            continue
        try:
            result = _fetch_location(query)
            cache[query] = {
                "status": "geocoded" if result else "not_found",
                "result": result,
                "retrieved_at": retrieved_at,
                "source": "Nominatim/OpenStreetMap",
            }
        except Exception as error:
            cache[query] = {
                "status": "error",
                "result": None,
                "error": str(error),
                "retrieved_at": retrieved_at,
                "source": "Nominatim/OpenStreetMap",
            }
        cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        time.sleep(delay_seconds)

    df["latitude"] = df["geocoded_query"].map(
        lambda query: (cache.get(query, {}).get("result") or {}).get("latitude")
    )
    df["longitude"] = df["geocoded_query"].map(
        lambda query: (cache.get(query, {}).get("result") or {}).get("longitude")
    )
    df["geocode_status"] = df["geocoded_query"].map(
        lambda query: cache.get(query, {}).get("status", "not_requested")
    )
    df["geocode_source"] = "Nominatim/OpenStreetMap"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Geocoder les lieux d'attaques les plus frequents")
    parser.add_argument("--limit", type=int, default=25, help="Nombre de lieux uniques a geocoder")
    parser.add_argument("--delay", type=float, default=1.1, help="Delai entre les requetes Nominatim")
    args = parser.parse_args()
    print(f"Dataset enrichi : {enrich_attacks(limit=args.limit, delay_seconds=args.delay)}")