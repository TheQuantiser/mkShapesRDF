import os
import sys

_this_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

if "load_selected_year" not in globals():
    _zzcr_config_dir = os.path.abspath(
        globals().get("ZZCR_CONFIG_DIR")
        or (os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None)
        or globals().get("folder")
        or os.getcwd()
    )
    exec(
        open(os.path.join(_zzcr_config_dir, "zzcr_year.py")).read(),
        globals(),
        globals(),
    )

# Sample groups
_samples_dict = globals().get("samples", {})
mc = [skey for skey in _samples_dict if skey not in ("DATA")]

nuisances = {}

ZZCR_YEAR, _selected_year, _ = load_selected_year()
_lumi_cfg = _selected_year["lumi_nuisance"]

nuisances[_lumi_cfg["name"]] = {
    "name": _lumi_cfg["name"],
    "type": "lnN",
    "samples": dict((skey, _lumi_cfg["value"]) for skey in mc),
}

autoStats = True
if autoStats:
    nuisances["stat"] = {
        "type": "auto",
        "maxPoiss": "10",
        "includeSignal": "0",
        "samples": {},
    }
