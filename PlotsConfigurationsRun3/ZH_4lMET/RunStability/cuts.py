"""Thin materialization of the declarative RunStability category registry."""

import os

if "build_categories" not in globals() or "PRESELECTION" not in globals():
    from category_config import PRESELECTION, build_categories

preselections = PRESELECTION

cuts, CATEGORY_METADATA, CATEGORY_PROFILE = build_categories(
    globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS"),
    globals().get("CATEGORY_PROFILE") or os.environ.get("CATEGORY_PROFILE"),
)
if (
    str(globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS", "")).upper()
    == "RUN_STABILITY"
):
    selected_categories = tuple(globals().get("RUN_STABILITY_CATEGORIES", ()))
    if not selected_categories:
        raise RuntimeError("RUN_STABILITY_CATEGORIES must be resolved before cuts.py")
    selected_set = set(selected_categories)
    CATEGORY_METADATA = type(CATEGORY_METADATA)(
        (name, definition)
        for name, definition in CATEGORY_METADATA.items()
        if name in selected_set
    )
    for parent in tuple(cuts):
        categories = cuts[parent].get("categories", {})
        cuts[parent]["categories"] = type(categories)(
            (suffix, expression)
            for suffix, expression in categories.items()
            if f"{parent}_{suffix}" in selected_set
        )
        if not cuts[parent]["categories"]:
            del cuts[parent]
    if tuple(CATEGORY_METADATA) != selected_categories:
        raise RuntimeError(
            "Resolved RUN_STABILITY category ordering diverges from cuts: "
            f"contract={selected_categories}, cuts={tuple(CATEGORY_METADATA)}"
        )
FINAL_CATEGORY_IDS = tuple(CATEGORY_METADATA)
