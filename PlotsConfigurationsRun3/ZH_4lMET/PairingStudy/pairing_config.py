"""Small all-era configuration resolver for the pairing study.

The physics catalogue remains owned by ``../ZZ_CR/year_config.json``.  This
module deliberately exposes only the ZH-HWW and ZZ intersections needed by
the study; it does not copy the large control-region configuration.
"""

from __future__ import annotations

import importlib.util
import json
import os
from functools import lru_cache
from pathlib import Path


SUPPORTED_YEARS = ("2022", "2022EE", "2023", "2023BPix", "2024")
STUDY_PLOT_GROUPS = {"ZH": "HWW_signal", "ZZ": "ZZ"}

PAIRING_CONFIG_DIR = Path(__file__).resolve().parent
REFERENCE_CONFIG_DIR = PAIRING_CONFIG_DIR.parent / "ZZ_CR"
REFERENCE_JSON = REFERENCE_CONFIG_DIR / "year_config.json"
REFERENCE_HELPER = REFERENCE_CONFIG_DIR / "year_config.py"

DEFAULT_TREE_BASE = "/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano"
DEFAULT_XRD_ENDPOINT = "root://eoscms.cern.ch"

TOPOLOGY_CODES = {
    "4e": 1,
    "4mu": 2,
    "2e2mu": 3,
    "3e1mu": 4,
    "1e3mu": 5,
}

REGION_CODES = {
    "outside": 0,
    "ZZCR": 1,
    "XSF_SR": 2,
    "XDF_SR": 3,
}


def _validate_year(year):
    selected = str(year)
    if selected not in SUPPORTED_YEARS:
        raise ValueError(
            f"Unsupported YEAR={selected!r}; available={list(SUPPORTED_YEARS)}"
        )
    return selected


@lru_cache(maxsize=1)
def load_reference_json():
    """Load the unmodified JSON catalogue for pure inventory checks."""
    with REFERENCE_JSON.open(encoding="utf-8") as handle:
        return json.load(handle)


def resolve_inventory_from_config(config, year):
    """Return ordered ZH/ZZ intersections from a JSON-like configuration."""
    selected = _validate_year(year)
    try:
        mc_samples = tuple(config["years"][selected]["mc"]["samples"])
        plot_groups = config["plot_groups"]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            f"Malformed pairing-study source configuration: {exc}"
        ) from exc

    inventory = {}
    for family, group_name in STUDY_PLOT_GROUPS.items():
        try:
            requested = tuple(plot_groups[group_name]["samples"])
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Missing plot group {group_name!r}: {exc}") from exc
        resolved = tuple(sample for sample in requested if sample in mc_samples)
        if not resolved:
            raise RuntimeError(
                f"YEAR={selected} resolves an empty {family} inventory from "
                f"plot_groups[{group_name!r}]"
            )
        inventory[family] = resolved

    overlap = set(inventory["ZH"]) & set(inventory["ZZ"])
    if overlap:
        raise RuntimeError(
            f"YEAR={selected} has samples assigned to both truth domains: {sorted(overlap)}"
        )
    return inventory


def resolve_study_inventory(year=None):
    """Resolve the live ordered study inventory without hard-coded aliases."""
    selected = _validate_year(year or os.environ.get("YEAR", "2024"))
    return resolve_inventory_from_config(load_reference_json(), selected)


@lru_cache(maxsize=1)
def _reference_helper():
    """Load the existing materializer under a private, read-only module name."""
    spec = importlib.util.spec_from_file_location(
        "_pairing_study_reference_year_config", REFERENCE_HELPER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load reference helper {REFERENCE_HELPER}")
    module = importlib.util.module_from_spec(spec)
    # The helper searches CONFIG_DIR first when locating year_config.json.
    module.CONFIG_DIR = str(REFERENCE_CONFIG_DIR)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=None)
def load_pairing_year(year=None):
    """Return one validated, materialized year and its compact study metadata."""
    selected = _validate_year(year or os.environ.get("YEAR", "2024"))
    helper = _reference_helper()
    full_config = helper.load_full_config("year_config.json")
    if selected not in full_config.get("years", {}):
        raise RuntimeError(f"Reference configuration is missing YEAR={selected}")
    year_config = full_config["years"][selected]

    # Reuse the live validators for production, overlap, and normalization
    # semantics while keeping the reference directory read-only.
    helper._validate_year_cfg(selected, year_config)
    overlap_model = helper.resolve_overlap_model(year_config, full_config)
    helper.resolve_production_normalizations(year_config, full_config)

    inventory = resolve_inventory_from_config(full_config, selected)
    logical_components = {}
    passthrough = set(overlap_model["passthrough_sources"])
    processes = overlap_model["processes"]
    for logical_sample in inventory["ZH"] + inventory["ZZ"]:
        if logical_sample in processes:
            components = tuple(
                dict(item) for item in processes[logical_sample]["components"]
            )
        elif logical_sample in passthrough:
            components = (
                {
                    "source_alias": logical_sample,
                    "region": "inclusive",
                    "weight": "1.",
                },
            )
        else:
            raise RuntimeError(
                f"YEAR={selected} logical sample {logical_sample!r} is neither an "
                "overlap output nor a passthrough source"
            )

        normalized = []
        for component in components:
            source = component["source_alias"]
            normalized.append(
                {
                    **component,
                    "source_normalization": float(
                        helper.source_normalization(source, year_config, full_config)
                    ),
                    "tree_base_dir": helper.resolve_tree_base_dir(
                        year_config, "mc", sample_name=source
                    ),
                }
            )
        logical_components[logical_sample] = tuple(normalized)

    lepton_ids = year_config["lepton_ids"]
    selection_profiles = lepton_ids.get("selection_profiles", {})
    if not selection_profiles:
        raise RuntimeError(f"YEAR={selected} has no lepton selection profile")
    selection_profile = next(iter(selection_profiles.values()))

    return {
        "year": selected,
        "year_config": year_config,
        "inventory": inventory,
        "logical_components": logical_components,
        "production": year_config["mc"]["production"],
        "steps": year_config["mc"]["steps"],
        "lumi_fb": float(year_config["lumi_fb"]),
        "electron_wp": lepton_ids["electron_wp"],
        "muon_wp": lepton_ids["muon_wp"],
        "candidate_z_pt_mins": tuple(float(x) for x in lepton_ids["z0_pt_mins"]),
        "ordered_4l_pt_mins": tuple(
            float(x) for x in selection_profile["ordered_4l_pt_mins"]
        ),
    }


def process_family(sample, year=None):
    """Return ``ZH`` or ``ZZ`` for a resolved logical sample, fail closed."""
    inventory = load_pairing_year(year)["inventory"]
    for family in ("ZH", "ZZ"):
        if sample in inventory[family]:
            return family
    raise KeyError(f"Sample {sample!r} is outside the pairing-study inventory")


__all__ = [
    "DEFAULT_TREE_BASE",
    "DEFAULT_XRD_ENDPOINT",
    "PAIRING_CONFIG_DIR",
    "REFERENCE_JSON",
    "REGION_CODES",
    "STUDY_PLOT_GROUPS",
    "SUPPORTED_YEARS",
    "TOPOLOGY_CODES",
    "load_pairing_year",
    "load_reference_json",
    "process_family",
    "resolve_inventory_from_config",
    "resolve_study_inventory",
]
