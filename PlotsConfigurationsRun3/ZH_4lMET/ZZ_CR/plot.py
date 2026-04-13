from zzcr_year import load_selected_year

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
