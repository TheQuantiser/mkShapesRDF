"""Derive plot and structure dictionaries from the era catalogue."""


def build_plot(samples, full_config, lumi_fb):
    active = set(samples)
    groups = {}
    assigned = set()
    for key, cfg in full_config["plot_groups"].items():
        members = [sample for sample in cfg["samples"] if sample in active]
        if not members:
            continue
        groups[key] = {
            "nameHR": cfg["nameHR"],
            "isSignal": int(cfg.get("isSignal", 0)),
            "color": int(cfg["color"]),
            "samples": members,
        }
        assigned.update(members)
    missing = sorted((active - {"DATA"}) - assigned)
    if missing:
        raise RuntimeError(f"Configured samples lack plot-group ownership: {missing}")
    plot = {}
    if "DATA" in active:
        plot["DATA"] = {
            "nameHR": "Data", "color": 1, "isData": 1, "isSignal": 0
        }
    for group_name, group in groups.items():
        for sample in group["samples"]:
            plot[sample] = {
                "nameHR": sample,
                "color": group["color"],
                "isData": 0,
                "isSignal": group["isSignal"],
                "group": group_name,
            }
    return groups, plot, {"lumi": f"L = {lumi_fb:.2f} fb^{{-1}}", "sqrt": "#sqrt{s} = 13.6 TeV"}


def build_structure(samples, full_config):
    signals = {
        sample
        for cfg in full_config["plot_groups"].values()
        if cfg.get("isSignal")
        for sample in cfg["samples"]
    }
    return {
        sample: {
            "isSignal": int(sample in signals),
            "isData": int(sample == "DATA"),
        }
        for sample in samples
    }
