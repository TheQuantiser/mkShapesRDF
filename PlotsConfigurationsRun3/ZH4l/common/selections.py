"""Selection predicates on fixed object references; no candidate reselection."""

import math

from .definitions import Candidate


def all_of(analysis, name, *predicates):
    return analysis.column(
        name,
        " && ".join(f"({p})" for p in predicates) or "true",
        dependencies=predicates,
    )


def any_of(analysis, name, *predicates):
    return analysis.column(
        name,
        " || ".join(f"({p})" for p in predicates) or "false",
        dependencies=predicates,
    )


def window(analysis, name, observable, low, high, *, inclusive=False):
    if not math.isfinite(low) or not math.isfinite(high) or low >= high:
        raise ValueError("A window requires finite increasing boundaries")
    lower, upper = (">=", "<=") if inclusive else (">", "<")
    return analysis.column(
        name,
        f"{observable} {lower} {float(low)} && {observable} {upper} {float(high)}",
        dependencies=(observable,),
    )


def ordered_pt(analysis, name, objects, thresholds, *, inclusive=False):
    thresholds = tuple(float(t) for t in thresholds)
    if (
        not thresholds
        or any(not math.isfinite(t) or t < 0 for t in thresholds)
        or any(a < b for a, b in zip(thresholds, thresholds[1:]))
    ):
        raise ValueError(
            "Ordered pT thresholds must be finite, nonnegative and descending"
        )
    view = objects.view if isinstance(objects, Candidate) else objects
    pt = view.source["pt"]
    return analysis._helper(
        name,
        f"ZH4lViews::orderedPt({pt},{view.indices},ROOT::RVecF{{{','.join(str(t)+'f' for t in thresholds)}}},{str(inclusive).lower()})",
        (pt, view.indices),
    )
