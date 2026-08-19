"""Validate and materialize the RunStability era/sample configuration."""

import json
import math
import os
import re
from copy import deepcopy
from functools import lru_cache

DEFAULT_TREE_BASE_DIR = "/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano"
SAMPLE_PROFILES = ("presentation",)


def _deep_merge(base, override):
    """Return a recursive copy of ``base`` updated by ``override``."""
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged


def _materialize_years(raw_cfg):
    """Expand shared defaults into the per-era runtime dictionaries."""
    if raw_cfg.get("schema_version") != 2:
        raise ValueError("year_config.json schema_version must be 2")

    defaults = raw_cfg.get("year_defaults")
    stream_triggers = raw_cfg.get("data_stream_triggers")
    years = raw_cfg.get("years")
    if not isinstance(defaults, dict):
        raise ValueError("year_config.json requires a year_defaults object")
    if not isinstance(stream_triggers, dict) or not stream_triggers:
        raise ValueError("year_config.json requires data_stream_triggers")
    if not isinstance(years, dict) or not years:
        raise ValueError("year_config.json requires a non-empty years object")
    if raw_cfg.get("default_year") not in years:
        raise ValueError("default_year must name a configured year")

    configured_triggers = set(defaults.get("trigger_paths", {}))
    for stream, rule in stream_triggers.items():
        if not isinstance(stream, str) or not stream:
            raise ValueError("DATA stream names must be non-empty strings")
        if not isinstance(rule, str) or not rule.strip():
            raise ValueError(f"DATA stream {stream!r} needs a trigger expression")
        unknown = sorted(
            set(re.findall(r"Trigger_[A-Za-z0-9_]+", rule)) - configured_triggers
        )
        if unknown:
            raise ValueError(
                f"DATA stream {stream!r} uses unconfigured trigger flags: {unknown}"
            )

    resolved = dict(raw_cfg)
    resolved_years = {}
    for year_key, year_override in years.items():
        if not isinstance(year_override, dict):
            raise ValueError(f"Year '{year_key}' configuration must be an object")
        raw_samples = year_override.get("data", {}).get("samples", [])
        if not isinstance(raw_samples, list):
            raise ValueError(f"Year '{year_key}' data.samples must be a list")
        if not all(isinstance(sample, dict) for sample in raw_samples):
            raise ValueError(f"Year '{year_key}' DATA samples must be objects")
        datasets = [sample.get("dataset") for sample in raw_samples]
        if len(datasets) != len(set(datasets)):
            raise ValueError(f"Year '{year_key}' has duplicate DATA datasets")
        year_cfg = _deep_merge(defaults, year_override)
        year_run_tags = resolve_data_run_tags(year_cfg)
        year_triggers = set(year_cfg.get("trigger_paths", {}))
        for sample_cfg in raw_samples:
            if sample_cfg.get("stream") not in stream_triggers:
                raise ValueError(
                    f"Year '{year_key}' DATA sample {sample_cfg.get('dataset')!r} "
                    f"uses unknown stream {sample_cfg.get('stream')!r}"
                )
            if "runs" in sample_cfg:
                sample_runs = sample_cfg["runs"]
                if (
                    not isinstance(sample_runs, list)
                    or not sample_runs
                    or not all(isinstance(run, str) and run for run in sample_runs)
                ):
                    raise ValueError(
                        f"Year '{year_key}' DATA sample {sample_cfg.get('dataset')!r} "
                        "runs must be a non-empty list of run-tag strings"
                    )
                if len(sample_runs) != len(set(sample_runs)):
                    raise ValueError(
                        f"Year '{year_key}' DATA sample {sample_cfg.get('dataset')!r} "
                        "runs contains duplicates"
                    )
                unknown_runs = sorted(set(sample_runs) - set(year_run_tags))
                if unknown_runs:
                    raise ValueError(
                        f"Year '{year_key}' DATA sample {sample_cfg.get('dataset')!r} "
                        f"runs contains unknown run tags: {unknown_runs}"
                    )
            if "trigger" in sample_cfg:
                trigger = sample_cfg["trigger"]
                if not isinstance(trigger, str) or not trigger.strip():
                    raise ValueError(
                        f"Year '{year_key}' DATA sample {sample_cfg.get('dataset')!r} "
                        "trigger must be a non-empty string"
                    )
                unknown = sorted(
                    set(re.findall(r"Trigger_[A-Za-z0-9_]+", trigger)) - year_triggers
                )
                if unknown:
                    raise ValueError(
                        f"Year '{year_key}' DATA sample {sample_cfg.get('dataset')!r} "
                        f"uses unconfigured trigger flags: {unknown}"
                    )
        for sample_cfg in year_cfg.get("data", {}).get("samples", []):
            stream = sample_cfg.get("stream")
            if "trigger" not in sample_cfg:
                if stream not in stream_triggers:
                    raise ValueError(
                        f"Year '{year_key}' DATA stream {stream!r} has no trigger rule"
                    )
                sample_cfg["trigger"] = stream_triggers[stream]
        resolved_years[year_key] = year_cfg
    resolved["years"] = resolved_years
    return resolved


