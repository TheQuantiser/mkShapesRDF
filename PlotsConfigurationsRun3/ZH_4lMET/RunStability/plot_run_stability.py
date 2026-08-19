#!/usr/bin/env python3
"""On-demand DATA/MC plots and run-ratio summaries for run-stability outputs."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import zlib

import cloudpickle
import matplotlib
import mplhep
import numpy as np
import ROOT


matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.legend_handler import HandlerTuple  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


ROOT.gROOT.SetBatch(True)


class _OverlayLegendTuple(tuple):
    """Legend artists that occupy the same handle box."""


class _SideBySideLegendTuple(tuple):
    """Legend artists that divide one handle box horizontally."""


ROOT.TH1.AddDirectory(False)
GARWOOD_COVERAGE = 0.682689492137

# Presentation tokens adapted to PyROOT from the maintained mkshapes-analysis-lab
# ``publication-light`` theme and comparison-panel grammar.  The numerical ROOT
# objects remain independent of these display-only choices.
RATIO_AUTORANGE_HARD_BOUNDS = (0.50, 1.50)
RATIO_STYLE = {
    "reference": "#1F5F8B",
    "data": "#111418",
    "data_error": "#343B43",
    "mc_band": "#1F5F8B",
    "mc_band_edge": "#1F5F8B",
    "period_separator": "#49667A",
    "period_label": "#304B5E",
    "warning": "#A83E00",
    "grid": "#CDD4DA",
    "spine": "#4D555D",
    "era_fill_even": "#F5F7F9",
    "era_fill_odd": "#EAF0F5",
}
RATIO_STYLE_PROVENANCE = {
    "source": "notebooks/mkshapes_analysis_lab",
    "theme": "publication-light",
    "theme_registry_version": "2026.08",
    "ratio_limits": "adaptive; exact range and inputs are serialized per plot",
    "ratio_hard_semantic_bounds": list(RATIO_AUTORANGE_HARD_BOUNDS),
    "data_uncertainty": "central Garwood Poisson interval only",
    "mc_uncertainty": "era-template relative Sumw2 band centered on one",
    "mc_band_alpha": 0.18,
    "mc_band_edge_width": 0.75,
    "mc_band_hatch": "////",
    "outlier_above": "filled upward triangle",
    "outlier_below": "filled downward triangle",
    "physical_period_lane": "short lower-edge separators with transparent letter labels",
}
CHI2_STYLE = {
    **RATIO_STYLE,
    "reference": "#286B72",
    "expected_band": "#77AEB1",
    "expected_band_edge": "#286B72",
}
CHI2_Y_AXIS_LABEL = r"$\chi^2_{\mathrm{red}}$"
CHI2_EXPECTATION_LEGEND_LABEL = r"Approx. $1 \pm \sqrt{2/\mathrm{ndf}}$"
CHI2_STYLE_PROVENANCE = {
    "source": "notebooks/mkshapes_analysis_lab",
    "theme": "publication-light",
    "theme_registry_version": "2026.08",
    "statistic": "interval-based Pearson reduced chi-square diagnostic",
    "reference": "one with approximate Gaussian standard-deviation band sqrt(2/ndf)",
    "autorange": "unity-anchored median/MAD core with directional outlier markers",
    "physical_period_lane": "short lower-edge separators with transparent letter labels",
    "runtime_dependency": False,
}
PERIOD_RATIO_STYLE_PROVENANCE = {
    "runtime_dependency": False,
    "robust_visibility_principle": {
        "source": "notebooks/mkshapes_analysis_lab/src/mkshapes_lab/plot_visibility.py",
        "function": "audit_plot_visibility",
        "adaptation": (
            "use a median-based robust reference so one scale-dominating finite "
            "value does not flatten the remaining evidence"
        ),
    },
    "clipped_marker_principle": {
        "source": "notebooks/mkshapes_analysis_lab/src/mkshapes_lab/plotting.py",
        "function": "_panel_outlier_indicators",
        "adaptation": (
            "place directional warning triangles at deliberate panel limits; "
            "period plots additionally distinguish clipped DATA intervals and MC bands"
        ),
    },
}
PERIOD_PLOT_TYPOGRAPHY = {
    "base_fontsize": 15.0,
    "axis_labelsize": 21.0,
    "tick_labelsize": 13.0,
    "legend_fontsize": 13.0,
    "annotation_fontsize": 14.0,
}
PERIOD_PLOT_MARGINS = {
    "left": 0.118,
    "right": 0.99,
    "bottom": 0.105,
    "top": 0.975,
}
PERIOD_PLOT_UPPER_HEADROOM = 1.34
PERIOD_PLOT_CANVAS_INSET_PIXELS = 6.0
DATA_MC_Y_AXIS_LABEL = "Data/MC"

_PHYSICAL_RUN_PERIOD = re.compile(r"^(?P<period>20(?:22|23|24)[A-Z])(?:_v\d+)?$")
_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9_-]+")
_OBSERVABLE_FILENAME_LABELS = {
    "Z0_mass": "Zmass",
    "Z0_pt": "Zpt",
    "Z0_eta": "Zeta",
    "lZ1_pt": "l1pt",
    "lZ2_pt": "l2pt",
    "lZ1_eta": "l1eta",
    "lZ2_eta": "l2eta",
}
MAX_OUTPUT_STEM_LENGTH = 160


def _filename_token(value, *, observable=False):
    """Return a deterministic safe token without conflating unsafe inputs."""
    original = str(value).strip()
    if not original:
        raise ValueError("Output filename tokens must be nonempty")
    semantic = (
        _OBSERVABLE_FILENAME_LABELS.get(original, original) if observable else original
    )
    safe = _FILENAME_SAFE.sub("-", semantic).strip("-_")
    if not safe:
        raise ValueError(f"Output filename token {original!r} has no safe characters")
    if safe != semantic or len(safe) > 48:
        digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:10]
        safe = f"{safe[:37].rstrip('-_')}-{digest}"
    return safe


def _bounded_output_stem(*tokens):
    stem = "_".join(tokens)
    if len(stem) > MAX_OUTPUT_STEM_LENGTH:
        digest = hashlib.sha256(stem.encode("utf-8")).hexdigest()[:12]
        stem = f"{stem[: MAX_OUTPUT_STEM_LENGTH - 13].rstrip('-_')}_{digest}"
    if not re.fullmatch(r"[A-Za-z0-9_-]+", stem):
        raise RuntimeError(f"Unsafe output stem generated: {stem!r}")
    return stem


def period_output_stem(period, observable, category, luminosity_source):
    return _bounded_output_stem(
        "datamc",
        _filename_token(period),
        _filename_token(observable, observable=True),
        _filename_token(category),
        _filename_token(luminosity_source),
    )


def stability_output_stem(datasets, observable, category, luminosity_source):
    years = []
    for dataset in datasets:
        era = str(dataset["contract"]["analysis_era"])
        match = re.match(r"^(20\d{2})", era)
        year = match.group(1) if match else era
        if year not in years:
            years.append(year)
    span = years[0] if len(years) == 1 else f"{years[0]}-{years[-1]}"
    return _bounded_output_stem(
        "stability",
        _filename_token(observable, observable=True),
        _filename_token(category),
        _filename_token(luminosity_source),
        _filename_token(span),
    )


def chi2_output_stem(datasets, observable, category, luminosity_source):
    """Concise identity for one multi-era distribution-shape diagnostic."""
    years = []
    for dataset in datasets:
        era = str(dataset["contract"]["analysis_era"])
        match = re.match(r"^(20\d{2})", era)
        year = match.group(1) if match else era
        if year not in years:
            years.append(year)
    span = years[0] if len(years) == 1 else f"{years[0]}-{years[-1]}"
    return _bounded_output_stem(
        "chi2",
        _filename_token(observable, observable=True),
        _filename_token(category),
        _filename_token(luminosity_source),
        _filename_token(span),
    )


def _guard_fresh_output_stem(output_dir, stem, extensions):
    output_dir = Path(output_dir)
    candidates = [output_dir / f"{stem}.{extension}" for extension in extensions]
    existing = [str(path) for path in candidates if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite an existing plot identity; use a fresh "
            f"campaign output directory. Existing: {existing}"
        )


def physical_run_period(label):
    """Collapse campaign variants to the physical year-letter run period."""
    match = _PHYSICAL_RUN_PERIOD.fullmatch(str(label))
    if not match:
        raise RuntimeError(f"Unsupported or empty configured run period {label!r}")
    return match.group("period")


def period_inventory(dataset, luminosity_source):
    """Return ordered physical periods and their exact compiled run membership."""
    raw_periods = dataset["run_periods"][luminosity_source]
    periods = []
    by_period = {}
    for index, (run, raw_period) in enumerate(zip(dataset["runs"], raw_periods)):
        period = physical_run_period(raw_period)
        if period not in by_period:
            periods.append(period)
            by_period[period] = {
                "period": period,
                "analysis_era": dataset["contract"]["analysis_era"],
                "run_indices": [],
                "runs": [],
                "configured_run_periods": [],
            }
        entry = by_period[period]
        entry["run_indices"].append(index)
        entry["runs"].append(int(run))
        if raw_period not in entry["configured_run_periods"]:
            entry["configured_run_periods"].append(raw_period)
    return [by_period[period] for period in periods]


def load_compiled_config(path):
    path = Path(path).resolve()
    try:
        config = cloudpickle.loads(zlib.decompress(path.read_bytes()))
    except Exception as exc:
        raise RuntimeError(f"Cannot load compiled configuration {path}: {exc}") from exc
    contract = config.get("RUN_STABILITY_CONTRACT")
    if not isinstance(contract, dict) or not contract.get("enabled"):
        raise RuntimeError(f"{path} has no enabled RUN_STABILITY_CONTRACT")
    return path, config


def open_root(path):
    handle = ROOT.TFile.Open(str(path), "READ")
    if not handle or handle.IsZombie():
        raise RuntimeError(f"Cannot open ROOT input {path}")
    return handle


def sha256(path):
    path = Path(path)
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def garwood_interval(count, coverage=GARWOOD_COVERAGE):
    """Return the central exact Poisson interval for an integer count."""
    count = int(count)
    if count < 0:
        raise ValueError("Poisson count cannot be negative")
    alpha = 1.0 - float(coverage)
    low = 0.0 if count == 0 else ROOT.Math.gamma_quantile(alpha / 2.0, count, 1.0)
    high = ROOT.Math.gamma_quantile_c(alpha / 2.0, count + 1, 1.0)
    return float(low), float(high)


def ratio_with_uncertainty(data, mc):
    """DATA/MC with asymmetric Garwood DATA errors only."""
    if mc <= 0.0:
        return None
    nearest = round(data)
    if data < 0.0 or abs(data - nearest) > 1.0e-6 * max(1.0, abs(data)):
        raise RuntimeError(
            f"DATA yield {data!r} is not an unweighted nonnegative integer count"
        )
    low, high = garwood_interval(nearest)
    ratio = data / mc
    return {
        "value": ratio,
        "error_low": (data - low) / mc,
        "error_high": (high - data) / mc,
        "data_low": low,
        "data_high": high,
    }


def chi2_bin_statistic(data, mc, mc_variance):
    """Return one interval-based Pearson contribution and its components.

    The symmetric DATA scale is half the central Garwood interval width.  This
    remains finite for an observed zero, unlike ``sqrt(D)``, but is still an
    interval-derived Gaussian scale rather than an exact Poisson likelihood.
    """
    values = (float(data), float(mc), float(mc_variance))
    if not all(math.isfinite(value) for value in values):
        raise RuntimeError(
            "Reduced-chi2 inputs must be finite: "
            f"data={data!r}, mc={mc!r}, mc_variance={mc_variance!r}"
        )
    nearest = round(values[0])
    if values[0] < 0.0 or abs(values[0] - nearest) > 1.0e-6 * max(1.0, values[0]):
        raise RuntimeError(
            f"DATA bin yield {data!r} is not an unweighted nonnegative integer count"
        )
    if values[2] < 0.0:
        raise RuntimeError(f"MC Sumw2 variance cannot be negative: {values[2]!r}")
    data_low, data_high = garwood_interval(nearest)
    data_sigma = 0.5 * (data_high - data_low)
    data_variance = data_sigma * data_sigma
    total_variance = data_variance + values[2]
    if not math.isfinite(total_variance) or total_variance <= 0.0:
        return {
            "valid": False,
            "invalid_reason": "nonpositive_total_stat_variance",
            "data": values[0],
            "mc": values[1],
            "data_low": data_low,
            "data_high": data_high,
            "data_symmetric_sigma": data_sigma,
            "data_variance": data_variance,
            "mc_variance": values[2],
            "total_variance": total_variance,
            "residual": values[0] - values[1],
            "chi2_contribution": None,
        }
    residual = values[0] - values[1]
    return {
        "valid": True,
        "invalid_reason": None,
        "data": values[0],
        "mc": values[1],
        "data_low": data_low,
        "data_high": data_high,
        "data_symmetric_sigma": data_sigma,
        "data_variance": data_variance,
        "mc_variance": values[2],
        "total_variance": total_variance,
        "residual": residual,
        "chi2_contribution": residual * residual / total_variance,
    }


def mc_ratio_covariance(ratios, era_indices, mc_yields, mc_variances):
    """Covariance from reusing one finite-MC template for every run in an era."""
    size = len(ratios)
    covariance = [[0.0] * size for _ in range(size)]
    for left in range(size):
        era = era_indices[left]
        mc_yield = mc_yields[era]
        if ratios[left] is None or mc_yield <= 0.0:
            continue
        relative_variance = mc_variances[era] / (mc_yield * mc_yield)
        for right in range(size):
            if era_indices[right] != era or ratios[right] is None:
                continue
            covariance[left][right] = ratios[left] * ratios[right] * relative_variance
    return covariance


def ratio_vs_run_autorange(rows):
    """Choose and fully audit a focused, uncertainty-aware run-ratio range."""
    if not rows:
        raise RuntimeError("Ratio-vs-run autoranging requires at least one run row")

    minimum_informative_points = 5
    maximum_data_relative_halfwidth = 0.55
    maximum_mc_relative_band = 0.35
    minimum_span = 0.30
    fallback_range = (0.70, 1.30)
    maximum_data_interval_influence = 0.18
    padding_fraction = 0.08
    minimum_padding = 0.025
    hard_low, hard_high = RATIO_AUTORANGE_HARD_BOUNDS

    selection_inputs = []
    informative = []
    finite_valid = []
    invalid = []
    for index, row in enumerate(rows, 1):
        point = {
            "bin": index,
            "era": str(row["era"]),
            "run": int(row["run"]),
            "ratio": row.get("ratio"),
        }
        diagnostic = {
            **point,
            "valid": bool(row.get("valid")),
            "informative": False,
            "reason_codes": [],
        }
        ratio = row.get("ratio")
        if not row.get("valid") or ratio is None or not math.isfinite(float(ratio)):
            diagnostic["reason_codes"].append("invalid_ratio")
            point["invalid_reason"] = row.get("invalid_reason") or "invalid_ratio"
            invalid.append(point)
            selection_inputs.append(diagnostic)
            continue

        ratio = float(ratio)
        error_low = float(row.get("ratio_error_low", float("nan")))
        error_high = float(row.get("ratio_error_high", float("nan")))
        data_yield = float(row.get("data_yield", float("nan")))
        mc_yield = float(row.get("mc_yield", float("nan")))
        mc_relative = float(row.get("mc_relative_uncertainty", float("nan")))
        finite_valid.append(row)
        diagnostic.update(
            {
                "ratio": ratio,
                "ratio_error_low": error_low,
                "ratio_error_high": error_high,
                "data_yield": data_yield,
                "mc_yield": mc_yield,
                "mc_relative_band": mc_relative,
            }
        )
        if data_yield <= 0.0 or not math.isfinite(data_yield):
            diagnostic["reason_codes"].append("nonpositive_data_count")
        if (
            not math.isfinite(error_low)
            or not math.isfinite(error_high)
            or error_low < 0.0
            or error_high < 0.0
            or not math.isfinite(mc_yield)
            or mc_yield <= 0.0
        ):
            diagnostic["reason_codes"].append("invalid_data_interval")
            data_relative = None
        else:
            # This equals the larger Garwood count displacement divided by
            # max(D, 1), while remaining computable from the serialized row.
            data_relative = max(error_low, error_high) * mc_yield / max(data_yield, 1.0)
            diagnostic["data_relative_halfwidth"] = data_relative
            if data_relative > maximum_data_relative_halfwidth:
                diagnostic["reason_codes"].append("data_poisson_precision")
        if not math.isfinite(mc_relative) or mc_relative < 0.0:
            diagnostic["reason_codes"].append("invalid_mc_relative_band")
        elif mc_relative > maximum_mc_relative_band:
            diagnostic["reason_codes"].append("mc_stat_precision")
        if not diagnostic["reason_codes"]:
            diagnostic["informative"] = True
            informative.append(row)
        selection_inputs.append(diagnostic)

    if not finite_valid:
        raise RuntimeError(
            "Ratio-vs-run autoranging has no finite valid DATA/MC points"
        )

    era_mc_bands = []
    seen_era_bands = {}
    excluded_mc_band_eras = []
    for row in rows:
        era = str(row["era"])
        relative = float(row.get("mc_relative_uncertainty", float("nan")))
        if not math.isfinite(relative) or relative < 0.0:
            if era not in excluded_mc_band_eras:
                excluded_mc_band_eras.append(era)
            continue
        if era in seen_era_bands:
            if not math.isclose(
                seen_era_bands[era], relative, rel_tol=1.0e-12, abs_tol=1.0e-15
            ):
                raise RuntimeError(
                    f"Era {era} has inconsistent MC relative uncertainties: "
                    f"{seen_era_bands[era]} and {relative}"
                )
            continue
        seen_era_bands[era] = relative
        era_mc_bands.append(
            {
                "era": era,
                "relative_uncertainty": relative,
                "low": 1.0 - relative,
                "high": 1.0 + relative,
            }
        )

    informative_ratios = [float(row["ratio"]) for row in informative]
    median = float(np.median(informative_ratios)) if informative_ratios else None
    mad = (
        float(np.median(np.abs(np.asarray(informative_ratios) - median)))
        if median is not None
        else None
    )
    if len(informative) >= minimum_informative_points:
        central_cut = max(0.08, 4.0 * 1.4826 * mad)
        core = [
            row
            for row in informative
            if abs(float(row["ratio"]) - median) <= central_cut
        ]
        if len(core) < minimum_informative_points:
            core = sorted(
                informative, key=lambda row: abs(float(row["ratio"]) - median)
            )[:minimum_informative_points]
        range_mode = "informative_median_mad_core"
    else:
        central_cut = None
        core = []
        range_mode = "unity_baseline_sparse_fallback"

    data_interval_cap = min(
        _robust_upper_cut(
            [
                max(float(row["ratio_error_low"]), float(row["ratio_error_high"]))
                for row in core
            ],
            minimum=0.04,
        ),
        maximum_data_interval_influence,
    )
    candidates = [1.0]
    for band in era_mc_bands:
        candidates.extend((band["low"], band["high"]))
    if range_mode == "unity_baseline_sparse_fallback":
        candidates.extend(fallback_range)
    else:
        for row in core:
            ratio = float(row["ratio"])
            candidates.extend(
                (
                    ratio,
                    ratio - min(float(row["ratio_error_low"]), data_interval_cap),
                    ratio + min(float(row["ratio_error_high"]), data_interval_cap),
                )
            )

    raw_low, raw_high = min(candidates), max(candidates)
    unpadded_span = max(raw_high - raw_low, minimum_span)
    midpoint = 0.5 * (raw_low + raw_high)
    unpadded_low = min(raw_low, midpoint - 0.5 * unpadded_span)
    unpadded_high = max(raw_high, midpoint + 0.5 * unpadded_span)
    padding = max(minimum_padding, padding_fraction * (unpadded_high - unpadded_low))
    requested_low = unpadded_low - padding
    requested_high = unpadded_high + padding
    low = max(hard_low, requested_low)
    high = min(hard_high, requested_high)
    if not low < 1.0 < high:
        raise RuntimeError(
            f"Ratio-vs-run autorange failed to retain unity: {low}..{high}"
        )

    classified = {"in_range": [], "above": [], "below": [], "invalid": invalid}
    clipped = {
        "data_central_below": [],
        "data_central_above": [],
        "data_interval_below": [],
        "data_interval_above": [],
        "mc_band_below": [],
        "mc_band_above": [],
        "invalid": invalid,
    }
    for index, row in enumerate(rows, 1):
        if not row.get("valid") or row.get("ratio") is None:
            continue
        ratio = float(row["ratio"])
        if not math.isfinite(ratio):
            continue
        point = {
            "bin": index,
            "era": str(row["era"]),
            "run": int(row["run"]),
            "ratio": ratio,
        }
        if ratio < low:
            classified["below"].append(point)
            clipped["data_central_below"].append(point)
        elif ratio > high:
            classified["above"].append(point)
            clipped["data_central_above"].append(point)
        else:
            classified["in_range"].append(point)
        interval_low = ratio - float(row["ratio_error_low"])
        interval_high = ratio + float(row["ratio_error_high"])
        interval_point = {
            **point,
            "interval_low": interval_low,
            "interval_high": interval_high,
        }
        if interval_low < low:
            clipped["data_interval_below"].append(interval_point)
        if interval_high > high:
            clipped["data_interval_above"].append(interval_point)
    for band in era_mc_bands:
        if band["low"] < low:
            clipped["mc_band_below"].append(dict(band))
        if band["high"] > high:
            clipped["mc_band_above"].append(dict(band))

    row_bins = {id(row): index for index, row in enumerate(rows, 1)}

    def point_identity(row):
        index = row_bins[id(row)]
        return {"bin": index, "era": str(row["era"]), "run": int(row["run"])}

    return {
        "range": [float(low), float(high)],
        **classified,
        "clipped": clipped,
        "policy": {
            "name": "uncertainty_aware_ratio_vs_run_v1",
            "range_mode": range_mode,
            "minimum_span": minimum_span,
            "hard_semantic_bounds": [hard_low, hard_high],
            "hard_bounds_applied": {
                "low": low > requested_low,
                "high": high < requested_high,
            },
            "fallback_range": list(fallback_range),
            "padding_fraction": padding_fraction,
            "minimum_padding": minimum_padding,
            "applied_padding": padding,
            "raw_candidate_range": [float(raw_low), float(raw_high)],
            "requested_padded_range": [float(requested_low), float(requested_high)],
            "minimum_informative_points": minimum_informative_points,
            "maximum_data_relative_halfwidth": maximum_data_relative_halfwidth,
            "maximum_mc_relative_band_for_information": maximum_mc_relative_band,
            "maximum_data_interval_influence": maximum_data_interval_influence,
            "data_interval_cap": float(data_interval_cap),
            "selection_inputs": selection_inputs,
            "informative_points": [point_identity(row) for row in informative],
            "range_central_input_points": [point_identity(row) for row in core],
            "excluded_uninformative_points": [
                {
                    "bin": item["bin"],
                    "era": item["era"],
                    "run": item["run"],
                    "reason_codes": item["reason_codes"],
                }
                for item in selection_inputs
                if item["valid"] and not item["informative"]
            ],
            "excluded_insufficient_population_points": (
                [point_identity(row) for row in informative]
                if range_mode == "unity_baseline_sparse_fallback"
                else []
            ),
            "central_outlier_points": [
                point_identity(row) for row in informative if row not in core
            ],
            "informative_ratio_median": median,
            "informative_ratio_mad": mad,
            "central_cut": central_cut,
            "era_mc_bands": era_mc_bands,
            "excluded_mc_band_eras": excluded_mc_band_eras,
            "anchors": [1.0],
            "style_provenance": PERIOD_RATIO_STYLE_PROVENANCE,
        },
    }


def ratio_display_summary(rows):
    """Compatibility name for the adaptive ratio-vs-run display contract."""
    return ratio_vs_run_autorange(rows)


def _dynamic_ratio_ticks(low, high):
    """Return a compact adaptive tick set that always labels unity."""
    locator = matplotlib.ticker.MaxNLocator(
        nbins=7, steps=[1.0, 2.0, 2.5, 5.0, 10.0], min_n_ticks=4
    )
    ticks = [
        float(value)
        for value in locator.tick_values(float(low), float(high))
        if low - 1.0e-12 <= value <= high + 1.0e-12
    ]
    if not any(math.isclose(value, 1.0, abs_tol=1.0e-12) for value in ticks):
        ticks.append(1.0)
    return sorted(set(round(value, 12) for value in ticks))


def chi2_display_summary(rows):
    """Choose and audit a focused range for nonnegative reduced-chi2 values."""
    minimum_informative_points = 5
    maximum_expected_sigma = 0.75
    diagnostic_hard_cap = 5.0
    minimum_span = 1.2
    sparse_fallback = (0.0, 1.6)
    padding_fraction = 0.08
    minimum_padding = 0.08

    finite_valid = []
    informative = []
    invalid = []
    selection_inputs = []
    for index, row in enumerate(rows, 1):
        point = {
            "bin": index,
            "era": str(row["era"]),
            "run": int(row["run"]),
            "reduced_chi2": row.get("reduced_chi2"),
            "ndf": int(row.get("ndf", 0)),
        }
        diagnostic = {**point, "informative": False, "reason_codes": []}
        value = row.get("reduced_chi2")
        if not row.get("valid") or value is None or not math.isfinite(float(value)):
            diagnostic["reason_codes"].append("invalid_run")
            point["invalid_reason"] = row.get("invalid_reason") or "invalid_run"
            invalid.append(point)
            selection_inputs.append(diagnostic)
            continue
        value = float(value)
        ndf = int(row.get("ndf", 0))
        finite_valid.append(row)
        diagnostic["reduced_chi2"] = value
        if ndf <= 0:
            diagnostic["reason_codes"].append("nonpositive_ndf")
        else:
            expected_sigma = math.sqrt(2.0 / ndf)
            diagnostic["expected_sigma"] = expected_sigma
            if expected_sigma > maximum_expected_sigma:
                diagnostic["reason_codes"].append("expected_band_too_broad")
        if value > diagnostic_hard_cap:
            diagnostic["reason_codes"].append("above_diagnostic_focus_cap")
        if not diagnostic["reason_codes"]:
            diagnostic["informative"] = True
            informative.append(row)
        selection_inputs.append(diagnostic)

    if not finite_valid:
        raise RuntimeError("Reduced-chi2 display has no finite valid run points")

    values = np.asarray(
        [float(row["reduced_chi2"]) for row in informative], dtype=float
    )
    median = float(np.median(values)) if values.size else None
    mad = float(np.median(np.abs(values - median))) if values.size else None
    if len(informative) >= minimum_informative_points:
        core_half_width = max(0.25, 4.0 * 1.4826 * mad)
        core = values[np.abs(values - median) <= core_half_width]
        if len(core) < minimum_informative_points:
            core = values[
                np.argsort(np.abs(values - median))[:minimum_informative_points]
            ]
        range_mode = "informative_median_mad_core"
    else:
        core_half_width = None
        core = np.asarray([], dtype=float)
        range_mode = "unity_sparse_fallback"

    expected_sigmas = [
        math.sqrt(2.0 / int(row["ndf"])) for row in finite_valid if int(row["ndf"]) > 0
    ]
    candidates = [0.0, 1.0]
    if range_mode == "unity_sparse_fallback":
        candidates.extend(sparse_fallback)
    else:
        candidates.extend(core.tolist())
    for sigma in expected_sigmas:
        candidates.extend((max(0.0, 1.0 - sigma), 1.0 + sigma))
    raw_high = max(candidates)
    unbounded_high = max(raw_high, minimum_span)
    padding = max(minimum_padding, padding_fraction * unbounded_high)
    requested_high = unbounded_high + padding
    low = 0.0
    high = min(diagnostic_hard_cap, requested_high)
    if not low <= 1.0 < high:
        raise RuntimeError(
            f"Reduced-chi2 autorange failed to retain unity: {low}..{high}"
        )

    classified = {"in_range": [], "above": [], "below": [], "invalid": invalid}
    for index, row in enumerate(rows, 1):
        point = {
            "bin": index,
            "era": row["era"],
            "run": int(row["run"]),
            "reduced_chi2": row.get("reduced_chi2"),
            "ndf": int(row.get("ndf", 0)),
        }
        if (
            not row.get("valid")
            or row.get("reduced_chi2") is None
            or not math.isfinite(float(row["reduced_chi2"]))
        ):
            continue
        if float(row["reduced_chi2"]) < low:
            classified["below"].append(point)
        elif float(row["reduced_chi2"]) > high:
            classified["above"].append(point)
        else:
            classified["in_range"].append(point)
    row_bins = {id(row): index for index, row in enumerate(rows, 1)}
    return {
        "range": [float(low), float(high)],
        "in_range": classified["in_range"],
        "above": classified["above"],
        "below": classified["below"],
        "invalid": classified["invalid"],
        "clipped": {
            "central_above": classified["above"],
            "central_below": classified["below"],
            "invalid": invalid,
        },
        "policy": {
            "name": "focused_reduced_chi2_informative_core_v2",
            "range_mode": range_mode,
            "minimum_span": minimum_span,
            "sparse_fallback": list(sparse_fallback),
            "padding_fraction": padding_fraction,
            "minimum_padding": minimum_padding,
            "applied_padding": padding,
            "raw_candidate_range": [0.0, float(raw_high)],
            "requested_padded_range": [0.0, float(requested_high)],
            "diagnostic_hard_bounds": [0.0, diagnostic_hard_cap],
            "hard_cap_applied": high < requested_high,
            "hard_cap_rationale": (
                "reduced chi2 >= 5 is already an extreme diagnostic discrepancy; "
                "values remain serialized and are shown with boundary markers"
            ),
            "minimum_informative_points": minimum_informative_points,
            "maximum_expected_sigma": maximum_expected_sigma,
            "finite_point_count": len(finite_valid),
            "informative_point_count": len(informative),
            "informative_median": median,
            "informative_mad": mad,
            "core_half_width": core_half_width,
            "core_values": [float(value) for value in core],
            "selection_inputs": selection_inputs,
            "informative_points": [
                {
                    "bin": row_bins[id(row)],
                    "era": str(row["era"]),
                    "run": int(row["run"]),
                }
                for row in informative
            ],
            "excluded_points": [
                {
                    "bin": item["bin"],
                    "era": item["era"],
                    "run": item["run"],
                    "reason_codes": item["reason_codes"],
                }
                for item in selection_inputs
                if item["reason_codes"]
            ],
            "anchors": [1.0],
            "expected_band": "1 +/- sqrt(2/ndf), clipped at zero for display",
            "style_provenance": PERIOD_RATIO_STYLE_PROVENANCE,
        },
    }


def _era_spans(rows):
    spans = []
    for index, row in enumerate(rows, 1):
        era = row["era"]
        if not spans or spans[-1]["era"] != era:
            spans.append(
                {
                    "era": era,
                    "first_bin": index,
                    "last_bin": index,
                    "recorded_lumi_fb": float(row["recorded_lumi_fb"]),
                    "mc_relative_uncertainty": row.get("mc_relative_uncertainty"),
                }
            )
        else:
            spans[-1]["last_bin"] = index
            spans[-1]["recorded_lumi_fb"] += float(row["recorded_lumi_fb"])
            current = spans[-1]["mc_relative_uncertainty"]
            candidate = row.get("mc_relative_uncertainty")
            if (
                current is not None
                and candidate is not None
                and not math.isclose(
                    float(current), float(candidate), rel_tol=1.0e-12, abs_tol=1.0e-15
                )
            ):
                raise RuntimeError(
                    f"Era {era} has inconsistent MC relative uncertainties"
                )
    return spans


def _physical_period_spans(rows):
    """Return consecutive physical year-letter spans for the run-axis lane."""
    spans = []
    seen = set()
    for index, row in enumerate(rows, 1):
        period = row.get("physical_run_period")
        if not period:
            raise RuntimeError(
                f"Era {row.get('era')} run {row.get('run')} has no physical run period"
            )
        period = physical_run_period(period)
        if not spans or spans[-1]["period"] != period:
            if period in seen:
                raise RuntimeError(
                    f"Physical run period {period} is noncontiguous on the run axis"
                )
            seen.add(period)
            spans.append(
                {
                    "period": period,
                    "label": period[-1],
                    "era": row["era"],
                    "first_bin": index,
                    "last_bin": index,
                    "first_run": int(row["run"]),
                    "last_run": int(row["run"]),
                    "run_count": 1,
                }
            )
        else:
            spans[-1]["last_bin"] = index
            spans[-1]["last_run"] = int(row["run"])
            spans[-1]["run_count"] += 1
    return spans


def _selected_run_labels(rows, spans):
    """Choose readable labels while retaining every era's first and last run."""
    selected = []
    for span in spans:
        first = span["first_bin"]
        last = span["last_bin"]
        width = last - first + 1
        label_count = max(2, math.ceil(width / 90.0) + 1)
        for label_index in range(label_count):
            fraction = label_index / (label_count - 1)
            index = first + int(round((width - 1) * fraction))
            if not selected or selected[-1][0] != index:
                selected.append((index, str(rows[index - 1]["run"])))
    return selected


