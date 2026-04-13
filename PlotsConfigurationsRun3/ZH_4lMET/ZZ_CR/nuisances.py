from zzcr_year import load_selected_year

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
