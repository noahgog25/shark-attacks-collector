"""Environmental hypothesis charts using the project's requested palette."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analysis.environment import INCONCLUSIVE, mann_whitney_summary

ROOT = Path(__file__).resolve().parents[2]
ENRICHED_PATH = ROOT / "data" / "curated" / "attacks_enriched.csv"
REPORT_DATA_DIR = ROOT / "reports" / "data"
REPORT_IMAGE_DIR = ROOT / "reports" / "images"
HYPOTHESES_PATH = REPORT_DATA_DIR / "environment_hypotheses.csv"
MONTHLY_PATH = REPORT_DATA_DIR / "environment_monthly_sst.csv"

OLIVE = "#69764A"
TERRACOTTA = "#C75C47"
ANTHRACITE = "#363B3C"
OCHRE = "#C79A3B"
CREAM = "#F6F1E5"
PALETTE = (OLIVE, TERRACOTTA, ANTHRACITE, OCHRE)


def _read_csv_or_empty(path: Path, columns: tuple[str, ...]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    return pd.read_csv(path)


def _base_figure(figsize: tuple[float, float]):
    figure, axis = plt.subplots(figsize=figsize)
    figure.patch.set_facecolor(CREAM)
    axis.set_facecolor(CREAM)
    axis.spines[["top", "right"]].set_visible(False)
    return figure, axis


def _footer(axis, n: int, source: str) -> None:
    axis.text(
        0,
        -0.2,
        f"n = {n:,} · Source : {source}",
        transform=axis.transAxes,
        fontsize=8,
        color=ANTHRACITE,
        va="top",
    )


def _plot_distributions(
    frame: pd.DataFrame,
    incident_column: str,
    control_column: str,
    title: str,
    unit: str,
    output_path: Path,
    source: str,
) -> Path:
    incident = pd.to_numeric(frame.get(incident_column), errors="coerce").dropna()
    controls = pd.to_numeric(frame.get(control_column), errors="coerce").dropna()
    paired = pd.concat(
        [incident.rename("incident"), controls.rename("control")], axis=1
    ).dropna()
    figure, axis = _base_figure((8.5, 5))
    if paired.empty:
        axis.text(0.5, 0.5, "Données insuffisantes\nn = 0", ha="center", va="center")
        axis.set_xticks([])
        axis.set_yticks([])
    else:
        bins = min(30, max(5, int(np.sqrt(len(paired)) * 2)))
        axis.hist(
            paired["incident"],
            bins=bins,
            density=True,
            alpha=0.58,
            color=OLIVE,
            label="Jour incident",
        )
        axis.hist(
            paired["control"],
            bins=bins,
            density=True,
            alpha=0.5,
            color=TERRACOTTA,
            label="Jours témoins",
        )
        axis.axvline(
            paired["incident"].median(),
            color=OLIVE,
            linestyle="--",
            linewidth=1.5,
        )
        axis.axvline(
            paired["control"].median(),
            color=TERRACOTTA,
            linestyle="--",
            linewidth=1.5,
        )
        axis.set_ylabel(unit)
        axis.set_xlabel(unit)
        axis.legend(frameon=False)
        axis.grid(axis="y", alpha=0.2, color=ANTHRACITE)
        result = mann_whitney_summary(
            paired["incident"], paired["control"], seed=20261027
        )
        axis.set_title(
            f"{title}\nDifférence médiane = {result['median_difference']:.2f} {unit}; "
            f"IC95% [{result['ci95_low']:.2f}, {result['ci95_high']:.2f}]",
            color=ANTHRACITE,
            fontsize=11,
        )
    _footer(axis, len(paired), source)
    figure.tight_layout(rect=(0, 0.08, 1, 1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, facecolor=CREAM)
    plt.close(figure)
    return output_path


def _plot_anomalies(frame: pd.DataFrame, output_path: Path) -> Path:
    values = pd.to_numeric(frame.get("sst_anom_c"), errors="coerce").dropna()
    figure, axis = _base_figure((8.5, 5))
    if values.empty:
        axis.text(0.5, 0.5, "Données insuffisantes\nn = 0", ha="center", va="center")
        axis.set_xticks([])
        axis.set_yticks([])
    else:
        axis.hist(values, bins=min(25, max(5, int(np.sqrt(len(values))))), color=OCHRE, edgecolor=CREAM)
        axis.axvline(0, color=TERRACOTTA, linestyle="--", linewidth=2, label="Anomalie nulle")
        axis.set_xlabel("SST − climatologie locale (°C)")
        axis.set_ylabel("Nombre d'incidents")
        axis.legend(frameon=False)
        axis.grid(axis="y", alpha=0.2, color=ANTHRACITE)
    axis.set_title("Anomalie locale de la température de surface", color=ANTHRACITE)
    _footer(axis, len(values), "NOAA OISST v2.1; climatologie locale 1982–2011, fenêtre 31 jours")
    figure.tight_layout(rect=(0, 0.08, 1, 1))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, facecolor=CREAM)
    plt.close(figure)
    return output_path


def _plot_monthly(frame: pd.DataFrame, output_path: Path) -> Path:
    countries = ("USA", "AUSTRALIA", "SOUTH AFRICA")
    groups = [
        (country, frame.loc[frame["pays"].str.upper() == country].sort_values("season_month"))
        for country in countries
    ]
    groups = [
        (country, group)
        for country, group in groups
        if not group.empty
        and pd.to_numeric(group["attacks"], errors="coerce").fillna(0).sum() > 0
        and pd.to_numeric(group["mean_sst_c"], errors="coerce").notna().any()
    ]
    figure, axes = plt.subplots(
        1, len(groups), figsize=(5 * len(groups), 5), sharey=False, squeeze=False
    )
    figure.patch.set_facecolor(CREAM)
    axes = axes[0]
    total_n = int(pd.to_numeric(frame.get("attacks"), errors="coerce").fillna(0).sum())
    for axis, (country, group), color in zip(axes, groups, PALETTE[:3]):
        axis.set_facecolor(CREAM)
        axis.bar(group["season_month"], group["attacks"], color=color, alpha=0.75)
        temperature_axis = axis.twinx()
        temperature_axis.set_facecolor("none")
        temperature_axis.plot(
            group["season_month"],
            group["mean_sst_c"],
            color=TERRACOTTA,
            marker="o",
            linewidth=1.8,
            label="SST moyenne",
        )
        temperature_axis.set_ylabel("SST moyenne (°C)", color=TERRACOTTA, fontsize=8)
        rho = group["spearman_month_sst"].dropna()
        rho_label = f"Spearman ρ = {rho.iloc[0]:.2f}" if not rho.empty else "Spearman ρ = n.d."
        axis.set_title(f"{country}\n{rho_label}", color=ANTHRACITE, fontsize=10)
        axis.set_xticks(range(1, 13))
        axis.set_xticklabels(
            ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"],
            rotation=45,
            fontsize=7,
        )
        axis.set_ylabel("Incidents déclarés", fontsize=8)
        axis.grid(axis="y", alpha=0.2, color=ANTHRACITE)
    figure.suptitle("Incidents et SST mensuelle (mois alignés par hémisphère)", color=ANTHRACITE)
    figure.text(
        0.5,
        0.015,
        f"n = {total_n:,} incidents · Source : incidents géocodés + NOAA OISST v2.1",
        ha="center",
        fontsize=8,
        color=ANTHRACITE,
    )
    figure.tight_layout(rect=(0, 0.06, 1, 0.91))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, facecolor=CREAM)
    plt.close(figure)
    return output_path


def _plot_hypotheses(
    frame: pd.DataFrame, output_path: Path, hypotheses_path: Path
) -> Path:
    hypotheses = _read_csv_or_empty(
        hypotheses_path,
        ("hypothesis_id", "test", "result", "status", "n_incident"),
    )
    if hypotheses.empty:
        hypotheses = pd.DataFrame(
            [
                {
                    "hypothesis_id": hypothesis_id,
                    "test": "Données environnementales locales",
                    "result": "n=0; enrichissement non calculé",
                    "status": INCONCLUSIVE,
                    "n_incident": 0,
                }
                for hypothesis_id in ("H1", "H2", "H3", "H4", "H5")
            ]
        )
    hypotheses = (
        hypotheses.sort_values("hypothesis_id")
        .drop_duplicates("hypothesis_id", keep="last")
        .set_index("hypothesis_id")
        .reindex(["H1", "H2", "H3", "H4", "H5"])
        .reset_index()
    )
    hypotheses["status"] = hypotheses["status"].fillna(INCONCLUSIVE)
    rows = [["Hypothèse", "Test", "Résultat chiffré", "Statut"]]
    for _, row in hypotheses.iterrows():
        result = str(row.get("result") or "")
        rows.append(
            [
                str(row["hypothesis_id"]),
                str(row.get("test") or ""),
                result[:210],
                str(row["status"]),
            ]
        )
    figure, axis = plt.subplots(figsize=(13, 5.2))
    figure.patch.set_facecolor(CREAM)
    axis.set_facecolor(CREAM)
    axis.axis("off")
    table = axis.table(
        cellText=rows[1:],
        colLabels=rows[0],
        colWidths=[0.1, 0.31, 0.39, 0.2],
        cellLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 2.25)
    for (row_index, _), cell in table.get_celld().items():
        cell.set_edgecolor(CREAM)
        if row_index == 0:
            cell.set_facecolor(ANTHRACITE)
            cell.get_text().set_color(CREAM)
            cell.get_text().set_weight("bold")
        else:
            status = str(hypotheses.iloc[row_index - 1]["status"])
            cell.set_facecolor(
                OLIVE if status == "Soutenue" else OCHRE if status == INCONCLUSIVE else TERRACOTTA
            )
            cell.get_text().set_color(CREAM)
            cell.get_text().set_wrap(True)
    figure.suptitle(
        "Synthèse des hypothèses — une association n'établit pas une cause",
        color=ANTHRACITE,
        fontsize=12,
    )
    figure.text(
        0.5,
        0.025,
        f"n = {int(pd.to_numeric(frame.get('sst_c'), errors='coerce').notna().sum()):,} SST valides · "
        "Sources : NOAA OISST v2.1 et Open-Meteo Archive (ERA5, CC BY 4.0)",
        ha="center",
        fontsize=8,
        color=ANTHRACITE,
    )
    figure.tight_layout(rect=(0, 0.07, 1, 0.9))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, facecolor=CREAM)
    plt.close(figure)
    return output_path


def write_environment_charts(
    enriched_path: Path = ENRICHED_PATH,
    hypotheses_path: Path = HYPOTHESES_PATH,
    monthly_path: Path = MONTHLY_PATH,
    output_dir: Path = REPORT_IMAGE_DIR,
) -> dict[str, Path]:
    """Create figures only when their underlying measurements are available."""
    frame = _read_csv_or_empty(
        enriched_path,
        (
            "incident_id", "date", "latitude", "longitude", "geocode_precision",
            "hemisphere", "sst_c", "sst_anom_c", "sst_control_mean_c",
            "air_tmax_c", "air_tmax_control_mean_c", "precip_mm",
            "precip_control_mean_mm", "wind_max_kmh", "wind_control_mean_kmh",
            "precip_3d_mm", "precip_3d_control_mean_mm",
            "gbif_2025_2026_within_100km", "env_status", "pays",
        ),
    )
    monthly = _read_csv_or_empty(
        monthly_path,
        ("pays", "hemisphere", "season_month", "attacks", "mean_sst_c", "spearman_month_sst"),
    )
    outputs: dict[str, Path] = {}
    sst_incident = pd.to_numeric(frame["sst_c"], errors="coerce")
    sst_control = pd.to_numeric(frame["sst_control_mean_c"], errors="coerce")
    sst_pairs = pd.concat(
        [sst_incident.rename("incident"), sst_control.rename("control")], axis=1
    ).dropna()
    anomaly = pd.to_numeric(frame["sst_anom_c"], errors="coerce").dropna()
    air_incident = pd.to_numeric(frame["air_tmax_c"], errors="coerce")
    air_control = pd.to_numeric(frame["air_tmax_control_mean_c"], errors="coerce")
    air_pairs = pd.concat(
        [air_incident.rename("incident"), air_control.rename("control")], axis=1
    ).dropna()
    monthly_has_data = any(
        not monthly.loc[monthly["pays"].str.upper() == country].empty
        and pd.to_numeric(
            monthly.loc[monthly["pays"].str.upper() == country, "attacks"],
            errors="coerce",
        ).fillna(0).sum() > 0
        and pd.to_numeric(
            monthly.loc[monthly["pays"].str.upper() == country, "mean_sst_c"],
            errors="coerce",
        ).notna().any()
        for country in ("USA", "AUSTRALIA", "SOUTH AFRICA")
    )
    hypotheses = _read_csv_or_empty(
        hypotheses_path,
        ("hypothesis_id", "test", "result", "status", "n_incident"),
    )
    hypotheses_have_data = (
        not hypotheses.empty
        and "n_incident" in hypotheses.columns
        and pd.to_numeric(hypotheses["n_incident"], errors="coerce").fillna(0).gt(0).any()
    )
    chart_paths = {
        "sst_controls": output_dir / "environment_sst_controls.png",
        "sst_anomaly": output_dir / "environment_sst_anomaly.png",
        "monthly_sst": output_dir / "environment_monthly_sst.png",
        "air_controls": output_dir / "environment_air_controls.png",
        "hypotheses": output_dir / "environment_hypotheses.png",
    }

    if not sst_pairs.empty:
        outputs["sst_controls"] = _plot_distributions(
            frame,
            "sst_c",
            "sst_control_mean_c",
            "SST le jour de l'incident vs jours témoins",
            "°C",
            chart_paths["sst_controls"],
            "NOAA OISST v2.1; contrôles même lieu et année",
        )
    if not anomaly.empty:
        outputs["sst_anomaly"] = _plot_anomalies(
            frame, chart_paths["sst_anomaly"]
        )
    if monthly_has_data:
        outputs["monthly_sst"] = _plot_monthly(
            monthly, chart_paths["monthly_sst"]
        )
    if not air_pairs.empty:
        outputs["air_controls"] = _plot_distributions(
            frame,
            "air_tmax_c",
            "air_tmax_control_mean_c",
            "Température maximale de l'air : incident vs témoins",
            "°C",
            chart_paths["air_controls"],
            "Open-Meteo Archive (ERA5), CC BY 4.0",
        )
    if hypotheses_have_data:
        outputs["hypotheses"] = _plot_hypotheses(
            frame, chart_paths["hypotheses"], hypotheses_path
        )

    for chart_name, path in chart_paths.items():
        if chart_name not in outputs:
            path.unlink(missing_ok=True)
    return outputs
