# RunStability file guide

`RunStability` is a complete configuration leaf. Generated pickles, contracts,
Condor material, ROOT files, and plots are products of this source tree; they
must not become a second configuration source.

## Declarative owners

| File | Owns |
| --- | --- |
| `run_stability_profiles.json` | Default production profile, 35/35 GeV selection, strict mass window, six axes, category IDs/labels/sources, trigger joins and TrigMaker families, active luminosity-binding path |
| `year_config.json` | Era campaigns, DATA components/run tags/streams/triggers, physical HLT paths, MC samples and exact nominal result luminosities |
| `lumi/run_stability_luminosity_binding.json` | Active live-year-config and immutable-source-audit identity/hashes |
| `plot_reproduction.json` | Exact retained historical pickle and merged-ROOT identities for manual plot reproduction only |

`plot_reproduction.json` is deliberately not an input to future production.

## Materialization and execution

| File | Responsibility |
| --- | --- |
| `run_stability_production.py` | Schema-validates the profile JSON and resolves `RUN_STABILITY_PRODUCTION_PROFILE` |
| `year_config.py` | Schema-validates and exposes era/sample declarations |
| `selection_config.py` | Builds selected-object state and joins profile aggregate/ordinal records to year-owned physical paths |
| `category_config.py` | Generates the deterministic 48 categories and category-to-luminosity-source map from materialized joins |
| `histogram_config.py` | Materializes the six-observable histogram registry |
| `run_stability_config.py` | Resolves and validates the embedded/overridden luminosity audit and run map |
| `configuration.py` | Derives the early canonical identity through pure loaders, then resolves execution mode and shared configuration |
| `samples.py` | Discovers DATA and MC files and defines sample weights |
| `aliases.py` | Defines selected-object, stream, trigger, weight, and run-index aliases |
| `cuts.py` | Emits the resolved 48-category DY cut graph |
| `variables.py` | Emits ordinary TH1 definitions and run-stability booking metadata |
| `plot.py`, `structure.py` | Compile process/group presentation metadata and process roles |
| `nuisances_nominal.py` | Supplies the supported nominal-only nuisance contract |
| `write_contract.py` | Serializes and checks the resolved analysis contract |
| `worker_payload.py` | Builds the self-contained worker payload from the compiled state |
| `run_stability_runner.py` | Delegates ordinary TH1 work and adds DATA-only run-resolved TH2/metadata booking |
| `macros/run_stability_helpers.cc` | Owns local selected-object alignment, ordering, stream-priority, and scale-factor helpers |
| `macros/selected_trigger_wrappers.cc` | Evaluates canonical TrigMaker algebra for the selected Z pair |

Do not add a competing hard-coded axis, category, luminosity, or sample list to
these Python files. Extend the correct JSON owner and its validation instead.

## Shared-global execution order

`ConfigLib` executes these entries from `filesToExec` in one namespace:

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

This order is part of the interface. A name can be produced in one file and
consumed later without an import. Trace both producers and consumers before
changing it.

## Luminosity and plotting

| Path | Responsibility |
| --- | --- |
| `lumi/run_stability_luminosity_binding.json` | Mutable active binding receipt for the live leaf and immutable audit hashes |
| `lumi/audits/<audit-id>/` | Immutable inputs, results, validation, and provenance for one historical luminosity identity |
| `lumi/README.md` | Binding, exact nominal result, override, and audit-regeneration boundary |
| `lumi/REPRODUCE.md` | Manual catalog, DBS, BRIL, aggregation, reproduction, validation, and rebinding sequence |
| `plot_run_stability.py` | Python/Matplotlib period, ratio-vs-run, and reduced-chi-square plotting |
| `reproduce_plots.py` | Hash-validates the retained inputs, prints commands by default, and executes only with `--execute` |

ROOT is the scientific container format. The supported presentation path uses
Python plotting packages through `plot_run_stability.py`.

## Validation and documentation

| Path | Responsibility |
| --- | --- |
| `tests/` | Configuration, category, axis, luminosity, runner, merge, plotting, and failure-path checks |
| `inspect_plan.py` | Read-only nominal plan; reports `nominal_action_estimate` and `systematic_action_estimate: 0` |
| `check_storage_paths_from_list.py` | All-parts storage check; optional receipt kind is `run_stability_all_parts_storage_audit` |
| `README.md` | Public DY contract and concise manual entry point |
| `ARCHITECTURE.md` | Ownership and lifecycle boundary |
| `CONFIGURATION.md` | Resolved physics/configuration contract |
| `USAGE.MD` | Bounded validation, batch preparation, and plot reproduction commands |
| `LUMINOSITY_PROPAGATION.md` | Denominator, scaling, covariance, uncertainty, and chi-square semantics |
| `production_history/README.md` | Status index separating failed, superseded, retained, and current-source evidence |
| `production_history/*.md` | Immutable campaign evidence; old paths and identities remain historical facts |
| `development/` | Historical design/audit evidence, not the current public interface |
| `skills/run-stability/` | Local operational guardrails for agents |

The active site wrappers are `lxplus_env.sh`, `lxplus_fnal_env.sh`, and
`fnal_lpc_packaged_env.sh`. `lxplus_fnal_env.sh` selects LXPLUS shared-checkout
execution with CERN XRootD input and FNAL EOS stage-out. No `zzcr` wrapper is
part of the active leaf.
