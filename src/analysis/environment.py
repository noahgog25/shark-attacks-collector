"""Descriptive environmental hypothesis tests with explicit sample limits."""

from __future__ import annotations

import math
import random
from typing import Iterable

import numpy as np
import pandas as pd

SUPPORTED = "Soutenue"
NOT_SUPPORTED = "Non soutenue"
INCONCLUSIVE = "Non concluante (échantillon ou données insuffisants)"
MIN_SAMPLE_SIZE = 30


def hemisphere_for_latitude(latitude: float | None) -> str | None:
    if latitude is None or pd.isna(latitude):
        return None
    return "S" if float(latitude) < 0 else "N"


def season_month(month: int, hemisphere: str) -> int:
    """Align southern-hemisphere months to the corresponding northern season."""
    if month not in range(1, 13):
        raise ValueError("month must be in 1..12")
    if hemisphere not in {"N", "S"}:
        raise ValueError("hemisphere must be N or S")
    return ((month - 1 + (6 if hemisphere == "S" else 0)) % 12) + 1


def prepare_eligible_population(
    incidents: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, dict[str, float | int]]]:
    """Apply and count each explicit date, location, and population filter."""
    required = {"date", "latitude", "longitude"}
    missing = required - set(incidents.columns)
    if missing:
        raise ValueError(f"Colonnes environnementales manquantes : {sorted(missing)}")

    frame = incidents.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["latitude"] = pd.to_numeric(frame["latitude"], errors="coerce")
    frame["longitude"] = pd.to_numeric(frame["longitude"], errors="coerce")
    frame["hemisphere"] = frame["latitude"].map(hemisphere_for_latitude)
    total = len(frame)
    stages: dict[str, dict[str, float | int]] = {}

    def record_filter(name: str, mask: pd.Series) -> None:
        nonlocal frame
        before = len(frame)
        frame = frame.loc[mask].copy()
        excluded = before - len(frame)
        stages[name] = {
            "input_rows": before,
            "excluded_rows": excluded,
            "excluded_pct": round(excluded / total * 100, 2) if total else 0.0,
        }

    record_filter(
        "geocoded",
        frame["latitude"].between(-90, 90)
        & frame["longitude"].between(-180, 180),
    )
    record_filter("date_valid", frame["date"].notna())
    record_filter(
        "exact_date_not_january_first",
        ~((frame["date"].dt.month == 1) & (frame["date"].dt.day == 1)),
    )
    if "type_attaque" in frame.columns:
        record_filter(
            "unprovoked",
            frame["type_attaque"].fillna("").astype(str).str.strip().str.casefold()
            .eq("unprovoked"),
        )
    else:
        stages["unprovoked"] = {
            "input_rows": len(frame),
            "excluded_rows": 0,
            "excluded_pct": 0.0,
        }

    base = frame.copy()
    oisst = base.loc[base["date"] >= pd.Timestamp("1982-01-01")].copy()
    era5 = base.loc[base["date"] >= pd.Timestamp("1940-01-01")].copy()
    stages["oisst_date_from_1982"] = {
        "input_rows": len(base),
        "excluded_rows": len(base) - len(oisst),
        "excluded_pct": round((len(base) - len(oisst)) / total * 100, 2) if total else 0.0,
    }
    stages["era5_date_from_1940"] = {
        "input_rows": len(base),
        "excluded_rows": len(base) - len(era5),
        "excluded_pct": round((len(base) - len(era5)) / total * 100, 2) if total else 0.0,
    }
    stages["input_rows"] = {"input_rows": total, "excluded_rows": 0, "excluded_pct": 0.0}
    return base, {"filters": stages, "oisst_rows": len(oisst), "era5_rows": len(era5)}


def local_climatology(
    daily_sst: pd.DataFrame, *, baseline_start: int = 1982, baseline_end: int = 2011
) -> pd.DataFrame:
    """Calculate a local day-of-year climatology with a circular 31-day window."""
    required = {"date", "sst"}
    missing = required - set(daily_sst.columns)
    if missing:
        raise ValueError(f"Colonnes SST manquantes : {sorted(missing)}")

    frame = daily_sst.loc[:, ["date", "sst"]].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["sst"] = pd.to_numeric(frame["sst"], errors="coerce")
    frame = frame.dropna(subset=["date", "sst"])
    frame = frame.loc[frame["date"].dt.year.between(baseline_start, baseline_end)]
    frame["day_of_year"] = frame["date"].map(_climatology_day)
    values_by_day = {
        int(day): group["sst"].to_numpy(dtype=float)
        for day, group in frame.groupby("day_of_year")
    }

    climatology = {}
    for day in range(1, 366):
        window_days = {
            ((day - 1 + offset) % 365) + 1 for offset in range(-15, 16)
        }
        window_values = [
            values
            for window_day in window_days
            for values in [values_by_day.get(window_day)]
            if values is not None
        ]
        climatology[day] = (
            float(np.concatenate(window_values).mean()) if window_values else math.nan
        )

    result = daily_sst.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["day_of_year"] = result["date"].map(_climatology_day)
    result["sst_clim_c"] = result["day_of_year"].map(climatology)
    result["sst_anom_c"] = pd.to_numeric(result["sst"], errors="coerce") - result["sst_clim_c"]
    return result


