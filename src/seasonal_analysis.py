"""Analyse descriptive des activites rapporte dans le temps."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CURATED_PATH = ROOT / "data" / "curated" / "shark_attacks_curated.csv"
REPORT_DATA_DIR = ROOT / "reports" / "data"
REPORT_IMAGE_DIR = ROOT / "reports" / "images"
REPORT_INTERPRETATION_DIR = ROOT / "reports" / "interpretation"
MONTH_NAMES = ["Jan", "Fev", "Mar", "Avr", "Mai", "Jun", "Jul", "Aou", "Sep", "Oct", "Nov", "Dec"]
UNKNOWN_ACTIVITIES = {"", "inconnue", "unknown", "nan", "none", "?"}


def _prepare_dates(curated: pd.DataFrame) -> pd.DataFrame:
    required = {"date_complete", "activite"}
    missing = required - set(curated.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes pour l'analyse saisonniere : {sorted(missing)}")

    work = curated.copy()
    dates = pd.to_datetime(work["date_complete"], errors="coerce")
    work["mois"] = dates.dt.month
    work["jour"] = dates.dt.day
    work["activite_nettoyee"] = work["activite"].fillna("").astype(str).str.strip()
    return work


def _activity_groups(work: pd.DataFrame, top_activities: list[str]) -> pd.Series:
    activity = work["activite_nettoyee"]
    known = ~activity.str.lower().isin(UNKNOWN_ACTIVITIES)
    return activity.where(activity.isin(top_activities), "Autres").where(known)


def _cramers_v(table: pd.DataFrame) -> float:
    observed = table.to_numpy(dtype=float)
    if observed.size == 0:
        return 0.0
    observed = observed[observed.sum(axis=1) > 0]
    observed = observed[:, observed.sum(axis=0) > 0]
    if min(observed.shape) < 2 or observed.sum() == 0:
        return 0.0

    expected = observed.sum(axis=1, keepdims=True) * observed.sum(axis=0, keepdims=True) / observed.sum()
    chi_squared = np.square(observed - expected) / expected
    return float(np.sqrt(chi_squared.sum() / (observed.sum() * min(observed.shape[0] - 1, observed.shape[1] - 1))))


def build_activity_month_distribution(
    curated: pd.DataFrame,
    top_activities: list[str] | None = None,
    exclude_january_first: bool = False,
) -> pd.DataFrame:
    """Retourne la part mensuelle de chaque activite, avec les activites rares regroupees."""
    work = _prepare_dates(curated).dropna(subset=["mois"])
    if exclude_january_first:
        work = work.loc[~((work["mois"] == 1) & (work["jour"] == 1))]

    activity = work["activite_nettoyee"]
    known = ~activity.str.lower().isin(UNKNOWN_ACTIVITIES)
    if top_activities is None:
        top_activities = activity.loc[known].value_counts().head(5).index.tolist()

    work = work.loc[known].copy()
    if work.empty:
        return pd.DataFrame(
            columns=["activite", "mois", "incidents_declares", "part_annuelle_pct"]
        )
    work["activite_groupee"] = _activity_groups(work, top_activities)
    counts = work.groupby(["activite_groupee", "mois"]).size()
    activity_order = top_activities + ["Autres"]
    full_index = pd.MultiIndex.from_product(
        [activity_order, range(1, 13)], names=["activite", "mois"]
    )
    result = counts.rename("incidents_declares").reindex(full_index, fill_value=0).reset_index()
    totals = result.groupby("activite")["incidents_declares"].transform("sum")
    result["part_annuelle_pct"] = np.where(
        totals > 0, result["incidents_declares"] / totals * 100, 0
    ).round(2)
    return result


def _association_strength(
    curated: pd.DataFrame, top_activities: list[str], exclude_january_first: bool = False
) -> tuple[float, int]:
    work = _prepare_dates(curated).dropna(subset=["mois"])
    if exclude_january_first:
        work = work.loc[~((work["mois"] == 1) & (work["jour"] == 1))]
    work["activite_groupee"] = _activity_groups(work, top_activities)
    work = work.dropna(subset=["activite_groupee"])
    table = pd.crosstab(work["mois"], work["activite_groupee"])
    return _cramers_v(table), len(work)


def analyze_seasonality(curated: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Calcule les volumes mensuels, l'association activite-mois et une sensibilite."""
    work = _prepare_dates(curated)
    dated = work.dropna(subset=["mois"])
    month_counts = (
        dated["mois"].astype(int).value_counts().reindex(range(1, 13), fill_value=0)
    )
    january_first_count = int(((dated["mois"] == 1) & (dated["jour"] == 1)).sum())
    activity = dated["activite_nettoyee"]
    known = ~activity.str.lower().isin(UNKNOWN_ACTIVITIES)
    top_activities = activity.loc[known].value_counts().head(5).index.tolist()

    full_distribution = build_activity_month_distribution(dated, top_activities)
    v_all, activity_rows = _association_strength(dated, top_activities)
    v_without_january_first, sensitivity_rows = _association_strength(
        dated, top_activities, exclude_january_first=True
    )

    without_january_first = dated.loc[
        ~((dated["mois"] == 1) & (dated["jour"] == 1))
    ]
    sensitivity_counts = (
        without_january_first["mois"]
        .astype(int)
        .value_counts()
        .reindex(range(1, 13), fill_value=0)
    )
    summary = {
        "dated_incidents": int(len(dated)),
        "missing_or_invalid_dates": int(len(work) - len(dated)),
        "january_first_dates": january_first_count,
        "top_activities": top_activities,
        "monthly_counts": {str(month): int(count) for month, count in month_counts.items()},
        "peak_month_all_dates": int(month_counts.idxmax()) if len(dated) else None,
        "peak_month_excluding_january_first": (
            int(sensitivity_counts.idxmax()) if len(without_january_first) else None
        ),
        "activity_month_cramers_v": round(v_all, 4),
        "activity_month_rows": activity_rows,
        "activity_month_cramers_v_excluding_january_first": round(
            v_without_january_first, 4
        ),
        "activity_month_rows_excluding_january_first": sensitivity_rows,
        "january_first_exclusion_is_sensitivity_only": True,
    }
    return summary, full_distribution


