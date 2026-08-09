"""Thin materialization of the declarative ZZ_CR category registry."""

import os

if "analysis_pass" not in globals() or "PAIR_ID_CONFIG" not in globals():
    from selection_config import PAIR_ID_CONFIG, analysis_pass

PRESELECTION = (
    "(Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || "
    "Trigger_sngEl || Trigger_dblEl)"
    " && nLepton >= 2 && L2TightLeading2 && nJetInHorn == 0"
)
preselections = PRESELECTION

from category_config import build_categories

cuts, CATEGORY_METADATA, CATEGORY_PROFILE = build_categories(
    globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS"),
    globals().get("CATEGORY_PROFILE") or os.environ.get("CATEGORY_PROFILE"),
)
FINAL_CATEGORY_IDS = tuple(CATEGORY_METADATA)