def _climatology_day(value: pd.Timestamp) -> int:
    if pd.isna(value):
        return 0
    day = int(value.dayofyear)
    if value.is_leap_year and value.month > 2:
        day -= 1
    return min(day, 365)


def mann_whitney_summary(
    incident_values: Iterable[float],
    control_values: Iterable[float],
    *,
    seed: int = 20261027,
    bootstrap_samples: int = 1000,
) -> dict[str, float | int | None]:
    """Return Mann–Whitney, Cliff delta, paired median difference, and bootstrap CI."""
    observed_series = pd.to_numeric(pd.Series(incident_values), errors="coerce")
    control_series = pd.to_numeric(pd.Series(control_values), errors="coerce")
    paired = pd.concat(
        [observed_series.rename("incident"), control_series.rename("control")], axis=1
    ).dropna()
    observed = observed_series.dropna().to_numpy()
    controls = control_series.dropna().to_numpy()
    observed = observed[np.isfinite(observed)]
    controls = controls[np.isfinite(controls)]
    n_observed, n_controls = len(observed), len(controls)
    if not n_observed or not n_controls:
        return {
            "n_incident": n_observed,
            "n_control": n_controls,
            "median_difference": None,
            "p_value": None,
            "cliffs_delta": None,
            "ci95_low": None,
            "ci95_high": None,
        }

    combined = np.concatenate((observed, controls))
    ranks = pd.Series(combined).rank(method="average").to_numpy()
    u_observed = float(ranks[:n_observed].sum() - n_observed * (n_observed + 1) / 2)
    u_expected = n_observed * n_controls / 2
    _, tie_counts = np.unique(combined, return_counts=True)
    total = n_observed + n_controls
    tie_adjustment = float(np.sum(tie_counts**3 - tie_counts))
    variance = (
        n_observed * n_controls / 12
        * (total + 1 - tie_adjustment / (total * (total - 1)))
        if total > 1
        else 0
    )
    z_value = (
        max(0.0, abs(u_observed - u_expected) - 0.5) / math.sqrt(variance)
        if variance > 0
        else 0.0
    )
    p_value = math.erfc(z_value / math.sqrt(2))

    sorted_controls = np.sort(controls)
    less = np.searchsorted(sorted_controls, observed, side="left")
    less_or_equal = np.searchsorted(sorted_controls, observed, side="right")
    cliffs_delta = float((less - (n_controls - less_or_equal)).sum() / (n_observed * n_controls))

    differences = (
        paired["incident"].to_numpy(dtype=float) - paired["control"].to_numpy(dtype=float)
    )
    if len(differences):
        median_difference = float(np.median(differences))
        rng = np.random.default_rng(seed)
        bootstrap_medians = np.median(
            rng.choice(differences, size=(bootstrap_samples, len(differences)), replace=True),
            axis=1,
        )
        ci_low, ci_high = np.quantile(bootstrap_medians, [0.025, 0.975])
    else:
        median_difference, ci_low, ci_high = None, None, None
    return {
        "n_incident": n_observed,
        "n_control": n_controls,
        "median_difference": median_difference,
        "p_value": float(p_value),
        "cliffs_delta": cliffs_delta,
        "ci95_low": float(ci_low),
        "ci95_high": float(ci_high),
    }


def _result_text(result: dict[str, float | int | None], unit: str) -> str:
    difference = result["median_difference"]
    if difference is None:
        return f"n={result['n_incident']}/{result['n_control']}; données indisponibles"
    return (
        f"n={result['n_incident']}/{result['n_control']}; différence médiane "
        f"{difference:.2f} {unit}; p={result['p_value']:.3g}; "
        f"delta de Cliff={result['cliffs_delta']:.2f}; "
        f"IC95% [{result['ci95_low']:.2f}, {result['ci95_high']:.2f}]"
    )


