# DY RunStability

`RunStability` is a self-contained, DY-only mkShapesRDF configuration. It
books ordinary one-dimensional MC and DATA histograms plus a DATA-only
run-resolved TH2 hierarchy. It does not expose ZZCR, SR, tree-output, or
systematic-production modes. The original `ZH_4lMET/ZZ_CR`, `ZH4l`, and
mkShapesRDF core are compatibility references, not implementation targets.

Here, self-contained means that the analysis contract, luminosity evidence,
validation, plotting, operational skill, and retained reproduction identities
live in this leaf without importing a sibling analysis. The leaf still uses
the mkShapesRDF framework and the workspace's generic BRIL/DBS audit engine;
those shared services are dependencies, not duplicate analysis configuration.

Read [ARCHITECTURE.md](ARCHITECTURE.md) for ownership,
[USAGE.MD](USAGE.MD) for commands, and
[LUMINOSITY_PROPAGATION.md](LUMINOSITY_PROPAGATION.md) for the statistical
definitions. The researched, not-yet-active catalog for possible pileup,
jet, isolation, recoil, FSR, and trigger-object additions is in
[OBSERVABLE_CANDIDATES.md](OBSERVABLE_CANDIDATES.md). The local operational
skill is
[`skills/run-stability/SKILL.md`](skills/run-stability/SKILL.md).
The exact luminosity reconstruction sequence is in
[`lumi/REPRODUCE.md`](lumi/REPRODUCE.md), and dated campaign status is indexed
by [`production_history/README.md`](production_history/README.md).

## Public contract

The only supported analysis graph is:

```bash
export YEAR=2024                         # 2022, 2022EE, 2023, 2023BPix, 2024
export ANALYSIS_PASS=RUN_STABILITY
export RUN_STABILITY_PRODUCTION_PROFILE=dy
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
```

The default `dy` profile applies strict selected-Z lepton thresholds of
35/35 GeV and a strict `60 < m(Z0) < 120 GeV` window. Its six observables are
`Z0_mass`, `Z0_pt`, `lZ1_pt`, `lZ2_pt`, `lZ1_eta`, and `lZ2_eta`.
Its deterministic 48 categories contain inclusive/flavor views, stream and
stream-by-flavor views, five positive trigger-family views, seven concrete
HLT-path views, and their selected-Z-flavor children. `DY_ALL`, `DY_ZEE`, and
`DY_ZMM` are Trigger-OR reference projections.

The focused axes use compact JSON triples `[n_bins, start, stop]`:

| Observable | Uniform axis | Fold |
| --- | --- | ---: |
| `Z0_mass` | `[60, 60.0, 120.0]` | 0 |
| `Z0_pt` | `[20, 0.0, 100.0]` | 2 |
| `lZ1_pt`, `lZ2_pt` | `[13, 35.0, 100.0]` | 2 |
| `lZ1_eta`, `lZ2_eta` | `[50, -2.5, 2.5]` | 0 |

`fold=0` retains neither flow; `fold=2` folds overflow only. The ordinary TH1
and DATA TH2 y axis use the same materialized definition.

Do not copy these values into another source. The authoritative profile is
`run_stability_profiles.json`; `run_stability_production.py` validates and
materializes it, and the other Python files consume that materialized state.

## Configuration ownership

| Concern | Declarative owner | Python materializer/consumer |
| --- | --- | --- |
| Eras, campaigns, MC/DATA samples, stream triggers, physical HLT paths, nominal result luminosity | `year_config.json` | `year_config.py`, `selection_config.py`, `samples.py`, `plot.py` |
| Selection thresholds, mass window, observable expressions/axes, category IDs/labels/sources, trigger aggregate joins, TrigMaker families, default profile, luminosity-binding path | `run_stability_profiles.json` | `run_stability_production.py` |
| Physical-path/category join and DY category-to-luminosity routing | profile aggregate/ordinal records joined to year-owned paths | `selection_config.py`, `category_config.py` |
| Selected objects and event aliases | materialized selection/profile state | `selection_config.py`, `aliases.py` |
| Histogram registry and active six-observable matrix | profile axes/observables | `histogram_config.py`, `variables.py` |
| Active-to-historical luminosity identity | `lumi/run_stability_luminosity_binding.json` plus immutable audit | `run_stability_config.py` |
| Compile, serialization, batch, and job identity | resolved state | `configuration.py`, `write_contract.py`, `worker_payload.py` |
| DATA run-resolved booking | compiled run contract | `run_stability_runner.py` |
| Plot formulas and rendering | compiled pickle and merged ROOT | `plot_run_stability.py` |

See [FILE_GUIDE.md](FILE_GUIDE.md) for the execution chain. Generated pickles,
contracts, payloads, jobs, ROOT files, and plots are outputs, not configuration
sources.

## Self-contained luminosity

The canonical profile names the active live-leaf receipt:

```text
lumi/run_stability_luminosity_binding.json
```

That receipt binds the current `year_config.json` and its semantic projection
to exact immutable source-audit hashes. The source audit remains:

