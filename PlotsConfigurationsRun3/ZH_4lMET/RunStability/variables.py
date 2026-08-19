"""Materialize the exact observable definitions declared in the JSON profile."""

from run_stability_production import run_stability_production_profile


if "CATEGORY_METADATA" not in globals():
    raise RuntimeError("cuts.py/category_config.py must run before variables.py")

_PROFILE = run_stability_production_profile()
_AXES = _PROFILE["axes"]
_ORDERED_OBSERVABLES = tuple(_PROFILE["observables"])
if tuple(_AXES) != _ORDERED_OBSERVABLES:
    raise RuntimeError("Configured observable and axis order diverge")
if tuple(globals().get("RUN_STABILITY_OBSERVABLES", ())) != _ORDERED_OBSERVABLES:
    raise RuntimeError(
        "RunStability requires the exact observable tuple declared by its profile"
    )


def _variable(name, definition):
    edges = [float(value) for value in definition["edges"]]
    return {
        "name": definition["expression"],
        "range": (edges,),
        "xaxis": definition["label"],
        "fold": int(definition["fold"]),
    }


_raw_variables = {name: _variable(name, _AXES[name]) for name in _ORDERED_OBSERVABLES}
HISTOGRAM_BINNING_CONTRACT = {
    name: {
        "source": {
            "profile": _PROFILE["name"],
            "uniform": list(_AXES[name]["uniform"]),
        },
        "resolved": list(_AXES[name]["edges"]),
        "fold": int(_AXES[name]["fold"]),
        "strategy": "declarative-uniform",
        "category_independent": True,
        "era_independent": True,
        "shared_by_variations": True,
    }
    for name in _ORDERED_OBSERVABLES
}

from histogram_config import materialize_histograms  # noqa: E402

(
    VARIABLE_REGISTRY,
    variables,
    CATEGORY_VARIABLES,
    HISTOGRAM_PROFILE,
) = materialize_histograms(
    _raw_variables,
    HISTOGRAM_BINNING_CONTRACT,
    CATEGORY_METADATA,
    globals().get("HISTOGRAM_PROFILE", "analysis"),
    globals().get("RUN_STABILITY_OBSERVABLES", ()),
    True,
)
VARIABLE_REGISTRY_HASHES = {
    name: definition["definition_sha256"]
    for name, definition in VARIABLE_REGISTRY.items()
}
