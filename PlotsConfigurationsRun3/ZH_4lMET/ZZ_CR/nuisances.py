# Dfinitions of groups of samples
mc = [skey for skey in samples if skey not in ("DATA")]

nuisances = {}

################################ EXPERIMENTAL UNCERTAINTIES  #################################

# https://twiki.cern.ch/twiki/bin/view/CMS/LumiRecommendationsRun3
nuisances["lumi_2024"] = {
    "name": "lumi_2024",
    "type": "lnN",
    "samples": dict((skey, "1.016") for skey in mc),
}

### MC statistical uncertainty
autoStats = True
if autoStats:
    nuisances["stat"] = {
        "type": "auto",
        "maxPoiss": "10",
        "includeSignal": "0",
        "samples": {},
    }