def _staggered_run_labels(selected_labels, spans):
    """Move the first label after each era boundary onto a second row."""
    boundary_starts = {span["first_bin"] for span in spans[1:]}
    labels = []
    staggered_bins = []
    for index, label in selected_labels:
        if index in boundary_starts:
            labels.append((index, f"\n{label}"))
            staggered_bins.append(index)
        else:
            labels.append((index, label))
    return labels, staggered_bins


def _category_annotation(category):
    """Return a compact LaTeX-style selection description for one DY category."""
    flavor = r"Inclusive $Z\rightarrow\ell\ell$"
    base = category
    for suffix, label in (
        ("_ZEE", r"$Z\rightarrow ee$"),
        ("_ZMM", r"$Z\rightarrow\mu\mu$"),
    ):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            flavor = label
            break

    if base in {"DY", "DY_ALL"}:
        selection = r"Trigger: inclusive OR"
    elif base.startswith("DY_STREAM_"):
        stream = base.removeprefix("DY_STREAM_")
        stream_labels = {
            "MUONEG": "MuonEG",
            "MUON": "Muon",
            "EGAMMA": "EGamma",
        }
        selection = f"Stream: {stream_labels.get(stream, stream)}"
    elif base.startswith("DY_TRGFAM_"):
        family = base.removeprefix("DY_TRGFAM_")
        family_labels = {
            "ELMU": r"$e\mu$",
            "SINGLEMU": r"single $\mu$",
            "DOUBLEMU": r"double $\mu$",
            "SINGLEEL": r"single $e$",
            "DOUBLEEL": r"double $e$",
        }
        selection = f"Trigger family: {family_labels.get(family, family)}"
    elif base.startswith("DY_HLT_"):
        path = base.removeprefix("DY_HLT_")
        path_labels = {
            "MU23_ELE12": r"$\mathrm{Mu23\_Ele12}$",
            "MU12_ELE23": r"$\mathrm{Mu12\_Ele23}$",
            "MU8_ELE23": r"$\mathrm{Mu8\_Ele23}$",
            "MU17_MU8": r"$\mathrm{Mu17\_Mu8}$",
            "ISOMU24": r"$\mathrm{IsoMu24}$",
            "ELE23_ELE12": r"$\mathrm{Ele23\_Ele12}$",
            "ELE30": r"$\mathrm{Ele30}$",
        }
        selection = f"HLT path: {path_labels.get(path, path)}"
    else:
        raise ValueError(f"Unsupported DY category annotation for {category!r}")
    return "\n".join((selection, flavor))


def _observable_annotation(observable):
    labels = {
        "Z0_mass": r"$m_{Z}$",
        "Z0_pt": r"$p_{T}^{Z}$",
        "lZ1_pt": r"$p_{T}^{\ell_{1}}$",
        "lZ2_pt": r"$p_{T}^{\ell_{2}}$",
        "lZ1_eta": r"$\eta^{\ell_{1}}$",
        "lZ2_eta": r"$\eta^{\ell_{2}}$",
    }
    return labels.get(observable, observable.replace("_", r"\_"))


