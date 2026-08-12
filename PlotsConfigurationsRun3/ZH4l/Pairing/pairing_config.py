"""Pairing-only codes and ZH/ZZ inventory resolved from ZH4l common."""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path


SUPPORTED_ERAS = ("2022", "2022EE", "2023", "2023BPix", "2024")
STUDY_PLOT_GROUPS = {"ZH": "HWW_signal", "ZZ": "ZZ"}

PAIRING_CONFIG_DIR = Path(__file__).resolve().parent
FAMILY_DIR = PAIRING_CONFIG_DIR.parent
if str(FAMILY_DIR) not in sys.path:
    sys.path.insert(0, str(FAMILY_DIR))

from common.eras import (  # noqa: E402
    load_full_config,
    resolve_era,
    resolve_overlap_model,
    resolve_production_normalizations,
    resolve_tree_base_dir,
    source_normalization,
)

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


def _validate_era(era):
    selected = str(era)
    if selected not in SUPPORTED_ERAS:
        raise ValueError(
            f"Unsupported ERA={selected!r}; available={list(SUPPORTED_ERAS)}"
        )
    return selected


@lru_cache(maxsize=1)
def load_reference_json():
    """Compatibility name returning the materialized common era catalogue."""
    return load_full_config()


def resolve_inventory_from_config(config, year):
    """Return ordered ZH/ZZ intersections from a JSON-like configuration."""
    selected = _validate_era(year)
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
                f"ERA={selected} resolves an empty {family} inventory from "
                f"plot_groups[{group_name!r}]"
            )
        inventory[family] = resolved

    overlap = set(inventory["ZH"]) & set(inventory["ZZ"])
    if overlap:
        raise RuntimeError(
            f"ERA={selected} has samples assigned to both truth domains: {sorted(overlap)}"
        )
    return inventory


def resolve_study_inventory(year=None):
    """Resolve the live ordered study inventory without hard-coded aliases."""
    selected = _validate_era(year or resolve_era() or "2024")
    return resolve_inventory_from_config(load_reference_json(), selected)


@lru_cache(maxsize=None)
def load_pairing_year(year=None):
    """Return one validated, materialized era and compact study metadata."""
    selected = _validate_era(year or resolve_era() or "2024")
    full_config = load_full_config()
    if selected not in full_config.get("years", {}):
        raise RuntimeError(f"Common configuration is missing ERA={selected}")
    era_config = full_config["years"][selected]

    overlap_model = resolve_overlap_model(era_config, full_config)
    resolve_production_normalizations(era_config, full_config)

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
                f"ERA={selected} logical sample {logical_sample!r} is neither an "
                "overlap output nor a passthrough source"
            )

        normalized = []
        for component in components:
            source = component["source_alias"]
            normalized.append(
                {
                    **component,
                    "source_normalization": float(
                        source_normalization(source, era_config, full_config)
                    ),
                    "tree_base_dir": resolve_tree_base_dir(
                        era_config, "mc", sample_name=source
                    ),
                }
            )
        logical_components[logical_sample] = tuple(normalized)

    lepton_ids = era_config["lepton_ids"]
    selection_profiles = lepton_ids.get("selection_profiles", {})
    if not selection_profiles:
        raise RuntimeError(f"ERA={selected} has no lepton selection profile")
    selection_profile = next(iter(selection_profiles.values()))

    return {
        "era": selected,
        "era_config": era_config,
        "inventory": inventory,
        "logical_components": logical_components,
        "production": era_config["mc"]["production"],
        "steps": era_config["mc"]["steps"],
        "lumi_fb": float(era_config["lumi_fb"]),
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
    "REGION_CODES",
    "STUDY_PLOT_GROUPS",
    "SUPPORTED_ERAS",
    "TOPOLOGY_CODES",
    "load_pairing_year",
    "load_reference_json",
    "process_family",
    "resolve_inventory_from_config",
    "resolve_study_inventory",
]
