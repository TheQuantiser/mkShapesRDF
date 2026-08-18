"""Compile-time run and luminosity contract for DATA run-stability shapes."""

import csv
import hashlib
import json
import math
import os
from pathlib import Path

from category_config import (
    RUN_STABILITY_HLT_PATH_SOURCES,
    RUN_STABILITY_TRIGGER_FAMILY_SOURCES,
    build_categories,
)
from histogram_config import DY_ANALYSIS


RUN_STABILITY_REGION = (
    str(
        globals().get("RUN_STABILITY_REGION")
        or os.environ.get("RUN_STABILITY_REGION", "DY")
    )
    .strip()
    .upper()
)


def _csv_selector(raw, setting):
    items = tuple(item.strip() for item in raw.split(",") if item.strip())
    duplicates = sorted({item for item in items if items.count(item) > 1})
    if duplicates:
        raise ValueError(f"Duplicate {setting} names are not allowed: {duplicates}")
    return items


def _resolve_run_stability_matrix():
    if RUN_STABILITY_REGION != "DY":
        raise ValueError(
            "ZZ_CR_RunStability now supports only RUN_STABILITY_REGION=DY; "
            f"received {RUN_STABILITY_REGION!r}"
        )
    _, category_metadata, _ = build_categories("RUN_STABILITY", "standard")
    available_categories = tuple(category_metadata)
    available_observables = tuple(DY_ANALYSIS)
    observable_selector = str(
        globals().get("RUN_STABILITY_OBSERVABLE_SELECTOR")
        or os.environ.get(
            "RUN_STABILITY_OBSERVABLES",
            "all_dy",
        )
    ).strip()
    category_selector = str(
        globals().get("RUN_STABILITY_CATEGORY_SELECTOR")
        or os.environ.get(
            "RUN_STABILITY_CATEGORIES",
            "all_dy",
        )
    ).strip()

    if observable_selector.lower() == "all_dy":
        observables = available_observables
    else:
        observables = _csv_selector(observable_selector, "RUN_STABILITY_OBSERVABLES")
    if category_selector.lower() == "all_dy":
        categories = available_categories
    else:
        categories = _csv_selector(category_selector, "RUN_STABILITY_CATEGORIES")

    missing_observables = sorted(set(observables) - set(available_observables))
    missing_categories = sorted(set(categories) - set(available_categories))
    if not observables or missing_observables:
        raise ValueError(
            "Invalid RUN_STABILITY_OBSERVABLES selection; "
            f"unknown={missing_observables}, available={list(available_observables)}"
        )
    if not categories or missing_categories:
        raise ValueError(
            "Invalid RUN_STABILITY_CATEGORIES selection; "
            f"unknown={missing_categories}, available={list(available_categories)}"
        )
    return (
        tuple(observables),
        tuple(categories),
        observable_selector,
        category_selector,
        available_observables,
        available_categories,
        {
            name: category_metadata[name]["run_stability_luminosity_source"]
            for name in categories
        },
    )


(
    RUN_STABILITY_OBSERVABLES,
    RUN_STABILITY_CATEGORIES,
    RUN_STABILITY_OBSERVABLE_SELECTOR,
    RUN_STABILITY_CATEGORY_SELECTOR,
    RUN_STABILITY_AVAILABLE_OBSERVABLES,
    RUN_STABILITY_AVAILABLE_CATEGORIES,
    RUN_STABILITY_CATEGORY_LUMINOSITY_SOURCES,
) = _resolve_run_stability_matrix()

RUN_STABILITY_LUMINOSITY_SOURCE_DEFINITIONS = {
    "nominal": {
        "kind": "nominal",
        "scope_name": "certified_configured_input",
        "label": "Nominal configured certified exposure",
    },
    "trigger_any": {
        "kind": "combination",
        "scope_name": "Trigger_Any",
        "label": "Positive all-path trigger union",
    },
}
for _split_id, (_source, _scope_name) in RUN_STABILITY_TRIGGER_FAMILY_SOURCES.items():
    RUN_STABILITY_LUMINOSITY_SOURCE_DEFINITIONS[_source] = {
        "kind": "combination",
        "scope_name": _scope_name,
        "label": f"Positive trigger family {_scope_name}",
    }