def plot_activity_month_rose(
    distribution: pd.DataFrame, summary: dict, output_path: Path
) -> Path:
    """Dessine une rosace : un anneau par activite et un secteur par mois."""
    if distribution.empty:
        raise ValueError("Aucune activite datee exploitable pour generer la rosace.")

    activities = distribution["activite"].drop_duplicates().tolist()
    matrix = (
        distribution.pivot(index="activite", columns="mois", values="part_annuelle_pct")
        .reindex(index=activities, columns=range(1, 13), fill_value=0)
        .fillna(0)
    )
    theta_edges = np.linspace(0, 2 * np.pi, 13)
    radius_edges = np.arange(len(activities) + 1) + 0.85
    fig, axis = plt.subplots(figsize=(11, 10), subplot_kw={"projection": "polar"})
    axis.set_theta_zero_location("N")
    axis.set_theta_direction(-1)
    mesh = axis.pcolormesh(
        theta_edges,
        radius_edges,
        matrix.to_numpy(),
        cmap="YlGnBu",
        shading="flat",
        vmin=0,
        vmax=max(10, float(matrix.to_numpy().max())),
    )
    axis.set_ylim(0, len(activities) + 1.5)
    axis.set_xticks((theta_edges[:-1] + theta_edges[1:]) / 2)
    axis.set_xticklabels(MONTH_NAMES, fontsize=9, fontweight="bold")
    axis.set_yticks(np.arange(len(activities)) + 1.35)
    axis.set_yticklabels(activities, fontsize=8)
    axis.set_rlabel_position(335)
    axis.grid(color="white", linewidth=0.9, alpha=0.9)
    axis.spines["polar"].set_color("#d7e1e5")
    axis.text(
        0,
        0,
        f"n = {summary['activity_month_rows']:,}\nV = {summary['activity_month_cramers_v']:.3f}\nactivite x mois",
        ha="center",
        va="center",
        fontsize=9,
        color="#17324d",
        fontweight="bold",
    )
    axis.set_title(
        "Rosace des activites : part annuelle des incidents par mois",
        pad=28,
        fontsize=14,
        fontweight="bold",
    )
    colorbar = fig.colorbar(mesh, ax=axis, orientation="horizontal", pad=0.12, shrink=0.72)
    colorbar.set_label("Part des incidents de l'activite sur l'annee (%)", fontsize=9)
    fig.text(
        0.5,
        0.035,
        "Anneaux = activites (5 principales + autres) · chaque anneau totalise 100 %",
        ha="center",
        fontsize=9,
        color="#40556b",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def write_seasonal_outputs(
    curated_path: Path = CURATED_PATH,
    data_dir: Path = REPORT_DATA_DIR,
    image_dir: Path = REPORT_IMAGE_DIR,
    interpretation_dir: Path = REPORT_INTERPRETATION_DIR,
) -> dict[str, Path]:
    """Ecrit la rosace, sa matrice, les statistiques et une interpretation."""
    curated = pd.read_csv(curated_path)
    summary, distribution = analyze_seasonality(curated)
    data_dir.mkdir(parents=True, exist_ok=True)
    interpretation_dir.mkdir(parents=True, exist_ok=True)
    distribution_path = data_dir / "activity_month_distribution.csv"
    summary_path = data_dir / "seasonality_analysis.json"
    figure_path = image_dir / "seasonal_activity_rose.png"
    interpretation_path = interpretation_dir / "seasonality_analysis.md"

    distribution.to_csv(distribution_path, index=False)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    plot_activity_month_rose(distribution, summary, figure_path)

    month_names = {month: name for month, name in enumerate(MONTH_NAMES, start=1)}
    peak_all = month_names.get(summary["peak_month_all_dates"], "inconnu")
    peak_sensitivity = month_names.get(
        summary["peak_month_excluding_january_first"], "inconnu"
    )
    jan_share = (
        summary["january_first_dates"] / summary["dated_incidents"] * 100
        if summary["dated_incidents"]
        else 0
    )
    lines = [
        "# Activites et saisonnalite des incidents declares",
        "",
        f"L'analyse porte sur {summary['dated_incidents']} incidents ayant une date exploitable. "
        f"{summary['activity_month_rows']} ont aussi une activite connue et non vide.",
        "",
        "## Association descriptive",
        "",
        f"Le V de Cramer entre le mois et l'activite (5 activites les plus frequentes + « Autres ») "
        f"est de **{summary['activity_month_cramers_v']:.3f}**. C'est une association faible dans "
        "ce regroupement, sans controle de l'annee, du pays, de l'hemisphere ni de la frequentation "
        "humaine. Ce coefficient descriptif ne prouve ni causalite ni niveau de risque.",
        "",
        "## Sensibilite des dates au 1er janvier",
        "",
        f"{summary['january_first_dates']} dates ({jan_share:.1f} % des dates exploitables) "
        "sont enregistrees au 1er janvier. Le projet ne possede pas de champ de precision de date "
        "permettant de distinguer une date exacte d'une date partielle representee ainsi. "
        f"Le mois le plus compte est **{peak_all}** avec toutes les dates, contre **{peak_sensitivity}** "
        "si l'on exclut ces lignes. Cette exclusion est une sensibilite, pas une correction des donnees.",
        "",
        f"Le V de Cramer passe de {summary['activity_month_cramers_v']:.3f} a "
        f"{summary['activity_month_cramers_v_excluding_january_first']:.3f} dans cette sensibilite.",
        "",
        "## Lecture du visuel",
        "",
        "Chaque anneau represente une activite (les cinq plus frequentes, puis les autres); ses "
        "douze secteurs montrent la part annuelle de cette activite pour chaque mois. Les anneaux "
        "sont normalises separement : la couleur compare la saisonnalite d'une activite, pas son "
        "volume avec une autre activite. « Inconnue » est exclue.",
        "",
        "![Rosace des activites et des mois](../images/seasonal_activity_rose.png)",
        "",
        "## Conclusion prudente",
        "",
        "Les activites declarees et les incidents varient selon les mois, mais les donnees ne "
        "contiennent pas le nombre de personnes exposees, le temps passe dans l'eau, une position "
        "GPS precise, ni une mesure coherente de l'effort de signalement. On ne peut donc pas "
        "deduire un risque individuel, une saison de danger universelle ou un effet biologique.",
        "",
        "Les donnees GBIF disponibles sont traitees separement dans `ecological_hypotheses.md`; "
        "elles suggerent un chevauchement geographique, mais leurs dates recentes ne permettent pas "
        "de relier temporellement les occurrences aux attaques historiques.",
    ]
    interpretation_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "distribution": distribution_path,
        "summary": summary_path,
        "figure": figure_path,
        "interpretation": interpretation_path,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyser les incidents selon le mois et l'activite declaree"
    )
    parser.add_argument(
        "--curated", type=Path, default=CURATED_PATH, help="CSV curated a analyser"
    )
    args = parser.parse_args()
    for name, path in write_seasonal_outputs(args.curated).items():
        print(f"{name}: {path}")