def _render_ratio_vs_run(
    rows,
    _ratio_hist,
    output_dir,
    stem,
    category,
    observable,
    luminosity_source,
):
    """Render the stability summary with the notebook plotting stack."""
    size = len(rows)
    display = ratio_vs_run_autorange(rows)
    low, high = display["range"]
    y_ticks = _dynamic_ratio_ticks(low, high)
    spans = _era_spans(rows)
    period_spans = _physical_period_spans(rows)
    selected_labels = _selected_run_labels(rows, spans)
    display_labels, staggered_label_bins = _staggered_run_labels(selected_labels, spans)
    render_dpi = 240
    canvas_width, canvas_height = 3000, 1560
    figure_size = (canvas_width / render_dpi, canvas_height / render_dpi)
    style = {
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 12.0,
        "axes.labelsize": 14.0,
        "axes.linewidth": 0.8,
        "axes.edgecolor": RATIO_STYLE["spine"],
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "xtick.labelsize": 10.0,
        "ytick.labelsize": 11.5,
        "legend.fontsize": 11.5,
        "xaxis.labellocation": "center",
        "yaxis.labellocation": "center",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
    with plt.style.context(mplhep.style.CMS), matplotlib.rc_context(style):
        figure, axis = plt.subplots(figsize=figure_size, dpi=render_dpi)
        figure.subplots_adjust(left=0.060, right=0.995, bottom=0.125, top=0.990)
        x = np.arange(1, size + 1, dtype=float)

        for span_index, span in enumerate(spans):
            fill = RATIO_STYLE[
                "era_fill_even" if span_index % 2 == 0 else "era_fill_odd"
            ]
            axis.axvspan(
                span["first_bin"] - 0.5,
                span["last_bin"] + 0.5,
                color=fill,
                linewidth=0.0,
                zorder=0,
            )
            if span_index:
                axis.axvline(
                    span["first_bin"] - 0.5,
                    color=RATIO_STYLE["spine"],
                    linewidth=0.8,
                    linestyle=":",
                    zorder=2,
                )

            relative_mc = span["mc_relative_uncertainty"]
            if relative_mc is not None:
                relative_mc = float(relative_mc)
                axis.fill_between(
                    [span["first_bin"] - 0.5, span["last_bin"] + 0.5],
                    [1.0 - relative_mc, 1.0 - relative_mc],
                    [1.0 + relative_mc, 1.0 + relative_mc],
                    facecolor=RATIO_STYLE["mc_band"],
                    edgecolor=RATIO_STYLE["mc_band_edge"],
                    linewidth=RATIO_STYLE_PROVENANCE["mc_band_edge_width"],
                    alpha=RATIO_STYLE_PROVENANCE["mc_band_alpha"],
                    hatch=RATIO_STYLE_PROVENANCE["mc_band_hatch"],
                    zorder=3,
                )

        in_range_indices = np.array(
            [point["bin"] - 1 for point in display["in_range"]], dtype=int
        )
        if in_range_indices.size:
            in_range_rows = [rows[index] for index in in_range_indices]
            axis.errorbar(
                x[in_range_indices],
                [row["ratio"] for row in in_range_rows],
                yerr=np.array(
                    [
                        [row["ratio_error_low"] for row in in_range_rows],
                        [row["ratio_error_high"] for row in in_range_rows],
                    ]
                ),
                fmt="none",
                ecolor=RATIO_STYLE["data_error"],
                elinewidth=0.55,
                capsize=0.0,
                alpha=0.68,
                zorder=5,
                clip_on=True,
            )
        in_range_bins = np.array(
            [point["bin"] for point in display["in_range"]], dtype=float
        )
        if in_range_bins.size:
            axis.scatter(
                in_range_bins,
                [point["ratio"] for point in display["in_range"]],
                marker="o",
                s=8.0,
                facecolor=RATIO_STYLE["data"],
                edgecolor="white",
                linewidth=0.2,
                alpha=0.9,
                zorder=7,
            )

        boundary_offset = 0.018 * (high - low)
        outlier_options = {
            "s": 26.0,
            "facecolor": RATIO_STYLE["warning"],
            "edgecolor": RATIO_STYLE["data"],
            "linewidth": 0.35,
            "clip_on": False,
            "zorder": 12,
        }
        for direction, marker, ordinate in (
            ("above", "^", high - boundary_offset),
            ("below", "v", low + 2.0 * boundary_offset),
        ):
            points = display[direction]
            if points:
                axis.scatter(
                    [point["bin"] for point in points],
                    [ordinate] * len(points),
                    marker=marker,
                    **outlier_options,
                )
        if display["invalid"]:
            axis.scatter(
                [point["bin"] for point in display["invalid"]],
                [low + 3.8 * boundary_offset] * len(display["invalid"]),
                marker="x",
                s=28.0,
                color=RATIO_STYLE["warning"],
                linewidth=1.0,
                zorder=13,
            )

        axis.axhline(
            1.0,
            color=RATIO_STYLE["reference"],
            linewidth=1.45,
            linestyle=(0, (6.0, 2.8)),
            zorder=4,
        )
        axis.set_xlim(0.5, size + 0.5)
        axis.set_ylim(low, high)
        axis.set_ylabel(DATA_MC_Y_AXIS_LABEL)
        axis.set_xlabel(r"$\mathrm{Run\ number}$", labelpad=12.0)
        axis.set_xticks([index for index, _ in display_labels])
        tick_labels = axis.set_xticklabels(
            [label for _, label in display_labels], fontsize=10.0
        )
        if tick_labels:
            tick_labels[0].set_horizontalalignment("left")
            tick_labels[-1].set_horizontalalignment("right")
        axis.set_yticks(y_ticks)
        axis.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        axis.tick_params(axis="x", which="both", top=False)
        axis.tick_params(axis="y", which="both", right=False)
        axis.grid(
            axis="y",
            color=RATIO_STYLE["grid"],
            linewidth=0.55,
            linestyle=(0, (1.5, 2.4)),
            zorder=1,
        )
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        period_label_artists = []
        for period_index, period_span in enumerate(period_spans):
            if period_index:
                axis.axvline(
                    period_span["first_bin"] - 0.5,
                    ymin=0.0,
                    ymax=0.06,
                    color=RATIO_STYLE["period_separator"],
                    linewidth=1.15,
                    solid_capstyle="butt",
                    zorder=14,
                )
            center = 0.5 * (period_span["first_bin"] + period_span["last_bin"])
            period_label_artists.append(
                axis.text(
                    center,
                    low + 0.006 * (high - low),
                    period_span["label"],
                    ha="center",
                    va="bottom",
                    color=RATIO_STYLE["period_label"],
                    fontsize=10.0,
                    fontweight="semibold",
                    zorder=14,
                )
            )

        era_label_artists = []
        for span in spans:
            center = 0.5 * (span["first_bin"] + span["last_bin"])
            era_label_artists.append(
                axis.text(
                    center,
                    high - 0.025 * (high - low),
                    f"{span['era']}\n${span['recorded_lumi_fb']:.3g}"
                    r"\,\mathrm{fb}^{-1}$",
                    ha="center",
                    va="top",
                    color=RATIO_STYLE["spine"],
                    fontsize=10.5,
                    fontweight="semibold",
                    linespacing=0.9,
                    zorder=15,
                )
            )

        annotation_artist = axis.text(
            0.012,
            0.875,
            _category_annotation(category),
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=12.0,
            linespacing=1.18,
            color=RATIO_STYLE["data"],
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": RATIO_STYLE["grid"],
                "linewidth": 0.65,
                "alpha": 0.95,
            },
            zorder=20,
        )

        handles = [
            Line2D(
                [],
                [],
                color=RATIO_STYLE["data"],
                marker="o",
                markerfacecolor=RATIO_STYLE["data"],
                markeredgecolor=RATIO_STYLE["data"],
                markersize=4.0,
                linewidth=0.6,
                label="Data",
            ),
            _OverlayLegendTuple(
                (
                    Patch(
                        facecolor=RATIO_STYLE["mc_band"],
                        edgecolor=RATIO_STYLE["mc_band_edge"],
                        linewidth=RATIO_STYLE_PROVENANCE["mc_band_edge_width"],
                        alpha=RATIO_STYLE_PROVENANCE["mc_band_alpha"],
                        hatch=RATIO_STYLE_PROVENANCE["mc_band_hatch"],
                    ),
                    Line2D(
                        [],
                        [],
                        color=RATIO_STYLE["reference"],
                        linestyle=(0, (6.0, 2.8)),
                        linewidth=1.45,
                    ),
                )
            ),
        ]
        labels = ["Data", "MC"]
        if display["above"] or display["below"]:
            handles.append(
                _SideBySideLegendTuple(
                    (
                        Line2D(
                            [],
                            [],
                            color=RATIO_STYLE["warning"],
                            marker="^",
                            linestyle="none",
                            markersize=5.0,
                        ),
                        Line2D(
                            [],
                            [],
                            color=RATIO_STYLE["warning"],
                            marker="v",
                            linestyle="none",
                            markersize=5.0,
                        ),
                    )
                )
            )
            labels.append("Out of range")
        if display["invalid"]:
            handles.append(
                Line2D(
                    [],
                    [],
                    color=RATIO_STYLE["warning"],
                    marker="x",
                    linestyle="none",
                    markersize=5.2,
                )
            )
            labels.append("Zero lumi.")
        legend_artist = axis.legend(
            handles=handles,
            labels=labels,
            loc="upper right",
            bbox_to_anchor=(0.992, 0.875),
            ncol=2,
            frameon=True,
            framealpha=0.88,
            facecolor="white",
            edgecolor=RATIO_STYLE["grid"],
            borderpad=0.55,
            handlelength=2.2,
            handletextpad=0.8,
            labelspacing=0.4,
            columnspacing=1.5,
            handler_map={
                _OverlayLegendTuple: HandlerTuple(ndivide=1, pad=0.0),
                _SideBySideLegendTuple: HandlerTuple(ndivide=None, pad=0.15),
            },
        )

        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        legend_bbox = legend_artist.get_window_extent(renderer=renderer)
        annotation_bbox = annotation_artist.get_window_extent(renderer=renderer)
        if legend_bbox.overlaps(annotation_bbox):
            plt.close(figure)
            raise RuntimeError(
                f"Ratio-vs-run legend and category annotation overlap for {category}"
            )
        figure_bbox = matplotlib.transforms.Bbox.from_bounds(
            0.0, 0.0, float(renderer.width), float(renderer.height)
        )
        out_of_range_tick_text_ids = set()
        for tick_axis, limits in (
            (axis.xaxis, axis.get_xlim()),
            (axis.yaxis, axis.get_ylim()),
        ):
            for tick in tick_axis.get_major_ticks() + tick_axis.get_minor_ticks():
                location = float(tick.get_loc())
                if not limits[0] - 1.0e-9 <= location <= limits[1] + 1.0e-9:
                    out_of_range_tick_text_ids.update(
                        (id(tick.label1), id(tick.label2))
                    )
        visible_text_artists = [
            artist
            for artist in figure.findobj(match=matplotlib.text.Text)
            if (
                artist.get_visible()
                and artist.get_text().strip()
                and id(artist) not in out_of_range_tick_text_ids
            )
        ]
        required_artists = [legend_artist, *visible_text_artists]
        clipped_required_artists = []
        artist_clearances = []
        for artist in required_artists:
            bbox = artist.get_window_extent(renderer=renderer)
            clearances = {
                "left": float(bbox.x0 - figure_bbox.x0),
                "right": float(figure_bbox.x1 - bbox.x1),
                "bottom": float(bbox.y0 - figure_bbox.y0),
                "top": float(figure_bbox.y1 - bbox.y1),
            }
            artist_clearances.append(clearances)
            if min(clearances.values()) < PERIOD_PLOT_CANVAS_INSET_PIXELS:
                clipped_required_artists.append(
                    {
                        "artist": type(artist).__name__,
                        "text": (
                            artist.get_text() if hasattr(artist, "get_text") else ""
                        ),
                        "bbox_pixels": [float(value) for value in bbox.extents],
                    }
                )
        if clipped_required_artists:
            plt.close(figure)
            raise RuntimeError(
                "Ratio-vs-run layout clips required artists: "
                f"{clipped_required_artists} for {category}"
            )
        minimum_edge_clearance = {
            edge: min(item[edge] for item in artist_clearances)
            for edge in ("left", "right", "bottom", "top")
        }
        layout_audit = {
            "legend_annotation_overlap": False,
            "clipped_required_artists": [],
            "canvas_inset_requirement_pixels": PERIOD_PLOT_CANVAS_INSET_PIXELS,
            "visible_text_artist_count": len(visible_text_artists),
            "minimum_edge_clearance_pixels": minimum_edge_clearance,
            "legend_bbox_pixels": [float(value) for value in legend_bbox.extents],
            "annotation_bbox_pixels": [
                float(value) for value in annotation_bbox.extents
            ],
        }

        png_path = output_dir / f"{stem}.png"
        pdf_path = output_dir / f"{stem}.pdf"
        metadata = {
            "Title": f"DY Data/MC run stability: {category}, {observable}",
            "Creator": "RunStability plot_run_stability.py",
        }
        figure.savefig(png_path, dpi=render_dpi, metadata=metadata)
        figure.savefig(pdf_path, metadata=metadata)
        plt.close(figure)

    style_record = dict(RATIO_STYLE_PROVENANCE)
    style_record.update(
        {
            "renderer": "matplotlib",
            "matplotlib_version": matplotlib.__version__,
            "mplhep_version": mplhep.__version__,
        }
    )
    return {
        "style": style_record,
        "canvas_pixels": [canvas_width, canvas_height],
        "ratio_display_range": [low, high],
        "ratio_autorange": display,
        "dynamic_y_ticks": y_ticks,
        "y_axis_label": DATA_MC_Y_AXIS_LABEL,
        "run_label_policy": (
            "first/last and one centered label per up-to-90-run era segment; "
            "following-era boundary labels are staggered; all points retained"
        ),
        "selected_run_labels": [
            {"bin": index, "run": int(label)} for index, label in selected_labels
        ],
        "staggered_run_label_bins": staggered_label_bins,
        "category_annotation": _category_annotation(category),
        "legend_entries": labels,
        "era_spans": spans,
        "physical_period_spans": period_spans,
        "physical_period_lane": {
            "membership_source": "compiled nominal run_period rows",
            "label_policy": "single period letter; year/analysis era supplied by the era lane",
            "separator_extent_axes_fraction": [0.0, 0.06],
            "transparent_label_background": True,
        },
        "out_of_range": {
            "above": display["above"],
            "below": display["below"],
        },
        "invalid": display["invalid"],
        "visible_semantics": {
            "legend_mc_entry": "MC",
            "top_ticks": False,
            "right_ticks": False,
            "dynamic_y_ticks": y_ticks,
            "layout_audit": layout_audit,
        },
    }


