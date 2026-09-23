"""Visualisation des occurrences GBIF par espece."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_DIR = ROOT / "data" / "reference"
OUTPUT_PATH = ROOT / "reports" / "species_occurrences.png"
WORLD_GEOJSON_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
WORLD_GEOJSON_PATH = REFERENCE_DIR / "ne_110m_admin_0_countries.geojson"


def _load_world_features() -> list[dict]:
    """Charge les frontieres mondiales et les conserve pour les prochains runs."""
    if not WORLD_GEOJSON_PATH.exists():
        with urlopen(WORLD_GEOJSON_URL, timeout=30) as response:
            WORLD_GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            WORLD_GEOJSON_PATH.write_bytes(response.read())
    data = json.loads(WORLD_GEOJSON_PATH.read_text(encoding="utf-8"))
    return data["features"]


def _draw_world(axis, features: list[dict]) -> None:
    """Dessine les polygones de frontiere dans un axe longitude/latitude."""
    for feature in features:
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates", [])
        polygons = coordinates if geometry.get("type") == "MultiPolygon" else [coordinates]
        for polygon in polygons:
            if not polygon:
                continue
            outline = polygon[0] if geometry.get("type") == "MultiPolygon" else polygon[0]
            axis.add_patch(
                Polygon(outline, closed=True, facecolor="#edf1f2", edgecolor="#aab7b8", linewidth=0.35, zorder=0)
            )


def plot_species_occurrences(
    reference_dir: Path = REFERENCE_DIR,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Trace les occurrences GBIF disponibles par espece et par latitude."""
    files = sorted(reference_dir.glob("gbif_*_occurrences.csv"))
    if not files:
        raise FileNotFoundError("Aucun export GBIF trouve dans data/reference")
    frames = []
    for path in files:
        frame = pd.read_csv(path)
        frame["source_file"] = path.name
        frames.append(frame)
    occurrences = pd.concat(frames, ignore_index=True)
    occurrences["latitude"] = pd.to_numeric(occurrences["latitude"], errors="coerce")
    occurrences["longitude"] = pd.to_numeric(occurrences["longitude"], errors="coerce")
    occurrences = occurrences.dropna(subset=["latitude", "longitude", "species"])

    features = _load_world_features()
    fig = plt.figure(figsize=(14, 11))
    grid = fig.add_gridspec(2, 2, height_ratios=[1, 1.25])
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]
    world_axis = fig.add_subplot(grid[1, :])
    colors = plt.cm.tab10.colors
    for index, (species, group) in enumerate(occurrences.groupby("species")):
        color = colors[index % len(colors)]
        axes[0].scatter(group["longitude"], group["latitude"], s=24, alpha=0.7, label=species, color=color)
        world_axis.scatter(group["longitude"], group["latitude"], s=30, alpha=0.75, label=species, color=color, zorder=2)
        axes[1].hist(group["latitude"], bins=18, alpha=0.45, label=species, color=color)

    axes[0].set_title("Occurrences GBIF par espece")
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[0].set_xlim(-180, 180)
    axes[0].set_ylim(-90, 90)
    axes[0].grid(alpha=0.2)
    axes[0].legend(fontsize=8, loc="upper right")
    axes[1].set_title("Repartition latitudinale")
    axes[1].set_xlabel("Latitude")
    axes[1].set_ylabel("Nombre d'observations")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.2)
    _draw_world(world_axis, features)
    world_axis.set_title("Carte mondiale des occurrences GBIF")
    world_axis.set_xlabel("Longitude")
    world_axis.set_ylabel("Latitude")
    world_axis.set_xlim(-180, 180)
    world_axis.set_ylim(-90, 90)
    world_axis.set_aspect("equal", adjustable="box")
    world_axis.grid(alpha=0.2, zorder=1)
    world_axis.legend(fontsize=8, loc="lower left")
    fig.suptitle("Presence documentee par GBIF (pas une abondance)", fontsize=14)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    print(f"Visualisation generee : {plot_species_occurrences()}")