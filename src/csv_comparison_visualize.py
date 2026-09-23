"""Visualisation construite uniquement a partir des deux CSV de comparaison."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROXIMITY_PATH = ROOT / "reports" / "data" / "attack_species_proximity.csv"
SUMMARY_PATH = ROOT / "reports" / "data" / "species_attack_comparison.csv"
OUTPUT_PATH = ROOT / "reports" / "images" / "csv_species_comparison.png"
PIE_OUTPUT_PATH = ROOT / "reports" / "images" / "candidate_species_pie.png"
TABLE_OUTPUT_PATH = ROOT / "reports" / "data" / "candidate_species_table.csv"
INTERPRETATION_OUTPUT_PATH = ROOT / "reports" / "interpretation" / "csv_species_interpretation.md"


def plot_csv_comparison(
    proximity_path: Path = PROXIMITY_PATH,
    summary_path: Path = SUMMARY_PATH,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Genere une figure synthetique a partir des deux CSV de comparaison."""
    proximity = pd.read_csv(proximity_path)
    summary = pd.read_csv(summary_path)
    required_proximity = {"species", "nearest_distance_km", "distance_band"}
    required_summary = {
        "species",
        "attaques_proximite_forte_25km",
        "attaques_proximite_regionale_100km",
        "occurrences_juvéniles_proches",
    }
    missing = (required_proximity - set(proximity.columns)) | (required_summary - set(summary.columns))
    if missing:
        raise ValueError(f"Colonnes manquantes dans les CSV : {sorted(missing)}")

    order = summary.sort_values("attaques_proximite_regionale_100km")["species"].tolist()
    summary = summary.set_index("species").reindex(order).reset_index()
    proximity["nearest_distance_km"] = pd.to_numeric(proximity["nearest_distance_km"], errors="coerce")

    fig = plt.figure(figsize=(14, 10), layout="constrained")
    grid = fig.add_gridspec(2, 2)
    bars_axis = fig.add_subplot(grid[0, 0])
    juvenile_axis = fig.add_subplot(grid[0, 1])
    distance_axis = fig.add_subplot(grid[1, :])

    labels = summary["species"]
    bars_axis.barh(labels, summary["attaques_proximite_regionale_100km"], color="#3a9d8f", label="0-100 km")
    bars_axis.barh(labels, summary["attaques_proximite_forte_25km"], color="#e07a5f", label="0-25 km")
    bars_axis.set_title("Attaques proches d'une occurrence GBIF")
    bars_axis.set_xlabel("Nombre d'attaques comparees")
    bars_axis.legend()
    bars_axis.grid(axis="x", alpha=0.2)

    juvenile_axis.barh(labels, summary["occurrences_juvéniles_proches"], color="#176b87")
    juvenile_axis.set_title("Attaques avec observation juvenile a moins de 100 km")
    juvenile_axis.set_xlabel("Nombre d'attaques")
    juvenile_axis.grid(axis="x", alpha=0.2)

    distance_data = [proximity.loc[proximity["species"] == species, "nearest_distance_km"].dropna() for species in order]
    distance_axis.boxplot(distance_data, vert=False, tick_labels=order, showfliers=False)
    distance_axis.axvline(25, color="#e07a5f", linestyle="--", linewidth=1.2, label="Seuil 25 km")
    distance_axis.axvline(100, color="#3a9d8f", linestyle="--", linewidth=1.2, label="Seuil 100 km")
    distance_axis.set_xscale("symlog", linthresh=25)
    distance_axis.set_title("Distribution de la distance vers l'occurrence GBIF la plus proche")
    distance_axis.set_xlabel("Distance en km, echelle symlog")
    distance_axis.legend()
    distance_axis.grid(axis="x", alpha=0.2)

    fig.suptitle("Comparaison des deux CSV : attaques et presence des especes", fontsize=15)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def write_candidate_species_outputs(
    summary_path: Path = SUMMARY_PATH,
    pie_output_path: Path = PIE_OUTPUT_PATH,
    table_output_path: Path = TABLE_OUTPUT_PATH,
    interpretation_output_path: Path = INTERPRETATION_OUTPUT_PATH,
) -> dict[str, Path]:
    """Produit un camembert et un tableau de candidates geographiques.

    Ce ne sont pas les especes effectivement identifiees lors des attaques.
    """
    summary = pd.read_csv(summary_path)
    required = {
        "species",
        "attaques_proximite_forte_25km",
        "attaques_proximite_regionale_100km",
        "occurrences_juvéniles_proches",
    }
    missing = required - set(summary.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le resume : {sorted(missing)}")

    candidates = summary.rename(
        columns={
            "species": "espece_candidate",
            "attaques_proximite_forte_25km": "attaques_a_moins_de_25_km",
            "attaques_proximite_regionale_100km": "attaques_a_moins_de_100_km",
            "occurrences_juvéniles_proches": "attaques_avec_juveniles_a_moins_de_100_km",
        }
    ).sort_values("attaques_a_moins_de_100_km", ascending=False)
    total = candidates["attaques_a_moins_de_100_km"].sum()
    candidates["part_des_proximités_100_km_pct"] = (
        candidates["attaques_a_moins_de_100_km"] / total * 100 if total else 0
    ).round(1)
    table_output_path.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(table_output_path, index=False)

    pie_output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots(figsize=(9, 7))
    axis.pie(
        candidates["attaques_a_moins_de_100_km"],
        labels=candidates["espece_candidate"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#3a9d8f", "#e07a5f", "#176b87", "#f2c14e"],
        wedgeprops={"linewidth": 1, "edgecolor": "white"},
    )
    axis.set_title("Especes candidates selon la proximite GBIF\n(pas une identification des attaquants)")
    fig.tight_layout()
    fig.savefig(pie_output_path, dpi=150)
    plt.close(fig)

    top_species = candidates.iloc[0]
    lines = [
        "# Interpretation du visuel CSV",
        "",
        "## Lecture simple",
        "",
        "Le camembert repartit les rapprochements entre attaques et especes ayant une occurrence GBIF a moins de 100 km. Une meme attaque peut apparaitre dans plusieurs especes : les parts ne sont donc pas exclusives et ne representent pas les especes effectivement identifiees lors des attaques.",
        "",
        f"L'espece qui ressort le plus comme candidate geographique est **{top_species['espece_candidate']}**, avec {int(top_species['attaques_a_moins_de_100_km'])} attaques proches, soit {top_species['part_des_proximités_100_km_pct']:.1f}% des proximités comptabilisees.",
        "",
        "## Interpretation prudente",
        "",
        "- Une forte part signifie que les lieux d'attaques recoupent des zones ou cette espece a ete observee par GBIF.",
        "- Les pourcentages portent sur les rapprochements espece-attaque, pas sur un nombre d'attaques uniques.",
        "- Cela peut refleter une presence regionale, mais aussi l'effort d'observation GBIF, la precision des coordonnees et la frequentation humaine des cotes.",
        "- Les observations juveniles peuvent signaler des zones candidates de nurserie, sans prouver une reproduction sur place.",
        "- Pour parler des especes qui ont reellement attaque, il faudrait des rapports d'identification, des photographies, des analyses ADN ou des donnees de suivi associees aux incidents.",
        "",
        "## Conclusion",
        "",
        "Le visuel est donc un classement de candidates geographiques, utile pour orienter l'analyse, et non un classement de responsabilite des especes.",
    ]
    interpretation_output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "pie": pie_output_path,
        "table": table_output_path,
        "interpretation": interpretation_output_path,
    }


if __name__ == "__main__":
    print(f"Visualisation generee : {plot_csv_comparison()}")
    for name, path in write_candidate_species_outputs().items():
        print(f"{name}: {path}")