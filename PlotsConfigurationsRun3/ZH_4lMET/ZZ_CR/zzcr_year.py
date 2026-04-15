"""Utilities for loading the ZZ_CR year-dependent configuration."""

import json
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def _load_year_config(config_filename):
    base_dir = globals().get("ZZCR_CONFIG_DIR") or globals().get("folder")
    if not base_dir:
        base_dir = (
            os.path.dirname(os.path.abspath(__file__))
            if "__file__" in globals()
            else os.getcwd()
        )
    base_dir = os.path.abspath(base_dir)
    cfg_path = os.path.join(base_dir, config_filename)
    with open(cfg_path, encoding="utf-8") as cfg_handle:
        return json.load(cfg_handle)


def load_selected_year(config_filename="zzcr_year_config.json", env_var="ZZCR_YEAR"):
    """Return (year_key, year_cfg, full_cfg) for the active ZZ_CR year."""
    full_cfg = _load_year_config(config_filename)

    year_key = os.environ.get(env_var, full_cfg["default_year"])
    available_years = sorted(full_cfg["years"])
    if year_key not in full_cfg["years"]:
        raise ValueError(
            f"Unsupported {env_var}='{year_key}'. Available years: {available_years}"
        )

    year_cfg = full_cfg["years"][year_key]
    _validate_year_cfg(year_key, year_cfg)

    return year_key, year_cfg, full_cfg


def _validate_year_cfg(year_key, year_cfg):
    required_top = ("mc", "data", "btag", "l2tight_era", "lumi_nuisance")
    for key in required_top:
        if key not in year_cfg:
            raise ValueError(f"Year '{year_key}' is missing required key '{key}'.")

    for key in ("production", "steps", "samples"):
        if key not in year_cfg["mc"]:
            raise ValueError(f"Year '{year_key}' is missing mc.{key}.")
    if not isinstance(year_cfg["mc"]["samples"], list) or not year_cfg["mc"]["samples"]:
        raise ValueError(f"Year '{year_key}' must define a non-empty mc.samples list.")

    for key in ("reco", "steps", "runs", "samples"):
        if key not in year_cfg["data"]:
            raise ValueError(f"Year '{year_key}' is missing data.{key}.")
    if not isinstance(year_cfg["data"]["samples"], list) or not year_cfg["data"]["samples"]:
        raise ValueError(f"Year '{year_key}' must define a non-empty data.samples list.")
    for i, sample_cfg in enumerate(year_cfg["data"]["samples"]):
        for sample_key in ("dataset", "stream", "trigger"):
            if sample_key not in sample_cfg:
                raise ValueError(
                    f"Year '{year_key}' data.samples[{i}] is missing '{sample_key}'."
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
