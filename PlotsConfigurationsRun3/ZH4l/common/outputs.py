"""Explicit event-tree projections shared by small analysis leaves."""

from copy import deepcopy
import os


BRANCH_GROUPS = {
    "identity": {name: name for name in ("run", "luminosityBlock", "event")},
    "source": {
        "source_file": "zh4l_internal_source_file",
        "source_entry": "zh4l_internal_source_entry",
    },
    "z": {
        name: name
        for name in (
            "z_lepton_index",
            "z_is_valid",
            "z_mass",
            "z_pt",
            "z_eta",
            "z_phi",
            "z_is_ee",
            "z_is_mumu",
        )
    },
    "x": {
        name: name
        for name in (
            "x_lepton_index",
            "x_is_valid",
            "x_mass",
            "x_pt",
            "x_eta",
            "x_phi",
            "x_is_ee",
            "x_is_mumu",
            "x_is_same_flavor",
            "x_is_different_flavor",
        )
    },
    "zx": {
        name: name
        for name in (
            "zx_is_valid",
            "zx_mass",
            "zx_pt",
            "zx_phi",
            "zx_min_pair_mass",
            "zx_charge",
            "zx_pass_ordered_pt",
            "event_pass_extra_lepton_veto",
        )
    },
    "leptons": {
        name: name
        for name in (
            "Lepton_pt",
            "Lepton_eta",
            "Lepton_phi",
            "Lepton_pdgId",
            "Lepton_electronIdx",
            "Lepton_muonIdx",
        )
    },
    "jets_met": {
        name: name
        for name in (
            "CleanJet_pt",
            "CleanJet_eta",
            "CleanJet_phi",
            "CleanJet_jetIdx",
            "PuppiMET_pt",
            "PuppiMET_phi",
        )
    },
    "corrections": {
        name: name
        for name in (
            "sf_lepton_z",
            "sf_lepton_zx",
            "sf_trigger_z",
            "sf_trigger_zx",
            "event_pass_b_veto",
            "sf_b_veto",
        )
    },
    "trigger": {
        name: name
        for name in (
            "Trigger_ElMu",
            "Trigger_sngMu",
            "Trigger_dblMu",
            "Trigger_sngEl",
            "Trigger_dblEl",
        )
    },
}


def branches(*groups, extra=None, exclude=()):
    """Compose named groups and typed definitions, preserving graph references."""
    from .definitions import Candidate, Column, Correction, View, Weight

    result = {}
    for group in groups:
        if isinstance(group, str):
            fields = BRANCH_GROUPS[group]
        elif isinstance(group, Candidate):
            columns = (group.indices, group.valid, *(v for _, v in group.observables))
            fields = {str(column): column for column in columns}
        elif isinstance(group, (Correction, Weight)):
            fields = {str(column): column for column in (group.value, group.valid)}
        elif isinstance(group, View):
            fields = {str(group.indices): group.indices}
        elif isinstance(group, Column):
            fields = {str(group): group}
        else:
            fields = group
        for name, expression in fields.items():
            if name in result and result[name] != expression:
                raise ValueError(f"Conflicting tree field {name}")
            result[name] = expression
    for name in exclude:
        if name not in result:
            raise ValueError(f"Cannot exclude unknown tree field {name}")
        del result[name]
    for name, expression in (extra or {}).items():
        if name in result:
            raise ValueError(
                f"Tree field {name} already exists; exclude it before replacing its group"
            )
        result[name] = expression
    return result


def output_mode():
    mode = os.environ.get("ZH4L_OUTPUT_MODE", "histograms").strip().lower()
    if mode not in {"histograms", "trees", "both"}:
        raise ValueError("ZH4L_OUTPUT_MODE must be histograms, trees or both")
    return mode


def with_tree_outputs(variables, cuts, fields, *, mode=None, tree_weight=None):
    mode = output_mode() if mode is None else mode
    if mode not in {"histograms", "trees", "both"}:
        raise ValueError(f"Invalid output mode {mode}")
    result = deepcopy(variables) if mode != "trees" else {}
    if mode != "histograms":
        if "events" in result:
            raise ValueError("The events output name is already used")
        result["events"] = {
            "tree": dict(fields),
            "cuts": list(cuts),
            "treeName": "Events",
            "rowUnit": "event",
        }
        if tree_weight is not None:
            result["events"]["treeWeight"] = tree_weight
    return result
