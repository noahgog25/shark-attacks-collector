import numpy as np
import pandas as pd

from src.analysis.environment import (
    INCONCLUSIVE,
    SUPPORTED,
    build_hypothesis_results,
    hemisphere_for_latitude,
    local_climatology,
    mann_whitney_summary,
    build_sensitivity_results,
    monthly_sst_summary,
    prepare_eligible_population,
    season_month,
)


def test_population_filters_january_first_and_counts_exclusions():
    incidents = pd.DataFrame(
        {
            "date": ["2020-01-01", "2020-01-02", "2020-01-03", "invalid"],
            "latitude": [10.0, -20.0, None, 10.0],
            "longitude": [20.0, 30.0, 40.0, 20.0],
            "type_attaque": ["Unprovoked", "Unprovoked", "Unprovoked", "Provoked"],
        }
    )

    eligible, report = prepare_eligible_population(incidents)

    assert eligible["date"].dt.strftime("%Y-%m-%d").tolist() == ["2020-01-02"]
    assert report["filters"]["geocoded"]["excluded_rows"] == 1
    assert report["filters"]["exact_date_not_january_first"]["excluded_rows"] == 1
    assert report["filters"]["unprovoked"]["excluded_rows"] == 0
    assert report["oisst_rows"] == report["era5_rows"] == 1


def test_hemisphere_months_are_aligned_by_six_months():
    assert hemisphere_for_latitude(-0.1) == "S"
    assert hemisphere_for_latitude(0.0) == "N"
    assert season_month(1, "S") == 7
    assert season_month(7, "S") == 1
    assert season_month(1, "N") == 1


def test_monthly_sst_summary_uses_hemisphere_aligned_months_and_spearman():
    enriched = pd.DataFrame(
        {
            "incident_id": ["a", "b", "c"],
            "date": ["2020-01-15", "2020-07-15", "2020-01-15"],
            "latitude": [-20.0, -20.0, 25.0],
            "pays": ["AUSTRALIA", "AUSTRALIA", "USA"],
            "sst_c": [28.0, 20.0, 22.0],
        }
    )

    summary = monthly_sst_summary(enriched)

    australia = summary.loc[summary["pays"].eq("AUSTRALIA")]
    assert australia["season_month"].tolist() == [1, 7]
    assert australia["spearman_month_sst"].notna().all()
    assert summary.loc[summary["pays"].eq("USA"), "hemisphere"].item() == "N"


def test_sensitivity_report_lists_geocode_and_country_subsets():
    enriched = pd.DataFrame(
        {
            "geocode_precision": ["centre_de_localite_approximatif", "street"],
            "pays": ["USA", "AUSTRALIA"],
            "sst_c": [22.0, 23.0],
            "sst_control_mean_c": [21.0, 22.0],
            "sst_anom_c": [1.0, 1.0],
            "air_tmax_c": [30.0, 31.0],
            "air_tmax_control_mean_c": [28.0, 29.0],
            "precip_mm": [0.0, 1.0],
            "precip_control_mean_mm": [1.0, 2.0],
            "wind_max_kmh": [5.0, 6.0],
            "wind_control_mean_kmh": [7.0, 8.0],
            "precip_3d_mm": [2.0, 3.0],
            "precip_3d_control_mean_mm": [1.0, 2.0],
            "gbif_2025_2026_within_100km": [0, 1],
        }
    )

    result = build_sensitivity_results(enriched)

    assert result["without_locality_centres"]["n"] == 1
    assert result["by_major_country"]["USA"]["n"] == 1
    assert result["by_major_country"]["SOUTH AFRICA"]["n"] == 0


def test_climatology_uses_local_31_day_window_and_1982_2011_baseline():
    dates = pd.date_range("1982-01-01", "1982-12-31", freq="D")
    frame = pd.DataFrame({"date": dates, "sst": 20.0})
    frame.loc[frame["date"].dt.month.eq(1) & frame["date"].dt.day.eq(3), "sst"] = 30.0
    frame = pd.concat(
        [frame, pd.DataFrame({"date": [pd.Timestamp("2020-01-03")], "sst": [40.0]})],
        ignore_index=True,
    )

    result = local_climatology(frame)
    target = result.loc[result["date"].eq(pd.Timestamp("2020-01-03"))].iloc[0]

    assert 20 < target["sst_clim_c"] < 30
    assert target["sst_anom_c"] == 40 - target["sst_clim_c"]


def test_mann_whitney_summary_reports_effect_and_bootstrap_interval():
    result = mann_whitney_summary([2, 3, 4, 5], [0, 1, 1, 2], bootstrap_samples=100)

    assert result["n_incident"] == 4
    assert result["median_difference"] == 2.5
    assert result["cliffs_delta"] > 0
    assert result["ci95_low"] <= result["median_difference"] <= result["ci95_high"]


def test_hypothesis_statuses_are_conservative_with_small_samples():
    small = pd.DataFrame(
        {
            "sst_c": [21.0] * 5,
            "sst_control_mean_c": [20.0] * 5,
            "sst_anom_c": [1.0] * 5,
            "air_tmax_c": [30.0] * 5,
            "air_tmax_control_mean_c": [25.0] * 5,
            "precip_mm": [0.0] * 5,
            "precip_control_mean_mm": [1.0] * 5,
            "wind_max_kmh": [5.0] * 5,
            "wind_control_mean_kmh": [10.0] * 5,
            "precip_3d_mm": [4.0] * 5,
            "precip_3d_control_mean_mm": [1.0] * 5,
            "gbif_2025_2026_within_100km": [1] * 5,
        }
    )

    results = build_hypothesis_results(small)

    assert results.loc[results["hypothesis_id"].eq("H1"), "status"].item() == INCONCLUSIVE
    assert results.loc[results["hypothesis_id"].eq("H4"), "status"].item() == INCONCLUSIVE


def test_h1_is_supported_only_with_sufficient_positive_signal():
    enriched = pd.DataFrame(
        {
            "sst_c": np.full(40, 22.0),
            "sst_control_mean_c": np.full(40, 20.0),
            "sst_anom_c": np.ones(40),
            "air_tmax_c": np.full(40, 30.0),
            "air_tmax_control_mean_c": np.full(40, 28.0),
            "precip_mm": np.zeros(40),
            "precip_control_mean_mm": np.ones(40),
            "wind_max_kmh": np.full(40, 5.0),
            "wind_control_mean_kmh": np.full(40, 7.0),
            "precip_3d_mm": np.full(40, 2.0),
            "precip_3d_control_mean_mm": np.zeros(40),
            "gbif_2025_2026_within_100km": np.zeros(40),
        }
    )

    results = build_hypothesis_results(enriched)

    h1 = results.loc[results["hypothesis_id"].eq("H1")].iloc[0]
    h3 = results.loc[
        results["hypothesis_id"].eq("H3")
        & results["test"].str.startswith("Synthèse")
    ].iloc[0]
    assert h1["status"] == SUPPORTED
    assert h3["status"] == SUPPORTED