@lru_cache(maxsize=1)
def _load_year_config(config_filename):
    candidates = [
        globals().get("CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    cfg_path = None
    for cand in candidates:
        if not cand:
            continue
        cand_abs = os.path.abspath(cand)
        test_path = os.path.join(cand_abs, config_filename)
        if os.path.exists(test_path):
            cfg_path = test_path
            break
    if cfg_path is None:
        fallback_dir = (
            os.path.dirname(os.path.abspath(__file__))
            if "__file__" in globals()
            else os.path.abspath(os.getcwd())
        )
        cfg_path = os.path.join(fallback_dir, config_filename)
    with open(cfg_path, encoding="utf-8") as cfg_handle:
        return _materialize_years(json.load(cfg_handle))


def load_selected_year(config_filename="year_config.json", env_var="YEAR"):
    """Return (year_key, year_cfg, full_cfg) for the active year."""
    full_cfg = load_full_config(config_filename)

    year_key = os.environ.get(env_var, full_cfg["default_year"])
    available_years = sorted(full_cfg["years"])
    if year_key not in full_cfg["years"]:
        raise ValueError(
            f"Unsupported {env_var}='{year_key}'. Available years: {available_years}"
        )

    year_cfg = full_cfg["years"][year_key]
    _validate_year_cfg(year_key, year_cfg)
    resolve_overlap_model(year_cfg, full_cfg)
    resolve_production_normalizations(year_cfg, full_cfg)

    return year_key, year_cfg, full_cfg


def load_full_config(config_filename="year_config.json"):
    """Return the materialized configuration with shared defaults expanded."""
    return _load_year_config(config_filename)


def resolve_production_normalizations(year_cfg, full_cfg):
    """Return validated per-physical-source YR5 central normalization ratios."""
    model = full_cfg.get("production_normalizations")
    if not isinstance(model, dict) or model.get("schema_version") != 1:
        raise ValueError("production_normalizations schema_version must be 1")
    reference = model.get("reference")
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError("production_normalizations requires a non-empty reference")
    active_sources = set(year_cfg["mc"]["samples"])
    known_sources = {
        source
        for configured_year in full_cfg.get("years", {}).values()
        for source in configured_year.get("mc", {}).get("samples", [])
    }
    resolved = {}
    for mode, cfg in model.get("modes", {}).items():
        if not isinstance(mode, str) or not isinstance(cfg, dict):
            raise ValueError("production_normalizations modes must be named objects")
        registry_xs = float(cfg.get("registry_xs_pb", 0.0))
        target_xs = float(cfg.get("target_xs_pb", 0.0))
        if registry_xs <= 0.0 or target_xs <= 0.0:
            raise ValueError(f"Invalid cross sections for production mode {mode!r}")
        aliases = cfg.get("aliases")
        if (
            not isinstance(aliases, list)
            or not aliases
            or not all(isinstance(alias, str) and alias for alias in aliases)
        ):
            raise ValueError(f"Production mode {mode!r} requires source aliases")
        factor = target_xs / registry_xs
        for alias in aliases:
            if alias not in known_sources:
                raise ValueError(
                    f"Production normalization alias {alias!r} is absent from all eras"
                )
            if alias in resolved:
                raise ValueError(
                    f"Production source {alias!r} is normalized by multiple modes"
                )
            if alias in active_sources:
                resolved[alias] = {
                    "mode": mode,
                    "registry_xs_pb": registry_xs,
                    "target_xs_pb": target_xs,
                    "factor": factor,
                    "reference": reference,
                }
    return resolved


def source_normalization(source_alias, year_cfg, full_cfg):
    """Return one physical input's central production normalization factor."""
    record = resolve_production_normalizations(year_cfg, full_cfg).get(source_alias)
    return 1.0 if record is None else float(record["factor"])


def resolve_overlap_model(year_cfg, full_cfg):
    """Resolve physical input aliases into disjoint logical processes."""
    model = full_cfg.get("overlap_model")
    if not isinstance(model, dict) or model.get("schema_version") != 1:
        raise ValueError("overlap_model schema_version must be 1")
    if model.get("unmatched_source_policy") != "passthrough":
        raise ValueError(
            "Only overlap_model unmatched_source_policy=passthrough is supported"
        )
    active_sources = list(year_cfg["mc"]["samples"])
    if len(active_sources) != len(set(active_sources)):
        raise ValueError("mc.samples contains duplicate physical aliases")

    resolved_sets = {}
    source_owner = {}
    for set_name, selector in model.get("source_sets", {}).items():
        if not isinstance(selector, dict) or len(selector) != 1:
            raise ValueError(
                f"overlap source set {set_name!r} needs exactly one selector"
            )
        if "prefix" in selector:
            members = [
                source
                for source in active_sources
                if source.startswith(selector["prefix"])
            ]
        elif "aliases" in selector:
            expected = list(selector["aliases"])
            members = [source for source in active_sources if source in expected]
            missing = sorted(set(expected) - set(members))
            if missing:
                raise ValueError(
                    f"overlap source set {set_name!r} is missing active aliases {missing}"
                )
        else:
            raise ValueError(
                f"Unsupported selector for overlap source set {set_name!r}"
            )
        if not members:
            raise ValueError(f"overlap source set {set_name!r} resolved no inputs")
        for source in members:
            if source in source_owner:
                raise ValueError(
                    f"Physical source {source!r} belongs to both "
                    f"{source_owner[source]!r} and {set_name!r}"
                )
            source_owner[source] = set_name
        resolved_sets[set_name] = tuple(members)

    regions = model.get("regions", {})
    if not isinstance(regions, dict) or not all(
        isinstance(name, str) and isinstance(expr, str) and expr.strip()
        for name, expr in regions.items()
    ):
        raise ValueError("overlap_model regions must be non-empty string expressions")
    resolved_processes = {}
    used_source_sets = set()
    for process_name, process_cfg in model.get("processes", {}).items():
        if not isinstance(process_name, str) or not isinstance(process_cfg, dict):
            raise ValueError("overlap_model processes must be named objects")
        theory_group = process_cfg.get("theory_group", process_name)
        if not isinstance(theory_group, str) or not theory_group.strip():
            raise ValueError(f"Invalid theory group for process {process_name!r}")
        components = []
        seen_sources = set()
        for component in process_cfg.get("components", []):
            if not isinstance(component, dict):
                raise ValueError(f"Invalid component in process {process_name!r}")
            set_name = component.get("source_set")
            region_name = component.get("region")
            if set_name not in resolved_sets or region_name not in regions:
                raise ValueError(
                    f"Invalid overlap component in process {process_name!r}: {component!r}"
                )
            used_source_sets.add(set_name)
            for source in resolved_sets[set_name]:
                if source in seen_sources:
                    raise ValueError(
                        f"Process {process_name!r} repeats physical source {source!r}"
                    )
                seen_sources.add(source)
                components.append(
                    {
                        "source_alias": source,
                        "source_set": set_name,
                        "region": region_name,
                        "weight": regions[region_name],
                    }
                )
        if not components:
            raise ValueError(
                f"Logical process {process_name!r} has no active components"
            )
        resolved_processes[process_name] = {
            "theory_group": theory_group,
            "components": tuple(components),
        }

    unused_source_sets = sorted(set(resolved_sets) - used_source_sets)
    if unused_source_sets:
        raise ValueError(
            f"overlap_model declares unused source sets: {unused_source_sets}"
        )
    consumed = {
        component["source_alias"]
        for process in resolved_processes.values()
        for component in process["components"]
    }
    passthrough = tuple(source for source in active_sources if source not in consumed)
    collisions = sorted(set(passthrough) & set(resolved_processes))
    if collisions:
        raise ValueError(f"Logical/pass-through output collisions: {collisions}")
    output_names = passthrough + tuple(resolved_processes)
    if len(output_names) != len(set(output_names)):
        raise ValueError("Resolved output process names are not unique")
    return {
        "physical_sources": tuple(active_sources),
        "source_sets": resolved_sets,
        "consumed_sources": tuple(
            source for source in active_sources if source in consumed
        ),
        "passthrough_sources": passthrough,
        "processes": resolved_processes,
        "output_names": output_names,
    }


def resolve_sample_profile(year_cfg, full_cfg, profile_name="presentation"):
    """Resolve one logical process scope from the live plot-group registry."""
    name = str(profile_name or "presentation").strip().lower()
    if name not in SAMPLE_PROFILES:
        raise ValueError(
            f"Unknown SAMPLE_PROFILE={name!r}; available={SAMPLE_PROFILES}"
        )

    overlap = resolve_overlap_model(year_cfg, full_cfg)
    known_mc = tuple(overlap["output_names"])
    known_mc_set = set(known_mc)
    plot_groups = full_cfg.get("plot_groups")
    if not isinstance(plot_groups, dict) or not plot_groups:
        raise ValueError("year_config.json requires non-empty plot_groups")

    selected_groups = tuple(plot_groups)
    missing_groups = [group for group in selected_groups if group not in plot_groups]
    if missing_groups:
        raise ValueError(
            f"SAMPLE_PROFILE={name!r} references missing plot groups {missing_groups}"
        )

    owners = {}
    for group_name, group_cfg in plot_groups.items():
        configured = group_cfg.get("samples", [])
        if not isinstance(configured, list):
            raise ValueError(f"plot_groups.{group_name}.samples must be a list")
        for sample_name in configured:
            if sample_name not in known_mc_set:
                continue
            if sample_name in owners:
                raise ValueError(
                    f"Logical output {sample_name!r} belongs to both plot groups "
                    f"{owners[sample_name]!r} and {group_name!r}"
                )
            owners[sample_name] = group_name

    if name == "presentation":
        ungrouped = sorted(known_mc_set - set(owners))
        if ungrouped:
            raise ValueError(
                "Presentation profile does not cover configured logical outputs: "
                f"{ungrouped}"
            )

    selected_group_set = set(selected_groups)
    selected_mc = tuple(
        sample_name
        for sample_name in known_mc
        if owners.get(sample_name) in selected_group_set
    )
    return {
        "name": name,
        "plot_groups": tuple(selected_groups),
        "mc_output_names": selected_mc,
        "output_names": selected_mc + ("DATA",),
        "sample_to_plot_group": {
            sample_name: owners[sample_name] for sample_name in selected_mc
        },
        "nonprompt_background_included": False,
    }


def resolve_sample_selection(
    year_cfg,
    full_cfg,
    profile_name="presentation",
    sample_filter=None,
):
    """Apply an optional exact SAMPLE_FILTER above a validated sample profile."""
    profile = resolve_sample_profile(year_cfg, full_cfg, profile_name)
    overlap = resolve_overlap_model(year_cfg, full_cfg)
    canonical_outputs = tuple(overlap["output_names"]) + ("DATA",)
    known_outputs = set(canonical_outputs)
    if sample_filter is None:
        active_outputs = tuple(profile["output_names"])
        source = "profile"
    else:
        if isinstance(sample_filter, str):
            requested = {
                item.strip() for item in sample_filter.split(",") if item.strip()
            }
        else:
            requested = {
                str(item).strip() for item in sample_filter if str(item).strip()
            }
        if not requested:
            raise ValueError("SAMPLE_FILTER was set but selected no logical outputs")
        unknown = sorted(requested - known_outputs)
        if unknown:
            raise ValueError(
                "SAMPLE_FILTER contains outputs absent from the selected year: "
                f"{unknown}"
            )
        active_outputs = tuple(
            sample_name for sample_name in canonical_outputs if sample_name in requested
        )
        source = "filter"
    return {
        **profile,
        "selection_source": source,
        "active_output_names": active_outputs,
    }


def _validate_year_cfg(year_key, year_cfg):
    required_top = (
        "mc",
        "data",
        "trigger_paths",
        "l2tight_era",
        "lepton_ids",
    )
    for key in required_top:
        if key not in year_cfg:
            raise ValueError(f"Year '{year_key}' is missing required key '{key}'.")

    lumi = year_cfg.get("lumi_fb")
    if not isinstance(lumi, (int, float)) or not math.isfinite(lumi) or lumi <= 0.0:
        raise ValueError(f"Year '{year_key}' lumi_fb must be finite and positive")

    for key in ("production", "steps", "samples"):
        if key not in year_cfg["mc"]:
            raise ValueError(f"Year '{year_key}' is missing mc.{key}.")
    for key in ("production", "steps", "common_weight"):
        if not isinstance(year_cfg["mc"].get(key), str) or not year_cfg["mc"][key]:
            raise ValueError(f"Year '{year_key}' mc.{key} must be a non-empty string")
    mc_samples = year_cfg["mc"]["samples"]
    if (
        not isinstance(mc_samples, list)
        or not mc_samples
        or not all(isinstance(sample, str) and sample for sample in mc_samples)
    ):
        raise ValueError(f"Year '{year_key}' mc.samples must contain sample names")
    if len(mc_samples) != len(set(mc_samples)):
        raise ValueError(f"Year '{year_key}' mc.samples contains duplicates")

    for key in ("reco", "steps", "runs", "samples"):
        if key not in year_cfg["data"]:
            raise ValueError(f"Year '{year_key}' is missing data.{key}.")
    if not isinstance(year_cfg["data"]["runs"], list):
        raise ValueError(f"Year '{year_key}' data.runs must be a list.")
    if not isinstance(year_cfg["data"]["samples"], list):
        raise ValueError(f"Year '{year_key}' data.samples must be a list.")
    for key in ("reco", "steps", "common_weight"):
        if not isinstance(year_cfg["data"].get(key), str) or not year_cfg["data"][key]:
            raise ValueError(f"Year '{year_key}' data.{key} must be a non-empty string")

    run_tags = resolve_data_run_tags(year_cfg)
    if not run_tags or not all(isinstance(tag, str) and tag for tag in run_tags):
        raise ValueError(f"Year '{year_key}' DATA run tags must be non-empty strings")
    if len(run_tags) != len(set(run_tags)):
        raise ValueError(f"Year '{year_key}' data.runs contains duplicate run tags.")

    for i, sample_cfg in enumerate(year_cfg["data"]["samples"]):
        for sample_key in ("dataset", "stream", "trigger"):
            if sample_key not in sample_cfg:
                raise ValueError(
                    f"Year '{year_key}' data.samples[{i}] is missing '{sample_key}'."
                )
            if (
                not isinstance(sample_cfg[sample_key], str)
                or not sample_cfg[sample_key]
            ):
                raise ValueError(
                    f"Year '{year_key}' data.samples[{i}].{sample_key} "
                    "must be a non-empty string"
                )
        if "runs" in sample_cfg:
            if (
                not isinstance(sample_cfg["runs"], list)
                or not sample_cfg["runs"]
                or not all(
                    isinstance(run_tag, str) and run_tag
                    for run_tag in sample_cfg["runs"]
                )
            ):
                raise ValueError(
                    f"Year '{year_key}' data.samples[{i}].runs must be a non-empty list of run-tag strings."
                )
            if len(sample_cfg["runs"]) != len(set(sample_cfg["runs"])):
                raise ValueError(
                    f"Year '{year_key}' data.samples[{i}].runs contains duplicates."
                )

            unknown_runs = sorted(set(sample_cfg["runs"]) - set(run_tags))
            if unknown_runs:
                raise ValueError(
                    f"Year '{year_key}' data.samples[{i}].runs contains unknown run tags: {unknown_runs}"
                )

        configured_trigger_flags = set(year_cfg.get("trigger_paths", {}))
        unknown_trigger_flags = sorted(
            set(re.findall(r"Trigger_[A-Za-z0-9_]+", sample_cfg["trigger"]))
            - configured_trigger_flags
        )
        if unknown_trigger_flags:
            raise ValueError(
                f"Year '{year_key}' data.samples[{i}].trigger uses unconfigured "
                f"trigger flags: {unknown_trigger_flags}"
            )

    trigger_paths_cfg = year_cfg["trigger_paths"]
    if not isinstance(trigger_paths_cfg, dict) or not trigger_paths_cfg:
        raise ValueError(
            f"Year '{year_key}' trigger_paths must be a non-empty dictionary."
        )

    all_hlt_paths = []
    for trigger_flag, trigger_cfg in trigger_paths_cfg.items():
        if not isinstance(trigger_flag, str) or not trigger_flag.startswith("Trigger_"):
            raise ValueError(
                f"Year '{year_key}' trigger_paths keys must be Trigger_* strings. Got: {trigger_flag!r}"
            )
        if not isinstance(trigger_cfg, dict):
            raise ValueError(
                f"Year '{year_key}' trigger_paths.{trigger_flag} must be a dictionary."
            )
        if "paths" not in trigger_cfg:
            raise ValueError(
                f"Year '{year_key}' trigger_paths.{trigger_flag} is missing 'paths'."
            )
        paths = trigger_cfg["paths"]
        if (
            not isinstance(paths, list)
            or not paths
            or not all(
                isinstance(path, str) and path.startswith("HLT_") for path in paths
            )
        ):
            raise ValueError(
                f"Year '{year_key}' trigger_paths.{trigger_flag}.paths must be a non-empty list of HLT_* strings."
            )
        if len(paths) != len(set(paths)):
            raise ValueError(
                f"Year '{year_key}' trigger_paths.{trigger_flag}.paths contains duplicates."
            )
        all_hlt_paths.extend(paths)
    if len(all_hlt_paths) != len(set(all_hlt_paths)):
        raise ValueError(f"Year '{year_key}' assigns an HLT path more than once")

    lepton_id_cfg = year_cfg["lepton_ids"]
    required_lepton_id_keys = (
        "electron_wp",
        "muon_wp",
        "z0_min_pass",
    )
    for key in required_lepton_id_keys:
        if key not in lepton_id_cfg:
            raise ValueError(f"Year '{year_key}' is missing lepton_ids.{key}.")

    if not isinstance(lepton_id_cfg["electron_wp"], str) or not isinstance(
        lepton_id_cfg["muon_wp"], str
    ):
        raise ValueError(
            f"Year '{year_key}' lepton_ids electron/muon working points must be strings."
        )

    for key in ("z0_min_pass",):
        if not isinstance(lepton_id_cfg[key], int):
            raise ValueError(f"Year '{year_key}' lepton_ids.{key} must be an integer.")

    storage_cfg = year_cfg.get("storage", {})
    if not isinstance(storage_cfg, dict):
        raise ValueError(f"Year '{year_key}' storage must be a dictionary.")

    string_fields = ("default_tree_base_dir", "mc_tree_base_dir", "data_tree_base_dir")
    for field in string_fields:
        if field in storage_cfg and not isinstance(storage_cfg[field], str):
            raise ValueError(f"Year '{year_key}' storage.{field} must be a string.")

    dict_fields = (
        "mc_tree_base_dir_by_sample",
        "data_tree_base_dir_by_sample",
        "data_tree_base_dir_by_stream",
    )
    for field in dict_fields:
        if field not in storage_cfg:
            continue
        if not isinstance(storage_cfg[field], dict):
            raise ValueError(f"Year '{year_key}' storage.{field} must be a dictionary.")
        for key, value in storage_cfg[field].items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(
                    f"Year '{year_key}' storage.{field} entries must be string->string."
                )


def resolve_data_run_tags(year_cfg):
    """
    Normalize data runs to a list of run-tag strings.

    Supports both legacy shape [["C", "Run2024C-..."], ...] and
    simplified shape ["Run2024C-...", ...].
    """
    run_tags = []
    for run_item in year_cfg["data"]["runs"]:
        if isinstance(run_item, str):
            run_tags.append(run_item)
        elif isinstance(run_item, (list, tuple)) and len(run_item) >= 2:
            run_tags.append(run_item[1])
        else:
            raise ValueError(
                "Unsupported run entry in year config. Expected string or [label, runTag]. "
                f"Got: {run_item!r}"
            )
    return run_tags


def resolve_data_run_filter(run_tags, run_filter=()):
    """Restrict a bounded DATA pilot to exact configured run-tag names."""
    ordered = tuple(dict.fromkeys(str(item) for item in run_tags))
    requested = {str(item).strip() for item in run_filter if str(item).strip()}
    if not requested:
        return list(ordered)
    unknown = sorted(requested - set(ordered))
    if unknown:
        raise ValueError(
            "DATA run filter contains unknown run tags: {}; available: {}".format(
                unknown, list(ordered)
            )
        )
    return [run_tag for run_tag in ordered if run_tag in requested]


def resolve_data_sample_run_tags(filtered_run_tags, sample_cfg):
    """Intersect one DATA component's configured runs with the ordered pilot runs."""
    ordered = tuple(dict.fromkeys(str(item) for item in filtered_run_tags))
    allowed = set(sample_cfg.get("runs", ordered))
    return [run_tag for run_tag in ordered if run_tag in allowed]


def resolve_data_samples(year_cfg, stream_filter=()):
    """Return DATA definitions, optionally restricted to exact stream names."""
    samples = list(year_cfg["data"]["samples"])
    requested = {str(item).strip() for item in stream_filter if str(item).strip()}
    if not requested:
        return samples
    known = {item["stream"] for item in samples}
    unknown = sorted(requested - known)
    if unknown:
        raise ValueError(
            "DATA stream filter contains unknown streams: {}; available: {}".format(
                unknown, sorted(known)
            )
        )
    return [item for item in samples if item["stream"] in requested]


def resolve_trigger_path_branches(year_cfg):
    """Return the ordered list of concrete HLT path branches configured for a year."""
    branches = []
    seen = set()
    for trigger_cfg in (year_cfg.get("trigger_paths", {}) or {}).values():
        for path in trigger_cfg.get("paths", []) or []:
            if path in seen:
                continue
            seen.add(path)
            branches.append(path)
    return branches


def iter_trigger_path_entries(year_cfg):
    """Yield dictionaries describing each configured aggregate trigger/path pair."""
    for aggregate, trigger_cfg in (year_cfg.get("trigger_paths", {}) or {}).items():
        for path in trigger_cfg.get("paths", []) or []:
            yield {
                "aggregate": aggregate,
                "family": trigger_cfg.get("family", ""),
                "description": trigger_cfg.get("description", ""),
                "path": path,
            }


def resolve_tree_base_dir(year_cfg, sample_kind, sample_name=None, stream_name=None):
    """
    Resolve the EOS tree base directory with support for per-kind and per-sample overrides.

    Priority:
      1. per-sample (MC: sample_name, DATA: sample_name then stream_name)
      2. per-kind default (mc_tree_base_dir / data_tree_base_dir)
      3. year default (default_tree_base_dir)
      4. legacy fallback constant
    """
    if sample_kind not in ("mc", "data"):
        raise ValueError(
            f"Unsupported sample_kind='{sample_kind}'. Use 'mc' or 'data'."
        )

    storage_cfg = year_cfg.get("storage", {})
    default_dir = storage_cfg.get("default_tree_base_dir", DEFAULT_TREE_BASE_DIR)
    kind_default = storage_cfg.get(f"{sample_kind}_tree_base_dir", default_dir)

    if sample_kind == "mc":
        sample_overrides = storage_cfg.get("mc_tree_base_dir_by_sample", {})
        if sample_name and sample_name in sample_overrides:
            return sample_overrides[sample_name]
        return kind_default

    data_sample_overrides = storage_cfg.get("data_tree_base_dir_by_sample", {})
    if sample_name and sample_name in data_sample_overrides:
        return data_sample_overrides[sample_name]

    data_stream_overrides = storage_cfg.get("data_tree_base_dir_by_stream", {})
    if stream_name and stream_name in data_stream_overrides:
        return data_stream_overrides[stream_name]

    return kind_default
