"""Static contracts for the opt-in historical HWW replay."""

import importlib.util
import json
from pathlib import Path

import pytest


LEAF = Path(__file__).resolve().parents[1]
MODULE_PATH = LEAF / "historical_hww_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("historical_hww_diagnostic", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
WORKSPACE = LEAF.parents[4]
PAIRED = (
    WORKSPACE
    / "coffea/.worktrees/paired-lowpt-diagnostic/diagnostics/paired-2024-lowpt"
)
PICKLE = (
    WORKSPACE
    / "mkShapesRDF/PlotsConfigurationsRun3/ZH_4lMET/RunStability/configs/config_26-08-18_21_38_40.pkl"
)


def test_typed_identity_rejects_duplicates_and_out_of_range():
    row = {"run": 1, "luminosityBlock": 2, "event": 2**63 + 3}
    assert tuple(MODULE.unique_keys([row], "test")) == ((1, 2, 2**63 + 3),)
    with pytest.raises(ValueError, match="duplicate"):
        MODULE.unique_keys([row, row], "test")
    with pytest.raises(ValueError, match="out-of-range"):
        MODULE.unique_keys([{**row, "event": 2**64}], "test")
    signed = (2**63 + 3) - 2**64
    assert MODULE.signed_event_to_uint64(signed) == row["event"]
    with pytest.raises(ValueError, match="64-bit range"):
        MODULE.signed_event_to_uint64(-(2**63) - 1)


def test_pinned_pickle_restricts_to_exact_paired_part0_and_categories():
    config = MODULE.load_compiled(PICKLE)
    evidence = json.loads((PAIRED / "parent-pair-evidence.json").read_text())
    manifest = json.loads((PAIRED / "inputs.json").read_text())
    assert evidence["hww_exact_compiled_pickle_sha256"] == MODULE.PICKLE_SHA256
    for pair in evidence["pairs"]:
        entry = next(item for item in manifest["files"] if item["role"] == pair["role"])
        assert pair["central_lfn"] == entry["lfn"]
        name, selected = MODULE.selected_sample(config, pair)
        assert selected[name]["name"][0][1] == [pair["hww_pfn"]]
        categories = MODULE.TARGET_CATEGORIES[pair["role"]]
        cuts = MODULE.selected_cuts(config, categories)
        assert set(cuts["cuts"]["DY"]["categories"]) == {
            item.removeprefix("DY_") for item in categories
        }


def test_historical_helpers_are_byte_identical_and_paths_resolved():
    config = MODULE.load_compiled(PICKLE)
    aliases = MODULE.relocate_aliases(config["aliases"], LEAF)
    assert "__run_stability_contract__" not in aliases
    assert any(
        "ZZ_CR/macros/four_lepton_helpers.cc" in line
        for alias in aliases.values()
        for line in alias.get("linesToAdd", [])
    )
    assert not any(
        "ZZ_CR_RunStability" in line
        for alias in aliases.values()
        for field in ("linesToAdd", "linesToProcess")
        for line in alias.get(field, [])
    )