def _status(result: dict[str, float | int | None], direction: str) -> str:
    if (
        result["n_incident"] < MIN_SAMPLE_SIZE
        or result["n_control"] < MIN_SAMPLE_SIZE
        or result["p_value"] is None
        or result["median_difference"] is None
    ):
        return INCONCLUSIVE
    difference = result["median_difference"]
    supported_direction = difference is not None and (
        difference > 0 if direction == "higher" else difference < 0
    )
    return SUPPORTED if supported_direction and result["p_value"] < 0.05 else NOT_SUPPORTED


def build_hypothesis_results(enriched: pd.DataFrame) -> pd.DataFrame:
    """Evaluate H1–H5 and emit French statuses without causal interpretation."""
    rows = []

    def comparison(
        hypothesis_id: str,
        test_name: str,
        value_column: str,
        control_column: str,
        unit: str,
        direction: str,
        *,
        record: bool = True,
    ) -> dict[str, float | int | None]:
        values = pd.to_numeric(enriched.get(value_column), errors="coerce")
        controls = pd.to_numeric(enriched.get(control_column), errors="coerce")
        result = mann_whitney_summary(values, controls, seed=20261027 + len(rows))
        if record:
            rows.append(
                {
                "hypothesis_id": hypothesis_id,
                "test": test_name,
                "result": _result_text(result, unit),
                "status": _status(result, direction),
                "n_incident": result["n_incident"],
                "n_control": result["n_control"],
                "median_difference": result["median_difference"],
                "p_value": result["p_value"],
                "cliffs_delta": result["cliffs_delta"],
                "ci95_low": result["ci95_low"],
                "ci95_high": result["ci95_high"],
                }
            )
        return result

    comparison("H1", "SST incident vs témoins; Mann–Whitney", "sst_c", "sst_control_mean_c", "°C", "higher")

    anomaly = pd.to_numeric(enriched.get("sst_anom_c"), errors="coerce").dropna()
    anomaly_test = mann_whitney_summary(
        anomaly.reset_index(drop=True), np.zeros(len(anomaly)), seed=20261028
    )
    anomaly_median = float(anomaly.median()) if len(anomaly) else None
    anomaly_status = (
        INCONCLUSIVE
        if len(anomaly) < MIN_SAMPLE_SIZE
        else SUPPORTED
        if anomaly_median is not None and anomaly_median > 0 and anomaly_test["p_value"] < 0.05
        else NOT_SUPPORTED
    )
    rows.append(
        {
            "hypothesis_id": "H2",
            "test": "Anomalie SST vs zéro; Mann–Whitney",
            "result": (
                f"n={len(anomaly)}; médiane={anomaly_median:.2f} °C; "
                f"{(anomaly.gt(0).mean() * 100):.1f} % d'anomalies positives; "
                f"p={anomaly_test['p_value']:.3g}"
                if len(anomaly)
                else "n=0; données indisponibles"
            ),
            "status": anomaly_status,
            "n_incident": len(anomaly),
            "n_control": len(anomaly),
            "median_difference": anomaly_median,
            "p_value": anomaly_test["p_value"],
            "cliffs_delta": anomaly_test["cliffs_delta"],
            "ci95_low": anomaly_test["ci95_low"],
            "ci95_high": anomaly_test["ci95_high"],
        }
    )

    h3_results = [
        comparison(
            "H3",
            f"{label} incident vs témoins; Mann–Whitney",
            value,
            control,
            unit,
            direction,
            record=False,
        )
        for label, value, control, unit, direction in (
            ("Air max", "air_tmax_c", "air_tmax_control_mean_c", "°C", "higher"),
            ("Pluie", "precip_mm", "precip_control_mean_mm", "mm", "lower"),
            ("Vent", "wind_max_kmh", "wind_control_mean_kmh", "km/h", "lower"),
        )
    ]
    h3_statuses = [_status(result, direction) for result, direction in zip(
        h3_results, ("higher", "lower", "lower")
    )]
    h3_combined_status = (
        INCONCLUSIVE if INCONCLUSIVE in h3_statuses
        else SUPPORTED if all(status == SUPPORTED for status in h3_statuses)
        else NOT_SUPPORTED
    )
    rows.append(
        {
            "hypothesis_id": "H3",
            "test": "Synthèse des trois indicateurs d’exposition humaine",
            "result": "; ".join(
                f"{label}: {_result_text(result, unit)}"
                for label, result, unit in zip(
                    ("air", "pluie", "vent"), h3_results, ("°C", "mm", "km/h")
                )
            ),
            "status": h3_combined_status,
            "n_incident": min(result["n_incident"] for result in h3_results),
            "n_control": min(result["n_control"] for result in h3_results),
            "median_difference": None,
            "p_value": None,
            "cliffs_delta": None,
            "ci95_low": None,
            "ci95_high": None,
        }
    )

    comparison(
        "H5",
        "Pluie cumulée des 3 jours précédents incident vs témoins; Mann–Whitney",
        "precip_3d_mm",
        "precip_3d_control_mean_mm",
        "mm",
        "higher",
    )
    gbif_count = int(
        pd.to_numeric(enriched.get("gbif_2025_2026_within_100km"), errors="coerce")
        .fillna(0)
        .gt(0)
        .sum()
    )
    gbif_n = int(len(enriched))
    rows.append(
        {
            "hypothesis_id": "H4",
            "test": "Présence GBIF 2025–2026 à moins de 100 km; exploration spatiale",
            "result": f"n={gbif_n}; {gbif_count} incident(s) avec occurrence proche; présence ≠ espèce responsable",
            "status": INCONCLUSIVE,
            "n_incident": gbif_n,
            "n_control": 0,
            "median_difference": None,
            "p_value": None,
            "cliffs_delta": None,
            "ci95_low": None,
            "ci95_high": None,
        }
    )
    return pd.DataFrame(rows)