def _render_chi2_vs_run(rows, output_dir, stem, category, observable):
    """Render one reduced-chi2 point per run with an approximate null band."""
    size = len(rows)
    display = chi2_display_summary(rows)
    low, high = display["range"]
    y_ticks = _dynamic_ratio_ticks(low, high)
    spans = _era_spans(rows)
    period_spans = _physical_period_spans(rows)
    selected_labels = _selected_run_labels(rows, spans)
    display_labels, staggered_label_bins = _staggered_run_labels(selected_labels, spans)
    render_dpi = 240
    canvas_width, canvas_height = 3000, 1560
    style = {
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 12.0,
        "axes.labelsize": 14.0,
        "axes.linewidth": 0.8,
        "axes.edgecolor": CHI2_STYLE["spine"],
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "xtick.labelsize": 10.0,
        "ytick.labelsize": 11.5,
        "legend.fontsize": 11.2,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
    with plt.style.context(mplhep.style.CMS), matplotlib.rc_context(style):
        figure, axis = plt.subplots(
            figsize=(canvas_width / render_dpi, canvas_height / render_dpi),
            dpi=render_dpi,
        )
        figure.subplots_adjust(left=0.060, right=0.995, bottom=0.125, top=0.982)
        x = np.arange(1, size + 1, dtype=float)

        for span_index, span in enumerate(spans):
            fill = CHI2_STYLE[
                "era_fill_even" if span_index % 2 == 0 else "era_fill_odd"
            ]
            axis.axvspan(
                span["first_bin"] - 0.5,
                span["last_bin"] + 0.5,
                color=fill,
                linewidth=0.0,
                zorder=0,
            )
            if span_index:
                axis.axvline(
                    span["first_bin"] - 0.5,
                    color=CHI2_STYLE["spine"],
                    linewidth=0.8,
                    linestyle=":",
                    zorder=2,
                )

        expected_low = np.full(size, np.nan, dtype=float)
        expected_high = np.full(size, np.nan, dtype=float)
        for index, row in enumerate(rows):
            if row["valid"] and int(row["ndf"]) > 0:
                sigma = math.sqrt(2.0 / int(row["ndf"]))
                expected_low[index] = max(0.0, 1.0 - sigma)
                expected_high[index] = 1.0 + sigma
        finite_band = np.isfinite(expected_low) & np.isfinite(expected_high)
        axis.fill_between(
            x,
            expected_low,
            expected_high,
            where=finite_band,
            interpolate=False,
            facecolor=CHI2_STYLE["expected_band"],
            edgecolor=CHI2_STYLE["expected_band_edge"],
            linewidth=0.65,
            alpha=0.28,
            zorder=3,
        )
        axis.axhline(
            1.0,
            color=CHI2_STYLE["reference"],
            linewidth=1.45,
            linestyle=(0, (6.0, 2.8)),
            zorder=4,
        )

        in_range = display["in_range"]
        if in_range:
            axis.scatter(
                [point["bin"] for point in in_range],
                [point["reduced_chi2"] for point in in_range],
                marker="o",
                s=9.0,
                facecolor=CHI2_STYLE["data"],
                edgecolor="white",
                linewidth=0.22,
                alpha=0.92,
                zorder=7,
            )
        boundary_offset = 0.018 * (high - low)
        outlier_options = {
            "s": 28.0,
            "facecolor": CHI2_STYLE["warning"],
            "edgecolor": CHI2_STYLE["data"],
            "linewidth": 0.35,
            "clip_on": False,
            "zorder": 12,
        }
        for direction, marker, ordinate in (
            ("above", "^", high - boundary_offset),
            ("below", "v", low + 2.0 * boundary_offset),
        ):
            points = display[direction]
            if points:
                axis.scatter(
                    [point["bin"] for point in points],
                    [ordinate] * len(points),
                    marker=marker,
                    **outlier_options,
                )
        if display["invalid"]:
            axis.scatter(
                [point["bin"] for point in display["invalid"]],
                [low + 3.8 * boundary_offset] * len(display["invalid"]),
                marker="x",
                s=28.0,
                color=CHI2_STYLE["warning"],
                linewidth=1.0,
                zorder=13,
            )

        axis.set_xlim(0.5, size + 0.5)
        axis.set_ylim(low, high)
        axis.set_ylabel(CHI2_Y_AXIS_LABEL)
        axis.set_xlabel(r"$\mathrm{Run\ number}$", labelpad=12.0)
        axis.set_xticks([index for index, _ in display_labels])
        tick_labels = axis.set_xticklabels(
            [label for _, label in display_labels], fontsize=10.0
        )
        if tick_labels:
            tick_labels[0].set_horizontalalignment("left")
            tick_labels[-1].set_horizontalalignment("right")
        axis.set_yticks(y_ticks)
        axis.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        axis.tick_params(axis="x", which="both", top=False)
        axis.tick_params(axis="y", which="both", right=False)
        axis.grid(
            axis="y",
            color=CHI2_STYLE["grid"],
            linewidth=0.55,
            linestyle=(0, (1.5, 2.4)),
            zorder=1,
        )
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

        for period_index, period_span in enumerate(period_spans):
            if period_index:
                axis.axvline(
                    period_span["first_bin"] - 0.5,
                    ymin=0.0,
                    ymax=0.06,
                    color=CHI2_STYLE["period_separator"],
                    linewidth=1.15,
                    solid_capstyle="butt",
                    zorder=14,
                )
            center = 0.5 * (period_span["first_bin"] + period_span["last_bin"])
            axis.text(
                center,
                low + 0.006 * (high - low),
                period_span["label"],
                ha="center",
                va="bottom",
                color=CHI2_STYLE["period_label"],
                fontsize=10.0,
                fontweight="semibold",
                zorder=14,
            )
        for span in spans:
            center = 0.5 * (span["first_bin"] + span["last_bin"])
            axis.text(
                center,
                high - 0.025 * (high - low),
                f"{span['era']}\n${span['recorded_lumi_fb']:.3g}"
                r"\,\mathrm{fb}^{-1}$",
                ha="center",
                va="top",
                color=CHI2_STYLE["spine"],
                fontsize=10.5,
                fontweight="semibold",
                linespacing=0.9,
                zorder=15,
            )

        category_text = (
            _category_annotation(category)
            + "\n"
            + f"Observable: {_observable_annotation(observable)}"
        )
        annotation_artist = axis.text(
            0.012,
            0.875,
            category_text,
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=11.8,
            linespacing=1.15,
            color=CHI2_STYLE["data"],
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": CHI2_STYLE["grid"],
                "linewidth": 0.65,
                "alpha": 0.95,
            },
            zorder=20,
        )

        handles = [
            Line2D(
                [],
                [],
                color=CHI2_STYLE["data"],
                marker="o",
                linestyle="none",
                markersize=4.0,
            ),
            _OverlayLegendTuple(
                (
                    Patch(
                        facecolor=CHI2_STYLE["expected_band"],
                        edgecolor=CHI2_STYLE["expected_band_edge"],
                        linewidth=0.65,
                        alpha=0.28,
                    ),
                    Line2D(
                        [],
                        [],
                        color=CHI2_STYLE["reference"],
                        linestyle=(0, (6.0, 2.8)),
                        linewidth=1.45,
                    ),
                )
            ),
        ]
        labels = ["Runs", CHI2_EXPECTATION_LEGEND_LABEL]
        if display["above"] or display["below"]:
            handles.append(
                _SideBySideLegendTuple(
                    (
                        Line2D(
                            [],
                            [],
                            color=CHI2_STYLE["warning"],
                            marker="^",
                            linestyle="none",
                            markersize=5.0,
                        ),
                        Line2D(
                            [],
                            [],
                            color=CHI2_STYLE["warning"],
                            marker="v",
                            linestyle="none",
                            markersize=5.0,
                        ),
                    )
                )
            )
            labels.append("Out of range")
        if display["invalid"]:
            handles.append(
                Line2D(
                    [],
                    [],
                    color=CHI2_STYLE["warning"],
                    marker="x",
                    linestyle="none",
                    markersize=5.2,
                )
            )
            labels.append("Invalid")
        legend_artist = axis.legend(
            handles=handles,
            labels=labels,
            loc="upper right",
            bbox_to_anchor=(0.992, 0.875),
            ncol=2,
            frameon=True,
            framealpha=1.0,
            facecolor="white",
            edgecolor=CHI2_STYLE["grid"],
            borderpad=0.55,
            handlelength=2.2,
            handletextpad=0.8,
            labelspacing=0.4,
            columnspacing=1.5,
            handler_map={
                _OverlayLegendTuple: HandlerTuple(ndivide=1, pad=0.0),
                _SideBySideLegendTuple: HandlerTuple(ndivide=None, pad=0.15),
            },
        )

        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        legend_bbox = legend_artist.get_window_extent(renderer=renderer)
        annotation_bbox = annotation_artist.get_window_extent(renderer=renderer)
        if legend_bbox.overlaps(annotation_bbox):
            plt.close(figure)
            raise RuntimeError(
                f"Reduced-chi2 legend and category annotation overlap for {category}"
            )
        figure_bbox = matplotlib.transforms.Bbox.from_bounds(
            0.0, 0.0, float(renderer.width), float(renderer.height)
        )
        out_of_range_tick_text_ids = set()
        for tick_axis, limits in (
            (axis.xaxis, axis.get_xlim()),
            (axis.yaxis, axis.get_ylim()),
        ):
            for tick in tick_axis.get_major_ticks() + tick_axis.get_minor_ticks():
                location = float(tick.get_loc())
                if not limits[0] - 1.0e-9 <= location <= limits[1] + 1.0e-9:
                    out_of_range_tick_text_ids.update(
                        (id(tick.label1), id(tick.label2))
                    )
        visible_text_artists = [
            artist
            for artist in figure.findobj(match=matplotlib.text.Text)
            if (
                artist.get_visible()
                and artist.get_text().strip()
                and id(artist) not in out_of_range_tick_text_ids
            )
        ]
        required_artists = [legend_artist, *visible_text_artists]
        clipped_required_artists = []
        artist_clearances = []
        for artist in required_artists:
            bbox = artist.get_window_extent(renderer=renderer)
            clearances = {
                "left": float(bbox.x0 - figure_bbox.x0),
                "right": float(figure_bbox.x1 - bbox.x1),
                "bottom": float(bbox.y0 - figure_bbox.y0),
                "top": float(figure_bbox.y1 - bbox.y1),
            }
            artist_clearances.append(clearances)
            if min(clearances.values()) < PERIOD_PLOT_CANVAS_INSET_PIXELS:
                clipped_required_artists.append(
                    {
                        "artist": type(artist).__name__,
                        "text": (
                            artist.get_text() if hasattr(artist, "get_text") else ""
                        ),
                        "bbox_pixels": [float(value) for value in bbox.extents],
                    }
                )
        if clipped_required_artists:
            plt.close(figure)
            raise RuntimeError(
                "Reduced-chi2 layout clips required artists: "
                f"{clipped_required_artists} for {category}"
            )
        minimum_edge_clearance = {
            edge: min(item[edge] for item in artist_clearances)
            for edge in ("left", "right", "bottom", "top")
        }
        layout_audit = {
            "legend_annotation_overlap": False,
            "clipped_required_artists": [],
            "canvas_inset_requirement_pixels": PERIOD_PLOT_CANVAS_INSET_PIXELS,
            "visible_text_artist_count": len(visible_text_artists),
            "minimum_edge_clearance_pixels": minimum_edge_clearance,
            "legend_bbox_pixels": [float(value) for value in legend_bbox.extents],
            "annotation_bbox_pixels": [
                float(value) for value in annotation_bbox.extents
            ],
        }

        png_path = output_dir / f"{stem}.png"
        pdf_path = output_dir / f"{stem}.pdf"
        metadata = {
            "Title": f"DY reduced chi-square run stability: {category}, {observable}",
            "Creator": "RunStability plot_run_stability.py",
        }
        figure.savefig(png_path, dpi=render_dpi, metadata=metadata)
        figure.savefig(pdf_path, metadata=metadata)
        plt.close(figure)

    style_record = dict(CHI2_STYLE_PROVENANCE)
    style_record.update(
        {
            "renderer": "matplotlib",
            "matplotlib_version": matplotlib.__version__,
            "mplhep_version": mplhep.__version__,
        }
    )
    return {
        "style": style_record,
        "canvas_pixels": [canvas_width, canvas_height],
        "display_range": display["range"],
        "autorange": display,
        "category_annotation": category_text,
        "legend_entries": labels,
        "visible_semantics": {
            "y_axis_label": CHI2_Y_AXIS_LABEL,
            "run_point_artist": "scatter_without_errorbars",
            "reference_line_y": 1.0,
            "expectation_legend_label": CHI2_EXPECTATION_LEGEND_LABEL,
            "legend_frame_alpha": 1.0,
            "top_ticks": False,
            "right_ticks": False,
            "dynamic_y_ticks": y_ticks,
            "layout_audit": layout_audit,
        },
        "era_spans": spans,
        "physical_period_spans": period_spans,
        "physical_period_lane": {
            "membership_source": "compiled nominal run_period rows",
            "label_policy": "single period letter; year/analysis era supplied by the era lane",
            "separator_extent_axes_fraction": [0.0, 0.06],
            "transparent_label_background": True,
        },
        "selected_run_labels": [
            {"bin": index, "run": int(label)} for index, label in selected_labels
        ],
        "staggered_run_label_bins": staggered_label_bins,
        "out_of_range": {
            "above": display["above"],
            "below": display["below"],
        },
        "invalid": display["invalid"],
    }


def _get(handle, path, class_name=None):
    obj = handle.Get(path)
    if not obj:
        raise RuntimeError(f"Missing ROOT object {path}")
    if class_name and not obj.InheritsFrom(class_name):
        raise RuntimeError(
            f"ROOT object {path} has class {obj.ClassName()}, expected {class_name}"
        )
    return obj


def _plot_metadata(config):
    wrapper = config.get("plot", {})
    if not isinstance(wrapper, dict):
        raise RuntimeError("Compiled plot metadata is malformed")
    return wrapper.get("plot", {}), wrapper.get("groupPlot", {})


def mc_processes(config):
    plots, _ = _plot_metadata(config)
    return tuple(
        name for name, definition in plots.items() if not definition.get("isData", 0)
    )


def _contract_luminosity_sources(contract):
    sources = contract.get("luminosity_sources")
    if sources:
        return sources
    return {
        "nominal": {"rows": contract["nominal"], "label": "Nominal recorded"},
        "trigger_any": {
            "rows": contract["trigger_any"],
            "label": "Trigger-Any effective recorded",
        },
    }


def resolve_luminosity_source(datasets, category, requested):
    if requested == "auto":
        resolved = set()
        for dataset in datasets:
            contract = dataset["contract"]
            mappings = contract.get("category_luminosity_sources", {})
            if category in mappings:
                resolved.add(mappings[category])
            elif int(contract.get("schema_version", 1)) >= 3:
                raise RuntimeError(
                    f"Schema-3 category {category!r} has no compiled luminosity "
                    "source mapping"
                )
            else:
                resolved.add("trigger_any")
        if len(resolved) != 1:
            raise RuntimeError(
                f"Category {category!r} resolves inconsistent luminosity sources "
                f"across eras: {sorted(resolved)}"
            )
        requested = resolved.pop()
    missing = [
        dataset["contract"]["analysis_era"]
        for dataset in datasets
        if requested not in dataset["luminosities"]
    ]
    if missing:
        raise ValueError(
            f"Luminosity source {requested!r} is unavailable in eras {missing}"
        )
    return requested


def validate_dataset(config_path, input_path, luminosity_source=None):
    config_path, config = load_compiled_config(config_path)
    contract = config["RUN_STABILITY_CONTRACT"]
    root_file = open_root(input_path)
    try:
        categories = tuple(contract.get("categories", ()))
        observables = tuple(contract.get("observables", ()))
        runs = tuple(int(run) for run in contract.get("ordered_runs", ()))
        if not categories or not observables or not runs:
            raise RuntimeError("Compiled run-stability matrix is empty")
        expected_paths = len(categories) * len(observables)
        if len(contract.get("auxiliary_output_paths", ())) != expected_paths:
            raise RuntimeError("Compiled auxiliary path inventory is inconsistent")

        for category in categories:
            for observable in observables:
                data = _get(
                    root_file,
                    f"run_stability/{category}/{observable}/histo_DATA",
                    "TH2",
                )
                if data.GetNbinsX() != len(runs):
                    raise RuntimeError(
                        f"{category}/{observable} has {data.GetNbinsX()} run bins; "
                        f"expected {len(runs)}"
                    )
                labels = tuple(
                    data.GetXaxis().GetBinLabel(index)
                    for index in range(1, len(runs) + 1)
                )
                if labels != tuple(map(str, runs)):
                    raise RuntimeError(
                        f"{category}/{observable} run-axis labels diverge from config"
                    )
                for xbin in (0, data.GetNbinsX() + 1):
                    for ybin in range(0, data.GetNbinsY() + 2):
                        if data.GetBinContent(xbin, ybin) != 0.0:
                            raise RuntimeError(
                                f"{category}/{observable} has nonempty run-axis flow"
                            )

        lumi_rows = {}
        run_periods = {}
        source_definitions = _contract_luminosity_sources(contract)
        reference_run_periods = None
        for source, source_definition in source_definitions.items():
            rows = source_definition["rows"]
            if len(rows) != len(runs):
                raise RuntimeError(
                    f"Compiled luminosity source {source} has {len(rows)} rows; "
                    f"expected {len(runs)}"
                )
            source_values = {}
            source_run_periods = tuple(str(row.get("run_period", "")) for row in rows)
            for label in source_run_periods:
                physical_run_period(label)
            if reference_run_periods is None:
                reference_run_periods = source_run_periods
            elif source_run_periods != reference_run_periods:
                raise RuntimeError(
                    f"Compiled luminosity source {source} has run-period membership "
                    "that diverges from the other sources"
                )
            for quantity, field in (
                ("delivered", "delivered_fb"),
                ("recorded", "recorded_fb"),
            ):
                path = f"run_stability/metadata/{source}_{quantity}_lumi_fb"
                hist = _get(root_file, path, "TH1")
                if hist.GetNbinsX() != len(runs):
                    raise RuntimeError(f"{path} run-bin count diverges")
                values = []
                for index, (run, row) in enumerate(zip(runs, rows), 1):
                    if int(row["run"]) != int(run):
                        raise RuntimeError(
                            f"Compiled luminosity source {source} row {index} is "
                            f"for run {row['run']}; expected {run}"
                        )
                    if hist.GetXaxis().GetBinLabel(index) != str(run):
                        raise RuntimeError(f"{path} run label diverges at bin {index}")
                    observed = float(hist.GetBinContent(index))
                    expected = float(row[field])
                    if not math.isclose(observed, expected, rel_tol=0.0, abs_tol=5e-12):
                        raise RuntimeError(
                            f"{path} luminosity diverges for run {run}: "
                            f"ROOT={observed}, config={expected}"
                        )
                    values.append(observed)
                source_values[quantity] = tuple(values)
            lumi_rows[source] = source_values["recorded"]
            run_periods[source] = source_run_periods

        source_hist = _get(root_file, "run_stability/metadata/mc_source_lumi_fb", "TH1")
        mc_source_lumi = float(source_hist.GetBinContent(1))
        expected_source = float(contract["mc_source_lumi_fb"])
        if not math.isclose(
            mc_source_lumi, expected_source, rel_tol=0.0, abs_tol=5e-12
        ):
            raise RuntimeError(
                f"MC source luminosity diverges: ROOT={mc_source_lumi}, "
                f"config={expected_source}"
            )
        if mc_source_lumi <= 0.0:
            raise RuntimeError("MC source luminosity must be positive")

        if (
            luminosity_source not in (None, "auto")
            and luminosity_source not in lumi_rows
        ):
            raise ValueError(
                f"luminosity_source must be one of {sorted(lumi_rows)} or auto"
            )
        processes = mc_processes(config)
        if not processes:
            raise RuntimeError("Compiled configuration has no prompt MC processes")
        missing_mc = []
        for category in categories:
            for observable in observables:
                for process in processes:
                    path = f"{category}/{observable}/histo_{process}"
                    if not root_file.Get(path):
                        missing_mc.append(path)
        if missing_mc:
            preview = ", ".join(missing_mc[:5])
            raise RuntimeError(
                f"Missing {len(missing_mc)} ordinary prompt-MC histograms; "
                f"first: {preview}"
            )
        return {
            "config_path": config_path,
            "config": config,
            "contract": contract,
            "input_path": str(input_path),
            "runs": runs,
            "luminosities": lumi_rows,
            "run_periods": run_periods,
            "mc_source_lumi_fb": mc_source_lumi,
            "processes": processes,
        }
    finally:
        root_file.Close()


def _mc_histograms(handle, dataset, category, observable):
    plots, groups = _plot_metadata(dataset["config"])
    process_hists = {}
    for process in dataset["processes"]:
        hist = _get(handle, f"{category}/{observable}/histo_{process}", "TH1").Clone()
        hist.SetDirectory(0)
        hist.Scale(float(plots[process].get("scale", 1.0)))
        process_hists[process] = hist

    grouped = []
    assigned = set()
    for name, definition in groups.items():
        members = [
            item for item in definition.get("samples", ()) if item in process_hists
        ]
        if not members:
            continue
        hist = process_hists[members[0]].Clone(f"group_{name}")
        hist.Reset("ICES")
        for member in members:
            hist.Add(process_hists[member])
            assigned.add(member)
        hist.SetDirectory(0)
        grouped.append((name, definition, hist))
    for process, hist in process_hists.items():
        if process not in assigned:
            grouped.append((process, plots[process], hist.Clone(f"group_{process}")))
    total = next(iter(process_hists.values())).Clone("total_prompt_mc")
    total.Reset("ICES")
    for hist in process_hists.values():
        total.Add(hist)
    total.SetDirectory(0)
    return process_hists, grouped, total


def _sum_visible(hist):
    total = sum(hist.GetBinContent(index) for index in range(1, hist.GetNbinsX() + 1))
    variance = sum(
        hist.GetBinError(index) ** 2 for index in range(1, hist.GetNbinsX() + 1)
    )
    return float(total), float(variance)


def _sum_process_histograms(process_hists, members, name):
    """Sum already scaled process histograms without losing their Sumw2."""
    members = tuple(members)
    if not members:
        raise RuntimeError(f"Period MC group {name!r} has no processes")
    histogram = process_hists[members[0]].Clone(name)
    histogram.Reset("ICES")
    for member in members:
        histogram.Add(process_hists[member])
    histogram.SetDirectory(0)
    return histogram


def _period_mc_groups(dataset, process_hists):
    """Build the exact two-group period presentation from compiled metadata."""
    plots, configured_groups = _plot_metadata(dataset["config"])
    active = tuple(process_hists)
    active_set = set(active)
    if set(mc_processes(dataset["config"])) != active_set:
        raise RuntimeError(
            "Compiled non-DATA plot inventory diverges from the loaded MC processes"
        )

    memberships = {}
    for group_name, definition in configured_groups.items():
        for process in definition.get("samples", ()):
            if process not in active_set:
                raise RuntimeError(
                    f"Compiled group {group_name!r} names inactive process {process!r}"
                )
            memberships.setdefault(process, []).append(group_name)
    duplicates = {
        process: groups for process, groups in memberships.items() if len(groups) != 1
    }
    if duplicates:
        raise RuntimeError(
            "Compiled MC process classification is ambiguous across plot groups: "
            f"{duplicates}"
        )

    dy_definition = configured_groups.get("DY")
    if not isinstance(dy_definition, dict):
        raise RuntimeError(
            "Period plots require one exact compiled groupPlot['DY'] definition"
        )
    dy_processes = tuple(dy_definition.get("samples", ()))
    if not dy_processes or len(set(dy_processes)) != len(dy_processes):
        raise RuntimeError(
            "Compiled groupPlot['DY'] must contain a nonempty unique process list"
        )
    if set(dy_processes) - active_set:
        raise RuntimeError(
            "Compiled groupPlot['DY'] contains a process outside the active MC inventory"
        )
    others_processes = tuple(
        process for process in active if process not in dy_processes
    )
    if not others_processes:
        raise RuntimeError(
            "Period plots require at least one non-DY MC process for the Others group"
        )
    if (
        set(dy_processes) & set(others_processes)
        or (set(dy_processes) | set(others_processes)) != active_set
    ):
        raise RuntimeError("DY/Others period MC classification does not partition MC")

    process_scales = {}
    for process in active:
        try:
            scale = float(plots[process].get("scale", 1.0))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"Compiled plot scale for MC process {process!r} is not numeric"
            ) from exc
        if not math.isfinite(scale) or scale < 0.0:
            raise RuntimeError(
                f"Compiled plot scale for MC process {process!r} is invalid: {scale}"
            )
        process_scales[process] = scale

    groups = [
        (
            "DY",
            {
                "nameHR": "DY",
                "color": dy_definition.get("color", ROOT.kGreen + 2),
            },
            _sum_process_histograms(process_hists, dy_processes, "group_DY"),
        ),
        (
            "Others",
            {"nameHR": "Others", "color": ROOT.kGray + 1},
            _sum_process_histograms(process_hists, others_processes, "group_Others"),
        ),
    ]
    classification = {
        "schema_version": 1,
        "source": "compiled plot.groupPlot['DY'].samples; Others is its complement in the compiled non-DATA plot inventory",
        "groups": {
            "DY": list(dy_processes),
            "Others": list(others_processes),
        },
        "process_scales_before_aggregation": process_scales,
        "sumw2_policy": "scale each process variance by scale^2 before independent-process aggregation",
    }
    return groups, classification


