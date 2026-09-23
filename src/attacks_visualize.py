"""Carte des attaques geocodees a partir des lieux textuels."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.species_visualize import _draw_world, _load_world_features

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "reports" / "attacks_with_coordinates.csv"
OUTPUT_PATH = ROOT / "reports" / "attack_locations.png"


def plot_attack_locations(
    input_path: Path = INPUT_PATH,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Genere une carte mondiale des attaques disposant de coordonnees."""
    attacks = pd.read_csv(input_path)
    attacks["latitude"] = pd.to_numeric(attacks["latitude"], errors="coerce")
    attacks["longitude"] = pd.to_numeric(attacks["longitude"], errors="coerce")
    attacks = attacks.dropna(subset=["latitude", "longitude"])
    if attacks.empty:
        raise ValueError("Aucune attaque geocodee dans le fichier enrichi")

    features = _load_world_features()
    fig = plt.figure(figsize=(14, 11), layout="constrained")
    grid = fig.add_gridspec(2, 2, height_ratios=[1.35, 1], hspace=0.3)
    world_axis = fig.add_subplot(grid[0, :])
    latitude_axis = fig.add_subplot(grid[1, 0])
    places_axis = fig.add_subplot(grid[1, 1])

    _draw_world(world_axis, features)
    world_axis.scatter(
        attacks["longitude"],
        attacks["latitude"],
        s=9,
        alpha=0.32,
        color="#d95f59",
        edgecolors="none",
        zorder=2,
    )
    world_axis.set_title(f"Carte mondiale des attaques geocodees ({len(attacks)} lignes)")
    world_axis.set_xlabel("Longitude")
    world_axis.set_ylabel("Latitude")
    world_axis.set_xlim(-180, 180)
    world_axis.set_ylim(-90, 90)
    world_axis.set_aspect("equal", adjustable="box")
    world_axis.grid(alpha=0.2, zorder=1)

    latitude_axis.hist(attacks["latitude"], bins=18, color="#3a9d8f", alpha=0.85)
    latitude_axis.set_title("Repartition latitudinale")
    latitude_axis.set_xlabel("Latitude")
    latitude_axis.set_ylabel("Attaques geocodees")
    latitude_axis.grid(alpha=0.2)

    places = attacks["geocoded_query"].value_counts().head(10).sort_values()
    places_axis.barh(places.index, places.values, color="#e07a5f")
    places_axis.set_title("Top des lieux geocodes")
    places_axis.set_xlabel("Attaques")
    places_axis.tick_params(axis="y", labelsize=8)
    places_axis.grid(axis="x", alpha=0.2)

    fig.suptitle("Repartition geographique des attaques recensees", fontsize=15)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    print(f"Visualisation generee : {plot_attack_locations()}")