```text
lumi/audits/ZZ_CR_RunStability_BCD_afa86d85_conjunction_20260818T200415Z/
```

The historical audit identifier is intentionally unchanged. It is immutable
evidence, not the current leaf name or active binding identity. With
`RUN_STABILITY_LUMI_DIR` unset, `run_stability_config.py` validates the active
binding and resolves its source audit. An explicit absolute results path is an
advanced override: it bypasses the default binding comparison, but not audit
manifest, provenance, schema, semantic-projection, run-set, aggregate, nominal
result, or runtime-luminosity checks.

The audit manifest must hash-match its embedded `inputs/year_config.json`
snapshot. The live and audited BRIL-input projections must then match exactly.
That projection contains only:

- DATA components, run tags, streams, and component trigger rules;
- `data_stream_triggers`;
- the processing-era identifier;
- the configured concrete trigger paths.

It deliberately excludes `lumi_fb`: nominal recorded luminosity is a derived
audit result, not a BRIL query input. Each live full-precision `lumi_fb` is
instead required to equal the exact validated
`luminosity_by_analysis_era.csv` result, and the selected runtime `lumi` must
equal that same value exactly. The default binding also hashes the complete
live `year_config.json`; refresh the active binding receipt after any live-file
change, and rebuild the audit only after a BRIL-input projection change.

Current nominal recorded luminosities, used as the era-level MC source
normalizations for future compiles, are stored at full precision:

| Era | Nominal recorded luminosity [fb^-1] |
| --- | ---: |
| 2022 | 8.076828657919002 |
| 2022EE | 26.671325997159986 |
| 2023 | 18.062658998219003 |
| 2023BPix | 9.693130030386998 |
| 2024 | 109.72830897472497 |

These nominal values are not trigger-effective exposures. Each category uses
`--luminosity-source auto`: reference and stream categories route to the
positive Trigger-OR exposure, trigger-family categories route to their family
exposure, and HLT categories route to their concrete-path exposure. Flavor
children inherit their parent's source. All effective sources are evaluated
per run after certification, dataset coverage, component baseline/de-duplication
trigger, and category-trigger conjunction. A zero effective exposure remains
zero; it is never replaced with nominal luminosity.

The compiler serializes all run rows and source routing into the exact pickle,
analysis contract, and worker payload. Workers and plotting commands consume
that compiled state; they do not reopen the audit bundle.

See [lumi/README.md](lumi/README.md) for the embedded bundle boundary and
[LUMINOSITY_PROPAGATION.md](LUMINOSITY_PROPAGATION.md) for scaling and
uncertainties.

## Output contract

Ordinary histograms retain the mkShapesRDF hierarchy:

```text
<category>/<observable>/histo_<sample>
```

DATA additionally contains:

```text
run_stability/<category>/<observable>/histo_DATA
```

The TH2 x axis is the exact audited run order; its y axis matches the ordinary
observable. The output also contains delivered and recorded run histograms for
all luminosity sources and `mc_source_lumi_fb`. Unknown runs and nonempty run
axis flows fail closed. MC remains era-inclusive and one-dimensional.

## Reproduce retained plots

`plot_reproduction.json` pins the five exact historical pickles and merged
ROOT files by SHA-256. Validate before plotting:

```bash
cd PlotsConfigurationsRun3/ZH_4lMET/RunStability
python reproduce_plots.py validate
```

Commands print without executing by default. Add `--execute` only after
reviewing the resolved command:

```bash
python reproduce_plots.py ratio-vs-run \
  --category DY_ALL --observable Z0_mass \
  --output-dir /absolute/new/ratio

python reproduce_plots.py chi2-vs-run \
  --category DY_ALL --observable Z0_pt \
  --output-dir /absolute/new/chi2

python reproduce_plots.py period-plot \
  --era 2024 --period 2024C \
  --category DY_ALL --observable Z0_mass \
  --output-dir /absolute/new/period
```

The reproduction manifest preserves the completed campaign's exact historical
numerical contract. It is not a source for a future production and does not
adopt later `year_config.json` values.

## Future production policy

Future campaigns are source-first:

1. Change the appropriate declarative JSON owner.
2. Rebuild the luminosity audit if and only if the BRIL-input projection
   changes; otherwise retain the immutable audit. Bind exact nominal results,
   then refresh and validate `run_stability_luminosity_binding.json`.
3. Run focused tests and inspect the fully resolved profile/category/axis and
   luminosity contracts.
4. Compile a fresh exact pickle without submission; reopen it and verify era,
   tag, local campaign, remote campaign, inputs, axes, sources, and hashes.
5. Submit that exact pickle only after separate authorization.
6. Verify scheduler history, durable split equality, every ROOT file, merge,
   formulas, and visual output before promotion.
7. Create a new pinned plot-reproduction manifest for the promoted campaign.

Never use the retained historical campaign, a moving `latest` pickle, or a
renamed directory as a numerical source for a future batch. Compile eras
serially because the leaf-global pickle filename has one-second resolution.

Historical production evidence under `production_history/` and copied audit
provenance retain their original paths and identifiers by design.
