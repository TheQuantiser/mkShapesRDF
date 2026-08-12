#!/usr/bin/env python3
"""Render concise PairingStudy figures from ``make_summary.py`` products."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ALGORITHMS = (
    "nearest_mZ",
    "core_l4kin_massless",
    "historical_run2_massless",
    "resolution_pull",
    "fsr_nearest_mZ",
    "fsr_resolution_pull",
)
ALGORITHM_LABELS = {
    "nearest_mZ": r"nearest $m_Z$",
    "core_l4kin_massless": "core massless",
    "historical_run2_massless": "Run-2 massless",
    "resolution_pull": "resolution pull",
    "fsr_nearest_mZ": r"FSR nearest $m_Z$",
    "fsr_resolution_pull": "FSR resolution pull",
}
YEARS = ("2022", "2022EE", "2023", "2023BPix", "2024")
TOPOLOGIES = ("4e", "4mu", "2e2mu", "3e1mu", "1e3mu")
REGION_LABELS = ("outside", "ZZCR", "XSF SR", "XDF SR")
CANDIDATE_LABELS = ("invalid", "0", "1", "2", "3", "4", "5", "6")


def _read_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path):
    if not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _number(value):
    if value in (None, "", "None", "null"):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _ratio(numerator, denominator):
    if numerator is None or denominator is None or abs(denominator) < 1e-15:
        return None
    value = numerator / denominator
    return value if math.isfinite(value) else None


def _sum(values):
    return float(math.fsum(float(value) for value in values))


class PlotBook:
    def __init__(self, output, formats, metadata):
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        self.plt = plt
        self.output = output
        self.formats = formats
        self.metadata = metadata
        self.records = []
        output.mkdir(parents=True, exist_ok=True)
        plt.rcParams.update(
            {
                "font.size": 10,
                "axes.labelsize": 11,
                "axes.titlesize": 11,
                "legend.fontsize": 8,
                "figure.dpi": 130,
                "savefig.bbox": "tight",
                "axes.grid": True,
                "grid.alpha": 0.2,
            }
        )

    def save(self, name, figure, note=None):
        files = []
        for extension in self.formats:
            path = self.output / f"{name}.{extension}"
            figure.savefig(path, dpi=180 if extension == "png" else None)
            files.append(path.name)
        self.plt.close(figure)
        self.records.append({"product": name, "status": "generated", "files": files, "note": note})

    def skip(self, name, reason):
        self.records.append({"product": name, "status": "skipped", "reason": reason})

    def finish(self):
        expected = [
            "01_zh_efficiency_by_algorithm", "02_zh_efficiency_by_year",
            "03_zh_efficiency_by_topology", "04_zz_partition_efficiency_by_algorithm",
            "05_zz_partition_efficiency_by_year", "06_zz_partition_efficiency_by_topology",
            "07_zh_efficiency_vs_truth_pTZ", "08_zz_efficiency_vs_score_gap",
            "09_candidate_multiplicity_by_process", "10_mX_response_zh",
            "11_mX_response_zz", "12_pTZ_response_zh",
            "13_algorithm_candidate_migration", "14_region_migration_zh",
            "15_region_migration_zz", "16_fsr_resolution_gain_loss",
        ]
        seen = {record["product"] for record in self.records}
        for product in expected:
            if product not in seen:
                self.skip(product, "No plotting implementation or supported source metric was available.")
        payload = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "summary_metadata": self.metadata,
            "formats": list(self.formats),
            "products": sorted(self.records, key=lambda item: item["product"]),
        }
        with (self.output / "plot_manifest.json").open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
            handle.write("\n")


def _primary_rows(rows, family, baseline):
    expected_sample = f"ALL_{family}"
    return [
        row for row in rows
        if row.get("sample") == expected_sample and row.get("baseline") == baseline
    ]


def _eff_by_algorithm(book, rows, family, number, title, baseline):
    selected = [
        row for row in _primary_rows(rows, family, baseline)
        if row.get("year") == "ALL_RUN3" and row.get("topology") == "ALL"
    ]
    lookup = {row["algorithm"]: row for row in selected}
    available = [algorithm for algorithm in ALGORITHMS if _number(lookup.get(algorithm, {}).get("raw_denominator"))]
    name = f"{number}_{'zh_efficiency' if family == 'ZH' else 'zz_partition_efficiency'}_by_algorithm"
    if not available:
        book.skip(name, "No nonzero raw truth denominator in ALL_RUN3.")
        return
    fig, ax = book.plt.subplots(figsize=(8.0, 4.8))
    x = list(range(len(available)))
    for offset, (prefix, label, marker) in enumerate(
        (("raw", "raw", "o"), ("signed_weight", "signed weight", "s"), ("absolute_weight", "absolute weight", "^"))
    ):
        values = [_number(lookup[algorithm].get(f"{prefix}_efficiency")) for algorithm in available]
        valid = [(index, value) for index, value in enumerate(values) if value is not None]
        if valid:
            ax.plot(
                [index + (offset - 1) * 0.08 for index, _ in valid],
                [value for _, value in valid], marker=marker, linestyle="none", label=label,
            )
    ax.set_xticks(x, [ALGORITHM_LABELS[item] for item in available], rotation=25, ha="right")
    ax.set_ylabel("Correct assignment / truth-valid")
    ax.set_ylim(0.0, 1.08)
    ax.set_title(title + " — yield-summed Run 3")
    ax.legend(frameon=False, ncol=3)
    book.save(name, fig)


def _eff_by_year(book, rows, family, number, title, baseline):
    selected = [
        row for row in _primary_rows(rows, family, baseline)
        if row.get("year") in YEARS and row.get("topology") == "ALL"
    ]
    lookup = {(row["year"], row["algorithm"]): row for row in selected}
    algorithms = [
        algorithm for algorithm in ALGORITHMS
        if any((_number(lookup.get((year, algorithm), {}).get("raw_denominator")) or 0) > 0 for year in YEARS)
    ]
    name = f"{number}_{'zh_efficiency' if family == 'ZH' else 'zz_partition_efficiency'}_by_year"
    if not algorithms:
        book.skip(name, "No algorithm has a nonzero raw truth denominator in any era.")
        return
    fig, ax = book.plt.subplots(figsize=(8.0, 4.8))
    for algorithm in algorithms:
        points = []
        for index, year in enumerate(YEARS):
            row = lookup.get((year, algorithm), {})
            value = _number(row.get("raw_efficiency"))
            if value is not None:
                points.append((index, value))
        if points:
            ax.plot([x for x, _ in points], [y for _, y in points], marker="o", label=ALGORITHM_LABELS[algorithm])
    ax.set_xticks(range(len(YEARS)), YEARS)
    ax.set_ylabel("Raw correctness efficiency")
    ax.set_ylim(0.0, 1.08)
    ax.set_title(title + " — era dependence")
    ax.legend(frameon=False, ncol=2)
    book.save(name, fig)


def _eff_by_topology(book, rows, family, number, title, baseline):
    selected = [
        row for row in _primary_rows(rows, family, baseline)
        if row.get("year") == "ALL_RUN3" and row.get("topology") in TOPOLOGIES
    ]
    lookup = {(row["topology"], row["algorithm"]): row for row in selected}
    algorithms = [
        algorithm for algorithm in ALGORITHMS
        if any((_number(lookup.get((topology, algorithm), {}).get("raw_denominator")) or 0) > 0 for topology in TOPOLOGIES)
    ]
    name = f"{number}_{'zh_efficiency' if family == 'ZH' else 'zz_partition_efficiency'}_by_topology"
    if not algorithms:
        book.skip(name, "No topology has a nonzero raw truth denominator.")
        return
    fig, ax = book.plt.subplots(figsize=(8.0, 4.8))
    for algorithm in algorithms:
        points = []
        for index, topology in enumerate(TOPOLOGIES):
            value = _number(lookup.get((topology, algorithm), {}).get("raw_efficiency"))
            if value is not None:
                points.append((index, value))
        if points:
            ax.plot([x for x, _ in points], [y for _, y in points], marker="o", label=ALGORITHM_LABELS[algorithm])
    ax.set_xticks(range(len(TOPOLOGIES)), TOPOLOGIES)
    ax.set_ylabel("Raw correctness efficiency")
    ax.set_ylim(0.0, 1.08)
    ax.set_title(title + " — yield-summed Run 3")
    ax.legend(frameon=False, ncol=2)
    book.save(name, fig)


def _summed_curve(records, family, baseline):
    grouped = defaultdict(lambda: [0.0, 0.0, None, None])
    for row in records:
        if row.get("family") != family or row.get("baseline") != baseline:
            continue
        key = (row["algorithm"], float(row["x_low"]), float(row["x_high"]))
        grouped[key][0] += float(row["wrong"])
        grouped[key][1] += float(row["correct"])
        grouped[key][2] = key[1]
        grouped[key][3] = key[2]
    curves = defaultdict(list)
    for (algorithm, low, high), (wrong, correct, _, _) in grouped.items():
        efficiency = _ratio(correct, wrong + correct)
        if efficiency is not None:
            curves[algorithm].append(((low + high) / 2.0, efficiency, wrong + correct))
    for curve in curves.values():
        curve.sort()
    return curves


def _curve_plot(book, name, curves, xlabel, title):
    curves = {algorithm: points for algorithm, points in curves.items() if points}
    if not curves:
        book.skip(name, "No nonempty truth-valid curve bins are available.")
        return
    if all(len(points) < 2 for points in curves.values()):
        book.skip(name, "Only one populated x bin is available; a curve would be trivial.")
        return
    fig, ax = book.plt.subplots(figsize=(7.4, 4.8))
    for algorithm in ALGORITHMS:
        points = curves.get(algorithm)
        if not points:
            continue
        ax.plot([x for x, _, _ in points], [y for _, y, _ in points], marker="o", markersize=3, label=ALGORITHM_LABELS[algorithm])
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Raw correctness efficiency")
    ax.set_ylim(0.0, 1.08)
    ax.set_title(title)
    ax.legend(frameon=False, ncol=2)
    book.save(name, fig)


def _candidate_multiplicity(book, records, baseline):
    grouped = defaultdict(float)
    for row in records:
        if row.get("baseline") == baseline:
            grouped[(row["family"], int(row["multiplicity"]))] += float(row["raw_events"])
    name = "09_candidate_multiplicity_by_process"
    if not grouped or all(abs(value) < 1e-15 for value in grouped.values()):
        book.skip(name, "Candidate-multiplicity histograms are empty or unavailable.")
        return
    fig, ax = book.plt.subplots(figsize=(7.0, 4.6))
    for family, marker in (("ZH", "o"), ("ZZ", "s")):
        x = list(range(7))
        y = [grouped[(family, value)] for value in x]
        norm = _sum(y)
        if norm > 0:
            ax.step(x, [value / norm for value in y], where="mid", label=family)
            ax.plot(x, [value / norm for value in y], marker=marker, linestyle="none")
    ax.set_xlabel("Number of OS-SF Z candidates")
    ax.set_ylabel("Raw event fraction")
    ax.set_title("Pairing-candidate multiplicity — yield-summed Run 3")
    ax.legend(frameon=False)
    book.save(name, fig)


def _ptz_response(book, records, baseline):
    grouped = defaultdict(float)
    for row in records:
        if row.get("family") == "ZH" and row.get("baseline") == baseline:
            key = (row["algorithm"], row["correctness"], float(row["x_low"]), float(row["x_high"]))
            grouped[key] += float(row["signed_yield"])
    name = "12_pTZ_response_zh"
    if not grouped or all(abs(value) < 1e-15 for value in grouped.values()):
        book.skip(name, "ZH pT(Z) response histogram is empty or unavailable.")
        return
    fig, axes = book.plt.subplots(1, 2, figsize=(12.0, 4.5), sharex=True)
    drew = False
    for axis, correctness in zip(axes, ("correct", "wrong")):
        for algorithm in ALGORITHMS:
            points = sorted(
                ((0.5 * (low + high), value) for (algo, state, low, high), value in grouped.items() if algo == algorithm and state == correctness),
                key=lambda item: item[0],
            )
            norm = _sum(abs(value) for _, value in points)
            if norm <= 1e-15:
                continue
            drew = True
            axis.plot([x for x, _ in points], [y / norm for _, y in points], label=ALGORITHM_LABELS[algorithm])
        axis.set_title(correctness.capitalize() + " assignment")
        axis.set_xlabel(r"$(p_T^{reco}(Z)-p_T^{truth}(Z))/p_T^{truth}(Z)$")
    if not drew:
        book.plt.close(fig)
        book.skip(name, "No nonzero ZH response curve remains after aggregation.")
        return
    axes[0].set_ylabel("Signed yield / sum absolute yield")
    axes[1].legend(frameon=False, fontsize=7)
    fig.suptitle("ZH associated-Z transverse-momentum response")
    book.save(name, fig, note="Curves use signed yields normalized by their sum of absolute bin yields.")


def _matrix_records(rows, matrix, family, baseline, weight_convention):
    grouped = defaultdict(float)
    for row in rows:
        if (
            row.get("year") == "ALL_RUN3"
            and row.get("sample") == f"ALL_{family}"
            and row.get("baseline") == baseline
            and row.get("matrix") == matrix
            and row.get("weight_convention") == weight_convention
        ):
            grouped[(row["algorithm"], int(row["from_code"]), int(row["to_code"]))] += float(row["yield"])
    return grouped


def _heatmap_grid(
    book,
    name,
    rows,
    matrix,
    families,
    labels,
    code_offset,
    baseline,
    weight_convention,
    title,
):
    comparisons = ALGORITHMS[1:]
    matrices = {
        family: _matrix_records(
            rows, matrix, family, baseline, weight_convention
        )
        for family in families
    }
    if not any(matrices[family] for family in families):
        book.skip(name, f"No {matrix} migration rows are available.")
        return
    nrows = len(families)
    fig, axes = book.plt.subplots(
        nrows,
        len(comparisons),
        figsize=(3.0 * len(comparisons) + 0.8, 3.2 * nrows),
        squeeze=False,
        layout="constrained",
    )
    drew = False
    for row_index, family in enumerate(families):
        family_values = {}
        family_scale = 0.0
        family_has_negative = False
        for algorithm in comparisons:
            values = [
                [
                    matrices[family].get(
                        (algorithm, i + code_offset, j + code_offset), 0.0
                    )
                    for j in range(len(labels))
                ]
                for i in range(len(labels))
            ]
            family_values[algorithm] = values
            family_scale = max(
                family_scale,
                max((abs(value) for line in values for value in line), default=0.0),
            )
            family_has_negative = family_has_negative or any(
                value < 0.0 for line in values for value in line
            )
        row_image = None
        for column, algorithm in enumerate(comparisons):
            axis = axes[row_index][column]
            values = family_values[algorithm]
            scale = max((abs(value) for line in values for value in line), default=0.0)
            if scale <= 1e-15:
                axis.set_axis_off()
                axis.set_title(ALGORITHM_LABELS[algorithm] + "\n(empty)")
                continue
            drew = True
            if family_has_negative:
                row_image = axis.imshow(
                    values,
                    origin="lower",
                    aspect="auto",
                    cmap="coolwarm",
                    vmin=-family_scale,
                    vmax=family_scale,
                )
            else:
                row_image = axis.imshow(
                    values,
                    origin="lower",
                    aspect="auto",
                    cmap="viridis",
                    vmin=0.0,
                    vmax=family_scale,
                )
            axis.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=7)
            axis.set_yticks(range(len(labels)), labels if column == 0 else [], fontsize=7)
            axis.set_title(ALGORITHM_LABELS[algorithm], fontsize=9)
            if column == 0:
                axis.set_ylabel(f"{family}: nearest $m_Z$")
            if row_index == nrows - 1:
                axis.set_xlabel("Comparator selection")
        if row_image is not None:
            colorbar = fig.colorbar(
                row_image,
                ax=list(axes[row_index]),
                fraction=0.018,
                pad=0.02,
            )
            colorbar.set_label(weight_convention + " yield", fontsize=9)
    if not drew:
        book.plt.close(fig)
        book.skip(name, f"All {matrix} comparator matrices are empty.")
        return
    fig.suptitle(title)
    book.save(name, fig)


def _region_migration(book, rows, family, baseline, number):
    name = f"{number}_region_migration_{family.lower()}"
    _heatmap_grid(
        book, name, rows, "region", (family,), REGION_LABELS, 0, baseline,
        "signed",
        f"{family} region migration relative to nearest $m_Z$ (signed yield)",
    )


def _gain_loss_plot(book, rows, baseline):
    """Plot exact joint transitions; never infer them from efficiency deltas."""
    algorithms = ALGORITHMS[3:6]
    selected = {
        (row.get("family"), row.get("algorithm")): row
        for row in rows
        if row.get("metric") == "truth_correctness_gain_loss"
        and row.get("year") == "ALL_RUN3"
        and row.get("sample") == f"ALL_{row.get('family')}"
        and row.get("baseline") == baseline
        and row.get("algorithm") in algorithms
    }
    name = "16_fsr_resolution_gain_loss"
    if not selected:
        book.skip(name, "Exact event-level gain/loss cubes are unavailable.")
        return
    fig, axes = book.plt.subplots(1, 2, figsize=(11.0, 4.5), sharey=True)
    width = 0.34
    drew = False
    for axis, family in zip(axes, ("ZH", "ZZ")):
        x = list(range(len(algorithms)))
        gain = []
        loss = []
        for algorithm in algorithms:
            row = selected.get((family, algorithm), {})
            gain.append(_number(row.get("raw_gain_fraction")))
            loss.append(_number(row.get("raw_loss_fraction")))
        if any(value is not None for value in gain + loss):
            drew = True
            axis.bar(
                [value - width / 2 for value in x],
                [value or 0.0 for value in gain],
                width, label="gain: baseline wrong, comparator correct", color="#2a9d8f",
            )
            axis.bar(
                [value + width / 2 for value in x],
                [value or 0.0 for value in loss],
                width, label="loss: baseline correct, comparator wrong", color="#e76f51",
            )
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_xticks(x, [ALGORITHM_LABELS[item] for item in algorithms], rotation=20, ha="right")
        axis.set_title(family)
        axis.set_xlabel(r"Comparator relative to nearest $m_Z$")
    if not drew:
        book.plt.close(fig)
        book.skip(name, "Exact event-level cubes exist but all truth-valid denominators are empty.")
        return
    axes[0].set_ylabel("Raw event fraction of truth-valid denominator")
    axes[1].legend(frameon=False, fontsize=8)
    fig.suptitle("Event-level pairing gains and losses — yield-summed Run 3")
    book.save(
        name,
        fig,
        note="Exact joint correctness states for algorithms 3–5; no marginal-efficiency inference.",
    )


def _parser():
    parser = argparse.ArgumentParser(description="Plot PairingStudy summary products as PNG/PDF.")
    parser.add_argument("--summary-dir", default=str(HERE / "summary"))
    parser.add_argument("-o", "--output-dir", default=str(HERE / "plots"))
    parser.add_argument(
        "--baseline", default="PAIRING_PHYS_BASE",
        choices=("PAIRING_OBJECT_BASE", "PAIRING_PHYS_BASE"),
    )
    parser.add_argument(
        "--formats", default="png,pdf",
        help="comma-separated output formats (default: png,pdf)",
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    formats = tuple(item.strip().lower() for item in args.formats.split(",") if item.strip())
    unsupported = set(formats) - {"png", "pdf"}
    if not formats or unsupported:
        raise ValueError(f"Formats must be png and/or pdf; invalid={sorted(unsupported)}")
    summary = Path(args.summary_dir).expanduser().resolve()
    required = (
        "zh_pairing_efficiency.json", "zz_partition_efficiency.json",
        "algorithm_agreement.csv", "migration_matrix.csv", "plot_data.json",
        "summary_manifest.json",
    )
    missing = [name for name in required if not (summary / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing summary products in {summary}: {missing}; run make_summary.py first")

    zh = _read_json(summary / "zh_pairing_efficiency.json")
    zz = _read_json(summary / "zz_partition_efficiency.json")
    plot_data = _read_json(summary / "plot_data.json")
    agreement = _read_csv(summary / "algorithm_agreement.csv")
    migrations = _read_csv(summary / "migration_matrix.csv")
    manifest = _read_json(summary / "summary_manifest.json")
    book = PlotBook(Path(args.output_dir).expanduser().resolve(), formats, {
        "years_present": manifest.get("years_present", []),
        "complete_run3": manifest.get("complete_run3", False),
        "baseline": args.baseline,
    })

    _eff_by_algorithm(book, zh["rows"], "ZH", "01", "ZH associated-Z correctness", args.baseline)
    _eff_by_year(book, zh["rows"], "ZH", "02", "ZH associated-Z correctness", args.baseline)
    _eff_by_topology(book, zh["rows"], "ZH", "03", "ZH associated-Z correctness", args.baseline)
    _eff_by_algorithm(book, zz["rows"], "ZZ", "04", "ZZ two-boson partition fidelity", args.baseline)
    _eff_by_year(book, zz["rows"], "ZZ", "05", "ZZ two-boson partition fidelity", args.baseline)
    _eff_by_topology(book, zz["rows"], "ZZ", "06", "ZZ two-boson partition fidelity", args.baseline)
    _curve_plot(
        book, "07_zh_efficiency_vs_truth_pTZ",
        _summed_curve(plot_data.get("efficiency_vs_truth_ptz", []), "ZH", args.baseline),
        r"truth $p_T(Z)$ [GeV]", "ZH associated-Z correctness versus truth kinematics",
    )
    _curve_plot(
        book, "08_zz_efficiency_vs_score_gap",
        _summed_curve(plot_data.get("efficiency_vs_score_gap", []), "ZZ", args.baseline),
        "best–second score gap", "ZZ partition fidelity versus score separation",
    )
    _candidate_multiplicity(book, plot_data.get("candidate_multiplicity", []), args.baseline)
    book.skip(
        "10_mX_response_zh",
        "No truth-mX response histogram is booked; selected_mx is not a response and is not relabeled.",
    )
    book.skip(
        "11_mX_response_zz",
        "No truth-mX response histogram is booked; selected_mx is not a response and is not relabeled.",
    )
    _ptz_response(book, plot_data.get("ptz_response", []), args.baseline)
    _heatmap_grid(
        book, "13_algorithm_candidate_migration", migrations, "candidate", ("ZH", "ZZ"),
        CANDIDATE_LABELS, -1, args.baseline,
        "raw",
        "Candidate migration relative to nearest $m_Z$ (raw events)",
    )
    _region_migration(book, migrations, "ZH", args.baseline, "14")
    _region_migration(book, migrations, "ZZ", args.baseline, "15")
    _gain_loss_plot(book, agreement, args.baseline)
    book.finish()
    print(f"Wrote PairingStudy plots and plot_manifest.json to {book.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
