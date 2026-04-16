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
