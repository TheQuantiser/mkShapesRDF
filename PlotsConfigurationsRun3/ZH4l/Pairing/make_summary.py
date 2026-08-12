#!/usr/bin/env python3
"""Build process-separated pairing-study tables from merged mkShapes ROOT files.

The mkShapes writer deliberately unrolls TH2/TH3 objects.  This reader restores
their logical axes from ``variables.py``'s stable contract; it never guesses an
axis order from bin labels.  ZH and ZZ are aggregated independently because
their truth definitions are different.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from pairing_config import SUPPORTED_ERAS, load_pairing_year  # noqa: E402

# Keep the historical summary JSON schema (``year``/``missing_years``) stable
# while the runtime-facing configuration consistently uses ERA.


ALGORITHMS = {
    0: "nearest_mZ",
    1: "core_l4kin_massless",
    2: "historical_run2_massless",
    3: "resolution_pull",
    4: "fsr_nearest_mZ",
    5: "fsr_resolution_pull",
}
TOPOLOGIES = {1: "4e", 2: "4mu", 3: "2e2mu", 4: "3e1mu", 5: "1e3mu"}
TRUTH_STATUS = {
    0: "unavailable",
    1: "direct",
    2: "tau",
    3: "unrecoverable",
    4: "recoverable",
    5: "ambiguous",
    6: "alignment_invalid",
}
REGIONS = {0: "outside", 1: "ZZCR", 2: "XSF_SR", 3: "XDF_SR"}
X_FLAVORS = {0: "invalid", 1: "SF", 2: "DF"}
CANDIDATES = {-1: "invalid", **{i: f"candidate_{i}" for i in range(7)}}
BASELINES = ("PAIRING_OBJECT_BASE", "PAIRING_PHYS_BASE")
CONVENTIONS = ("raw", "signed", "absolute")
EFF_SHAPE = (6, 5, 4)  # algorithm, topology, correctness {-2,-1,0,1}


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _json_number(value):
    if value is None:
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _ratio(numerator, denominator):
    if numerator is None or denominator is None:
        return None
    if not math.isfinite(float(denominator)) or abs(float(denominator)) < 1e-15:
        return None
    value = float(numerator) / float(denominator)
    return value if math.isfinite(value) else None


def _sum(values):
    return float(math.fsum(float(v) for v in values))


def _add_arrays(arrays, size):
    out = [0.0] * size
    for array in arrays:
        for index, value in enumerate(array):
            out[index] += value
    return out


def _flat_index(shape, indices):
    # mkShapesRDF's postPlot unroller preserves ROOT's bin order: x (the
    # first logical axis) changes fastest, then y, then z.
    index = 0
    stride = 1
    for bins, coordinate in zip(shape, indices):
        if coordinate < 0 or coordinate >= bins:
            raise IndexError(f"axis index {coordinate} outside [0,{bins})")
        index += coordinate * stride
        stride *= bins
    return index


def _cell(array, shape, *indices):
    return array[_flat_index(shape, indices)]


def _project(array, shape, fixed):
    """Sum a flat logical cube, optionally fixing axis indices."""
    total = 0.0
    for flat, value in enumerate(array):
        remainder = flat
        coordinates = [0] * len(shape)
        for axis in range(len(shape)):
            coordinates[axis] = remainder % shape[axis]
            remainder //= shape[axis]
        if all(coordinates[axis] == coordinate for axis, coordinate in fixed.items()):
            total += value
    return total


def _physical_xflavor_offdiagonal(cube):
    """Count only physical SF<->DF changes, excluding unavailable bin zero."""
    shape = (6, 3, 3)
    return _sum(
        _cell(cube, shape, algorithm, x_from, x_to)
        for algorithm in range(shape[0])
        for x_from, x_to in ((1, 2), (2, 1))
    )


class RootReader:
    """Small lazy PyROOT reader with strict logical-shape validation."""

    def __init__(self, inputs, warnings, strict=False):
        try:
            import ROOT
        except ImportError as exc:  # pragma: no cover - environment diagnostic
            raise RuntimeError("PyROOT is required; source the repository start.sh") from exc
        ROOT.gROOT.SetBatch(True)
        self.ROOT = ROOT
        self.warnings = warnings
        self.strict = strict
        self.files = {}
        self.cache = {}
        for year, path in inputs.items():
            handle = ROOT.TFile.Open(str(path), "READ")
            if not handle or handle.IsZombie():
                raise OSError(f"Cannot open ERA={year} ROOT input: {path}")
            self.files[year] = handle

    def close(self):
        for handle in self.files.values():
            handle.Close()

    def read(self, year, baseline, variable, sample, shape, required=False):
        cache_key = (year, baseline, variable, sample, shape)
        if cache_key in self.cache:
            return self.cache[cache_key]
        path = f"{baseline}/{variable}/histo_{sample}"
        histogram = self.files[year].Get(path)
        if not histogram:
            message = f"ERA={year}: missing {path}"
            if required or self.strict:
                raise KeyError(message)
            self.warnings.append(message)
            self.cache[cache_key] = None
            return None
        expected = math.prod(shape)
        if histogram.GetDimension() == 1:
            if histogram.GetNbinsX() != expected:
                message = (
                    f"ERA={year}: {path} has {histogram.GetNbinsX()} unrolled bins; "
                    f"expected {expected} for logical shape {shape}"
                )
                if required or self.strict:
                    raise ValueError(message)
                self.warnings.append(message)
                self.cache[cache_key] = None
                return None
            result = [float(histogram.GetBinContent(index + 1)) for index in range(expected)]
        elif histogram.GetDimension() == len(shape):
            actual = tuple(
                (histogram.GetNbinsX(), histogram.GetNbinsY(), histogram.GetNbinsZ())[axis]
                for axis in range(len(shape))
            )
            if actual != tuple(shape):
                raise ValueError(f"ERA={year}: {path} shape {actual}, expected {shape}")
            result = [0.0] * expected
            if len(shape) == 2:
                for x in range(1, shape[0] + 1):
                    for y in range(1, shape[1] + 1):
                        result[_flat_index(shape, (x - 1, y - 1))] = float(
                            histogram.GetBinContent(x, y)
                        )
            elif len(shape) == 3:
                for x in range(1, shape[0] + 1):
                    for y in range(1, shape[1] + 1):
                        for z in range(1, shape[2] + 1):
                            result[_flat_index(shape, (x - 1, y - 1, z - 1))] = float(
                                histogram.GetBinContent(x, y, z)
                            )
            else:
                raise ValueError(f"Unsupported logical dimension {len(shape)}")
        else:
            raise ValueError(
                f"ERA={year}: {path} is dimension {histogram.GetDimension()}, "
                f"expected flattened TH1 or {len(shape)}D"
            )
        self.cache[cache_key] = result
        return result

    def aggregate(self, year, baseline, variable, samples, shape, required=False):
        arrays = []
        for sample in samples:
            array = self.read(year, baseline, variable, sample, shape, required=required)
            if array is not None:
                arrays.append(array)
        if not arrays:
            return None
        return _add_arrays(arrays, math.prod(shape))


def _year_token(path, year):
    stem = Path(path).name
    return bool(re.search(rf"(?:^|[_-]){re.escape(year)}(?:[_-]|\.)", stem))


def _discover_inputs(root):
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Auto-discovery root does not exist: {root}")
    result = {}
    all_roots = list(root.rglob("*.root"))
    for year in SUPPORTED_ERAS:
        pattern = re.compile(rf"^mkShapes__PairingStudy_{re.escape(year)}_.+\.root$")
        candidates = [path for path in all_roots if pattern.match(path.name)]
        if not candidates:
            continue
        if len(candidates) > 1:
            details = "\n  ".join(str(path) for path in sorted(candidates))
            raise RuntimeError(
                f"Ambiguous merged ROOT files for ERA={year} below {root}:\n  {details}\n"
                "Pass explicit ERA=ROOT inputs."
            )
        result[year] = str(candidates[0])
    if not result:
        raise FileNotFoundError(f"No merged PairingStudy ROOT files found below {root}")
    return result


def _parse_input_specs(specs):
    result = {}
    for spec in specs:
        if "=" not in spec:
            raise ValueError(f"Input must be ERA=ROOT, got {spec!r}")
        year, path = spec.split("=", 1)
        year = year.strip()
        path = path.strip()
        if year not in SUPPORTED_ERAS:
            raise ValueError(f"Unsupported input year {year!r}")
        if not path:
            raise ValueError(f"Empty ROOT path for ERA={year}")
        if year in result:
            raise ValueError(f"ERA={year} was supplied more than once")
        if not path.startswith("root://") and not Path(path).expanduser().is_file():
            raise FileNotFoundError(f"ERA={year} input does not exist: {path}")
        result[year] = str(Path(path).expanduser().resolve()) if not path.startswith("root://") else path
    return result


def _config_inventory(year, root_path):
    live = load_pairing_year(year)
    campaign = None
    match = re.match(rf"mkShapes__PairingStudy_{re.escape(year)}_(.+)\.root$", Path(root_path).name)
    if match:
        campaign = match.group(1)
    metadata = None
    if campaign:
        config_path = HERE / "configs" / campaign / year / "config.json"
        if config_path.is_file():
            with config_path.open(encoding="utf-8") as handle:
                metadata = json.load(handle).get("PAIRING_SAMPLE_INVENTORY")
    families = {}
    for family in ("ZH", "ZZ"):
        logical = []
        by_name = {}
        if metadata:
            by_name = {
                item["logical_sample"]: item for item in metadata["families"].get(family, [])
            }
        for sample in live["inventory"][family]:
            recorded = by_name.get(sample)
            components = []
            for component in live["logical_components"][sample]:
                item = dict(component)
                item.setdefault("file_count", None)
                item.setdefault("available_file_count", None)
                components.append(item)
            if recorded:
                components = recorded.get("components", components)
            logical.append(
                {
                    "logical_sample": sample,
                    "file_count": recorded.get("file_count") if recorded else None,
                    "available_file_count": recorded.get("available_file_count") if recorded else None,
                    "components": components,
                }
            )
        families[family] = logical
    return {
        "year": year,
        "root_file": root_path,
        "campaign": campaign,
        "production": live["production"],
        "steps": live["steps"],
        "lumi_fb": live["lumi_fb"],
        "families": families,
        "metadata_source": "compiled config.json" if metadata else "live configuration; file counts unavailable",
    }


def _sample_groups(inventory, family):
    samples = tuple(inventory[family])
    return [(sample, (sample,)) for sample in samples] + [(f"ALL_{family}", samples)]


def _topology_indices(topology):
    return range(5) if topology == "ALL" else (int(topology) - 1,)


def _truth_counts(reader, year, baseline, family, samples, topology):
    prefix = family.lower()
    total_hist = reader.aggregate(year, baseline, "quartet_topology", samples, (5,))
    status_hist = reader.aggregate(
        year, baseline, f"{prefix}_truth_status_topology", samples, (7, 5)
    )
    direct_hist = reader.aggregate(
        year, baseline, f"{prefix}_truth_direct_topology", samples, (2, 5)
    )
    indices = tuple(_topology_indices(topology))
    n_total = _sum(total_hist[index] for index in indices) if total_hist else None
    statuses = {
        TRUTH_STATUS[status]: _sum(_cell(status_hist, (7, 5), status, index) for index in indices)
        for status in TRUTH_STATUS
    } if status_hist else {}
    n_direct = (
        _sum(_cell(direct_hist, (2, 5), 1, index) for index in indices)
        if direct_hist else None
    )
    n_record_ambiguous = None
    if family == "ZZ" and topology == "ALL":
        ambiguity = reader.aggregate(
            year, baseline, "zz_record_ambiguous", samples, (2,)
        )
        n_record_ambiguous = ambiguity[1] if ambiguity else None
    return n_total, n_direct, statuses, n_record_ambiguous


def _efficiency_rows(reader, inputs, inventories, family, baselines, warnings):
    rows = []
    year_combined = []
    for year in inputs:
        for sample_label, samples in _sample_groups(inventories[year], family):
            for baseline in baselines:
                cubes = {
                    convention: reader.aggregate(
                        year,
                        baseline,
                        f"{family.lower()}_efficiency_{convention}",
                        samples,
                        EFF_SHAPE,
                        required=False,
                    )
                    for convention in CONVENTIONS
                }
                if cubes["raw"] is None:
                    warnings.append(
                        f"ERA={year} family={family} sample={sample_label} baseline={baseline}: "
                        "efficiency cube unavailable"
                    )
                    continue
                for topology in [*TOPOLOGIES, "ALL"]:
                    n_total, n_direct, statuses, n_record_ambiguous = _truth_counts(
                        reader, year, baseline, family, samples, topology
                    )
                    topology_indices = tuple(_topology_indices(topology))
                    for algorithm, algorithm_name in ALGORITHMS.items():
                        row = {
                            "year": year,
                            "sample": sample_label,
                            "family": family,
                            "metric": (
                                "associated_z_label_correct"
                                if family == "ZH"
                                else "two_boson_partition_correct"
                            ),
                            "algorithm": algorithm_name,
                            "algorithm_code": algorithm,
                            "topology": TOPOLOGIES.get(topology, topology),
                            "topology_code": topology,
                            "baseline": baseline,
                            "N_total": _json_number(n_total),
                            "N_truth_direct_Zll" if family == "ZH" else "N_truth_direct_4l": _json_number(n_direct),
                            "N_truth_recoverable" if family == "ZH" else "N_partition_valid": None,
                            "N_record_ambiguous": (
                                _json_number(n_record_ambiguous) if family == "ZZ" else None
                            ),
                            "record_ambiguity_scope": (
                                "all topologies from dedicated truth flag"
                                if family == "ZZ" and topology == "ALL"
                                else (
                                    "not booked by topology"
                                    if family == "ZZ" else None
                                )
                            ),
                            "N_correct": None,
                            "truth_interpretation": (
                                "associated-Z label-sensitive"
                                if family == "ZH"
                                else _zz_interpretation(topology)
                            ),
                        }
                        for convention, cube in cubes.items():
                            prefix = {
                                "raw": "raw",
                                "signed": "signed_weight",
                                "absolute": "absolute_weight",
                            }[convention]
                            if cube is None:
                                wrong = correct = unavailable_truth = unavailable_algorithm = None
                            else:
                                wrong = _sum(
                                    _cell(cube, EFF_SHAPE, algorithm, index, 2)
                                    for index in topology_indices
                                )
                                correct = _sum(
                                    _cell(cube, EFF_SHAPE, algorithm, index, 3)
                                    for index in topology_indices
                                )
                                unavailable_algorithm = _sum(
                                    _cell(cube, EFF_SHAPE, algorithm, index, 0)
                                    for index in topology_indices
                                )
                                unavailable_truth = _sum(
                                    _cell(cube, EFF_SHAPE, algorithm, index, 1)
                                    for index in topology_indices
                                )
                            denominator = None if wrong is None else wrong + correct
                            row[f"{prefix}_wrong"] = _json_number(wrong)
                            row[f"{prefix}_correct"] = _json_number(correct)
                            row[f"{prefix}_denominator"] = _json_number(denominator)
                            row[f"{prefix}_truth_unavailable"] = _json_number(unavailable_truth)
                            row[f"{prefix}_algorithm_unavailable"] = _json_number(unavailable_algorithm)
                            row[f"{prefix}_efficiency"] = _json_number(_ratio(correct, denominator))
                        # The truth-valid population is algorithm independent.
                        # The cube denominator can be smaller for an unavailable
                        # comparator, so retain both quantities explicitly.
                        row["N_truth_recoverable" if family == "ZH" else "N_partition_valid"] = _json_number(
                            statuses.get("recoverable")
                        )
                        row["N_correct"] = row["raw_correct"]
                        rows.append(row)
                        if sample_label == f"ALL_{family}":
                            year_combined.append(row)

    # ALL_RUN3 is always built from family-aggregated yields.  It is not an
    # average of era efficiencies, and is still emitted for partial pilots.
    keys = defaultdict(list)
    for row in year_combined:
        keys[(row["algorithm_code"], row["topology_code"], row["baseline"])].append(row)
    for (_, _, _), group in keys.items():
        template = dict(group[0])
        template["year"] = "ALL_RUN3"
        template["sample"] = f"ALL_{family}"
        for field in list(template):
            if field.startswith(("raw_", "signed_weight_", "absolute_weight_")) and not field.endswith("efficiency"):
                values = [row[field] for row in group]
                template[field] = None if any(value is None for value in values) else _sum(values)
        for prefix in ("raw", "signed_weight", "absolute_weight"):
            template[f"{prefix}_efficiency"] = _json_number(
                _ratio(template[f"{prefix}_correct"], template[f"{prefix}_denominator"])
            )
        for field in (
            "N_total",
            "N_truth_direct_Zll" if family == "ZH" else "N_truth_direct_4l",
            "N_truth_recoverable" if family == "ZH" else "N_partition_valid",
            "N_record_ambiguous",
            "N_correct",
        ):
            values = [row.get(field) for row in group]
            template[field] = None if any(value is None for value in values) else _sum(values)
        rows.append(template)
    return rows


def _zz_interpretation(topology):
    if topology in (1, 2):
        return "identical-flavor generator-record convention"
    if topology == 3:
        return "flavor-distinguishable two-boson partition"
    if topology in (4, 5):
        return "not direct-four-lepton ZZ truth topology"
    return "mixed: distinguishable and identical-flavor record convention"


def _aggregate_metric_rows(reader, inputs, inventories, baselines):
    agreement = []
    migrations = []
    aggregate_cache = defaultdict(list)
    matrix_specs = (
        ("candidate", "candidate_migration", (6, 8, 8), CANDIDATES, -1, "raw"),
        ("region", "region_migration", (6, 4, 4), REGIONS, 0, "signed"),
        ("region", "region_migration_raw", (6, 4, 4), REGIONS, 0, "raw"),
        (
            "region",
            "region_migration_absolute",
            (6, 4, 4),
            REGIONS,
            0,
            "absolute",
        ),
        ("x_flavor", "xflavor_closure", (6, 3, 3), X_FLAVORS, 0, "raw"),
    )
    for year in inputs:
        for family in ("ZH", "ZZ"):
            for sample_label, samples in _sample_groups(inventories[year], family):
                for baseline in baselines:
                    for matrix, variable, shape, labels, offset, convention in matrix_specs:
                        cube = reader.aggregate(year, baseline, variable, samples, shape)
                        if cube is None:
                            continue
                        for algorithm, algorithm_name in ALGORITHMS.items():
                            total = _project(cube, shape, {0: algorithm})
                            diagonal = _sum(
                                _cell(cube, shape, algorithm, index, index)
                                for index in range(shape[1])
                            )
                            if matrix == "candidate":
                                agreement.append(
                                    {
                                        "year": year,
                                        "family": family,
                                        "sample": sample_label,
                                        "baseline": baseline,
                                        "metric": "candidate_assignment_agreement",
                                        "algorithm": algorithm_name,
                                        "algorithm_code": algorithm,
                                        "weight_convention": convention,
                                        "N_total": _json_number(total),
                                        "N_agree_with_nearest_mZ": _json_number(diagonal),
                                        "agreement_fraction": _json_number(_ratio(diagonal, total)),
                                    }
                                )
                            for from_index in range(shape[1]):
                                for to_index in range(shape[2]):
                                    row = {
                                        "year": year,
                                        "family": family,
                                        "sample": sample_label,
                                        "baseline": baseline,
                                        "matrix": matrix,
                                        "algorithm": algorithm_name,
                                        "algorithm_code": algorithm,
                                        "weight_convention": convention,
                                        "from_code": from_index + offset,
                                        "from_label": labels[from_index + offset],
                                        "to_code": to_index + offset,
                                        "to_label": labels[to_index + offset],
                                        "yield": _json_number(_cell(cube, shape, algorithm, from_index, to_index)),
                                    }
                                    migrations.append(row)
                                    if sample_label == f"ALL_{family}":
                                        aggregate_cache[
                                            (
                                                family,
                                                baseline,
                                                matrix,
                                                convention,
                                                algorithm,
                                                from_index,
                                                to_index,
                                            )
                                        ].append(row)

    for key, group in aggregate_cache.items():
        (
            family,
            baseline,
            matrix,
            convention,
            algorithm,
            from_index,
            to_index,
        ) = key
        row = dict(group[0])
        row["year"] = "ALL_RUN3"
        row["sample"] = f"ALL_{family}"
        row["yield"] = _sum(item["yield"] for item in group)
        migrations.append(row)

    agreement_groups = defaultdict(list)
    for row in agreement:
        if row["sample"] == f"ALL_{row['family']}":
            agreement_groups[(row["family"], row["baseline"], row["algorithm_code"])].append(row)
    for group in agreement_groups.values():
        row = dict(group[0])
        row["year"] = "ALL_RUN3"
        row["sample"] = f"ALL_{row['family']}"
        row["N_total"] = _sum(item["N_total"] for item in group)
        row["N_agree_with_nearest_mZ"] = _sum(item["N_agree_with_nearest_mZ"] for item in group)
        row["agreement_fraction"] = _json_number(
            _ratio(row["N_agree_with_nearest_mZ"], row["N_total"])
        )
        agreement.append(row)
    agreement.extend(_gain_loss_rows(reader, inputs, inventories, baselines))
    return agreement, migrations


def _gain_loss_rows(reader, inputs, inventories, baselines):
    """Extract exact event-level correctness transitions relative to algo 0."""
    rows = []
    aggregate = defaultdict(list)
    outcome_fields = (
        "algorithm_unavailable",
        "truth_unavailable",
        "both_wrong",
        "loss",
        "gain",
        "both_correct",
    )
    for year in inputs:
        for family in ("ZH", "ZZ"):
            for sample_label, samples in _sample_groups(inventories[year], family):
                for baseline in baselines:
                    cubes = {
                        convention: reader.aggregate(
                            year,
                            baseline,
                            f"{family.lower()}_gain_loss_{convention}",
                            samples,
                            (6, 6),
                        )
                        for convention in CONVENTIONS
                    }
                    if cubes["raw"] is None:
                        continue
                    for algorithm, algorithm_name in ALGORITHMS.items():
                        row = {
                            "year": year,
                            "family": family,
                            "sample": sample_label,
                            "baseline": baseline,
                            "metric": "truth_correctness_gain_loss",
                            "algorithm": algorithm_name,
                            "algorithm_code": algorithm,
                            "reference_algorithm": ALGORITHMS[0],
                        }
                        for convention, cube in cubes.items():
                            prefix = {
                                "raw": "raw",
                                "signed": "signed_weight",
                                "absolute": "absolute_weight",
                            }[convention]
                            values = [
                                _cell(cube, (6, 6), algorithm, outcome)
                                if cube is not None else None
                                for outcome in range(6)
                            ]
                            for field, value in zip(outcome_fields, values):
                                row[f"{prefix}_{field}"] = _json_number(value)
                            valid = (
                                None if values[2] is None else _sum(values[2:])
                            )
                            row[f"{prefix}_truth_valid"] = _json_number(valid)
                            row[f"{prefix}_net_gain"] = _json_number(
                                None if values[3] is None else values[4] - values[3]
                            )
                            row[f"{prefix}_gain_fraction"] = _json_number(
                                _ratio(values[4], valid)
                            )
                            row[f"{prefix}_loss_fraction"] = _json_number(
                                _ratio(values[3], valid)
                            )
                        rows.append(row)
                        if sample_label == f"ALL_{family}":
                            aggregate[(family, baseline, algorithm)].append(row)

    for group in aggregate.values():
        row = dict(group[0])
        row["year"] = "ALL_RUN3"
        row["sample"] = f"ALL_{row['family']}"
        for prefix in ("raw", "signed_weight", "absolute_weight"):
            for field in (*outcome_fields, "truth_valid", "net_gain"):
                key = f"{prefix}_{field}"
                values = [item[key] for item in group]
                row[key] = None if any(value is None for value in values) else _sum(values)
            row[f"{prefix}_gain_fraction"] = _json_number(
                _ratio(row[f"{prefix}_gain"], row[f"{prefix}_truth_valid"])
            )
            row[f"{prefix}_loss_fraction"] = _json_number(
                _ratio(row[f"{prefix}_loss"], row[f"{prefix}_truth_valid"])
            )
        rows.append(row)
    return rows


def _truth_diagnostics(reader, inputs, inventories, baselines):
    records = []
    negatives = []
    matching_quality = []
    for year in inputs:
        for family in ("ZH", "ZZ"):
            for sample_label, samples in _sample_groups(inventories[year], family):
                for baseline in baselines:
                    status = reader.aggregate(
                        year, baseline, f"{family.lower()}_truth_status_topology", samples, (7, 5)
                    )
                    if status is not None:
                        for status_code, status_label in TRUTH_STATUS.items():
                            for topology_code, topology_label in TOPOLOGIES.items():
                                records.append(
                                    {
                                        "year": year,
                                        "family": family,
                                        "sample": sample_label,
                                        "baseline": baseline,
                                        "status_code": status_code,
                                        "status": status_label,
                                        "topology_code": topology_code,
                                        "topology": topology_label,
                                        "raw_events": _cell(status, (7, 5), status_code, topology_code - 1),
                                    }
                                )
                    signs = reader.aggregate(
                        year, baseline, "event_weight_sign", samples, (3,)
                    )
                    if signs is not None:
                        negative, zero, positive = signs
                        negatives.append(
                            {
                                "year": year,
                                "family": family,
                                "sample": sample_label,
                                "baseline": baseline,
                                "negative_raw_events": negative,
                                "positive_raw_events": positive,
                                "zero_raw_events": zero,
                                "negative_fraction": _json_number(_ratio(negative, negative + positive + zero)),
                                "source": "categorical event_weight_sign histogram",
                            }
                        )

                    # These two-bin counters are deliberately exported alongside
                    # the truth-status cube.  Keeping them event-level makes the
                    # distinction between source-record validity, score validity,
                    # and truth recoverability explicit instead of silently
                    # folding all failures into one efficiency denominator.
                    counter_names = {
                        "source_alignment": "source_alignment_valid",
                        "resolution_scores": "resolution_scores_valid",
                        "fsr_scores": "fsr_scores_valid",
                    }
                    counters = {
                        label: reader.aggregate(year, baseline, histogram, samples, (2,))
                        for label, histogram in counter_names.items()
                    }
                    family_counter_name = (
                        "zh_hww_complement_valid"
                        if family == "ZH"
                        else "zz_record_ambiguous"
                    )
                    family_counter = reader.aggregate(
                        year, baseline, family_counter_name, samples, (2,)
                    )
                    if status is not None or any(value is not None for value in counters.values()):
                        n_recoverable = (
                            _sum(
                                _cell(status, (7, 5), 4, topology_code - 1)
                                for topology_code in TOPOLOGIES
                            )
                            if status is not None
                            else None
                        )
                        quality = {
                            "year": year,
                            "family": family,
                            "sample": sample_label,
                            "baseline": baseline,
                            "N_truth_recoverable": _json_number(n_recoverable),
                        }
                        for label, counter in counters.items():
                            total = _sum(counter) if counter is not None else None
                            valid = counter[1] if counter is not None else None
                            quality[f"N_{label}_total"] = _json_number(total)
                            quality[f"N_{label}_valid"] = _json_number(valid)
                            quality[f"{label}_valid_fraction"] = _json_number(
                                _ratio(valid, total)
                            )
                        if family_counter is not None:
                            family_true = family_counter[1]
                            if family == "ZH":
                                quality["N_hww_complement_valid"] = _json_number(family_true)
                                quality["hww_complement_fraction_of_recoverable"] = _json_number(
                                    _ratio(family_true, n_recoverable)
                                )
                            else:
                                quality["N_record_ambiguous"] = _json_number(family_true)
                                quality["record_ambiguous_fraction_of_recoverable"] = _json_number(
                                    _ratio(family_true, n_recoverable)
                                )
                        matching_quality.append(quality)

    # Form complete-Run-3 diagnostics from summed event counts, never from an
    # average of per-era fractions.  Restrict aggregation to the family-combined
    # rows so component aliases with year-dependent names cannot be mixed.
    count_fields = (
        "N_truth_recoverable",
        "N_source_alignment_total",
        "N_source_alignment_valid",
        "N_resolution_scores_total",
        "N_resolution_scores_valid",
        "N_fsr_scores_total",
        "N_fsr_scores_valid",
    )
    for family in ("ZH", "ZZ"):
        for baseline in baselines:
            group = [
                item
                for item in matching_quality
                if item["year"] in inputs
                and item["family"] == family
                and item["sample"] == f"ALL_{family}"
                and item["baseline"] == baseline
            ]
            if not group:
                continue
            aggregate = {
                "year": "ALL_RUN3",
                "family": family,
                "sample": f"ALL_{family}",
                "baseline": baseline,
            }
            for field in count_fields:
                values = [item.get(field) for item in group]
                aggregate[field] = (
                    None if any(value is None for value in values) else _sum(values)
                )
            for label in ("source_alignment", "resolution_scores", "fsr_scores"):
                aggregate[f"{label}_valid_fraction"] = _json_number(
                    _ratio(
                        aggregate[f"N_{label}_valid"],
                        aggregate[f"N_{label}_total"],
                    )
                )
            family_field = (
                "N_hww_complement_valid" if family == "ZH" else "N_record_ambiguous"
            )
            family_values = [item.get(family_field) for item in group]
            aggregate[family_field] = (
                None
                if any(value is None for value in family_values)
                else _sum(family_values)
            )
            fraction_field = (
                "hww_complement_fraction_of_recoverable"
                if family == "ZH"
                else "record_ambiguous_fraction_of_recoverable"
            )
            aggregate[fraction_field] = _json_number(
                _ratio(aggregate[family_field], aggregate["N_truth_recoverable"])
            )
            matching_quality.append(aggregate)

    return {
        "truth_status": records,
        "negative_weight_diagnostics": negatives,
        "matching_quality": matching_quality,
    }


def _x_ranking(reader, inputs, inventories, baselines):
    records = []
    for year in inputs:
        for family in ("ZH", "ZZ"):
            for sample_label, samples in _sample_groups(inventories[year], family):
                for baseline in baselines:
                    identity = reader.aggregate(year, baseline, "x_complement_identical", samples, (2,))
                    reasons = reader.aggregate(year, baseline, "x_difference_reason", samples, (4,))
                    closure = reader.aggregate(year, baseline, "xflavor_closure", samples, (6, 3, 3))
                    if identity is None and reasons is None and closure is None:
                        continue
                    n_total = _sum(identity) if identity else None
                    valid_z_total = (
                        _sum(reasons[index] for index in (0, 1, 2))
                        if reasons
                        else None
                    )
                    record = {
                        "year": year,
                        "family": family,
                        "sample": sample_label,
                        "baseline": baseline,
                        "raw_total": n_total,
                        "raw_identical": identity[1] if identity else None,
                        "raw_different": identity[0] if identity else None,
                        "identity_fraction_all_events": (
                            _json_number(_ratio(identity[1], n_total))
                            if identity
                            else None
                        ),
                        "raw_valid_nearest_z": valid_z_total,
                        "identity_fraction": (
                            _json_number(_ratio(reasons[0], valid_z_total))
                            if reasons
                            else None
                        ),
                        "identity_fraction_scope": "events with a valid nearest-mZ candidate",
                        "difference_reasons": {
                            "identical": reasons[0],
                            "live_x_invalid_or_not_two": reasons[1],
                            "different_pair": reasons[2],
                            "no_valid_nearest_z": reasons[3],
                        } if reasons else None,
                    }
                    if closure:
                        off_diagonal = _physical_xflavor_offdiagonal(closure)
                        record["x_flavor_off_diagonal_raw"] = off_diagonal
                        record["fixed_quartet_xsf_xdf_diagonal"] = abs(off_diagonal) < 1e-12
                    records.append(record)

    # Aggregate only the already family-combined rows.  This keeps unlike ZH
    # aliases across production campaigns out of the key while still forming
    # ALL_RUN3 from summed event counts rather than averaged fractions.
    for family in ("ZH", "ZZ"):
        for baseline in baselines:
            group = [
                record
                for record in records
                if record["family"] == family
                and record["sample"] == f"ALL_{family}"
                and record["baseline"] == baseline
                and record["year"] in inputs
            ]
            if not group:
                continue
            reasons = {
                label: _sum(record["difference_reasons"][label] for record in group)
                for label in (
                    "identical",
                    "live_x_invalid_or_not_two",
                    "different_pair",
                    "no_valid_nearest_z",
                )
            }
            raw_total = _sum(record["raw_total"] for record in group)
            raw_identical = _sum(record["raw_identical"] for record in group)
            raw_valid = _sum(record["raw_valid_nearest_z"] for record in group)
            off_diagonal = _sum(
                record.get("x_flavor_off_diagonal_raw", 0.0) for record in group
            )
            records.append(
                {
                    "year": "ALL_RUN3",
                    "family": family,
                    "sample": f"ALL_{family}",
                    "baseline": baseline,
                    "raw_total": raw_total,
                    "raw_identical": raw_identical,
                    "raw_different": raw_total - raw_identical,
                    "identity_fraction_all_events": _json_number(
                        _ratio(raw_identical, raw_total)
                    ),
                    "raw_valid_nearest_z": raw_valid,
                    "identity_fraction": _json_number(
                        _ratio(reasons["identical"], raw_valid)
                    ),
                    "identity_fraction_scope": (
                        "events with a valid nearest-mZ candidate"
                    ),
                    "difference_reasons": reasons,
                    "x_flavor_off_diagonal_raw": off_diagonal,
                    "fixed_quartet_xsf_xdf_diagonal": abs(off_diagonal) < 1e-12,
                }
            )
    return {
        "claim": (
            "Within a fixed charge-zero quartet, an OS Z leaves a unique OS X complement; "
            "explicit X ranking has no additional combinatorial freedom."
        ),
        "records": records,
    }


def _plot_data(reader, inputs, inventories, baselines):
    data = {
        "efficiency_vs_truth_ptz": [],
        "efficiency_vs_score_gap": [],
        "candidate_multiplicity": [],
        "selected_mx": [],
        "ptz_response": [],
    }
    curve_specs = (
        ("ZH", "zh_correct_vs_truth_ptz", "efficiency_vs_truth_ptz", 60, 0.0, 300.0),
        ("ZZ", "zz_score_gap_correctness", "efficiency_vs_score_gap", 80, 0.0, 40.0),
    )
    for year in inputs:
        for family in ("ZH", "ZZ"):
            samples = inventories[year][family]
            for baseline in baselines:
                for curve_family, variable, destination, bins, low, high in curve_specs:
                    if family != curve_family:
                        continue
                    cube = reader.aggregate(year, baseline, variable, samples, (6, bins, 4))
                    if cube:
                        width = (high - low) / bins
                        for algorithm, algorithm_name in ALGORITHMS.items():
                            for axis_bin in range(bins):
                                wrong = _cell(cube, (6, bins, 4), algorithm, axis_bin, 2)
                                correct = _cell(cube, (6, bins, 4), algorithm, axis_bin, 3)
                                data[destination].append(
                                    {
                                        "year": year,
                                        "family": family,
                                        "sample": f"ALL_{family}",
                                        "baseline": baseline,
                                        "algorithm": algorithm_name,
                                        "algorithm_code": algorithm,
                                        "x_low": low + axis_bin * width,
                                        "x_high": low + (axis_bin + 1) * width,
                                        "wrong": wrong,
                                        "correct": correct,
                                        "efficiency": _json_number(_ratio(correct, wrong + correct)),
                                    }
                                )
                multiplicity = reader.aggregate(year, baseline, "candidate_multiplicity", samples, (7,))
                if multiplicity:
                    for code, value in enumerate(multiplicity):
                        data["candidate_multiplicity"].append(
                            {"year": year, "family": family, "baseline": baseline, "multiplicity": code, "raw_events": value}
                        )
                selected_mx = reader.aggregate(year, baseline, "selected_mx", samples, (6, 100))
                if selected_mx:
                    for algorithm, algorithm_name in ALGORITHMS.items():
                        for axis_bin in range(100):
                            data["selected_mx"].append(
                                {
                                    "year": year, "family": family, "baseline": baseline,
                                    "algorithm": algorithm_name, "algorithm_code": algorithm,
                                    "x_low": axis_bin * 2.0, "x_high": (axis_bin + 1) * 2.0,
                                    "signed_yield": _cell(selected_mx, (6, 100), algorithm, axis_bin),
                                }
                            )
                response = reader.aggregate(year, baseline, f"{family.lower()}_ptz_response", samples, (6, 80, 4))
                if response:
                    for algorithm, algorithm_name in ALGORITHMS.items():
                        for axis_bin in range(80):
                            for correct_index, correctness in ((2, "wrong"), (3, "correct")):
                                data["ptz_response"].append(
                                    {
                                        "year": year, "family": family, "baseline": baseline,
                                        "algorithm": algorithm_name, "algorithm_code": algorithm,
                                        "correctness": correctness,
                                        "x_low": -2.0 + axis_bin * 0.05,
                                        "x_high": -2.0 + (axis_bin + 1) * 0.05,
                                        "signed_yield": _cell(response, (6, 80, 4), algorithm, axis_bin, correct_index),
                                    }
                                )
    return data


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def _parser():
    parser = argparse.ArgumentParser(
        description="Summarize merged ZH/ZZ PairingStudy ROOT files without mixing truth domains."
    )
    parser.add_argument(
        "inputs", nargs="*", metavar="ERA=ROOT",
        help="explicit merged input; may be repeated (also accepted via --input)",
    )
    parser.add_argument("-i", "--input", action="append", default=[], metavar="ERA=ROOT")
    parser.add_argument(
        "--input-root", default=os.environ.get("PAIRING_OUTPUT_ROOT"),
        help="campaign directory to auto-discover when no ERA=ROOT is supplied",
    )
    parser.add_argument("-o", "--output-dir", default=str(HERE / "summary"))
    parser.add_argument(
        "--baseline", action="append", choices=BASELINES,
        help="baseline to summarize; repeatable (default: both)",
    )
    parser.add_argument("--strict", action="store_true", help="fail on every missing optional histogram")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    specs = [*args.inputs, *args.input]
    if specs:
        inputs = _parse_input_specs(specs)
    else:
        input_root = args.input_root or str(HERE / "rootFiles")
        inputs = _discover_inputs(input_root)
    inputs = {year: inputs[year] for year in SUPPORTED_ERAS if year in inputs}
    baselines = tuple(args.baseline or BASELINES)
    output = Path(args.output_dir).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    warnings = []
    inventories = {year: load_pairing_year(year)["inventory"] for year in inputs}
    inventory_payload = {
        "generated_at_utc": _utc_now(),
        "complete_run3": tuple(inputs) == tuple(SUPPORTED_ERAS),
        "missing_years": [year for year in SUPPORTED_ERAS if year not in inputs],
        "years": [_config_inventory(year, path) for year, path in inputs.items()],
    }
    _write_json(output / "sample_inventory.json", inventory_payload)

    reader = RootReader(inputs, warnings, strict=args.strict)
    try:
        zh_rows = _efficiency_rows(reader, inputs, inventories, "ZH", baselines, warnings)
        zz_rows = _efficiency_rows(reader, inputs, inventories, "ZZ", baselines, warnings)
        agreement, migrations = _aggregate_metric_rows(reader, inputs, inventories, baselines)
        truth = _truth_diagnostics(reader, inputs, inventories, baselines)
        x_ranking = _x_ranking(reader, inputs, inventories, baselines)
        plot_data = _plot_data(reader, inputs, inventories, baselines)
    finally:
        reader.close()

    common_metadata = {
        "generated_at_utc": _utc_now(),
        "years_present": list(inputs),
        "complete_run3": tuple(inputs) == tuple(SUPPORTED_ERAS),
        "all_run3_aggregation": "sum numerators and denominators, then divide",
        "correctness_axis": {"-2": "algorithm unavailable", "-1": "truth unavailable", "0": "wrong", "1": "correct"},
        "baselines": list(baselines),
    }
    _write_csv(output / "zh_pairing_efficiency.csv", zh_rows)
    _write_json(output / "zh_pairing_efficiency.json", {**common_metadata, "truth_contract": "unique associated-Z label correctness", "rows": zh_rows})
    _write_csv(output / "zz_partition_efficiency.csv", zz_rows)
    _write_json(output / "zz_partition_efficiency.json", {**common_metadata, "truth_contract": "label-invariant two-boson partition fidelity", "rows": zz_rows})
    _write_csv(output / "algorithm_agreement.csv", agreement)
    _write_csv(output / "migration_matrix.csv", migrations)
    _write_json(output / "truth_matching_diagnostics.json", {**common_metadata, **truth})
    _write_json(output / "x_ranking_redundancy.json", {**common_metadata, **x_ranking})
    _write_json(output / "plot_data.json", {**common_metadata, **plot_data})
    _write_json(
        output / "summary_manifest.json",
        {
            **common_metadata,
            "inputs": inputs,
            "warnings": sorted(set(warnings)),
            "products": [
                "sample_inventory.json", "zh_pairing_efficiency.csv", "zh_pairing_efficiency.json",
                "zz_partition_efficiency.csv", "zz_partition_efficiency.json",
                "algorithm_agreement.csv", "migration_matrix.csv",
                "truth_matching_diagnostics.json", "x_ranking_redundancy.json", "plot_data.json",
            ],
                "weight_availability": {
                    "efficiency": ["raw", "signed", "absolute"],
                    "event_level_gain_loss": ["raw", "signed", "absolute"],
                    "candidate_migration_and_agreement": ["raw"],
                    "region_migration": ["raw", "signed", "absolute"],
                "truth_and_x_ranking": ["raw"],
            },
        },
    )
    print(f"Wrote PairingStudy summaries to {output}")
    if warnings:
        print(f"Recorded {len(set(warnings))} non-fatal warning(s) in summary_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
