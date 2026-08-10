"""Thin materialization of the declarative ZZ_CR category registry."""

import os

from category_config import PRESELECTION, build_categories

preselections = PRESELECTION

cuts, CATEGORY_METADATA, CATEGORY_PROFILE = build_categories(
    globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS"),
    globals().get("CATEGORY_PROFILE") or os.environ.get("CATEGORY_PROFILE"),
)
FINAL_CATEGORY_IDS = tuple(CATEGORY_METADATA)
