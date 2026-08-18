#!/usr/bin/env python3
"""On-demand DATA/MC plots and run-ratio summaries for run-stability outputs."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import zlib

import cloudpickle
import matplotlib
import mplhep
import numpy as np
import ROOT


matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402


ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)
GARWOOD_COVERAGE = 0.682689492137

# Presentation tokens adapted to PyROOT from the maintained mkshapes-analysis-lab
# ``publication-light`` theme and comparison-panel grammar.  The numerical ROOT
# objects remain independent of these display-only choices.
RATIO_DISPLAY_RANGE = (0.5, 1.5)
RATIO_STYLE = {
    "reference": "#596168",
    "data": "#202124",
    "accent": "#2F6B9A",
    "warning": "#A23B00",
    "grid": "#D9DEE2",
    "era_fill_even": "#F5F7F9",
    "era_fill_odd": "#EAF0F5",
}
RATIO_STYLE_PROVENANCE = {
    "source": "notebooks/mkshapes_analysis_lab",
    "theme": "publication-light",
    "theme_registry_version": "2026.08",
    "ratio_limits": list(RATIO_DISPLAY_RANGE),
    "outlier_above": "filled upward triangle",
    "outlier_below": "filled downward triangle",
}


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


def ratio_with_uncertainty(data, mc, mc_variance):
    """DATA/MC with Garwood DATA errors and independent MC Sumw2 propagation."""
    if mc <= 0.0:
        return None
    nearest = round(data)
    if data < 0.0 or abs(data - nearest) > 1.0e-6 * max(1.0, abs(data)):
        raise RuntimeError(
            f"DATA yield {data!r} is not an unweighted nonnegative integer count"
        )
    low, high = garwood_interval(nearest)
    ratio = data / mc
    mc_term = data * math.sqrt(max(0.0, mc_variance)) / (mc * mc)
    return {
        "value": ratio,
        "error_low": math.hypot((data - low) / mc, mc_term),
        "error_high": math.hypot((high - data) / mc, mc_term),
        "data_low": low,
        "data_high": high,
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


def ratio_display_summary(rows, limits=RATIO_DISPLAY_RANGE):
    """Classify ratio points for the bounded semantic display range."""
    low, high = map(float, limits)
    if not math.isfinite(low) or not math.isfinite(high) or high <= low:
        raise ValueError("ratio display limits must be finite and increasing")
    result = {"in_range": [], "above": [], "below": [], "invalid": []}
    for index, row in enumerate(rows, 1):
        point = {
            "bin": index,
            "era": row["era"],
            "run": int(row["run"]),
            "ratio": row["ratio"],
        }
        if not row["valid"]:
            point["invalid_reason"] = row["invalid_reason"]
            result["invalid"].append(point)
        elif row["ratio"] < low:
            result["below"].append(point)
        elif row["ratio"] > high:
            result["above"].append(point)
        else:
            result["in_range"].append(point)
    return result


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
                }
            )
        else:
            spans[-1]["last_bin"] = index
            spans[-1]["recorded_lumi_fb"] += float(row["recorded_lumi_fb"])
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
    low, high = RATIO_DISPLAY_RANGE
    display = ratio_display_summary(rows)
    spans = _era_spans(rows)
    selected_labels = _selected_run_labels(rows, spans)
    canvas_width, canvas_height = 1500, 840
    figure_size = (canvas_width / 120.0, canvas_height / 120.0)
    style = {
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 10.5,
        "axes.labelsize": 12.0,
        "axes.linewidth": 0.8,
        "axes.edgecolor": RATIO_STYLE["reference"],
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "legend.fontsize": 9.0,
        "xaxis.labellocation": "center",
        "yaxis.labellocation": "center",
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
    with plt.style.context(mplhep.style.CMS), matplotlib.rc_context(style):
        figure, axis = plt.subplots(figsize=figure_size, dpi=120)
        figure.subplots_adjust(left=0.085, right=0.98, bottom=0.15, top=0.77)
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
                    color=RATIO_STYLE["reference"],
                    linewidth=0.8,
                    linestyle=":",
                    zorder=2,
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
                ecolor=RATIO_STYLE["accent"],
                elinewidth=0.5,
                capsize=0.0,
                alpha=0.42,
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
                alpha=0.78,
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
            ("below", "v", low + boundary_offset),
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
                [low + 2.8 * boundary_offset] * len(display["invalid"]),
                marker="x",
                s=28.0,
                color=RATIO_STYLE["warning"],
                linewidth=1.0,
                zorder=13,
            )

        axis.axhline(
            1.0,
            color=RATIO_STYLE["reference"],
            linewidth=1.15,
            linestyle=(0, (5.0, 2.5)),
            zorder=3,
        )
        axis.set_xlim(0.5, size + 0.5)
        axis.set_ylim(low, high)
        axis.set_ylabel("Data / prompt MC")
        axis.set_xlabel(f"Run number (selected labels; all {size} runs shown)")
        axis.set_xticks([index for index, _ in selected_labels])
        axis.set_xticklabels([label for _, label in selected_labels], fontsize=8.2)
        axis.set_yticks(np.arange(low, high + 0.001, 0.1))
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

        for span in spans:
            center = 0.5 * (span["first_bin"] + span["last_bin"])
            axis.text(
                center,
                high - 0.025 * (high - low),
                f"{span['era']}\n{span['recorded_lumi_fb']:.3g} fb$^{{-1}}$",
                ha="center",
                va="top",
                color=RATIO_STYLE["reference"],
                fontsize=8.8,
                fontweight="semibold",
                linespacing=0.9,
                zorder=15,
            )

        figure.text(
            0.085,
            0.955,
            "CMS",
            ha="left",
            va="top",
            fontsize=18.0,
            fontweight="bold",
        )
        figure.text(
            0.132,
            0.953,
            "Work in progress",
            ha="left",
            va="top",
            fontsize=12.0,
            fontstyle="italic",
        )
        figure.text(
            0.98,
            0.953,
            "2022–2024 (13.6 TeV)",
            ha="right",
            va="top",
            fontsize=11.5,
        )
        figure.text(
            0.085,
            0.895,
            "DY Data/MC run stability",
            ha="left",
            va="top",
            fontsize=15.0,
            fontweight="bold",
        )
        if luminosity_source == "nominal":
            source_label = "nominal recorded luminosity"
        elif luminosity_source == "trigger_any":
            source_label = "Trigger-Any effective recorded luminosity"
        else:
            source_label = (
                luminosity_source.replace("_", " ") + " effective recorded luminosity"
            )
        observable_label = "Z mass yield" if observable == "Z0_mass" else observable
        category_label = category.replace("_", " ")
        figure.text(
            0.085,
            0.855,
            f"{category_label}  |  {observable_label}  |  {source_label}",
            ha="left",
            va="top",
            fontsize=10.5,
            color=RATIO_STYLE["reference"],
        )

        handles = [
            Line2D(
                [],
                [],
                color=RATIO_STYLE["accent"],
                marker="o",
                markerfacecolor=RATIO_STYLE["data"],
                markeredgecolor=RATIO_STYLE["data"],
                markersize=4.0,
                linewidth=0.7,
                label="Data/MC (68% stat.)",
            ),
            Line2D(
                [],
                [],
                color=RATIO_STYLE["reference"],
                linestyle=(0, (5.0, 2.5)),
                linewidth=1.15,
                label="Unity",
            ),
        ]
        if display["above"] or display["below"]:
            handles.append(
                Line2D(
                    [],
                    [],
                    color=RATIO_STYLE["warning"],
                    marker="^",
                    linestyle="none",
                    markersize=5.2,
                    label=(
                        "Outside 0.5–1.5 (directional; "
                        f"{len(display['above']) + len(display['below'])})"
                    ),
                )
            )
        if display["invalid"]:
            handles.append(
                Line2D(
                    [],
                    [],
                    color=RATIO_STYLE["warning"],
                    marker="x",
                    linestyle="none",
                    markersize=5.2,
                    label=f"Zero-lumi / undefined ({len(display['invalid'])})",
                )
            )
        figure.legend(
            handles=handles,
            loc="upper right",
            bbox_to_anchor=(0.98, 0.895),
            ncol=2,
            frameon=False,
            handlelength=2.0,
            columnspacing=1.2,
        )
        figure.text(
            0.98,
            0.025,
            "Triangles mark central values outside the display range; full values and uncertainties are retained in CSV/ROOT.",
            ha="right",
            va="bottom",
            fontsize=8.0,
            color=RATIO_STYLE["reference"],
        )

        png_path = output_dir / f"{stem}.png"
        pdf_path = output_dir / f"{stem}.pdf"
        metadata = {
            "Title": f"DY Data/MC run stability: {category}, {observable}",
            "Creator": "ZZ_CR_RunStability plot_run_stability.py",
        }
        figure.savefig(png_path, dpi=120, metadata=metadata)
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
        "run_label_policy": "one centered label per up-to-90-run era segment; all points retained",
        "selected_run_labels": [
            {"bin": index, "run": int(label)} for index, label in selected_labels
        ],
        "era_spans": spans,
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
        source_definitions = _contract_luminosity_sources(contract)
        for source, source_definition in source_definitions.items():
            rows = source_definition["rows"]
            if len(rows) != len(runs):
                raise RuntimeError(
                    f"Compiled luminosity source {source} has {len(rows)} rows; "
                    f"expected {len(runs)}"
                )
            source_values = {}
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
        vm = float(mc_total.GetBinError(index) ** 2)
        result = ratio_with_uncertainty(d, m, vm)
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
                result = ratio_with_uncertainty(
                    data_yield, denominator, mc_variance * scale * scale
                )
            rows.append(
                {
                    "era": era,
                    "run": int(run),
                    "recorded_lumi_fb": luminosity,
                    "data_yield": data_yield,
                    "mc_yield": denominator,
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
    output_dir.mkdir(parents=True, exist_ok=True)
    era_token = "_".join(dataset["contract"]["analysis_era"] for dataset in datasets)
    stem = f"ratio_vs_run_{era_token}_{category}_{observable}_{luminosity_source}"
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
    mc_hist = ROOT.TH1D(
        "mc_yield_by_run", ";Run;Scaled prompt MC", size, 0.5, size + 0.5
    )
    lumi_hist = ROOT.TH1D(
        "recorded_lumi_fb_by_run",
        ";Run;Recorded luminosity [fb^{-1}]",
        size,
        0.5,
        size + 0.5,
    )
    graph = ROOT.TGraphAsymmErrors(size)
    graph.SetName("ratio_graph_garwood_plus_mcstat")
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
                index, math.sqrt(covariance_total[index - 1][index - 1])
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
        "schema_version": 2,
        "kind": "data_mc_ratio_vs_run",
        "datasets": [_dataset_identity(dataset) for dataset in datasets],
        "category": category,
        "observable": observable,
        "luminosity_source": luminosity_source,
        "uncertainty_model": {
            "data_graph": "central 68.2689492137% Garwood Poisson interval",
            "mc": "ordinary TH1 Sumw2 scaled by (L_run/L_MC_source)^2",
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


def _single_dataset(args, require_lumi=False):
    luminosity_source = getattr(args, "luminosity_source", None)
    if require_lumi and not luminosity_source:
        raise RuntimeError("--luminosity-source is required")
    return validate_dataset(args.config, args.input, luminosity_source)


def _print_inventory(dataset, as_json=False):
    inventory = {
        "analysis_era": dataset["contract"]["analysis_era"],
        "target_region": dataset["contract"].get("target_region", "DY"),
        "categories": list(dataset["contract"]["categories"]),
        "observables": list(dataset["contract"]["observables"]),
        "runs": list(dataset["runs"]),
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
        print(f"prompt MC processes: {len(inventory['mc_processes'])}")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "validate", "plot"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument(
            "--config", required=True, help="exact compiled config pickle"
        )
        subparser.add_argument(
            "--input", required=True, help="exact merged ROOT file or XRootD URL"
        )
        if name == "list":
            subparser.add_argument("--json", action="store_true")
        if name == "plot":
            subparser.add_argument("--category", required=True)
            subparser.add_argument("--observable", required=True)
            subparser.add_argument("--run", required=True, type=int)
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
    receipt = make_ratio_vs_run(
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