def _robust_upper_cut(values, *, minimum):
    values = np.asarray(
        [value for value in values if math.isfinite(value)], dtype=float
    )
    if not len(values):
        return float(minimum)
    if len(values) < 4:
        return max(float(minimum), float(np.max(values)))
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    return max(float(minimum), median + 4.0 * 1.4826 * mad)


def period_ratio_autorange(rows):
    """Choose a robust period-ratio range and inventory every clipped feature."""
    valid_rows = [
        row
        for row in rows
        if row.get("valid")
        and row.get("ratio") is not None
        and math.isfinite(float(row["ratio"]))
    ]
    if not valid_rows:
        raise RuntimeError("Period ratio autoranging has no finite valid DATA/MC bins")

    minimum_informative_bins = 3
    maximum_data_relative_halfwidth = 0.55
    maximum_mc_relative_band = 0.35
    fallback_range = (0.60, 1.40)
    maximum_mc_range_influence = 0.40

    selection_inputs = []
    informative_rows = []
    for row in rows:
        diagnostic = {
            "bin": int(row["bin"]),
            "valid": bool(row.get("valid")),
            "informative": False,
            "reason_codes": [],
        }
        if row not in valid_rows:
            diagnostic["reason_codes"].append("invalid_ratio")
            selection_inputs.append(diagnostic)
            continue
        data_yield = float(row["data_yield"])
        data_relative = max(
            float(row["data_error_low"]), float(row["data_error_high"])
        ) / max(data_yield, 1.0)
        mc_relative = float(row["mc_stat_uncertainty"]) / float(row["mc_yield"])
        diagnostic.update(
            {
                "ratio": float(row["ratio"]),
                "data_yield": data_yield,
                "data_relative_halfwidth": data_relative,
                "mc_relative_band": mc_relative,
            }
        )
        if data_yield <= 0.0:
            diagnostic["reason_codes"].append("nonpositive_data_count")
        if data_relative > maximum_data_relative_halfwidth:
            diagnostic["reason_codes"].append("data_poisson_precision")
        if mc_relative > maximum_mc_relative_band:
            diagnostic["reason_codes"].append("mc_stat_precision")
        if not diagnostic["reason_codes"]:
            diagnostic["informative"] = True
            informative_rows.append(row)
        selection_inputs.append(diagnostic)

    informative_ratios = [float(row["ratio"]) for row in informative_rows]
    median = float(np.median(informative_ratios)) if informative_ratios else None
    mad = (
        float(np.median(np.abs(np.asarray(informative_ratios, dtype=float) - median)))
        if median is not None
        else None
    )
    if len(informative_rows) >= minimum_informative_bins:
        central_cut = max(0.20, 4.0 * 1.4826 * mad)
        core_rows = [
            row
            for row in informative_rows
            if abs(float(row["ratio"]) - median) <= central_cut
        ]
        if len(core_rows) < minimum_informative_bins:
            core_rows = sorted(
                informative_rows,
                key=lambda row: abs(float(row["ratio"]) - median),
            )[:minimum_informative_bins]
        range_mode = "informative_median_mad_core"
    else:
        central_cut = None
        core_rows = []
        range_mode = "unity_baseline_sparse_fallback"

    data_error_cut = _robust_upper_cut(
        [
            max(float(row["ratio_error_low"]), float(row["ratio_error_high"]))
            for row in core_rows
        ],
        minimum=0.20,
    )
    mc_input_rows = core_rows or informative_rows or valid_rows
    mc_relative_cut = min(
        _robust_upper_cut(
            [
                float(row["mc_stat_uncertainty"]) / float(row["mc_yield"])
                for row in mc_input_rows
                if float(row["mc_yield"]) > 0.0
            ],
            minimum=0.08,
        ),
        maximum_mc_range_influence,
    )

    candidates = [1.0, 1.0 - mc_relative_cut, 1.0 + mc_relative_cut]
    if range_mode == "unity_baseline_sparse_fallback":
        candidates.extend(fallback_range)
    else:
        for row in core_rows:
            ratio = float(row["ratio"])
            candidates.extend(
                (
                    ratio,
                    ratio - min(float(row["ratio_error_low"]), data_error_cut),
                    ratio + min(float(row["ratio_error_high"]), data_error_cut),
                )
            )
    raw_low = min(candidates)
    raw_high = max(candidates)
    span = max(raw_high - raw_low, 0.4)
    midpoint = 0.5 * (raw_low + raw_high)
    low = min(raw_low, midpoint - 0.5 * span)
    high = max(raw_high, midpoint + 0.5 * span)
    padding = max(0.04, 0.10 * (high - low))
    low = max(0.0, low - padding)
    high += padding
    if high - low < 0.4:
        center = 0.5 * (low + high)
        low = max(0.0, center - 0.2)
        high = low + 0.4

    clipped = {
        "data_central_below": [],
        "data_central_above": [],
        "data_interval_below": [],
        "data_interval_above": [],
        "mc_band_below": [],
        "mc_band_above": [],
    }
    for row in valid_rows:
        index = int(row["bin"])
        ratio = float(row["ratio"])
        if ratio < low:
            clipped["data_central_below"].append(index)
        elif ratio > high:
            clipped["data_central_above"].append(index)
        if ratio - float(row["ratio_error_low"]) < low:
            clipped["data_interval_below"].append(index)
        if ratio + float(row["ratio_error_high"]) > high:
            clipped["data_interval_above"].append(index)
        relative = float(row["mc_stat_uncertainty"]) / float(row["mc_yield"])
        if 1.0 - relative < low:
            clipped["mc_band_below"].append(index)
        if 1.0 + relative > high:
            clipped["mc_band_above"].append(index)

    return {
        "range": [float(low), float(high)],
        "policy": {
            "name": "uncertainty_aware_period_ratio_intervals_v2",
            "minimum_span": 0.4,
            "padding_fraction": 0.10,
            "minimum_padding": 0.04,
            "range_mode": range_mode,
            "minimum_informative_bins": minimum_informative_bins,
            "maximum_data_relative_halfwidth": maximum_data_relative_halfwidth,
            "maximum_mc_relative_band": maximum_mc_relative_band,
            "fallback_range": list(fallback_range),
            "maximum_mc_range_influence": maximum_mc_range_influence,
            "informative_bins": [int(row["bin"]) for row in informative_rows],
            "range_central_input_bins": [int(row["bin"]) for row in core_rows],
            "excluded_uninformative_bins": [
                item["bin"]
                for item in selection_inputs
                if item["valid"] and not item["informative"]
            ],
            "excluded_insufficient_population_bins": (
                [int(row["bin"]) for row in informative_rows]
                if range_mode == "unity_baseline_sparse_fallback"
                else []
            ),
            "central_outlier_bins": [
                int(row["bin"]) for row in informative_rows if row not in core_rows
            ],
            "selection_inputs": selection_inputs,
            "informative_ratio_median": median,
            "informative_ratio_mad": mad,
            "central_cut": central_cut,
            "data_interval_cap": float(data_error_cut),
            "mc_relative_band_cap": float(mc_relative_cut),
            "mc_band_input_bins": [int(row["bin"]) for row in mc_input_rows],
            "anchors": [1.0],
            "style_provenance": PERIOD_RATIO_STYLE_PROVENANCE,
        },
        "clipped_bins": clipped,
    }


def _dataset_identity(dataset):
    input_path = dataset["input_path"]
    return {
        "analysis_era": dataset["contract"]["analysis_era"],
        "tag": dataset["config"].get("tag"),
        "config_path": str(dataset["config_path"]),
        "config_sha256": sha256(dataset["config_path"]),
        "input_path": input_path,
        "input_sha256": sha256(input_path),
        "luminosity_inputs": dataset["contract"].get("inputs", {}),
    }