for _split_id, (_source, _scope_name) in RUN_STABILITY_HLT_PATH_SOURCES.items():
    RUN_STABILITY_LUMINOSITY_SOURCE_DEFINITIONS[_source] = {
        "kind": "hlt_path",
        "scope_name": _scope_name,
        "label": f"Concrete HLT path {_scope_name}",
    }

RUN_STABILITY_METADATA_PATHS = tuple(
    f"run_stability/metadata/{source}_{quantity}_lumi_fb"
    for source in RUN_STABILITY_LUMINOSITY_SOURCE_DEFINITIONS
    for quantity in ("delivered", "recorded")
) + ("run_stability/metadata/mc_source_lumi_fb",)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid run-stability JSON input {path}: {exc}") from exc


def _read_csv(path):
    try:
        with open(path, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error) as exc:
        raise RuntimeError(f"Invalid run-stability CSV input {path}: {exc}") from exc
    if not rows:
        raise RuntimeError(f"Run-stability CSV input is empty: {path}")
    return rows


def _finite_nonnegative(value, *, field, source):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"{source}: {field} must be numeric, received {value!r}"
        ) from exc
    if not math.isfinite(number) or number < 0.0:
        raise RuntimeError(
            f"{source}: {field} must be finite and nonnegative, received {number!r}"
        )
    return number


def _unique_run_rows(rows, *, era, scope_name, source):
    selected = [
        row
        for row in rows
        if row.get("analysis_era") == era and row.get("scope_name") == scope_name
    ]
    if not selected:
        raise RuntimeError(
            f"{source}: no rows for analysis_era={era!r}, scope_name={scope_name!r}"
        )
    out = []
    seen = set()
    for row in selected:
        try:
            run = int(row.get("run", ""))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                f"{source}: invalid run value {row.get('run')!r}"
            ) from exc
        if run in seen:
            raise RuntimeError(f"{source}: duplicate run {run} for analysis_era={era}")
        seen.add(run)
        out.append(
            {
                "run": run,
                "run_period": row.get("run_period", ""),
                "delivered_fb": _finite_nonnegative(
                    row.get("delivered_fb"), field="delivered_fb", source=source
                ),
                "recorded_fb": _finite_nonnegative(
                    row.get("recorded_fb"), field="recorded_fb", source=source
                ),
                "n_lumisections": int(row.get("n_lumisections", 0)),
                "status": row.get("status", ""),
                "method": row.get("method", ""),
            }
        )
    ordered = [row["run"] for row in out]
    if ordered != sorted(ordered):
        raise RuntimeError(
            f"{source}: run rows for analysis_era={era} are not strictly ordered"
        )
    return out


def _one_aggregate(rows, *, era, scope_name, source):
    selected = [
        row
        for row in rows
        if row.get("analysis_era") == era and row.get("scope_name") == scope_name
    ]
    if len(selected) != 1:
        raise RuntimeError(
            f"{source}: expected one aggregate for era={era!r}, "
            f"scope_name={scope_name!r}; found {len(selected)}"
        )
    row = selected[0]
    return {
        "delivered_fb": _finite_nonnegative(
            row.get("delivered_fb"), field="delivered_fb", source=source
        ),
        "recorded_fb": _finite_nonnegative(
            row.get("recorded_fb"), field="recorded_fb", source=source
        ),
        "n_runs": int(row.get("n_runs", 0)),
        "n_lumisections": int(row.get("n_lumisections", 0)),
    }


