# RunStability configuration contract

The public contract is DY-only, nominal-only, and histogram-only:

```bash
export ANALYSIS_PASS=RUN_STABILITY
export RUN_STABILITY_PRODUCTION_PROFILE=dy
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
```

The leaf does not expose ZZCR, SR, tree-output, or systematic-production
graphs. The canonical declaration is `run_stability_profiles.json`; the
Python configuration validates and materializes it rather than maintaining a
second list of selections, axes, observables, or categories.

## Ownership

| Concern | Authoritative declaration | Materializer/consumer |
| --- | --- | --- |
| Eras, samples, run tags, stream triggers, physical HLT paths, nominal result luminosity | `year_config.json` | `year_config.py`, `selection_config.py`, `samples.py`, `plot.py` |
| Default profile, selected-lepton thresholds, mass window, axes, category IDs/labels/sources, trigger aggregate joins and TrigMaker families, binding path | `run_stability_profiles.json` | `run_stability_production.py` |
| Physical-path join, category graph, luminosity-source routing | profile aggregate/ordinal records joined to year paths | `selection_config.py`, `category_config.py` |
| Aliases and selected-object logic | materialized profile | `selection_config.py`, `aliases.py` |
| Histogram matrix | materialized observable names and axes | `histogram_config.py`, `variables.py` |
| Active live-to-audit identity | `lumi/run_stability_luminosity_binding.json` plus immutable audit | `run_stability_config.py` |
| Exact execution snapshot | resolved shared configuration | `configuration.py`, `write_contract.py`, `worker_payload.py` |
| Run-resolved DATA booking | compiled contract | `run_stability_runner.py` |
| Plot statistics and presentation | exact pickle plus merged ROOT | `plot_run_stability.py` |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the data flow and
[FILE_GUIDE.md](FILE_GUIDE.md) for the execution order.

## Canonical DY profile

The `dy` profile applies:

- a closest-OSSF selected `Z0` pair whose ordered leptons each satisfy the
  strict threshold `pT > 35 GeV`;
- a strict `60 < Z0_mass < 120 GeV` selection;
- six observables in fixed order: `Z0_mass`, `Z0_pt`, `lZ1_pt`, `lZ2_pt`,
  `lZ1_eta`, and `lZ2_eta`;
- a deterministic 48-category graph generated from flavor, stream, five
  trigger-family, and configured concrete-HLT-path dimensions.

The three leading reference projections, `DY_ALL`, `DY_ZEE`, and `DY_ZMM`,
use the positive Trigger-OR exposure. Stream categories also use that source.
Trigger-family categories use their family source and concrete-path categories
use their HLT-path source. A selected-Z-flavor child inherits its parent's
source because flavor is an event category, not a different exposure.

Physical HLT branch strings live only in `year_config.json`. The profile's
seven concrete-path records contain stable IDs, labels, luminosity sources,
and aggregate/ordinal joins, not repeated paths. `selection_config.py` joins
them, checks the exact DATA/MC TrigMaker path inventory, and requires every
year-owned path exactly once. Category generation must retain deterministic
order and uniqueness and close at exactly 48 categories.

## Axes

Uniform axes are represented as compact triples `[n_bins, start, stop]`:

| Observable | Axis | Bin width | Fold |
| --- | --- | ---: | ---: |
| `Z0_mass` | `[60, 60.0, 120.0]` | 1 GeV | 0 |
| `Z0_pt` | `[20, 0.0, 100.0]` | 5 GeV | 2 |
| `lZ1_pt`, `lZ2_pt` | `[13, 35.0, 100.0]` | 5 GeV | 2 |
| `lZ1_eta`, `lZ2_eta` | `[50, -2.5, 2.5]` | 0.1 | 0 |

`fold=0` keeps neither flow; `fold=2` folds overflow only. The ordinary TH1
and run-resolved DATA TH2 y axis are produced from the same materialized axis.

## Era and luminosity inputs

`YEAR` must be one of `2022`, `2022EE`, `2023`, `2023BPix`, or `2024`.
`year_config.json` stores the nominal recorded luminosity used to normalize
each era's MC source template:

| Era | MC source luminosity [fb^-1] |
| --- | ---: |
| 2022 | 8.076828657919002 |
| 2022EE | 26.671325997159986 |
| 2023 | 18.062658998219003 |
| 2023BPix | 9.693130030386998 |
| 2024 | 109.72830897472497 |

These values are not category-effective luminosities. The immutable audit
provides nominal and trigger-effective values by run. For trigger categories,
exposure is the conjunction of certification, dataset coverage, each DATA
component's baseline/de-duplication trigger, and the requested category
trigger. Zero exposure remains zero.

The `dy` profile selects
`lumi/run_stability_luminosity_binding.json`. With
`RUN_STABILITY_LUMI_DIR` unset, that active receipt must match the live
year-config path/hash/projection and exact source-audit hashes. The audit
manifest independently binds its copied snapshot. Copied and live BRIL-input
projections compare DATA membership and trigger rules, processing era, stream
triggers, and physical paths; they exclude `lumi_fb`. Every live `lumi_fb` is
instead bound by exact equality to the validated nominal recorded result, and
runtime `lumi` must equal it exactly. See [lumi/README.md](lumi/README.md).

## Histogram and sample behavior

Ordinary DATA and MC histograms use:

```text
<category>/<observable>/histo_<sample>
```

DATA alone adds:

```text
run_stability/<category>/<observable>/histo_DATA
```

The TH2 x axis is the exact audited run order. Unknown runs and nonempty
run-axis flows fail closed. The runner also writes run-aligned delivered and
recorded luminosity metadata plus `mc_source_lumi_fb`. MC remains era-inclusive
and one-dimensional; the plotter projects it to a run or physical period.

`SAMPLE_PROFILE=presentation` supplies the complete compiled prompt model.
Period plots derive the `DY` membership from compiled plot metadata and group
the disjoint complement as `Others`; they do not infer group membership from
sample-name substrings.

## Compiled identity

Before `filesToExec`, `configuration.py` derives its canonical tag through only
the pure profile and year loaders. It does not execute later materializers or
use a fallback tag. `ConfigLib` then executes year, selection, category,
samples, luminosity, aliases, cuts, variables, plot, nominal nuisances,
structure, contract, and payload in one shared namespace. That order is part
of the interface. A timestamped pickle is a resolved executable snapshot, not
a pointer to current JSON or Python files. Before batch submission, reopen
the exact pickle and verify its era, local and remote campaign identities,
input inventory, six axes, 48 categories, luminosity source map, audit
provenance, and hashes. Compile eras serially and never resolve production
state through `latest`.

The retained `plot_reproduction.json` intentionally pins a completed
historical contract. Future campaigns compile from current sources; retained
history never silently absorbs later nominal-luminosity or profile changes.
