"""Compare prudemment les attaques geocodees avec les occurrences GBIF."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.species_visualize import _draw_world, _load_world_features

ROOT = Path(__file__).resolve().parent.parent
ATTACKS_PATH = ROOT / "reports" / "attacks_with_coordinates.csv"
REFERENCE_DIR = ROOT / "data" / "reference"
REPORTS_DIR = ROOT / "reports"
PROXIMITY_PATH = REPORTS_DIR / "attack_species_proximity.csv"
SUMMARY_PATH = REPORTS_DIR / "species_attack_comparison.csv"
HYPOTHESES_PATH = REPORTS_DIR / "ecological_hypotheses.md"
FIGURE_PATH = REPORTS_DIR / "attack_species_comparison.png"


def haversine_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    """Calcule la distance orthodromique approximative entre deux points."""
    earth_radius_km = 6371.0088
    lat_a, lat_b = math.radians(latitude_a), math.radians(latitude_b)
    delta_lat = math.radians(latitude_b - latitude_a)
    delta_lon = math.radians(longitude_b - longitude_a)
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    return 2 * earth_radius_km * math.asin(math.sqrt(value))


def compare_attacks_to_species(attacks: pd.DataFrame, occurrences: pd.DataFrame) -> pd.DataFrame:
    """Associe chaque attaque geocodee a la presence GBIF la plus proche par espece."""
    attacks = attacks.copy()
    occurrences = occurrences.copy()
    attacks["latitude"] = pd.to_numeric(attacks["latitude"], errors="coerce")
    attacks["longitude"] = pd.to_numeric(attacks["longitude"], errors="coerce")
    occurrences["latitude"] = pd.to_numeric(occurrences["latitude"], errors="coerce")
    occurrences["longitude"] = pd.to_numeric(occurrences["longitude"], errors="coerce")
    attacks = attacks.dropna(subset=["latitude", "longitude"]).reset_index(names="attack_row_id")
    occurrences = occurrences.dropna(subset=["latitude", "longitude", "species"])

    rows = []
    for _, attack in attacks.iterrows():
        for species, species_rows in occurrences.groupby("species"):
            distances = species_rows.apply(
                lambda occurrence: haversine_km(
                    attack["latitude"], attack["longitude"], occurrence["latitude"], occurrence["longitude"]
                ),
                axis=1,
            )
            nearest_index = distances.idxmin()
            nearest = species_rows.loc[nearest_index]
            distance = float(distances.loc[nearest_index])
            within_25 = int((distances <= 25).sum())
            within_100 = int((distances <= 100).sum())
            juvenile_within_100 = int(((distances <= 100) & species_rows["life_stage"].fillna("").str.upper().eq("JUVENILE")).sum())
            if distance <= 25:
                distance_band = "proximite_forte"
            elif distance <= 100:
                distance_band = "proximite_regionale"
            else:
                distance_band = "pas_de_proximite_100km"
            rows.append(
                {
                    "attack_row_id": int(attack["attack_row_id"]),
                    "date_complete": attack.get("date_complete"),
                    "annee": attack.get("annee"),
                    "pays": attack.get("pays"),
                    "zone": attack.get("zone"),
                    "localite": attack.get("localite"),
                    "activite": attack.get("activite"),
                    "type_attaque": attack.get("type_attaque"),
                    "attack_latitude": attack["latitude"],
                    "attack_longitude": attack["longitude"],
                    "species": species,
                    "nearest_gbif_record_id": nearest.get("source_record_id"),
                    "nearest_distance_km": round(distance, 2),
                    "gbif_coordinate_uncertainty_m": nearest.get("coordinate_uncertainty_m"),
                    "distance_band": distance_band,
                    "occurrences_within_25km": within_25,
                    "occurrences_within_100km": within_100,
                    "juvenile_occurrences_within_100km": juvenile_within_100,
                    "gbif_observed_at": nearest.get("observed_at"),
                    "gbif_source_url": nearest.get("source_url"),
                }
            )
    return pd.DataFrame(rows)


def _build_summary(proximity: pd.DataFrame) -> pd.DataFrame:
    summary = (
        proximity.assign(
            close_25km=proximity["nearest_distance_km"] <= 25,
            regional_100km=proximity["nearest_distance_km"] <= 100,
        )
        .groupby("species")
        .agg(
            attaques_comparees=("attack_row_id", "nunique"),
            attaques_proximite_forte_25km=("close_25km", "sum"),
            attaques_proximite_regionale_100km=("regional_100km", "sum"),
            occurrences_juvéniles_proches=("juvenile_occurrences_within_100km", lambda values: int((values > 0).sum())),
        )
        .reset_index()
    )
    return summary


def _write_hypotheses(summary: pd.DataFrame, proximity: pd.DataFrame, path: Path) -> None:
    total_attacks = proximity["attack_row_id"].nunique()
    activities = proximity[proximity["nearest_distance_km"] <= 100]["activite"].fillna("Inconnue").value_counts().head(5)
    activity_text = ", ".join(f"{name} ({count})" for name, count in activities.items()) or "aucune activite exploitable"
    lines = [
        "# Comparaison attaques et presence des especes",
        "",
        f"Cette analyse compare {total_attacks} attaques geocodees aux occurrences GBIF disponibles dans `data/reference/`.",
        "Elle produit des hypotheses de proximite, pas une identification de l'espece responsable.",
        "",
        "## Ce que les donnees montrent",
        "",
        "- Une attaque est consideree proche d'une espece si une occurrence GBIF se trouve a moins de 25 km (proximite forte) ou 100 km (proximite regionale).",
        "- Les coordonnees des attaques sont des coordonnees de villes ou de lieux textuels, et les occurrences GBIF sont soumises a un biais d'observation.",
        f"- Parmi les attaques avec une presence d'espece a moins de 100 km, les activites les plus frequentes sont : {activity_text}.",
        "",
        "## Hypotheses prudentes",
        "",
        "1. **Chevauchement geographique** : une espece est candidate uniquement lorsqu'une occurrence GBIF est proche. Cela indique une presence documentee dans la region, pas la presence de l'animal au moment de l'attaque.",
        "2. **Nurserie possible** : des occurrences GBIF marquees `JUVENILE` proches d'une zone peuvent signaler un habitat de juveniles. Elles ne prouvent pas un lieu de reproduction et ne disent rien sur l'agressivite.",
        "3. **Activite humaine** : la frequence des activites comme la baignade, le surf ou la peche est un proxy de chevauchement humain. Sans nombre de personnes exposees ni temps passe dans l'eau, on ne peut pas calculer un risque.",
        "4. **Courants chauds** : cette hypothese n'est pas testee ici. Le projet ne contient pas encore de temperature de surface, d'anomalie thermique ni de vecteur de courant. Il faut joindre une serie NOAA ou Copernicus par date et position.",
        "5. **Reproduction et agressivite** : aucune donnee actuelle ne permet de conclure que la reproduction rend les requins plus agressifs. Il faudrait l'espece, le sexe, le stade de vie, la saison de reproduction et une mesure de l'exposition humaine.",
        "",
        "## Conclusion",
        "",
        "Les seules conclusions solides sont des proximités entre des lieux d'attaques approximatifs et des observations GBIF. Les noms d'especes produits sont des candidates geographiques et doivent etre confirmes par des donnees d'identification de l'animal, comme un rapport de terrain ou une trajectoire OCEARCH.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _plot_comparison(proximity: pd.DataFrame, path: Path) -> None:
    features = _load_world_features()
    fig = plt.figure(figsize=(14, 10), layout="constrained")
    grid = fig.add_gridspec(2, 1, height_ratios=[1.5, 1])
    world_axis = fig.add_subplot(grid[0, 0])
    summary_axis = fig.add_subplot(grid[1, 0])
    _draw_world(world_axis, features)
    attacks = proximity.drop_duplicates("attack_row_id")
    world_axis.scatter(attacks["attack_longitude"], attacks["attack_latitude"], s=8, alpha=0.25, color="#d95f59", label="Attaques")
    for index, (species, rows) in enumerate(proximity.groupby("species")):
        world_axis.scatter([], [], color=plt.cm.tab10.colors[index % 10], label=species)
    world_axis.set_title("Attaques et especes presentes dans la region")
    world_axis.set_xlim(-180, 180)
    world_axis.set_ylim(-90, 90)
    world_axis.set_xlabel("Longitude")
    world_axis.set_ylabel("Latitude")
    world_axis.set_aspect("equal", adjustable="box")
    world_axis.legend(fontsize=8, loc="lower left")
    summary = _build_summary(proximity).sort_values("attaques_proximite_regionale_100km")
    summary_axis.barh(summary["species"], summary["attaques_proximite_regionale_100km"], color="#3a9d8f")
    summary_axis.set_title("Attaques avec une occurrence GBIF a moins de 100 km")
    summary_axis.set_xlabel("Attaques comparees")
    summary_axis.grid(axis="x", alpha=0.2)
    fig.suptitle("Comparaison spatiale : attaques et occurrences GBIF", fontsize=15)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run_comparison(
    attacks_path: Path = ATTACKS_PATH,
    reference_dir: Path = REFERENCE_DIR,
    reports_dir: Path = REPORTS_DIR,
) -> dict[str, str]:
    attacks = pd.read_csv(attacks_path)
    occurrence_files = sorted(reference_dir.glob("gbif_*_occurrences.csv"))
    if not occurrence_files:
        raise FileNotFoundError("Aucun export GBIF disponible")
    occurrences = pd.concat([pd.read_csv(path) for path in occurrence_files], ignore_index=True)
    proximity = compare_attacks_to_species(attacks, occurrences)
    summary = _build_summary(proximity)
    reports_dir.mkdir(parents=True, exist_ok=True)
    proximity.to_csv(PROXIMITY_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)
    _write_hypotheses(summary, proximity, HYPOTHESES_PATH)
    _plot_comparison(proximity, FIGURE_PATH)
    return {"proximity": str(PROXIMITY_PATH), "summary": str(SUMMARY_PATH), "hypotheses": str(HYPOTHESES_PATH), "figure": str(FIGURE_PATH)}


if __name__ == "__main__":
    for name, path in run_comparison().items():
        print(f"{name}: {path}")