def _one_year_aggregate(rows, *, analysis_year, scope_name, source):
    selected = [
        row
        for row in rows
        if row.get("analysis_year") == analysis_year
        and not row.get("analysis_era")
        and row.get("scope_name") == scope_name
    ]
    if len(selected) != 1:
        raise RuntimeError(
            f"{source}: expected one year aggregate for year={analysis_year!r}, "
            f"scope_name={scope_name!r}; found {len(selected)}"
        )
    row = selected[0]
    return {
        "delivered_fb": _finite_nonnegative(
            row.get("delivered_fb"), field="delivered_fb", source=source
        ),
        "recorded_fb": _finite_nonnegative(
            row.get("recorded_fb"), field="recorded_fb", source=source
        ),
        "n_runs": int(row.get("n_runs", 0)),
    }


def _require_close(label, observed, expected, tolerance):
    difference = abs(float(observed) - float(expected))
    if difference > tolerance:
        raise RuntimeError(
            f"Run-stability luminosity aggregate mismatch for {label}: "
            f"observed={observed:.15g}, expected={expected:.15g}, "
            f"difference={difference:.3g}, tolerance={tolerance:.3g}"
        )


def _build_cpp_index(runs):
    identity = hashlib.sha256(",".join(map(str, runs)).encode()).hexdigest()[:16]
    namespace = f"RunStability_{identity}"
    guard = f"MKSHAPESRDF_RUN_STABILITY_{identity.upper()}"
    cases = "\n".join(
        f"    case {run}u: return {index};" for index, run in enumerate(runs, 1)
    )
    source = f"""
#ifndef {guard}
#define {guard}
#include <stdexcept>
#include <string>
namespace {namespace} {{
inline int index(const unsigned int run) {{
  switch (run) {{
{cases}
    default:
      throw std::runtime_error(
          std::string("RUN_STABILITY has no audited bin for run ") +
          std::to_string(run));
  }}
}}
}}
#endif
"""
    return namespace, source.strip()


def _resolve_lumi_inputs():
    configured = os.environ.get("RUN_STABILITY_LUMI_DIR")
    if configured:
        results_dir = Path(configured).expanduser().resolve()
    else:
        workspace_root = Path(CONFIG_DIR).resolve().parents[3]
        results_dir = workspace_root / "lumi" / "results"
    lumi_root = results_dir.parent
    paths = {
        "luminosity_by_run": results_dir / "luminosity_by_run.csv",
        "luminosity_by_analysis_era": results_dir / "luminosity_by_analysis_era.csv",
        "luminosity_by_year": results_dir / "luminosity_by_year.csv",
        "trigger_combinations_by_run": results_dir / "trigger_combinations_by_run.csv",
        "trigger_combinations_by_era": results_dir / "trigger_combinations_by_era.csv",
        "trigger_combinations_by_year": results_dir
        / "trigger_combinations_by_year.csv",
        "trigger_paths_by_run": results_dir / "trigger_paths_by_run.csv",
        "trigger_paths_by_era": results_dir / "trigger_paths_by_era.csv",
        "trigger_paths_by_year": results_dir / "trigger_paths_by_year.csv",
        "validation_report": results_dir / "validation_report.json",
        "manifest": lumi_root / "inputs" / "manifest.json",
        "provenance": lumi_root / "provenance.json",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "RUN_STABILITY luminosity inputs are incomplete; missing: "
            + ", ".join(missing)
        )
    return results_dir, paths