def monthly_sst_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    """Aggregate attacks and SST by hemisphere-aligned month and major country."""
    required = {"date", "latitude", "pays", "sst_c"}
    missing = required - set(enriched.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes pour les mois et la SST : {sorted(missing)}")
    frame = enriched.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["latitude"] = pd.to_numeric(frame["latitude"], errors="coerce")
    frame["sst_c"] = pd.to_numeric(frame["sst_c"], errors="coerce")
    frame["hemisphere"] = frame["latitude"].map(hemisphere_for_latitude)
    frame = frame.dropna(subset=["date", "sst_c", "hemisphere"])
    frame = frame.loc[frame["pays"].str.upper().isin({"USA", "AUSTRALIA", "SOUTH AFRICA"})].copy()
    frame["month"] = frame["date"].dt.month
    frame["season_month"] = [
        season_month(int(month), hemisphere)
        for month, hemisphere in zip(frame["month"], frame["hemisphere"])
    ]
    summary = (
        frame.groupby(["pays", "hemisphere", "season_month"], as_index=False)
        .agg(attacks=("incident_id", "count"), mean_sst_c=("sst_c", "mean"))
        .sort_values(["pays", "season_month"])
        .reset_index(drop=True)
    )
    summary["spearman_month_sst"] = np.nan
    for (country, hemisphere), indexes in summary.groupby(["pays", "hemisphere"]).groups.items():
        group = summary.loc[indexes]
        rho = spearman_rho(group["season_month"], group["mean_sst_c"])
        summary.loc[indexes, "spearman_month_sst"] = rho
    return summary


def spearman_rho(left: Iterable[float], right: Iterable[float]) -> float | None:
    """Calculate Spearman's rank correlation without an additional dependency."""
    left_ranks = pd.to_numeric(pd.Series(left), errors="coerce")
    right_ranks = pd.to_numeric(pd.Series(right), errors="coerce")
    pairs = pd.concat([left_ranks, right_ranks], axis=1).dropna()
    if len(pairs) < 2:
        return None
    ranked = pairs.rank(method="average")
    if ranked.iloc[:, 0].nunique() < 2 or ranked.iloc[:, 1].nunique() < 2:
        return None
    return float(ranked.iloc[:, 0].corr(ranked.iloc[:, 1]))


def build_sensitivity_results(enriched: pd.DataFrame) -> dict:
    """Summarize required sensitivity subsets, retaining n for empty groups."""
    without_centres = enriched.loc[
        ~enriched["geocode_precision"]
        .fillna("")
        .astype(str)
        .str.casefold()
        .str.contains("centre_de_localite_approximatif|city|town|village", regex=True)
    ]
    by_country = {}
    for country in ("USA", "AUSTRALIA", "SOUTH AFRICA"):
        subset = enriched.loc[enriched["pays"].fillna("").str.upper() == country]
        by_country[country] = {
            "n": int(len(subset)),
            "hypotheses": build_hypothesis_results(subset).to_dict(orient="records"),
        }
    return {
        "without_january_first": {
            "n": int(len(enriched)),
            "hypotheses": build_hypothesis_results(enriched).to_dict(orient="records"),
        },
        "without_locality_centres": {
            "n": int(len(without_centres)),
            "hypotheses": build_hypothesis_results(without_centres).to_dict(orient="records"),
        },
        "by_major_country": by_country,
    }
