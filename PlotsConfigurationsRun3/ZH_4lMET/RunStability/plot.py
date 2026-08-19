import os
import sys

_this_dir = (
    os.path.dirname(os.path.abspath(__file__))
    if "__file__" in globals()
    else os.getcwd()
)
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

if "load_selected_year" not in globals():
    _candidates = [
        globals().get("CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    _config_dir = None
    for _cand in _candidates:
        if not _cand:
            continue
        _cand_abs = os.path.abspath(_cand)
        if os.path.exists(os.path.join(_cand_abs, "year_config.py")):
            _config_dir = _cand_abs
            break
    if _config_dir is None:
        _config_dir = os.path.abspath(os.getcwd())
    exec(
        open(os.path.join(_config_dir, "year_config.py")).read(),
        globals(),
        globals(),
    )

if "CUT_DISPLAY_LABELS" not in globals():
    from selection_config import (
        CATEGORY_DISPLAY_LABELS,
        CUT_DISPLAY_LABELS,
    )

groupPlot = {}
plot = {}
legend = {}
_samples_dict = globals().get("samples", {})

_, _selected_year, _full_config = load_selected_year()
legend["lumi"] = f"L = {_selected_year.get('lumi_fb', 0.0):.2f} fb^{{-1}}"
legend["sqrt"] = "#sqrt{s} = 13.6 TeV"
legend["cutDisplayLabels"] = dict(CUT_DISPLAY_LABELS)
legend["categoryDisplayLabels"] = dict(CATEGORY_DISPLAY_LABELS)

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

for _group_name, _group_cfg in _plot_groups.items():
    _active_samples = [
        _sample_name
        for _sample_name in _group_cfg.get("samples", [])
        if _sample_name in _samples_dict and _sample_name != "DATA"
    ]
    if not _active_samples:
        continue
    groupPlot[_group_name] = {
        "nameHR": _group_cfg["nameHR"],
        "isSignal": int(_group_cfg.get("isSignal", 0)),
        "color": int(_group_cfg["color"]),
        "samples": _active_samples,
    }

for idx, sample_name in enumerate(s for s in _samples_dict if s != "DATA"):
    _group_name = _sample_to_group.get(sample_name)
    _group_cfg = _plot_groups.get(_group_name, {})
    plot[sample_name] = {
        # Keep the ordinary PlotsConfigurations per-sample label contract even
        # though the primary presentation uses groupPlot labels.
        "nameHR": sample_name,
        "color": 400 + idx,
        "isSignal": int(_group_cfg.get("isSignal", 0)),
        "isData": 0,
        "scale": 1.0,
    }

if "DATA" in _samples_dict:
    plot["DATA"] = {
        "nameHR": "Data",
        "color": 1,
        "isSignal": 0,
        "isData": 1,
        "isBlind": 0,
    }