def make_run_plot(dataset, category, observable, run, luminosity_source, output_dir):
    contract = dataset["contract"]
    if category not in contract["categories"]:
        raise ValueError(f"Unknown category {category!r}")
    if observable not in contract["observables"]:
        raise ValueError(f"Unknown observable {observable!r}")
    try:
        run_index = dataset["runs"].index(int(run))
    except ValueError as exc:
        raise ValueError(f"Run {run} is not in the audited run map") from exc
    luminosity = dataset["luminosities"][luminosity_source][run_index]
    if luminosity <= 0.0:
        raise RuntimeError(
            f"Run {run} has zero {luminosity_source} recorded luminosity; "
            "no fallback luminosity is permitted"
        )
    scale = luminosity / dataset["mc_source_lumi_fb"]
    handle = open_root(dataset["input_path"])
    try:
        data2d = _get(
            handle,
            f"run_stability/{category}/{observable}/histo_DATA",
            "TH2",
        )
        data = data2d.ProjectionY(
            f"data_{category}_{observable}_{run}", run_index + 1, run_index + 1, "e"
        )
        data.SetDirectory(0)
        _, groups, mc_total = _mc_histograms(handle, dataset, category, observable)
    finally:
        handle.Close()
    for _, _, hist in groups:
        hist.Scale(scale)
    mc_total.Scale(scale)

    n_bins = data.GetNbinsX()
    graph = ROOT.TGraphAsymmErrors(n_bins)
    invalid_bins = []
    for index in range(1, n_bins + 1):
        d = float(data.GetBinContent(index))
        data_variance = float(data.GetBinError(index) ** 2)
        if abs(data_variance - d) > 1.0e-5 * max(1.0, d):
            raise RuntimeError(
                f"Run {run} observable bin {index} DATA is not a binary-weight "
                f"Poisson count: sumw={d}, sumw2={data_variance}"
            )
        m = float(mc_total.GetBinContent(index))
        result = ratio_with_uncertainty(d, m)
        x = data.GetXaxis().GetBinCenter(index)
        ex = data.GetXaxis().GetBinWidth(index) / 2.0
        if result is None:
            invalid_bins.append(index)
            graph.SetPoint(index - 1, x, float("nan"))
            graph.SetPointError(index - 1, ex, ex, 0.0, 0.0)
        else:
            graph.SetPoint(index - 1, x, result["value"])
            graph.SetPointError(
                index - 1, ex, ex, result["error_low"], result["error_high"]
            )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{contract['analysis_era']}_{category}_{observable}_run{run}_{luminosity_source}"
    canvas = ROOT.TCanvas("canvas", "canvas", 900, 850)
    upper = ROOT.TPad("upper", "upper", 0.0, 0.30, 1.0, 1.0)
    lower = ROOT.TPad("lower", "lower", 0.0, 0.0, 1.0, 0.30)
    upper.SetBottomMargin(0.02)
    lower.SetTopMargin(0.03)
    lower.SetBottomMargin(0.32)
    upper.Draw()
    lower.Draw()
    upper.cd()
    stack = ROOT.THStack("mc_stack", "")
    legend = ROOT.TLegend(0.62, 0.48, 0.90, 0.88)
    for name, definition, hist in groups:
        hist.SetFillColor(int(definition.get("color", ROOT.kGray)))
        hist.SetLineColor(ROOT.kBlack)
        stack.Add(hist)
        legend.AddEntry(hist, str(definition.get("nameHR", name)), "f")
    stack.Draw("hist")
    stack.GetYaxis().SetTitle("Events")
    stack.GetXaxis().SetLabelSize(0)
    data.SetMarkerStyle(20)
    data.SetLineColor(ROOT.kBlack)
    maximum = max(stack.GetMaximum(), data.GetMaximum())
    stack.SetMaximum(maximum * 1.55 if maximum > 0.0 else 1.0)
    data.Draw("E1 same")
    legend.AddEntry(data, "Data", "lep")
    legend.Draw()
    label = ROOT.TLatex()
    label.SetNDC(True)
    label.SetTextSize(0.035)
    label.DrawLatex(0.14, 0.93, "CMS Preliminary")
    label.DrawLatex(
        0.55,
        0.93,
        f"Run {run}, {luminosity * 1000.0:.3g} pb^{{-1}} ({luminosity_source})",
    )
    lower.cd()
    frame = mc_total.Clone("ratio_frame")
    frame.Reset("ICES")
    frame.SetMinimum(0.0)
    frame.SetMaximum(2.0)
    frame.GetYaxis().SetTitle("Data/MC")
    frame.GetXaxis().SetTitle(data.GetXaxis().GetTitle())
    frame.GetYaxis().SetNdivisions(505)
    frame.GetYaxis().SetTitleSize(0.10)
    frame.GetYaxis().SetLabelSize(0.08)
    frame.GetXaxis().SetTitleSize(0.12)
    frame.GetXaxis().SetLabelSize(0.10)
    frame.Draw("axis")
    graph.SetMarkerStyle(20)
    graph.Draw("P same")
    line = ROOT.TLine(frame.GetXaxis().GetXmin(), 1.0, frame.GetXaxis().GetXmax(), 1.0)
    line.SetLineStyle(2)
    line.Draw()
    canvas.SaveAs(str(output_dir / f"{stem}.png"))
    canvas.SaveAs(str(output_dir / f"{stem}.pdf"))
    output_paths = {
        "png": output_dir / f"{stem}.png",
        "pdf": output_dir / f"{stem}.pdf",
    }
    receipt = {
        "schema_version": 1,
        "kind": "run_observable_data_mc",
        "dataset": _dataset_identity(dataset),
        "category": category,
        "observable": observable,
        "run": int(run),
        "luminosity_source": luminosity_source,
        "recorded_lumi_fb": luminosity,
        "mc_source_lumi_fb": dataset["mc_source_lumi_fb"],
        "mc_scale": scale,
        "mc_processes": list(dataset["processes"]),
        "invalid_zero_mc_bins": invalid_bins,
        "outputs": {name: str(path) for name, path in output_paths.items()},
        "output_sha256": {name: sha256(path) for name, path in output_paths.items()},
    }
    (output_dir / f"{stem}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def _matplotlib_color(root_color):
    color = ROOT.gROOT.GetColor(int(root_color))
    if not color:
        return "#8A9096"
    return tuple(
        float(value) for value in (color.GetRed(), color.GetGreen(), color.GetBlue())
    )


def _matplotlib_label(label):
    """Translate the small ROOT-TLatex subset used by plot.py legends."""
    label = str(label)
    label = label.replace("#gamma^{*}", r"$\gamma^{*}$")
    label = label.replace("#gamma", r"$\gamma$")
    label = label.replace("#rightarrow", r"$\rightarrow$")
    return label


def _matplotlib_axis_title(title):
    """Translate focused ROOT TLatex and put the expression in math mode."""
    title = str(title or "Observable")
    title = title.replace("#it{l}", r"\mathit{l}")
    title = title.replace("#eta", r"\eta")
    match = re.fullmatch(r"(.+?)\s*(\[[^]]+\])", title)
    if match:
        return f"${match.group(1).strip()}$ {match.group(2)}"
    if any(token in title for token in ("_", "^", "{")):
        return f"${title}$"
    return title


def _visible_histogram_moments(histogram):
    """Visible-bin Sumw and Sumw2 for one plotted histogram."""
    bins = range(1, histogram.GetNbinsX() + 1)
    return {
        "yield": math.fsum(float(histogram.GetBinContent(index)) for index in bins),
        "variance": math.fsum(
            float(histogram.GetBinError(index)) ** 2 for index in bins
        ),
    }


def _yield_label_number(value, decimals):
    """Compact fixed-point number safe inside Matplotlib mathtext."""
    value = float(value)
    if not math.isfinite(value):
        raise RuntimeError(f"Legend yield value is not finite: {value!r}")
    rendered = f"{value:,.{int(decimals)}f}"
    return rendered.replace(",", r"{,}")


def _uncertainty_decimals(*uncertainties):
    finite = [abs(float(value)) for value in uncertainties if float(value) > 0.0]
    if not finite:
        return 2
    exponent = math.floor(math.log10(max(finite)))
    return max(0, min(4, 1 - exponent))


def _period_yield_legend(data, groups, mc_total):
    """Build exact visible-bin yield values and concise two-line labels."""
    data_moments = _visible_histogram_moments(data)
    nearest = round(data_moments["yield"])
    if (
        data_moments["yield"] < 0.0
        or abs(data_moments["yield"] - nearest)
        > 1.0e-6 * max(1.0, data_moments["yield"])
        or not math.isclose(
            data_moments["variance"],
            data_moments["yield"],
            rel_tol=1.0e-6,
            abs_tol=1.0e-6,
        )
    ):
        raise RuntimeError(
            "Visible DATA legend total is not a binary-weight Poisson count: "
            f"sumw={data_moments['yield']}, sumw2={data_moments['variance']}"
        )
    data_low, data_high = garwood_interval(nearest)
    data_error_low = data_moments["yield"] - data_low
    data_error_high = data_high - data_moments["yield"]
    data_decimals = _uncertainty_decimals(data_error_low, data_error_high)
    data_label = (
        "Data\n$"
        f"{_yield_label_number(nearest, 0)}"
        f"^{{+{_yield_label_number(data_error_high, data_decimals)}}}"
        f"_{{-{_yield_label_number(data_error_low, data_decimals)}}}$"
    )

    entries = [
        {
            "name": "Data",
            "label": data_label,
            "yield": data_moments["yield"],
            "variance": data_moments["variance"],
            "uncertainty_kind": "Garwood Poisson 68.268949%",
            "uncertainty_low": data_error_low,
            "uncertainty_high": data_error_high,
            "display_decimals": data_decimals,
        }
    ]
    group_moments = {}
    for name, _, histogram in groups:
        moments = _visible_histogram_moments(histogram)
        uncertainty = math.sqrt(max(0.0, moments["variance"]))
        decimals = _uncertainty_decimals(uncertainty)
        label = (
            f"{name}\n${_yield_label_number(moments['yield'], decimals)}"
            rf"\pm{_yield_label_number(uncertainty, decimals)}$"
        )
        group_moments[name] = moments
        entries.append(
            {
                "name": name,
                "label": label,
                **moments,
                "uncertainty_kind": "sqrt(visible Sumw2)",
                "uncertainty": uncertainty,
                "display_decimals": decimals,
            }
        )

    mc_moments = _visible_histogram_moments(mc_total)
    mc_uncertainty = math.sqrt(max(0.0, mc_moments["variance"]))
    mc_decimals = _uncertainty_decimals(mc_uncertainty)
    mc_label = (
        f"Total MC\n${_yield_label_number(mc_moments['yield'], mc_decimals)}"
        rf"\pm{_yield_label_number(mc_uncertainty, mc_decimals)}$"
    )
    entries.append(
        {
            "name": "Total MC",
            "label": mc_label,
            **mc_moments,
            "uncertainty_kind": "sqrt(visible Sumw2)",
            "uncertainty": mc_uncertainty,
            "display_decimals": mc_decimals,
        }
    )
    group_yield = math.fsum(item["yield"] for item in group_moments.values())
    group_variance = math.fsum(item["variance"] for item in group_moments.values())
    if not math.isclose(group_yield, mc_moments["yield"], rel_tol=1e-10, abs_tol=1e-10):
        raise RuntimeError("Visible DY/Others legend yields do not close to total MC")
    if not math.isclose(
        group_variance, mc_moments["variance"], rel_tol=1e-10, abs_tol=1e-10
    ):
        raise RuntimeError("Visible DY/Others legend Sumw2 does not close to total MC")
    return {
        "format_policy": (
            "two lines per entry without an N= prefix; exact integer DATA yield; "
            "adaptive fixed-point "
            "precision from visible statistical uncertainty; mathtext thousands "
            "separators"
        ),
        "entries": entries,
        "closure": {
            "group_yield_minus_mc": group_yield - mc_moments["yield"],
            "group_variance_minus_mc": group_variance - mc_moments["variance"],
        },
    }


def _period_histograms(dataset, category, observable, period, luminosity_source):
    inventories = {
        entry["period"]: entry for entry in period_inventory(dataset, luminosity_source)
    }
    if period not in inventories:
        raise ValueError(
            f"Physical run period {period!r} is unavailable; "
            f"choose one of {list(inventories)}"
        )
    selected = inventories[period]
    run_indices = selected["run_indices"]
    luminosity = math.fsum(
        dataset["luminosities"][luminosity_source][index] for index in run_indices
    )
    if luminosity <= 0.0:
        raise RuntimeError(
            f"Period {period} has nonpositive {luminosity_source} recorded "
            "luminosity; no fallback luminosity is permitted"
        )
    scale = luminosity / dataset["mc_source_lumi_fb"]

    handle = open_root(dataset["input_path"])
    try:
        data2d = _get(
            handle,
            f"run_stability/{category}/{observable}/histo_DATA",
            "TH2",
        )
        data = data2d.ProjectionY(
            f"data_{period}_{category}_{observable}",
            run_indices[0] + 1,
            run_indices[0] + 1,
            "e",
        )
        data.SetDirectory(0)
        for run_index in run_indices[1:]:
            contribution = data2d.ProjectionY(
                f"data_{period}_{category}_{observable}_{run_index}",
                run_index + 1,
                run_index + 1,
                "e",
            )
            contribution.SetDirectory(0)
            data.Add(contribution)
        process_hists, _, mc_total = _mc_histograms(
            handle, dataset, category, observable
        )
    finally:
        handle.Close()

    groups, classification = _period_mc_groups(dataset, process_hists)
    for hist in process_hists.values():
        hist.Scale(scale)
    for _, _, hist in groups:
        hist.Scale(scale)
    mc_total.Scale(scale)
    total_yield, total_variance = _sum_visible(mc_total)
    if total_yield <= 0.0:
        raise RuntimeError(
            f"Period {period}, category {category} has nonpositive total prompt-MC "
            "yield"
        )

    for index in range(1, data.GetNbinsX() + 1):
        count = float(data.GetBinContent(index))
        variance = float(data.GetBinError(index) ** 2)
        nearest = round(count)
        if (
            count < 0.0
            or abs(count - nearest) > 1.0e-6 * max(1.0, abs(count))
            or abs(variance - count) > 1.0e-5 * max(1.0, count)
        ):
            raise RuntimeError(
                f"Period {period} observable bin {index} DATA is not a "
                f"binary-weight Poisson count: sumw={count}, sumw2={variance}"
            )

    for index in range(1, mc_total.GetNbinsX() + 1):
        grouped = math.fsum(hist.GetBinContent(index) for _, _, hist in groups)
        total = float(mc_total.GetBinContent(index))
        if not math.isclose(grouped, total, rel_tol=1.0e-10, abs_tol=1.0e-10):
            raise RuntimeError(
                f"Period {period} MC presentation groups do not close to the "
                f"prompt-MC total in bin {index}: groups={grouped}, total={total}"
            )
    return (
        selected,
        luminosity,
        scale,
        data,
        groups,
        mc_total,
        total_yield,
        total_variance,
        classification,
    )


def _render_period_plot(
    data,
    groups,
    mc_total,
    rows,
    output_dir,
    stem,
    period,
    category,
    luminosity_fb,
):
    ratio_display = period_ratio_autorange(rows)
    ratio_low_limit, ratio_high_limit = ratio_display["range"]
    clipped_bins = ratio_display["clipped_bins"]
    edges = np.array(
        [data.GetXaxis().GetBinLowEdge(1)]
        + [
            data.GetXaxis().GetBinUpEdge(index)
            for index in range(1, data.GetNbinsX() + 1)
        ],
        dtype=float,
    )
    centers = 0.5 * (edges[:-1] + edges[1:])
    axis_title = _matplotlib_axis_title(data.GetXaxis().GetTitle())
    yield_legend = _period_yield_legend(data, groups, mc_total)
    yield_labels = {entry["name"]: entry["label"] for entry in yield_legend["entries"]}
    with (
        plt.style.context(mplhep.style.CMS),
        matplotlib.rc_context(
            {
                "font.family": "serif",
                "font.serif": ["STIXGeneral", "DejaVu Serif"],
                "mathtext.fontset": "stix",
                "axes.formatter.use_mathtext": True,
                "font.size": PERIOD_PLOT_TYPOGRAPHY["base_fontsize"],
                "axes.labelsize": PERIOD_PLOT_TYPOGRAPHY["axis_labelsize"],
                "legend.fontsize": PERIOD_PLOT_TYPOGRAPHY["legend_fontsize"],
                "axes.edgecolor": RATIO_STYLE["spine"],
                "xtick.direction": "out",
                "ytick.direction": "out",
                "xtick.labelsize": PERIOD_PLOT_TYPOGRAPHY["tick_labelsize"],
                "ytick.labelsize": PERIOD_PLOT_TYPOGRAPHY["tick_labelsize"],
            }
        ),
    ):
        figure, (upper, lower) = plt.subplots(
            2,
            1,
            figsize=(9.5, 8.5),
            dpi=240,
            sharex=True,
            gridspec_kw={"height_ratios": [3.1, 1.0], "hspace": 0.025},
        )
        figure.subplots_adjust(**PERIOD_PLOT_MARGINS)
        bottom = np.zeros(len(centers), dtype=float)
        group_legend_handles = []
        group_legend_labels = []
        group_fill_semantics = []
        for name, definition, hist in groups:
            values = np.array(
                [hist.GetBinContent(index) for index in range(1, hist.GetNbinsX() + 1)]
            )
            group_artist = upper.stairs(
                bottom + values,
                edges,
                baseline=bottom,
                fill=True,
                color=_matplotlib_color(definition.get("color", ROOT.kGray)),
                edgecolor="none",
                linewidth=0.0,
                label=_matplotlib_label(definition.get("nameHR", name)),
            )
            group_legend_handles.append(group_artist)
            group_legend_labels.append(name)
            facecolor = tuple(float(value) for value in group_artist.get_facecolor())
            edgecolor = tuple(float(value) for value in group_artist.get_edgecolor())
            group_semantics = {
                "name": name,
                "artist_class": type(group_artist).__name__,
                "facecolor_rgba": list(facecolor),
                "facecolor_alpha": facecolor[3],
                "edgecolor_rgba": list(edgecolor),
                "linewidth": float(group_artist.get_linewidth()),
                "hatch": group_artist.get_hatch(),
                "per_bin_rectangles": False,
                "vertical_bin_boundaries": False,
            }
            if (
                not isinstance(group_artist, matplotlib.patches.StepPatch)
                or not math.isclose(facecolor[3], 1.0)
                or not math.isclose(edgecolor[3], 0.0)
                or not math.isclose(group_semantics["linewidth"], 0.0)
                or group_semantics["hatch"] is not None
            ):
                plt.close(figure)
                raise RuntimeError(
                    f"Period group {name} violates the solid edge-free StepPatch contract: "
                    f"{group_semantics}"
                )
            group_fill_semantics.append(group_semantics)
            bottom += values

        mc_values = np.array([row["mc_yield"] for row in rows], dtype=float)
        mc_errors = np.array([row["mc_stat_uncertainty"] for row in rows], dtype=float)
        data_values = np.array([row["data_yield"] for row in rows], dtype=float)
        data_low = np.array([row["data_error_low"] for row in rows], dtype=float)
        data_high = np.array([row["data_error_high"] for row in rows], dtype=float)
        upper.fill_between(
            edges,
            np.r_[mc_values - mc_errors, (mc_values - mc_errors)[-1]],
            np.r_[mc_values + mc_errors, (mc_values + mc_errors)[-1]],
            step="post",
            facecolor=RATIO_STYLE["mc_band"],
            edgecolor=RATIO_STYLE["mc_band_edge"],
            alpha=0.18,
            hatch="////",
            linewidth=0.7,
            label="_nolegend_",
        )
        upper.stairs(
            mc_values,
            edges,
            fill=False,
            color=RATIO_STYLE["mc_band_edge"],
            linewidth=1.6,
            label="_nolegend_",
            zorder=7,
        )
        upper_data_visible = data_values > 0.0
        data_artist = upper.errorbar(
            centers[upper_data_visible],
            data_values[upper_data_visible],
            yerr=np.vstack(
                (data_low[upper_data_visible], data_high[upper_data_visible])
            ),
            fmt="o",
            color=RATIO_STYLE["data"],
            markersize=4.2,
            linewidth=0.8,
            capsize=0.0,
            label="Data",
            zorder=8,
        )
        upper.set_ylabel("Events")
        visible_peak = max(
            1.0,
            float(max(np.max(data_values + data_high), np.max(mc_values + mc_errors))),
        )
        upper_limit = visible_peak * PERIOD_PLOT_UPPER_HEADROOM
        upper.set_ylim(0.0, upper_limit)
        upper.set_xlim(float(edges[0]), float(edges[-1]))
        upper.grid(axis="y", color=RATIO_STYLE["grid"], linestyle=":", linewidth=0.55)
        mc_legend_handle = _OverlayLegendTuple(
            (
                Patch(
                    facecolor=RATIO_STYLE["mc_band"],
                    edgecolor=RATIO_STYLE["mc_band_edge"],
                    alpha=0.18,
                    hatch="////",
                    linewidth=0.7,
                ),
                Line2D(
                    [],
                    [],
                    color=RATIO_STYLE["mc_band_edge"],
                    linewidth=1.6,
                ),
            )
        )
        legend_names = ["Data", *group_legend_labels, "Total MC"]
        legend_labels = [yield_labels[name] for name in legend_names]
        legend_artist = upper.legend(
            handles=[data_artist, *group_legend_handles, mc_legend_handle],
            labels=legend_labels,
            loc="upper right",
            bbox_to_anchor=(0.995, 0.99),
            borderaxespad=0.1,
            frameon=True,
            framealpha=0.9,
            ncol=2,
            fontsize=PERIOD_PLOT_TYPOGRAPHY["legend_fontsize"],
            borderpad=0.7,
            labelspacing=0.5,
            columnspacing=1.2,
            handlelength=1.9,
            handletextpad=0.7,
            handler_map={_OverlayLegendTuple: HandlerTuple(ndivide=1, pad=0.0)},
        )
        luminosity_mathtext = rf"${luminosity_fb:.3f}\,\mathrm{{fb}}^{{-1}}$"
        annotation_text = (
            f"{period}\n{luminosity_mathtext}\n{_category_annotation(category)}"
        )
        annotation_artist = upper.text(
            0.012,
            0.985,
            annotation_text,
            transform=upper.transAxes,
            va="top",
            ha="left",
            fontsize=PERIOD_PLOT_TYPOGRAPHY["annotation_fontsize"],
            linespacing=1.15,
            bbox={
                "boxstyle": "round,pad=0.35",
                "facecolor": "white",
                "edgecolor": RATIO_STYLE["grid"],
                "alpha": 0.92,
            },
        )

        valid = np.array([row["valid"] for row in rows], dtype=bool)
        ratio = np.array(
            [np.nan if row["ratio"] is None else row["ratio"] for row in rows]
        )
        ratio_low = np.array(
            [
                0.0 if row["ratio_error_low"] is None else row["ratio_error_low"]
                for row in rows
            ]
        )
        ratio_high = np.array(
            [
                0.0 if row["ratio_error_high"] is None else row["ratio_error_high"]
                for row in rows
            ]
        )
        relative_mc = np.divide(
            mc_errors,
            mc_values,
            out=np.zeros_like(mc_errors),
            where=mc_values > 0.0,
        )
        band_low = np.clip(1.0 - relative_mc, ratio_low_limit, ratio_high_limit)
        band_high = np.clip(1.0 + relative_mc, ratio_low_limit, ratio_high_limit)
        lower.fill_between(
            edges,
            np.r_[band_low, band_low[-1]],
            np.r_[band_high, band_high[-1]],
            step="post",
            facecolor=RATIO_STYLE["mc_band"],
            edgecolor=RATIO_STYLE["mc_band_edge"],
            alpha=0.18,
            hatch="////",
            linewidth=0.7,
        )
        lower.axhline(
            1.0, color=RATIO_STYLE["reference"], linewidth=1.25, linestyle="--"
        )
        central_in_range = (
            valid & (ratio >= ratio_low_limit) & (ratio <= ratio_high_limit)
        )
        if np.any(central_in_range):
            displayed_low = np.minimum(
                ratio_low[central_in_range],
                ratio[central_in_range] - ratio_low_limit,
            )
            displayed_high = np.minimum(
                ratio_high[central_in_range],
                ratio_high_limit - ratio[central_in_range],
            )
            lower.errorbar(
                centers[central_in_range],
                ratio[central_in_range],
                yerr=np.vstack((displayed_low, displayed_high)),
                fmt="o",
                color=RATIO_STYLE["data"],
                markersize=3.8,
                linewidth=0.75,
                capsize=0.0,
                zorder=8,
            )
        span = ratio_high_limit - ratio_low_limit
        central_below = np.array(
            [
                index in clipped_bins["data_central_below"]
                for index in range(1, len(rows) + 1)
            ]
        )
        central_above = np.array(
            [
                index in clipped_bins["data_central_above"]
                for index in range(1, len(rows) + 1)
            ]
        )
        if np.any(central_below):
            lower.scatter(
                centers[central_below],
                np.full(
                    np.count_nonzero(central_below), ratio_low_limit + 0.025 * span
                ),
                marker="v",
                s=42,
                color=RATIO_STYLE["warning"],
                zorder=10,
                clip_on=False,
            )
        if np.any(central_above):
            lower.scatter(
                centers[central_above],
                np.full(
                    np.count_nonzero(central_above), ratio_high_limit - 0.025 * span
                ),
                marker="^",
                s=42,
                color=RATIO_STYLE["warning"],
                zorder=10,
                clip_on=False,
            )

        for direction, bins in (
            ("below", clipped_bins["data_interval_below"]),
            ("above", clipped_bins["data_interval_above"]),
        ):
            for bin_index in bins:
                if bin_index in (
                    clipped_bins["data_central_below"]
                    + clipped_bins["data_central_above"]
                ):
                    continue
                boundary = (
                    ratio_low_limit + 0.012 * span
                    if direction == "below"
                    else ratio_high_limit - 0.012 * span
                )
                interior = boundary + (
                    0.075 * span if direction == "below" else -0.075 * span
                )
                lower.annotate(
                    "",
                    xy=(centers[bin_index - 1], boundary),
                    xytext=(centers[bin_index - 1], interior),
                    arrowprops={
                        "arrowstyle": "-|>",
                        "color": RATIO_STYLE["warning"],
                        "linewidth": 0.8,
                        "mutation_scale": 7,
                    },
                    zorder=9,
                )
        for direction, bins in (
            ("below", clipped_bins["mc_band_below"]),
            ("above", clipped_bins["mc_band_above"]),
        ):
            if not bins:
                continue
            y = (
                ratio_low_limit + 0.045 * span
                if direction == "below"
                else ratio_high_limit - 0.045 * span
            )
            lower.scatter(
                [centers[index - 1] for index in bins],
                [y] * len(bins),
                marker="v" if direction == "below" else "^",
                s=24,
                facecolors="none",
                edgecolors=RATIO_STYLE["mc_band_edge"],
                linewidths=0.9,
                zorder=9,
            )
        lower.set_ylim(ratio_low_limit, ratio_high_limit)
        lower.set_ylabel(DATA_MC_Y_AXIS_LABEL)
        lower.set_xlabel(axis_title)
        lower.grid(axis="y", color=RATIO_STYLE["grid"], linestyle=":", linewidth=0.55)
        for axis in (upper, lower):
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            axis.tick_params(which="both", top=False, right=False)

        x_low, x_high = lower.get_xlim()
        in_range_xlabels = [
            label
            for position, label in zip(lower.get_xticks(), lower.get_xticklabels())
            if x_low - 1.0e-9 <= position <= x_high + 1.0e-9
        ]
        if in_range_xlabels:
            in_range_xlabels[0].set_horizontalalignment("left")
            in_range_xlabels[-1].set_horizontalalignment("right")

        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        legend_bbox = legend_artist.get_window_extent(renderer=renderer)
        annotation_bbox = annotation_artist.get_window_extent(renderer=renderer)
        if legend_bbox.overlaps(annotation_bbox):
            plt.close(figure)
            raise RuntimeError(
                f"Period plot legend and category annotation overlap for {period}/{category}"
            )
        figure_bbox = matplotlib.transforms.Bbox.from_bounds(
            0.0, 0.0, float(renderer.width), float(renderer.height)
        )
        axis_offset_texts = [
            artist
            for artist in (
                upper.yaxis.get_offset_text(),
                lower.yaxis.get_offset_text(),
                lower.xaxis.get_offset_text(),
            )
            if artist.get_visible() and artist.get_text()
        ]
        out_of_range_tick_text_ids = set()
        for axis in (upper, lower):
            for tick_axis, limits in (
                (axis.xaxis, axis.get_xlim()),
                (axis.yaxis, axis.get_ylim()),
            ):
                for tick in tick_axis.get_major_ticks() + tick_axis.get_minor_ticks():
                    location = float(tick.get_loc())
                    if not limits[0] - 1.0e-9 <= location <= limits[1] + 1.0e-9:
                        out_of_range_tick_text_ids.update(
                            (id(tick.label1), id(tick.label2))
                        )
        visible_text_artists = [
            artist
            for artist in figure.findobj(match=matplotlib.text.Text)
            if (
                artist.get_visible()
                and artist.get_text().strip()
                and id(artist) not in out_of_range_tick_text_ids
            )
        ]
        required_artists = [legend_artist, *visible_text_artists]
        clipped_layout_artists = []
        artist_clearances = []
        for artist in required_artists:
            if not artist.get_visible():
                continue
            bbox = artist.get_window_extent(renderer=renderer)
            clearances = {
                "left": float(bbox.x0 - figure_bbox.x0),
                "right": float(figure_bbox.x1 - bbox.x1),
                "bottom": float(bbox.y0 - figure_bbox.y0),
                "top": float(figure_bbox.y1 - bbox.y1),
            }
            artist_clearances.append(
                {
                    "artist": type(artist).__name__,
                    "text": artist.get_text() if hasattr(artist, "get_text") else "",
                    "clearance_pixels": clearances,
                }
            )
            if min(clearances.values()) < PERIOD_PLOT_CANVAS_INSET_PIXELS:
                clipped_layout_artists.append(
                    {
                        "artist": type(artist).__name__,
                        "text": (
                            artist.get_text() if hasattr(artist, "get_text") else ""
                        ),
                        "bbox_pixels": [float(value) for value in bbox.extents],
                    }
                )
        if clipped_layout_artists:
            plt.close(figure)
            raise RuntimeError(
                "Period plot layout clips required artists: "
                f"{clipped_layout_artists} for {period}/{category}"
            )

        minimum_edge_clearance = {
            edge: min(item["clearance_pixels"][edge] for item in artist_clearances)
            for edge in ("left", "right", "bottom", "top")
        }

        def axes_bbox_fraction(bbox):
            transformed = bbox.transformed(upper.transAxes.inverted())
            return [
                float(transformed.x0),
                float(transformed.y0),
                float(transformed.x1),
                float(transformed.y1),
            ]

        layout_audit = {
            "legend_bbox_axes_fraction": axes_bbox_fraction(legend_bbox),
            "annotation_bbox_axes_fraction": axes_bbox_fraction(annotation_bbox),
            "legend_annotation_overlap": False,
            "clipped_required_artists": [],
            "visible_peak_fraction_of_upper_axis": visible_peak / upper_limit,
            "x_limits": [float(value) for value in upper.get_xlim()],
            "axis_offset_texts": [
                {
                    "text": artist.get_text(),
                    "bbox_axes_fraction": axes_bbox_fraction(
                        artist.get_window_extent(renderer=renderer)
                    ),
                }
                for artist in axis_offset_texts
            ],
            "canvas_inset_requirement_pixels": PERIOD_PLOT_CANVAS_INSET_PIXELS,
            "visible_text_artist_count": len(visible_text_artists),
            "minimum_edge_clearance_pixels": minimum_edge_clearance,
        }

        png_path = output_dir / f"{stem}.png"
        pdf_path = output_dir / f"{stem}.pdf"
        metadata = {
            "Title": f"DY Data/MC: {period}, {category}",
            "Creator": "RunStability plot_run_stability.py",
        }
        figure.savefig(png_path, dpi=240, metadata=metadata)
        figure.savefig(pdf_path, metadata=metadata)
        plt.close(figure)
    return {
        "renderer": "matplotlib",
        "matplotlib_version": matplotlib.__version__,
        "mplhep_version": mplhep.__version__,
        "canvas_pixels": [2280, 2040],
        "ratio_display_range": ratio_display["range"],
        "ratio_autorange": ratio_display,
        "category_annotation": _category_annotation(category),
        "visible_semantics": {
            "stack_groups": [name for name, _, _ in groups],
            "upper_data_zero_count_limits_rendered": False,
            "upper_data_positive_bin_count": int(np.count_nonzero(upper_data_visible)),
            "upper_data_suppressed_zero_bin_count": int(
                np.count_nonzero(~upper_data_visible)
            ),
            "stack_artist": "filled_stairs",
            "stack_artist_class": "StepPatch",
            "stack_fill": "solid",
            "stack_facecolor_alpha": 1.0,
            "stack_edgecolor": "none",
            "stack_linewidth": 0.0,
            "stack_hatch": None,
            "stack_per_bin_rectangles": False,
            "stack_vertical_bin_boundaries": False,
            "stack_group_artist_semantics": group_fill_semantics,
            "mc_stat_band": {
                "fill": "translucent_hatched",
                "alpha": 0.18,
                "hatch": "////",
                "facecolor": RATIO_STYLE["mc_band"],
                "edgecolor": RATIO_STYLE["mc_band_edge"],
            },
            "mc_total_line": {
                "artist": "stairs",
                "color": RATIO_STYLE["mc_band_edge"],
                "linewidth": 1.6,
            },
            "legend": {
                "inside_axes": True,
                "location": "upper right",
                "bbox_anchor_axes_fraction": [0.995, 0.99],
                "columns": 2,
                "fontsize": PERIOD_PLOT_TYPOGRAPHY["legend_fontsize"],
                "handlelength": 1.9,
                "entry_names": legend_names,
                "labels": legend_labels,
                "mc_handle": "overlay_line_and_band",
            },
            "category_annotation": {
                "inside_axes": True,
                "location": "upper left",
                "anchor_axes_fraction": [0.012, 0.985],
                "fontsize": PERIOD_PLOT_TYPOGRAPHY["annotation_fontsize"],
                "visible_text": annotation_text,
                "luminosity_mathtext": luminosity_mathtext,
                "luminosity_unit_spacing": r"LaTeX thin space \,",
            },
            "typography_points": dict(PERIOD_PLOT_TYPOGRAPHY),
            "scientific_notation": "mathtext",
            "margins_figure_fraction": dict(PERIOD_PLOT_MARGINS),
            "panel_hspace": 0.025,
            "upper_headroom_factor": PERIOD_PLOT_UPPER_HEADROOM,
            "ticks": {
                "top": False,
                "right": False,
                "applies_to": ["upper", "lower"],
                "which": "both",
                "x_endpoint_label_alignment": ["left", "right"],
            },
            "layout_audit": layout_audit,
            "observable_axis_title": axis_title,
            "ratio_y_axis_label": DATA_MC_Y_AXIS_LABEL,
            "yield_legend": yield_legend,
        },
    }


def make_period_plot(
    dataset, category, observable, period, luminosity_source, output_dir
):
    era = dataset["contract"]["analysis_era"]
    if category not in dataset["contract"]["categories"]:
        raise ValueError(f"Category {category!r} is unavailable in era {era}")
    if observable not in dataset["contract"]["observables"]:
        raise ValueError(f"Observable {observable!r} is unavailable in era {era}")
    requested_period = str(period)
    period = physical_run_period(requested_period)
    if requested_period != period:
        raise ValueError(
            f"--period selects a physical year-letter period; use {period!r}, "
            f"not configured subdivision {requested_period!r}"
        )
    (
        selected,
        luminosity,
        scale,
        data,
        groups,
        mc_total,
        total_yield,
        total_variance,
        classification,
    ) = _period_histograms(dataset, category, observable, period, luminosity_source)

    group_totals = {}
    for group_name, _, histogram in groups:
        group_yield, group_variance = _sum_visible(histogram)
        group_totals[group_name] = {
            "yield": group_yield,
            "variance": group_variance,
        }
    if not math.isclose(
        math.fsum(item["yield"] for item in group_totals.values()),
        total_yield,
        rel_tol=1.0e-10,
        abs_tol=1.0e-10,
    ) or not math.isclose(
        math.fsum(item["variance"] for item in group_totals.values()),
        total_variance,
        rel_tol=1.0e-10,
        abs_tol=1.0e-10,
    ):
        raise RuntimeError(
            "DY/Others period groups do not close to total MC Sumw/Sumw2"
        )

    dy_hist = groups[0][2]
    others_hist = groups[1][2]
    classification_source = classification["source"]
    dy_process_list = ";".join(classification["groups"]["DY"])
    others_process_list = ";".join(classification["groups"]["Others"])
    rows = []
    for index in range(1, data.GetNbinsX() + 1):
        data_yield = float(data.GetBinContent(index))
        data_interval = garwood_interval(round(data_yield))
        mc_yield = float(mc_total.GetBinContent(index))
        mc_uncertainty = float(mc_total.GetBinError(index))
        result = ratio_with_uncertainty(data_yield, mc_yield)
        rows.append(
            {
                "bin": index,
                "bin_low": float(data.GetXaxis().GetBinLowEdge(index)),
                "bin_high": float(data.GetXaxis().GetBinUpEdge(index)),
                "data_yield": data_yield,
                "data_error_low": data_yield - data_interval[0],
                "data_error_high": data_interval[1] - data_yield,
                "mc_yield": mc_yield,
                "mc_stat_uncertainty": mc_uncertainty,
                "mc_dy_yield": float(dy_hist.GetBinContent(index)),
                "mc_dy_stat_uncertainty": float(dy_hist.GetBinError(index)),
                "mc_dy_variance": float(dy_hist.GetBinError(index) ** 2),
                "mc_others_yield": float(others_hist.GetBinContent(index)),
                "mc_others_stat_uncertainty": float(others_hist.GetBinError(index)),
                "mc_others_variance": float(others_hist.GetBinError(index) ** 2),
                "ratio": None if result is None else result["value"],
                "ratio_error_low": None if result is None else result["error_low"],
                "ratio_error_high": None if result is None else result["error_high"],
                "valid": result is not None,
                "invalid_reason": None if result is not None else "nonpositive_mc_bin",
                "mc_group_classification_source": classification_source,
                "mc_dy_processes": dy_process_list,
                "mc_others_processes": others_process_list,
            }
        )

    # All scientific guards above run before the first output artifact is created.
    output_dir = Path(output_dir)
    stem = period_output_stem(period, observable, category, luminosity_source)
    _guard_fresh_output_stem(output_dir, stem, ("csv", "root", "png", "pdf", "json"))
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    root_path = output_dir / f"{stem}.root"
    output = ROOT.TFile.Open(str(root_path), "RECREATE")
    data.SetName("data_period")
    mc_total.SetName("mc_total_scaled")
    data.Write()
    mc_total.Write()
    for group_name, _, histogram in groups:
        safe_name = re.sub(r"[^A-Za-z0-9_]+", "_", group_name).strip("_")
        histogram.SetName(f"mc_group_{safe_name}")
        histogram.Write()
    ROOT.TNamed(
        "mc_group_classification_json",
        json.dumps(classification, sort_keys=True, separators=(",", ":")),
    ).Write()
    data_graph = ROOT.TGraphAsymmErrors(len(rows))
    data_graph.SetName("data_graph_garwood")
    ratio_graph = ROOT.TGraphAsymmErrors(len(rows))
    ratio_graph.SetName("ratio_graph_garwood_data")
    mc_band = ROOT.TGraphAsymmErrors(len(rows))
    mc_band.SetName("ratio_mc_stat_band")
    for graph_index, row in enumerate(rows):
        x = 0.5 * (row["bin_low"] + row["bin_high"])
        ex = 0.5 * (row["bin_high"] - row["bin_low"])
        data_graph.SetPoint(graph_index, x, row["data_yield"])
        data_graph.SetPointError(
            graph_index,
            ex,
            ex,
            row["data_error_low"],
            row["data_error_high"],
        )
        if row["valid"]:
            ratio_graph.SetPoint(graph_index, x, row["ratio"])
            ratio_graph.SetPointError(
                graph_index,
                ex,
                ex,
                row["ratio_error_low"],
                row["ratio_error_high"],
            )
        else:
            ratio_graph.SetPoint(graph_index, x, float("nan"))
        relative = (
            row["mc_stat_uncertainty"] / row["mc_yield"]
            if row["mc_yield"] > 0.0
            else 0.0
        )
        mc_band.SetPoint(graph_index, x, 1.0)
        mc_band.SetPointError(graph_index, ex, ex, relative, relative)
    data_graph.Write()
    ratio_graph.Write()
    mc_band.Write()
    output.Close()

    presentation = _render_period_plot(
        data,
        groups,
        mc_total,
        rows,
        output_dir,
        stem,
        period,
        category,
        luminosity,
    )
    outputs = {
        "csv": str(csv_path),
        "root": str(root_path),
        "png": str(output_dir / f"{stem}.png"),
        "pdf": str(output_dir / f"{stem}.pdf"),
    }
    receipt = {
        "schema_version": 2,
        "kind": "physical_run_period_data_mc",
        "output_stem": stem,
        "dataset": _dataset_identity(dataset),
        "analysis_era": era,
        "physical_run_period": period,
        "configured_run_periods": selected["configured_run_periods"],
        "runs": selected["runs"],
        "run_count": len(selected["runs"]),
        "category": category,
        "observable": observable,
        "luminosity_source": luminosity_source,
        "recorded_lumi_fb": luminosity,
        "mc_source_lumi_fb": dataset["mc_source_lumi_fb"],
        "mc_scale": scale,
        "mc_variance_scale": scale * scale,
        "data_yield": float(sum(row["data_yield"] for row in rows)),
        "mc_yield": total_yield,
        "mc_variance": total_variance,
        "mc_processes": list(dataset["processes"]),
        "mc_grouping": {
            **classification,
            "group_totals_after_period_scale": group_totals,
            "root_object": "mc_group_classification_json",
            "csv_columns": {
                "classification": [
                    "mc_group_classification_source",
                    "mc_dy_processes",
                    "mc_others_processes",
                ],
                "per_bin_sumw_sumw2": [
                    "mc_dy_yield",
                    "mc_dy_stat_uncertainty",
                    "mc_dy_variance",
                    "mc_others_yield",
                    "mc_others_stat_uncertainty",
                    "mc_others_variance",
                ],
            },
        },
        "uncertainty_model": {
            "data": "central 68.2689492137% Garwood Poisson interval only",
            "mc": "scaled source-template Sumw2, displayed as a separate band",
        },
        "invalid_nonpositive_mc_bins": [row["bin"] for row in rows if not row["valid"]],
        "presentation": presentation,
        "outputs": outputs,
    }
    receipt["output_sha256"] = {name: sha256(path) for name, path in outputs.items()}
    receipt_path = output_dir / f"{stem}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def make_ratio_vs_run(datasets, category, observable, luminosity_source, output_dir):
    rows = []
    era_indices = []
    mc_yields = {}
    mc_variances = {}
    for dataset in datasets:
        era = dataset["contract"]["analysis_era"]
        if category not in dataset["contract"]["categories"]:
            raise ValueError(f"Category {category!r} is unavailable in era {era}")
        if observable not in dataset["contract"]["observables"]:
            raise ValueError(f"Observable {observable!r} is unavailable in era {era}")
        handle = open_root(dataset["input_path"])
        try:
            data2d = _get(
                handle,
                f"run_stability/{category}/{observable}/histo_DATA",
                "TH2",
            )
            _, _, mc_total = _mc_histograms(handle, dataset, category, observable)
        finally:
            handle.Close()
        mc_yield, mc_variance = _sum_visible(mc_total)
        if mc_yield <= 0.0:
            raise RuntimeError(f"Era {era} has nonpositive total prompt-MC yield")
        mc_yields[era] = mc_yield
        mc_variances[era] = mc_variance
        mc_relative_uncertainty = math.sqrt(max(0.0, mc_variance)) / mc_yield
        for run_index, run in enumerate(dataset["runs"]):
            luminosity = dataset["luminosities"][luminosity_source][run_index]
            data_yield = sum(
                data2d.GetBinContent(run_index + 1, ybin)
                for ybin in range(1, data2d.GetNbinsY() + 1)
            )
            data_error2 = sum(
                data2d.GetBinError(run_index + 1, ybin) ** 2
                for ybin in range(1, data2d.GetNbinsY() + 1)
            )
            nearest = round(data_yield)
            if (
                data_yield < 0.0
                or abs(data_yield - nearest) > 1.0e-6 * max(1.0, abs(data_yield))
                or abs(data_error2 - data_yield) > 1.0e-5 * max(1.0, data_yield)
            ):
                raise RuntimeError(
                    f"Era {era} run {run} DATA is not a binary-weight Poisson count: "
                    f"sumw={data_yield}, sumw2={data_error2}"
                )
            if luminosity <= 0.0:
                result = None
                denominator = 0.0
            else:
                scale = luminosity / dataset["mc_source_lumi_fb"]
                denominator = mc_yield * scale
                result = ratio_with_uncertainty(data_yield, denominator)
            rows.append(
                {
                    "era": era,
                    "run": int(run),
                    "physical_run_period": physical_run_period(
                        dataset["run_periods"]["nominal"][run_index]
                    ),
                    "recorded_lumi_fb": luminosity,
                    "data_yield": data_yield,
                    "mc_yield": denominator,
                    "mc_relative_uncertainty": mc_relative_uncertainty,
                    "ratio": None if result is None else result["value"],
                    "ratio_error_low": None if result is None else result["error_low"],
                    "ratio_error_high": (
                        None if result is None else result["error_high"]
                    ),
                    "valid": result is not None,
                    "invalid_reason": None if result is not None else "zero_luminosity",
                }
            )
            era_indices.append(era)

    ratios = [row["ratio"] for row in rows]
    covariance_mc = mc_ratio_covariance(ratios, era_indices, mc_yields, mc_variances)
    covariance_total = [line[:] for line in covariance_mc]
    for index, row in enumerate(rows):
        if row["valid"]:
            covariance_total[index][index] += row["data_yield"] / (
                row["mc_yield"] * row["mc_yield"]
            )

    output_dir = Path(output_dir)
    stem = stability_output_stem(datasets, observable, category, luminosity_source)
    _guard_fresh_output_stem(output_dir, stem, ("csv", "root", "png", "pdf", "json"))
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    size = len(rows)
    root_path = output_dir / f"{stem}.root"
    output = ROOT.TFile.Open(str(root_path), "RECREATE")
    ratio_hist = ROOT.TH1D("ratio_by_run", ";Run;Data/MC", size, 0.5, size + 0.5)
    ratio_hist.SetStats(False)
    data_hist = ROOT.TH1D(
        "data_yield_by_run", ";Run;Data events", size, 0.5, size + 0.5
    )
    mc_hist = ROOT.TH1D("mc_yield_by_run", ";Run;Scaled MC", size, 0.5, size + 0.5)
    lumi_hist = ROOT.TH1D(
        "recorded_lumi_fb_by_run",
        ";Run;Recorded luminosity [fb^{-1}]",
        size,
        0.5,
        size + 0.5,
    )
    graph = ROOT.TGraphAsymmErrors(size)
    graph.SetName("ratio_graph_garwood_data")
    cov_mc_hist = ROOT.TH2D(
        "ratio_covariance_mcstat",
        ";Run;Run",
        size,
        0.5,
        size + 0.5,
        size,
        0.5,
        size + 0.5,
    )
    cov_total_hist = ROOT.TH2D(
        "ratio_covariance_total_symmetric",
        ";Run;Run",
        size,
        0.5,
        size + 0.5,
        size,
        0.5,
        size + 0.5,
    )
    for index, row in enumerate(rows, 1):
        label = str(row["run"])
        for hist in (ratio_hist, data_hist, mc_hist, lumi_hist):
            hist.GetXaxis().SetBinLabel(index, label)
        cov_mc_hist.GetXaxis().SetBinLabel(index, label)
        cov_mc_hist.GetYaxis().SetBinLabel(index, label)
        cov_total_hist.GetXaxis().SetBinLabel(index, label)
        cov_total_hist.GetYaxis().SetBinLabel(index, label)
        data_hist.SetBinContent(index, row["data_yield"])
        mc_hist.SetBinContent(index, row["mc_yield"])
        lumi_hist.SetBinContent(index, row["recorded_lumi_fb"])
        if row["valid"]:
            ratio_hist.SetBinContent(index, row["ratio"])
            ratio_hist.SetBinError(
                index, math.sqrt(row["data_yield"]) / row["mc_yield"]
            )
            graph.SetPoint(index - 1, index, row["ratio"])
            graph.SetPointError(
                index - 1,
                0.0,
                0.0,
                row["ratio_error_low"],
                row["ratio_error_high"],
            )
        else:
            graph.SetPoint(index - 1, index, float("nan"))
        for other in range(1, size + 1):
            cov_mc_hist.SetBinContent(index, other, covariance_mc[index - 1][other - 1])
            cov_total_hist.SetBinContent(
                index, other, covariance_total[index - 1][other - 1]
            )
    for obj in (
        ratio_hist,
        data_hist,
        mc_hist,
        lumi_hist,
        graph,
        cov_mc_hist,
        cov_total_hist,
    ):
        obj.Write()
    output.Close()

    presentation = _render_ratio_vs_run(
        rows,
        ratio_hist,
        output_dir,
        stem,
        category,
        observable,
        luminosity_source,
    )

    receipt = {
        "schema_version": 4,
        "kind": "data_mc_ratio_vs_run",
        "output_stem": stem,
        "datasets": [_dataset_identity(dataset) for dataset in datasets],
        "category": category,
        "observable": observable,
        "luminosity_source": luminosity_source,
        "uncertainty_model": {
            "data_graph": "central 68.2689492137% Garwood Poisson interval divided by MC; no MC term",
            "mc_band": "sqrt(source-template Sumw2)/source-template yield centered on one, constant within each era",
            "mc_covariance": "fully correlated between runs sharing an era template; zero across eras",
            "total_covariance": "MC covariance plus symmetric Poisson data variance D/MC^2 on the diagonal",
        },
        "invalid_zero_luminosity_runs": [
            row["run"] for row in rows if not row["valid"]
        ],
        "presentation": presentation,
        "outputs": {
            "csv": str(csv_path),
            "root": str(root_path),
            "png": str(output_dir / f"{stem}.png"),
            "pdf": str(output_dir / f"{stem}.pdf"),
        },
    }
    receipt["output_sha256"] = {
        name: sha256(path) for name, path in receipt["outputs"].items()
    }
    (output_dir / f"{stem}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def make_chi2_vs_run(datasets, category, observable, luminosity_source, output_dir):
    """Build one distribution-level reduced-chi2 diagnostic per physical run."""
    rows = []
    run_bin_statistics = []
    reference_edges = None
    for dataset in datasets:
        era = dataset["contract"]["analysis_era"]
        if category not in dataset["contract"]["categories"]:
            raise ValueError(f"Category {category!r} is unavailable in era {era}")
        if observable not in dataset["contract"]["observables"]:
            raise ValueError(f"Observable {observable!r} is unavailable in era {era}")
        handle = open_root(dataset["input_path"])
        try:
            data2d = _get(
                handle,
                f"run_stability/{category}/{observable}/histo_DATA",
                "TH2",
            ).Clone(f"chi2_data_{era}")
            data2d.SetDirectory(0)
            _, _, mc_total = _mc_histograms(handle, dataset, category, observable)
        finally:
            handle.Close()
        if data2d.GetNbinsY() != mc_total.GetNbinsX():
            raise RuntimeError(
                f"Era {era} DATA/MC observable bin counts diverge for {observable}"
            )
        edges = [
            float(mc_total.GetXaxis().GetBinLowEdge(index))
            for index in range(1, mc_total.GetNbinsX() + 2)
        ]
        data_edges = [
            float(data2d.GetYaxis().GetBinLowEdge(index))
            for index in range(1, data2d.GetNbinsY() + 2)
        ]
        if not np.allclose(edges, data_edges, rtol=0.0, atol=1.0e-12):
            raise RuntimeError(f"Era {era} DATA/MC observable edges diverge")
        if reference_edges is None:
            reference_edges = edges
        elif not np.allclose(reference_edges, edges, rtol=0.0, atol=1.0e-12):
            raise RuntimeError(
                f"Observable {observable} edges diverge between analysis eras"
            )
        source_yield, _ = _sum_visible(mc_total)
        if source_yield <= 0.0:
            raise RuntimeError(f"Era {era} has nonpositive total MC yield")

        identity = _dataset_identity(dataset)
        for run_index, run in enumerate(dataset["runs"]):
            luminosity = float(dataset["luminosities"][luminosity_source][run_index])
            scale = luminosity / float(dataset["mc_source_lumi_fb"])
            bin_rows = []
            for observable_bin in range(1, mc_total.GetNbinsX() + 1):
                data = float(data2d.GetBinContent(run_index + 1, observable_bin))
                data_sumw2 = float(
                    data2d.GetBinError(run_index + 1, observable_bin) ** 2
                )
                nearest = round(data)
                if (
                    data < 0.0
                    or abs(data - nearest) > 1.0e-6 * max(1.0, abs(data))
                    or abs(data_sumw2 - data) > 1.0e-5 * max(1.0, data)
                ):
                    raise RuntimeError(
                        f"Era {era} run {run} bin {observable_bin} DATA is not a "
                        f"binary-weight Poisson count: sumw={data}, sumw2={data_sumw2}"
                    )
                mc_source = float(mc_total.GetBinContent(observable_bin))
                mc_source_variance = float(mc_total.GetBinError(observable_bin) ** 2)
                mc = scale * mc_source
                mc_variance = scale * scale * mc_source_variance
                statistic = chi2_bin_statistic(data, mc, mc_variance)
                bin_rows.append(
                    {
                        "bin": observable_bin,
                        "low_edge": edges[observable_bin - 1],
                        "high_edge": edges[observable_bin],
                        "data_sumw2": data_sumw2,
                        "mc_source": mc_source,
                        "mc_source_variance": mc_source_variance,
                        **statistic,
                    }
                )

            contributing = (
                [item for item in bin_rows if item["valid"]] if luminosity > 0.0 else []
            )
            chi2 = sum(float(item["chi2_contribution"]) for item in contributing)
            ndf = len(contributing)
            if luminosity <= 0.0:
                invalid_reason = "zero_luminosity"
            elif ndf == 0:
                invalid_reason = "no_contributing_bins"
            else:
                invalid_reason = None
            reduced = chi2 / ndf if invalid_reason is None else None
            row = {
                "era": era,
                "run": int(run),
                "physical_run_period": physical_run_period(
                    dataset["run_periods"]["nominal"][run_index]
                ),
                "category": category,
                "observable": observable,
                "luminosity_source": luminosity_source,
                "recorded_lumi_fb": luminosity,
                "mc_source_lumi_fb": float(dataset["mc_source_lumi_fb"]),
                "mc_scale": scale,
                "mc_variance_scale": scale * scale,
                "data_yield": sum(item["data"] for item in bin_rows),
                "mc_yield": sum(item["mc"] for item in bin_rows),
                "data_interval_variance_sum": sum(
                    item["data_variance"] for item in contributing
                ),
                "mc_sumw2_variance_sum": sum(
                    item["mc_variance"] for item in contributing
                ),
                "total_stat_variance_sum": sum(
                    item["total_variance"] for item in contributing
                ),
                "negative_mc_bin_count": sum(item["mc"] < 0.0 for item in bin_rows),
                "contributing_bin_count": ndf,
                "excluded_bin_count": len(bin_rows) - ndf,
                "chi2": chi2 if invalid_reason is None else None,
                "ndf": ndf,
                "reduced_chi2": reduced,
                "approx_expected_std": (
                    math.sqrt(2.0 / ndf) if invalid_reason is None else None
                ),
                "n_fitted_parameters": 0,
                "valid": invalid_reason is None,
                "invalid_reason": invalid_reason,
                "config_sha256": identity["config_sha256"],
                "input_sha256": identity["input_sha256"],
            }
            rows.append(row)
            run_bin_statistics.append(
                {
                    "era": era,
                    "run": int(run),
                    "recorded_lumi_fb": luminosity,
                    "mc_scale": scale,
                    "mc_variance_scale": scale * scale,
                    "bins": bin_rows,
                }
            )

    output_dir = Path(output_dir)
    stem = chi2_output_stem(datasets, observable, category, luminosity_source)
    _guard_fresh_output_stem(output_dir, stem, ("csv", "root", "png", "pdf", "json"))
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{stem}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    size = len(rows)
    n_observable_bins = len(reference_edges) - 1
    root_path = output_dir / f"{stem}.root"
    output = ROOT.TFile.Open(str(root_path), "RECREATE")
    reduced_hist = ROOT.TH1D(
        "reduced_chi2_by_run", ";Run;Reduced chi2", size, 0.5, size + 0.5
    )
    reduced_hist.SetStats(False)
    chi2_hist = ROOT.TH1D("chi2_by_run", ";Run;chi2", size, 0.5, size + 0.5)
    ndf_hist = ROOT.TH1I("ndf_by_run", ";Run;ndf", size, 0.5, size + 0.5)
    lumi_hist = ROOT.TH1D(
        "recorded_lumi_fb_by_run",
        ";Run;Recorded luminosity [fb^{-1}]",
        size,
        0.5,
        size + 0.5,
    )
    scale_hist = ROOT.TH1D("mc_scale_by_run", ";Run;MC scale", size, 0.5, size + 0.5)
    graph = ROOT.TGraph(size)
    graph.SetName("reduced_chi2_graph")
    expected_band = ROOT.TGraphAsymmErrors(size)
    expected_band.SetName("approx_expected_reduced_chi2_band")
    matrices = {
        name: ROOT.TH2D(
            name,
            ";Run;Observable bin",
            size,
            0.5,
            size + 0.5,
            n_observable_bins,
            0.5,
            n_observable_bins + 0.5,
        )
        for name in (
            "data_yield_by_run_bin",
            "mc_yield_by_run_bin",
            "data_interval_variance_by_run_bin",
            "mc_sumw2_variance_by_run_bin",
            "chi2_contribution_by_run_bin",
            "contributing_bin_mask",
        )
    }
    for index, (row, detailed) in enumerate(zip(rows, run_bin_statistics), 1):
        label = str(row["run"])
        for hist in (reduced_hist, chi2_hist, ndf_hist, lumi_hist, scale_hist):
            hist.GetXaxis().SetBinLabel(index, label)
        for hist in matrices.values():
            hist.GetXaxis().SetBinLabel(index, label)
        lumi_hist.SetBinContent(index, row["recorded_lumi_fb"])
        scale_hist.SetBinContent(index, row["mc_scale"])
        ndf_hist.SetBinContent(index, row["ndf"])
        if row["valid"]:
            reduced_hist.SetBinContent(index, row["reduced_chi2"])
            chi2_hist.SetBinContent(index, row["chi2"])
            graph.SetPoint(index - 1, index, row["reduced_chi2"])
            expected_band.SetPoint(index - 1, index, 1.0)
            expected_band.SetPointError(
                index - 1,
                0.0,
                0.0,
                row["approx_expected_std"],
                row["approx_expected_std"],
            )
        else:
            graph.SetPoint(index - 1, index, float("nan"))
            expected_band.SetPoint(index - 1, index, float("nan"))
        for item in detailed["bins"]:
            ybin = int(item["bin"])
            matrices["data_yield_by_run_bin"].SetBinContent(index, ybin, item["data"])
            matrices["mc_yield_by_run_bin"].SetBinContent(index, ybin, item["mc"])
            matrices["data_interval_variance_by_run_bin"].SetBinContent(
                index, ybin, item["data_variance"]
            )
            matrices["mc_sumw2_variance_by_run_bin"].SetBinContent(
                index, ybin, item["mc_variance"]
            )
            if row["valid"] and item["valid"]:
                matrices["chi2_contribution_by_run_bin"].SetBinContent(
                    index, ybin, item["chi2_contribution"]
                )
                matrices["contributing_bin_mask"].SetBinContent(index, ybin, 1.0)
    definition = {
        "schema_version": 1,
        "formula": "sum_bins (D-M)^2 / (sigma_D_Garwood^2 + Sumw2_MC_scaled); reduced=chi2/ndf",
        "data_sigma_convention": "half-width of central 68.2689492137% Garwood interval",
        "mc_variance_convention": "ordinary era-template Sumw2 scaled by (recorded_run_lumi/mc_source_lumi)^2",
        "ndf": "number of visible bins with finite positive total variance; no fitted parameters",
        "observable_bin_edges": reference_edges,
        "interpretation": "diagnostic Gaussian approximation; not an exact Poisson or finite-MC likelihood goodness-of-fit",
    }
    covariance_status = {
        "status": "not_computed",
        "reason": (
            "the reduced-chi2 statistic is nonlinear and the available histograms "
            "do not encode the bin-to-bin/process covariance needed to derive a "
            "run-point covariance; shared era MC makes same-era points correlated"
        ),
    }
    for obj in (
        reduced_hist,
        chi2_hist,
        ndf_hist,
        lumi_hist,
        scale_hist,
        graph,
        expected_band,
        *matrices.values(),
    ):
        obj.Write()
    ROOT.TNamed(
        "statistic_definition_json", json.dumps(definition, sort_keys=True)
    ).Write()
    ROOT.TNamed(
        "covariance_status_json", json.dumps(covariance_status, sort_keys=True)
    ).Write()
    output.Close()

    presentation = _render_chi2_vs_run(rows, output_dir, stem, category, observable)
    receipt = {
        "schema_version": 2,
        "kind": "reduced_chi2_vs_run",
        "output_stem": stem,
        "datasets": [_dataset_identity(dataset) for dataset in datasets],
        "category": category,
        "observable": observable,
        "luminosity_source": luminosity_source,
        "statistic_definition": definition,
        "covariance": covariance_status,
        "runs": rows,
        "run_bin_statistics": run_bin_statistics,
        "invalid_runs": [
            {"era": row["era"], "run": row["run"], "reason": row["invalid_reason"]}
            for row in rows
            if not row["valid"]
        ],
        "presentation": presentation,
        "outputs": {
            "csv": str(csv_path),
            "root": str(root_path),
            "png": str(output_dir / f"{stem}.png"),
            "pdf": str(output_dir / f"{stem}.pdf"),
        },
    }
    receipt["output_sha256"] = {
        name: sha256(path) for name, path in receipt["outputs"].items()
    }
    (output_dir / f"{stem}.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    return receipt


def _single_dataset(args, require_lumi=False):
    luminosity_source = getattr(args, "luminosity_source", None)
    if require_lumi and not luminosity_source:
        raise RuntimeError("--luminosity-source is required")
    return validate_dataset(args.config, args.input, luminosity_source)


def _print_inventory(dataset, as_json=False):
    first_source = next(iter(dataset["run_periods"]))
    inventory = {
        "analysis_era": dataset["contract"]["analysis_era"],
        "target_region": dataset["contract"].get("target_region", "DY"),
        "categories": list(dataset["contract"]["categories"]),
        "observables": list(dataset["contract"]["observables"]),
        "runs": list(dataset["runs"]),
        "physical_run_periods": [
            {
                "period": entry["period"],
                "configured_run_periods": entry["configured_run_periods"],
                "run_count": len(entry["runs"]),
                "first_run": entry["runs"][0],
                "last_run": entry["runs"][-1],
            }
            for entry in period_inventory(dataset, first_source)
        ],
        "mc_processes": list(dataset["processes"]),
        "mc_source_lumi_fb": dataset["mc_source_lumi_fb"],
        "dataset": _dataset_identity(dataset),
    }
    if as_json:
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print(f"era: {inventory['analysis_era']}")
        print(f"target region: {inventory['target_region']}")
        print("categories: " + ", ".join(inventory["categories"]))
        print("observables: " + ", ".join(inventory["observables"]))
        print(
            f"runs: {len(inventory['runs'])} ({inventory['runs'][0]}..{inventory['runs'][-1]})"
        )
        print(
            "physical run periods: "
            + ", ".join(
                f"{entry['period']} ({entry['run_count']} runs)"
                for entry in inventory["physical_run_periods"]
            )
        )
        print(f"prompt MC processes: {len(inventory['mc_processes'])}")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "validate", "plot", "period-plot"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument(
            "--config", required=True, help="exact compiled config pickle"
        )
        subparser.add_argument(
            "--input", required=True, help="exact merged ROOT file or XRootD URL"
        )
        if name == "list":
            subparser.add_argument("--json", action="store_true")
        if name in ("plot", "period-plot"):
            subparser.add_argument("--category", required=True)
            subparser.add_argument("--observable", required=True)
            if name == "plot":
                subparser.add_argument("--run", required=True, type=int)
            else:
                subparser.add_argument(
                    "--period",
                    required=True,
                    help="physical year-letter period, e.g. 2023C or 2024I",
                )
            subparser.add_argument(
                "--luminosity-source",
                required=True,
                help="exact compiled source key, or auto for the category mapping",
            )
            subparser.add_argument("--output-dir", required=True)
    ratio = subparsers.add_parser("ratio-vs-run")
    ratio.add_argument(
        "--dataset",
        action="append",
        nargs=3,
        metavar=("ERA", "CONFIG", "INPUT"),
        required=True,
        help="repeat once per era, in desired run-axis order",
    )
    ratio.add_argument("--category", required=True)
    ratio.add_argument("--observable", default="Z0_mass")
    ratio.add_argument(
        "--luminosity-source",
        required=True,
        help="exact compiled source key, or auto for the category mapping",
    )
    ratio.add_argument("--output-dir", required=True)
    chi2 = subparsers.add_parser("chi2-vs-run")
    chi2.add_argument(
        "--dataset",
        action="append",
        nargs=3,
        metavar=("ERA", "CONFIG", "INPUT"),
        required=True,
        help="repeat once per era, in desired run-axis order",
    )
    chi2.add_argument("--category", required=True)
    chi2.add_argument("--observable", required=True)
    chi2.add_argument(
        "--luminosity-source",
        required=True,
        help="exact compiled source key, or auto for the category mapping",
    )
    chi2.add_argument("--output-dir", required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command in ("list", "validate"):
        dataset = _single_dataset(args)
        _print_inventory(dataset, getattr(args, "json", False))
        return 0
    if args.command == "plot":
        dataset = _single_dataset(args, require_lumi=True)
        luminosity_source = resolve_luminosity_source(
            [dataset], args.category, args.luminosity_source
        )
        receipt = make_run_plot(
            dataset,
            args.category,
            args.observable,
            args.run,
            luminosity_source,
            args.output_dir,
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    if args.command == "period-plot":
        dataset = _single_dataset(args, require_lumi=True)
        luminosity_source = resolve_luminosity_source(
            [dataset], args.category, args.luminosity_source
        )
        receipt = make_period_plot(
            dataset,
            args.category,
            args.observable,
            args.period,
            luminosity_source,
            args.output_dir,
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    datasets = []
    seen_eras = set()
    for declared_era, config_path, input_path in args.dataset:
        dataset = validate_dataset(config_path, input_path, args.luminosity_source)
        actual_era = dataset["contract"]["analysis_era"]
        if actual_era != declared_era:
            raise RuntimeError(
                f"Declared era {declared_era!r} does not match config era {actual_era!r}"
            )
        if actual_era in seen_eras:
            raise RuntimeError(f"Duplicate era {actual_era!r}")
        seen_eras.add(actual_era)
        datasets.append(dataset)
    luminosity_source = resolve_luminosity_source(
        datasets, args.category, args.luminosity_source
    )
    if args.command == "ratio-vs-run":
        receipt = make_ratio_vs_run(
            datasets,
            args.category,
            args.observable,
            luminosity_source,
            args.output_dir,
        )
    else:
        receipt = make_chi2_vs_run(
            datasets,
            args.category,
            args.observable,
            luminosity_source,
            args.output_dir,
        )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
