# Run-3 ZH four-lepton analysis family

`ZH4l` contains the shared Run-3 four-lepton object and correction contract
and three independent mkShapesRDF leaves:

- `ZZCR/` — nominal four-lepton ZZ control and ZH signal-region production;
- `Pairing/` — comparison of nominal and alternative Z/X pairing algorithms;
- `Closure/` — the DY-to-ZZ selection, trigger, flavor, and weight closure
  ladder found in the working tree when the migration began.

The leaves never import one another.  They consume the one authoritative
implementation in `common/`.  The existing `ZH_4lMET/` tree is intentionally
untouched, as required for this migration.

## Where things are

| Question | Owner |
|---|---|
| Inputs, logical processes, stitching | `common/eras.json`, `common/catalog.py`, then each leaf's `samples.py` |
| Tight leptons and nominal Z/X pairing | `common/objects.py`, `common/macros/objects.cc` |
| Common kinematics and binnings | `common/observables.py` |
| Lepton/trigger/b-veto weights | `common/corrections.py` and `common/macros/` |
| Physical regions | `<leaf>/cuts.py` |
| Plotted observables | `<leaf>/variables.py` |
| Process display/bookkeeping | `common/presentation.py`, `<leaf>/plot.py`, `<leaf>/structure.py` |
| Uncertainties | `<leaf>/nuisances.py` |
| Site and batch settings | `common/runtime.py`, `env/` |

## Setup and quick start

Run from the repository root. `ERA` is the preferred selector; supported
values are `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`. `YEAR` is accepted
only as a checked compatibility alias. Conflicting `ERA` and `YEAR` values
fail immediately.

```bash
source start.sh
source PlotsConfigurationsRun3/ZH4l/env/lxplus.sh   # or fnal.sh

export ERA=2024
export SAMPLE_FILTER=ZZ
export LIMIT_FILES_PER_SAMPLE=1
export ENABLE_SYSTEMATICS=0
export ZH4L_CAMPAIGN=zzcr_smoke

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH4l/ZZCR -l 100
```

Use `ENABLE_SYSTEMATICS=1` for the full ZZCR nuisance model.  `SAMPLE_PROFILE`
selects a centrally validated operational scope and `SAMPLE_FILTER` narrows it
to a comma-separated set of logical outputs.  Generated `configs/`, `condor/`,
`rootFiles/`, plots, caches, and rendered reports are ignored.

For the studies:

```bash
PlotsConfigurationsRun3/ZH4l/Pairing/run_all_eras.sh pilot
PlotsConfigurationsRun3/ZH4l/Closure/run_all_eras.sh compile
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for ownership and naming, the leaf
READMEs for analysis commands, [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md)
for the reuse decision record, and [MIGRATION_REPORT.md](MIGRATION_REPORT.md)
for validation evidence and limitations.