def build_run_stability_contract():
    if str(globals().get("ANALYSIS_PASS", "")).upper() != "RUN_STABILITY":
        return (
            {
                "schema_version": 1,
                "enabled": False,
                "analysis_pass": globals().get("ANALYSIS_PASS"),
            },
            "",
            "",
        )

    results_dir, paths = _resolve_lumi_inputs()
    hashes = {name: _sha256(path) for name, path in paths.items()}
    validation = _read_json(paths["validation_report"])
    manifest = _read_json(paths["manifest"])
    provenance = _read_json(paths["provenance"])
    if validation.get("status") != "passed":
        raise RuntimeError(
            "RUN_STABILITY requires a passed luminosity validation receipt; "
            f"received {validation.get('status')!r}"
        )
    tolerance = _finite_nonnegative(
        validation.get("absolute_aggregate_tolerance_fb", 0.0),
        field="absolute_aggregate_tolerance_fb",
        source=str(paths["validation_report"]),
    )

    provenance_hashes = provenance.get("results_sha256", {})
    for name, path in paths.items():
        if name in {"manifest", "provenance"}:
            continue
        relative = f"results/{path.name}"
        if provenance_hashes.get(relative) != hashes[name]:
            raise RuntimeError(
                f"RUN_STABILITY provenance hash mismatch for {relative}: "
                f"receipt={provenance_hashes.get(relative)!r}, actual={hashes[name]!r}"
            )

    receipt_manifest_hash = provenance.get("inputs", {}).get("manifest_sha256")
    if receipt_manifest_hash != hashes["manifest"]:
        raise RuntimeError(
            "RUN_STABILITY provenance hash mismatch for inputs/manifest.json: "
            f"receipt={receipt_manifest_hash!r}, actual={hashes['manifest']!r}"
        )

    live_year_config_path = Path(CONFIG_DIR).resolve() / "year_config.json"
    if not live_year_config_path.is_file():
        raise FileNotFoundError(
            f"RUN_STABILITY live year configuration is missing: {live_year_config_path}"
        )
    live_year_config_hash = _sha256(live_year_config_path)
    manifest_year_config = manifest.get("year_config")
    if not isinstance(manifest_year_config, dict):
        raise RuntimeError(
            "RUN_STABILITY luminosity manifest has no year_config identity"
        )
    manifest_year_config_path = manifest_year_config.get("path")
    if (
        not isinstance(manifest_year_config_path, str)
        or not manifest_year_config_path.strip()
    ):
        raise RuntimeError(
            "RUN_STABILITY luminosity manifest year_config path must be a "
            "non-empty string"
        )
    manifest_year_config_candidate = Path(manifest_year_config_path).expanduser()
    if manifest_year_config_candidate.is_absolute():
        resolved_manifest_year_config_path = manifest_year_config_candidate.resolve()
    else:
        workspace_root = Path(CONFIG_DIR).resolve().parents[3]
        resolved_manifest_year_config_path = (
            workspace_root / manifest_year_config_candidate
        ).resolve()
    if resolved_manifest_year_config_path != live_year_config_path:
        raise RuntimeError(
            "RUN_STABILITY luminosity manifest year_config path mismatch: "
            f"manifest_path={manifest_year_config_path!r}, "
            f"resolved_manifest_path={str(resolved_manifest_year_config_path)!r}, "
            f"live_path={str(live_year_config_path)!r}"
        )
    manifest_year_config_hash = manifest_year_config.get("sha256")
    if manifest_year_config_hash != live_year_config_hash:
        raise RuntimeError(
            "RUN_STABILITY luminosity manifest year_config hash mismatch: "
            f"manifest_path={manifest_year_config.get('path')!r}, "
            f"manifest_sha256={manifest_year_config_hash!r}, "
            f"live_path={str(live_year_config_path)!r}, "
            f"live_sha256={live_year_config_hash!r}"
        )

    nominal_rows_all = _read_csv(paths["luminosity_by_run"])
    era = str(YEAR)
    analysis_year = str(_selected_year.get("analysis_year", era[:4]))
    nominal_rows = _unique_run_rows(
        nominal_rows_all,
        era=era,
        scope_name="certified_configured_input",
        source=str(paths["luminosity_by_run"]),
    )
    runs = [row["run"] for row in nominal_rows]
    nominal_era = _one_aggregate(
        _read_csv(paths["luminosity_by_analysis_era"]),
        era=era,
        scope_name="configured_analysis_era",
        source=str(paths["luminosity_by_analysis_era"]),
    )
    for field in ("delivered_fb", "recorded_fb"):
        _require_close(
            f"{era} nominal {field}",
            sum(row[field] for row in nominal_rows),
            nominal_era[field],
            tolerance,
        )
    if nominal_era["n_runs"] != len(runs):
        raise RuntimeError(
            "RUN_STABILITY era aggregate run counts diverge: "
            f"nominal={nominal_era['n_runs']} expected={len(runs)}"
        )

    nominal_year = _one_year_aggregate(
        _read_csv(paths["luminosity_by_year"]),
        analysis_year=analysis_year,
        scope_name="configured_analysis_year",
        source=str(paths["luminosity_by_year"]),
    )
    nominal_year_rows = [
        row
        for row in nominal_rows_all
        if row.get("analysis_year") == analysis_year
        and row.get("scope_name") == "certified_configured_input"
    ]
    for field in ("delivered_fb", "recorded_fb"):
        _require_close(
            f"{analysis_year} nominal {field}",
            sum(
                _finite_nonnegative(
                    row[field], field=field, source=str(paths["luminosity_by_run"])
                )
                for row in nominal_year_rows
            ),
            nominal_year[field],
            tolerance,
        )
    if nominal_year["n_runs"] != len(nominal_year_rows):
        raise RuntimeError(
            "RUN_STABILITY year aggregate run counts diverge: "
            f"nominal={nominal_year['n_runs']} expected={len(nominal_year_rows)}"
        )

    luminosity_sources = {
        "nominal": {
            **RUN_STABILITY_LUMINOSITY_SOURCE_DEFINITIONS["nominal"],
            "rows": nominal_rows,
            "era_aggregate": nominal_era,
            "year_aggregate": nominal_year,
        }
    }
    aggregate_checks = {
        "nominal_era": nominal_era,
        "nominal_year": nominal_year,
    }
    source_tables = {
        "combination": {
            "run": ("trigger_combinations_by_run",),
            "era": ("trigger_combinations_by_era",),
            "year": ("trigger_combinations_by_year",),
        },
        "hlt_path": {
            "run": ("trigger_paths_by_run",),
            "era": ("trigger_paths_by_era",),
            "year": ("trigger_paths_by_year",),
        },
    }
    table_cache = {}
    for source, definition in RUN_STABILITY_LUMINOSITY_SOURCE_DEFINITIONS.items():
        if source == "nominal":
            continue
        table_names = {
            grain: names[0]
            for grain, names in source_tables[definition["kind"]].items()
        }
        for table_name in table_names.values():
            table_cache.setdefault(table_name, _read_csv(paths[table_name]))
        run_table = table_names["run"]
        source_rows = _unique_run_rows(
            table_cache[run_table],
            era=era,
            scope_name=definition["scope_name"],
            source=str(paths[run_table]),
        )
        source_runs = [row["run"] for row in source_rows]
        if source_runs != runs:
            raise RuntimeError(
                f"RUN_STABILITY nominal and {source} run sets differ: "
                f"missing_source={sorted(set(runs) - set(source_runs))}, "
                f"missing_nominal={sorted(set(source_runs) - set(runs))}"
            )
        era_table = table_names["era"]
        era_aggregate = _one_aggregate(
            table_cache[era_table],
            era=era,
            scope_name=definition["scope_name"],
            source=str(paths[era_table]),
        )
        year_table = table_names["year"]
        year_aggregate = _one_year_aggregate(
            table_cache[year_table],
            analysis_year=analysis_year,
            scope_name=definition["scope_name"],
            source=str(paths[year_table]),
        )
        year_rows = [
            row
            for row in table_cache[run_table]
            if row.get("analysis_year") == analysis_year
            and row.get("scope_name") == definition["scope_name"]
        ]
        for field in ("delivered_fb", "recorded_fb"):
            _require_close(
                f"{era} {source} {field}",
                sum(row[field] for row in source_rows),
                era_aggregate[field],
                tolerance,
            )
            _require_close(
                f"{analysis_year} {source} {field}",
                sum(
                    _finite_nonnegative(
                        row[field], field=field, source=str(paths[run_table])
                    )
                    for row in year_rows
                ),
                year_aggregate[field],
                tolerance,
            )
        active_era_runs = sum(
            row["delivered_fb"] > 0.0 or row["recorded_fb"] > 0.0 for row in source_rows
        )
        active_year_runs = sum(
            _finite_nonnegative(
                row["delivered_fb"],
                field="delivered_fb",
                source=str(paths[run_table]),
            )
            > 0.0
            or _finite_nonnegative(
                row["recorded_fb"],
                field="recorded_fb",
                source=str(paths[run_table]),
            )
            > 0.0
            for row in year_rows
        )
        if (
            era_aggregate["n_runs"] != active_era_runs
            or year_aggregate["n_runs"] != active_year_runs
        ):
            raise RuntimeError(
                f"RUN_STABILITY {source} aggregate run counts diverge: "
                f"era={era_aggregate['n_runs']} expected={active_era_runs}, "
                f"year={year_aggregate['n_runs']} expected={active_year_runs}"
            )
        luminosity_sources[source] = {
            **definition,
            "rows": source_rows,
            "era_aggregate": era_aggregate,
            "year_aggregate": year_aggregate,
        }
        aggregate_checks[f"{source}_era"] = era_aggregate
        aggregate_checks[f"{source}_year"] = year_aggregate

    trigger_rows = luminosity_sources["trigger_any"]["rows"]

    namespace, cpp_source = _build_cpp_index(runs)
    run_to_bin = {run: index for index, run in enumerate(runs, 1)}
    output_paths = [
        f"run_stability/{category}/{observable}/histo_DATA"
        for category in RUN_STABILITY_CATEGORIES
        for observable in RUN_STABILITY_OBSERVABLES
    ]
    source_contract = {
        name: {"path": str(path), "sha256": hashes[name]}
        for name, path in paths.items()
    }
    source_contract["year_config"] = {
        "path": str(live_year_config_path),
        "sha256": live_year_config_hash,
    }
    contract = {
        "schema_version": 3,
        "enabled": True,
        "analysis_pass": "RUN_STABILITY",
        "analysis_year": analysis_year,
        "analysis_era": era,
        "target_region": RUN_STABILITY_REGION,
        "observable_selector": RUN_STABILITY_OBSERVABLE_SELECTOR,
        "category_selector": RUN_STABILITY_CATEGORY_SELECTOR,
        "ordered_runs": runs,
        "run_to_bin": run_to_bin,
        "nominal": nominal_rows,
        "trigger_any": trigger_rows,
        "luminosity_sources": luminosity_sources,
        "category_luminosity_sources": dict(RUN_STABILITY_CATEGORY_LUMINOSITY_SOURCES),
        "aggregate_tolerance_fb": tolerance,
        "aggregate_checks": aggregate_checks,
        "input_results_dir": str(results_dir),
        "inputs": source_contract,
        "luminosity_validation_status": validation.get("status"),
        "luminosity_provenance_created_utc": provenance.get("created_utc"),
        "mc_source_lumi_fb": float(globals().get("lumi", _selected_year["lumi_fb"])),
        "categories": list(RUN_STABILITY_CATEGORIES),
        "observables": list(RUN_STABILITY_OBSERVABLES),
        "available_categories": list(RUN_STABILITY_AVAILABLE_CATEGORIES),
        "available_observables": list(RUN_STABILITY_AVAILABLE_OBSERVABLES),
        "auxiliary_output_paths": output_paths,
        "metadata_output_paths": list(RUN_STABILITY_METADATA_PATHS),
        "metadata_writer": {"sample": "DATA", "split_index": 0},
        "future_luminosity_source_default": None,
        "cpp_namespace": namespace,
    }
    return contract, namespace, cpp_source


RUN_STABILITY_CONTRACT, RUN_STABILITY_CPP_NAMESPACE, RUN_STABILITY_CPP = (
    build_run_stability_contract()
)
