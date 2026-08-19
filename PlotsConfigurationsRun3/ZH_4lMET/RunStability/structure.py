structure = {}
_samples_dict = globals().get("samples", {})

_, _selected_year, _full_config = load_selected_year()
_plot_groups = _full_config.get("plot_groups", {})
_sample_to_group = {}
for _group_name, _group_cfg in _plot_groups.items():
    for _sample_name in _group_cfg.get("samples", []):
        if _sample_name in _sample_to_group:
            raise ValueError(
                f"Sample '{_sample_name}' is assigned to multiple plot groups: "
                f"{_sample_to_group[_sample_name]} and {_group_name}"
            )
        _sample_to_group[_sample_name] = _group_name

_configured_mc = set(
    resolve_overlap_model(_selected_year, _full_config)["output_names"]
)
_ungrouped_mc = sorted(_configured_mc - set(_sample_to_group))
if _ungrouped_mc:
    raise ValueError(
        "Every configured MC output process must belong to one plot group; "
        f"ungrouped samples: {_ungrouped_mc}"
    )

for sample_name in _samples_dict:
    _group_name = _sample_to_group.get(sample_name)
    _group_cfg = _plot_groups.get(_group_name, {})
    structure[sample_name] = {
        "isSignal": int(_group_cfg.get("isSignal", 0)),
        "isData": 1 if sample_name == "DATA" else 0,
    }
