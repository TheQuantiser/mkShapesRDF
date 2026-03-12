# Sample groups
mc = [skey for skey in samples if skey not in ("DATA")]

nuisances = {}

nuisances["lumi_2024"] = {
    "name": "lumi_2024",
    "type": "lnN",
    "samples": dict((skey, "1.016") for skey in mc),
}

autoStats = True
if autoStats:
    nuisances["stat"] = {
        "type": "auto",
        "maxPoiss": "10",
        "includeSignal": "0",
        "samples": {},
    }
