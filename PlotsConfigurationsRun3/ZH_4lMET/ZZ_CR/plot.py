import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

if "load_selected_year" not in globals():
    _candidates = [
        globals().get("ZZCR_CONFIG_DIR"),
        globals().get("folder"),
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None,
    ]
    _zzcr_config_dir = None
    for _cand in _candidates:
        if not _cand:
            continue
        _cand_abs = os.path.abspath(_cand)
        if os.path.exists(os.path.join(_cand_abs, "zzcr_year.py")):
            _zzcr_config_dir = _cand_abs
            break
    if _zzcr_config_dir is None:
        _zzcr_config_dir = os.path.abspath(os.getcwd())
    exec(
        open(os.path.join(_zzcr_config_dir, "zzcr_year.py")).read(),
        globals(),
        globals(),
    )

groupPlot = {}
plot = {}
legend = {}
_samples_dict = globals().get("samples", {})

_, _selected_year, _ = load_selected_year()
legend["lumi"] = f"L = {_selected_year.get('lumi_fb', 0.0):.2f} fb^{{-1}}"
legend["sqrt"] = "#sqrt{s} = 13.6 TeV"

for idx, sample_name in enumerate(s for s in _samples_dict if s != "DATA"):
    plot[sample_name] = {
        "color": 400 + idx,
        "isSignal": 0,
        "isData": 0,
        "scale": 1.0,
    }

if "DATA" in _samples_dict:
    plot["DATA"] = {"nameHR": "Data", "color": 1, "isSignal": 0, "isData": 1, "isBlind": 0}
