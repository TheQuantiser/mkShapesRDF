"""Keep plotting/model dictionaries consistent with a bounded sample selection."""

plot = {name: value for name, value in plot.items() if name in samples}
structure = {name: value for name, value in structure.items() if name in samples}
for group in groupPlot.values():
    group["samples"] = [name for name in group["samples"] if name in samples]
groupPlot = {name: value for name, value in groupPlot.items() if value["samples"]}
if not zpt["systematics"]:
    nuisances = {}
else:
    for nuisance in nuisances.values():
        if "samples" in nuisance:
            nuisance["samples"] = {
                name: value
                for name, value in nuisance["samples"].items()
                if name in samples
            }
    nuisances = {
        name: value
        for name, value in nuisances.items()
        if value.get("samples") or value.get("type") == "auto"
    }
