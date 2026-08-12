"""Minimal process styling for study ROOT outputs."""

_zh_samples = list(PAIRING_ERA["inventory"]["ZH"])
_zz_samples = list(PAIRING_ERA["inventory"]["ZZ"])

groupPlot = {
    "ZH": {
        "nameHR": "ZH/ggZH, H#rightarrowWW",
        "isSignal": 1,
        "color": ROOT.kRed + 1,
        "samples": _zh_samples,
    },
    "ZZ": {
        "nameHR": "ZZ/Z#gamma^{*}/#gamma^{*}#gamma^{*}",
        "isSignal": 0,
        "color": ROOT.kAzure + 1,
        "samples": _zz_samples,
    },
}

plot = {}
for _index, _sample in enumerate(_zh_samples):
    plot[_sample] = {
        "nameHR": _sample,
        "color": ROOT.kRed + 1 + _index,
        "isSignal": 1,
        "isData": 0,
    }
for _index, _sample in enumerate(_zz_samples):
    plot[_sample] = {
        "nameHR": _sample,
        "color": ROOT.kAzure + 1 + _index,
        "isSignal": 0,
        "isData": 0,
    }

legend = {
    "lumi": f"L = {PAIRING_ERA['lumi_fb']:.3f} fb^{{-1}}",
    "sqrt": "#sqrt{s} = 13.6 TeV",
}
