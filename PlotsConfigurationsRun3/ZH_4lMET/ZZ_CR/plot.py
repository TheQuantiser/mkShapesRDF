groupPlot = {}
plot = {}
legend = {}

legend["lumi"] = "L = %.1f fb^{-1}" % 8.0
legend["sqrt"] = "#sqrt{s} = 13.6 TeV"

# Example plotting configuration. Update colors and ordering as needed.
if "ZZ" not in groupPlot:
    groupPlot["ZZ"] = {
        "nameHR": "ZZ",
        "isSignal": 0,
        "color": 600,
        "samples": ["ZZ"],
    }

if "WZ" not in groupPlot:
    groupPlot["WZ"] = {
        "nameHR": "WZ",
        "isSignal": 0,
        "color": 617,
        "samples": ["WZ"],
    }

if "DY" not in groupPlot:
    groupPlot["DY"] = {
        "nameHR": "DY",
        "isSignal": 0,
        "color": 418,
        "samples": ["DY"],
    }

if "top" not in groupPlot:
    groupPlot["top"] = {
        "nameHR": "Top",
        "isSignal": 0,
        "color": 400,
        "samples": ["top"],
    }

if "DATA" not in groupPlot:
    groupPlot["DATA"] = {
        "nameHR": "Data",
        "isSignal": 0,
        "color": 1,
        "samples": ["DATA"],
    }

plot["ZZ"] = {
    "color": 600,
    "isSignal": 0,
    "isData": 0,
    "scale": 1.0,
}

plot["WZ"] = {
    "color": 617,
    "isSignal": 0,
    "isData": 0,
    "scale": 1.0,
}

plot["DY"] = {
    "color": 418,
    "isSignal": 0,
    "isData": 0,
    "scale": 1.0,
}

plot["top"] = {
    "color": 400,
    "isSignal": 0,
    "isData": 0,
    "scale": 1.0,
}

plot["DATA"] = {
    "color": 1,
    "isSignal": 0,
    "isData": 1,
    "scale": 1.0,
}
