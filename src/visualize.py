"""
Premiere visualisation, volontairement simple : nombre d'attaques par
annee sur le dataset curated. A enrichir au fil des iterations (repartition
par activite, par pays, etc.).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.analyze import build_hotspots

ROOT = Path(__file__).resolve().parent.parent
CURATED_PATH = ROOT / "data" / "curated" / "global_shark_attacks-selected-columns.csv"
OUTPUT_PATH = ROOT / "reports" / "attaques_par_annee.png"
DASHBOARD_PATH = ROOT / "reports" / "dashboard_incidents.png"


def plot_attacks_per_year() -> Path:
    df = pd.read_csv(CURATED_PATH)
    counts = df.dropna(subset=["annee"]).groupby("annee").size()
    counts = counts[counts.index >= 1900]  # dates tres anciennes ecartees pour la lisibilite

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(counts.index, counts.values, color="#1E6B67", linewidth=1.6)
    ax.fill_between(counts.index, counts.values, color="#1E6B67", alpha=0.12)
    ax.set_title("Attaques de requins recensees par annee")
    ax.set_xlabel("Annee")
    ax.set_ylabel("Nombre d'attaques")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=150)
    plt.close(fig)
    return OUTPUT_PATH


def plot_incident_dashboard() -> Path:
    """Genere une vue synthetique des incidents declares."""
    df = pd.read_csv(CURATED_PATH)
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce")
    df["date_complete"] = pd.to_datetime(df["date_complete"], errors="coerce")
    hotspots = build_hotspots(df).head(10).sort_values("incidents_declares")

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("Incidents de requins recenses : tendances et lieux", fontsize=15)

    yearly = df.dropna(subset=["annee"]).query("annee >= 1900").groupby("annee").size()
    axes[0, 0].plot(yearly.index, yearly.values, color="#176b87", linewidth=1.8)
    axes[0, 0].set_title("Evolution annuelle")
    axes[0, 0].set_xlabel("Annee")
    axes[0, 0].set_ylabel("Incidents declares")

    labels = hotspots["localite"].str.slice(0, 28)
    axes[0, 1].barh(labels, hotspots["incidents_declares"], color="#e07a5f")
    axes[0, 1].set_title("Top 10 localites")
    axes[0, 1].set_xlabel("Incidents declares")

    monthly = df.dropna(subset=["date_complete"]).groupby(df["date_complete"].dt.month).size()
    axes[1, 0].bar(monthly.index, monthly.values, color="#3a9d8f")
    axes[1, 0].set_title("Saisonnalite des dates recensees")
    axes[1, 0].set_xlabel("Mois")
    axes[1, 0].set_ylabel("Incidents declares")
    axes[1, 0].set_xticks(range(1, 13))

    countries = df["pays"].fillna("Inconnu").value_counts().head(10).sort_values()
    axes[1, 1].barh(countries.index, countries.values, color="#264653")
    axes[1, 1].set_title("Top 10 pays")
    axes[1, 1].set_xlabel("Incidents declares")

    for axis in axes.flat:
        axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(DASHBOARD_PATH, dpi=150)
    plt.close(fig)
    return DASHBOARD_PATH


if __name__ == "__main__":
    chemin = plot_attacks_per_year()
    print(f"Graphique genere -> {chemin}")
