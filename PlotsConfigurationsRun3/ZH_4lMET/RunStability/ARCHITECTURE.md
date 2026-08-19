# RunStability architecture

## Boundary

`RunStability` is a complete DY-only configuration leaf. It owns its
declarative production profile, era/sample configuration, active luminosity
binding, immutable luminosity evidence, custom runner, Python plotting,
validation, production history, and retained plot-reproduction manifest.

Only `ANALYSIS_PASS=RUN_STABILITY` is public. The runner delegates ordinary
TH1 work to core `RunAnalysis` and adds DATA-only run-resolved TH2 booking and
metadata. ROOT files are scientific containers; Python/Matplotlib is the
presentation path.

## Sources of truth

| Layer | Owner | Materializer | Main consumers |
| --- | --- | --- | --- |
| Era/sample inputs, physical HLT paths, nominal luminosity results | `year_config.json` | `year_config.py` | selection, samples, plotting, luminosity validation |
| DY selection, axes, category IDs/labels/sources, trigger aggregate joins and TrigMaker families | `run_stability_profiles.json` | `run_stability_production.py` | early identity, selection, categories, variables |
| Active live-leaf luminosity identity | `lumi/run_stability_luminosity_binding.json` | `run_stability_config.py` | compiled contract and provenance |
| Immutable BRIL audit | `lumi/audits/<audit-id>/` | `run_stability_config.py` | run rows, exposure sources, exact nominal results |
| Exact compiled execution | timestamped pickle plus `analysis_contract.json` | `configuration.py`, `write_contract.py` | batch, merge, plotting |
| Retained plot reproduction | `plot_reproduction.json` | `reproduce_plots.py` | manual ratio, chi-square, and period plots |

Physical HLT branch strings occur only in `year_config.json`. The profile owns
stable category IDs, display labels, luminosity sources, trigger aggregates,
TrigMaker-family names, and concrete-path aggregate/ordinal joins. Selection
materialization joins those records to the year-owned paths, verifies exact
DATA/MC TrigMaker agreement, and requires every configured path exactly once.

## Compile flow and identity

Before shared-global execution, `configuration.py` uses only pure validated
loaders from `run_stability_production.py` and `year_config.py` to derive the
canonical era/profile/category identity and tag. It does not execute analysis
materializers early or infer a fallback identity.

`ConfigLib` then executes this semantic order once:

```text
year_config.py
selection_config.py
category_config.py
samples.py
run_stability_config.py
aliases.py
cuts.py
variables.py
plot.py
nuisances_nominal.py
structure.py
write_contract.py
worker_payload.py
```

Selection resolves year/profile trigger joins before categories, and
categories resolve before sample discovery. All entries share one global
namespace; their order is part of the interface. The resulting pickle is a
snapshot of resolved state, not a pointer to current JSON or Python.

## Luminosity binding

The profile points to the active binding receipt, not directly to a historical
audit. In default mode the receipt binds the current live year-config path,
whole-file SHA-256, BRIL-input projection SHA-256, source-audit path, manifest,
provenance, and nominal-era-result hashes. The historical audit remains
byte-for-byte evidence with its original identity.

The BRIL-input projection contains DATA membership, component and stream
trigger rules, processing era, and physical HLT paths. It excludes `lumi_fb`
because luminosity is a query result. Every live `lumi_fb` is bound separately
by exact equality to the validated nominal recorded result for its analysis
era; selected runtime `lumi` must equal that value exactly.

Nominal recorded luminosity normalizes the era-level MC template. Category
exposure is a separate run-resolved certified, dataset-covered,
component-trigger/category-trigger conjunction. The plotter scales MC once by
`L_category(run) / L_MC_source(era)`.

## Artifact lifecycle

Source changes create a fresh compiled identity. Submission, completion,
stage-out, split verification, merge, numerical audit, visual audit, promotion,
and cleanup are separate gates. Historical pickles, ROOT files, production
ledgers, audit receipts, and copied audit provenance are immutable evidence.

`plot_reproduction.json` pins the completed historical campaign so plots remain
reproducible after live-source evolution. Future campaigns compile from
current sources and receive a new reproduction manifest only after promotion.

## Change workflow

All numerical changes are source-first. Modify exactly one declarative owner,
extend its validator when necessary, and let the shared execution chain derive
cuts, weights, axes, identities, contracts, and worker payloads. Never edit a
compiled pickle, tag-local contract, worker payload, JDL, merged ROOT file,
plot CSV/JSON/ROOT receipt, or promoted image to imitate a source change.

Changes to the BRIL-input projection require a fresh immutable luminosity
audit. Changes outside that projection may retain the audit only after the
active binding is refreshed and all bound hashes and exact nominal-result
equalities pass. Historical evidence is never rewritten to match the live
leaf.
