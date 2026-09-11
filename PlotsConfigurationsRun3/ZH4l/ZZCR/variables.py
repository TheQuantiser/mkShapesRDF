"""Explicit compact observable set for nominal ZZCR/SR production."""

from common.observables import select_observables
from common.outputs import branches, with_tree_outputs

variables = select_observables(
    "z_mass",
    "x_mass",
    "zx_mass",
    "z_pt",
    "x_pt",
    "zx_pt",
    "PuppiMET_pt",
    "zx_min_pair_mass",
    "veto_lepton_count",
)
variables = with_tree_outputs(
    variables,
    globals().get("cuts", {}),
    branches("identity", "source", "z", "x", "zx", "jets_met", "corrections"),
)
