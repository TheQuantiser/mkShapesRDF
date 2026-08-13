"""Materialize a flat sparse cut graph; every cut includes the live preselection."""

import os
from collections import OrderedDict

from study_config import PRESELECTION, build_categories, nominal_factor


CLOSURE_PROFILE = os.environ.get("CLOSURE_PROFILE", "default").strip().lower()
_stage_expressions = build_categories(CLOSURE_PROFILE)
preselections = "1"
cuts = OrderedDict(
    (
        name,
        {
            "expr": f"({PRESELECTION}) && ({expression})",
            "weights": {"*": nominal_factor(name)},
        },
    )
    for name, expression in _stage_expressions.items()
)
CATEGORY_METADATA = OrderedDict(
    (
        name,
        {
            "category_id": name,
            "stage_expression": expression,
            "full_cut_expression": cuts[name]["expr"],
            "nominal_factor": nominal_factor(name),
            "nonprompt_background_included": False,
        },
    )
    for name, expression in _stage_expressions.items()
)

