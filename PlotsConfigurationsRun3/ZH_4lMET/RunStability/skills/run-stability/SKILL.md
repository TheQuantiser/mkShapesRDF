---
name: run-stability
description: Compile, run, submit, merge, reproduce, plot, or validate the self-contained DY-only ZH_4lMET RunStability leaf, including its declarative profile, active luminosity binding to immutable audit evidence, exact compiled identities, run-resolved DATA histograms, Python stability plots, and campaign-local cleanup.
---

# Operate DY RunStability safely

## Establish the live contract

Work from the writable `mkShapesRDF` checkout. Read the leaf `README.md`,
`ARCHITECTURE.md`, `USAGE.MD`, `LUMINOSITY_PROPAGATION.md`, and
`lumi/README.md`. Read `lumi/REPRODUCE.md` before rebuilding luminosity and
`production_history/README.md` before interpreting a retained campaign. Apply
the workspace plot-configuration inspection and
validation skills. Apply the CMS luminosity-audit skill when denominators,
certification, dataset coverage, or trigger-effective exposure are in scope.

Do not modify mkShapesRDF core, the original `ZH_4lMET/ZZ_CR`, the read-only
sibling configuration checkout, or `ZH4l` for this workflow. Source changes,
local execution, scheduler submission, remote writes, remote deletion, Git
publication, and cleanup are separate actions.

The public contract is exactly:

```bash
export ANALYSIS_PASS=RUN_STABILITY
export RUN_STABILITY_PRODUCTION_PROFILE=dy
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
```

Set `YEAR` to `2022`, `2022EE`, `2023`, `2023BPix`, or `2024`. Reject requests
to add ZZCR, SR, tree output, or systematic production to this leaf unless the
user explicitly authorizes a new architecture and its validation.

## Preserve single-source ownership

Inspect `run_stability_profiles.json` and `year_config.json` before editing any
Python materializer.

- `run_stability_profiles.json` owns the default profile, selection thresholds,
  mass window, observable expressions and compact axes, category IDs/labels/
  luminosity sources, trigger aggregate/ordinal joins, TrigMaker-family names,
  and the active luminosity-binding path.
- `year_config.json` owns era campaigns, DATA components and stream triggers,
  physical HLT path strings, MC samples, and exact nominal result luminosities.
- `lumi/run_stability_luminosity_binding.json` binds the live year config to
  exact immutable source-audit identities and hashes.
- Python validates and materializes these declarations. Do not introduce a
  second hard-coded registry.
- Generated pickles, contracts, payloads, JDLs, ROOT outputs, and plot
  receipts are immutable products. Never patch them to implement a requested
  numerical change; change the owning JSON or source, validate, and compile a
  fresh identity.
- `plot_reproduction.json` pins retained historical inputs only. Never use it
  as the numerical source for a future campaign.

For the current `dy` profile require strict selected-Z `pT > 35 GeV` for both
leptons, strict `60 < Z0_mass < 120 GeV`, six observables, and 48 deterministic
categories. Require these compact uniform axes:

```text
Z0_mass: [60, 60.0, 120.0], fold 0
Z0_pt:   [20, 0.0, 100.0],  fold 2
lZ1_pt:  [13, 35.0, 100.0], fold 2
lZ2_pt:  [13, 35.0, 100.0], fold 2
lZ1_eta: [50, -2.5, 2.5],   fold 0
lZ2_eta: [50, -2.5, 2.5],   fold 0
```

Require `selection_config.py` to join each profile concrete-path record to one
year-owned physical path through its aggregate and ordinal. Require exact
DATA/MC TrigMaker path agreement and exact-once coverage: neither the profile
nor Python may repeat physical path strings. Require category order and
uniqueness, and require each flavor child to inherit its parent's luminosity
source. Reference and stream categories use Trigger-OR, families use their
family source, and paths use their concrete-path source.

## Validate luminosity before compiling

With `RUN_STABILITY_LUMI_DIR` unset, require the profile-selected
`lumi/run_stability_luminosity_binding.json` to match before resolving its
immutable audit under `lumi/audits/`. An explicit absolute results path is an
advanced override, not a way to bypass audit or numerical validation.

Require all of the following:

1. active binding schema/kind/status, live path/hash/projection, and source
   path/manifest/provenance/nominal-era-result hashes match;
2. every required audit input/result exists and all result hashes close;
3. the audit manifest hashes its copied `inputs/year_config.json` exactly;
4. copied and live canonical BRIL-input projections match;
5. every live `lumi_fb` equals its exact validated nominal era result;
6. selected runtime `lumi` equals that configured/audited value exactly;
7. run order, source schemas, category routing, and aggregates validate.

The BRIL-input projection covers DATA component/run-tag/stream/baseline-trigger
membership, `data_stream_triggers`, processing era, and physical trigger paths.
It excludes `lumi_fb`, which is a validated result bound separately to
`luminosity_by_analysis_era.csv`. Rebuild the audit after a projected-input
change. For an unrelated live-file change, retain the audit and refresh the
active binding. Never patch a nominal result independently of its audit.

Keep the exact future MC source luminosities from `year_config.json`:

```text
2022      8.076828657919002 fb^-1
2022EE   26.671325997159986 fb^-1
2023     18.062658998219003 fb^-1
2023BPix  9.693130030386998 fb^-1
2024    109.72830897472497  fb^-1
```

These are not trigger-effective values. Effective luminosity is the certified,
dataset-covered positive conjunction of each component's baseline/de-duplication
trigger with the category trigger. A zero source remains zero.

## Audit DATA completeness independently of MC

Before production, reconcile the live sample-specific primary-dataset,
run-tag, logical-stream, trigger-weight, and exact file inventory against:

1. the live leaf;
2. the matching processor sample catalog;
3. the analysis-aligned read-only configuration family;
4. the materialized HWWNano production and step.

Require the reconciled union with no unresolved missing or unexpected
components or files. A storage catalog is comparison evidence, not a
replacement for the processor catalog or an all-parts materialization audit.

For 2022 require exactly the ten-component transition matrix: MuonEG B/C/D,
SingleMuon B/C, Muon C/D, and EGamma B/C/D. There is no Muon B and no
SingleMuon D. Preserve the component-specific Muon-stream trigger rules:
`!Trigger_ElMu && Trigger_sngMu` for SingleMuon and
`!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)` for Muon.

Use the default `make_sample_catalog.py crawl` part0-else-part1 behavior per
exact identity. A part0-only crawl omits valid
`MuonEG_Run2022B-ReReco-v1` and `MuonEG_Run2022F-Prompt-v1` components, both
of which materialize first as part1. Inspect exact files, not only component
names or event totals.

Use `check_storage_paths_from_list.py` for an independent all-parts check.
Require deterministic receipt kind `run_stability_all_parts_storage_audit`,
`complete: true`, and the exact intended inventory/config hashes. Do not accept
the former ZZ_CR receipt kind as the active schema.

For trigger categories require component-trigger conjunction evidence. A
`SingleMuon` contribution to a double-muon category must satisfy
`Trigger_sngMu && Trigger_dblMu`. Do not interpret zero early-2022 exposure as
physical inactivity until complete DATA coverage and the conjunction are
proved. Never infer missing runs from adaptive plot tick labels; inspect the
compiled run rows and luminosity contract.

## Run bounded real-input pilots

Run `inspect_plan.py --year <era>` before discovery. Require one DY region,
48 categories, six active variables, 288 nominal actions,
`nominal_action_estimate: 288`, and `systematic_action_estimate: 0`. Treat it
as a nominal-only static plan, not input-discovery or execution evidence.

Source `start.sh`. Use local XRootD input and local output. Select one exact
sample, `LIMIT_FILES_PER_SAMPLE=1`, and a finite event limit. Run DATA and one
DY MC sample in separate compiled snapshots. For DATA, use one exact configured
stream and run tag; clear both filters before the MC pilot. An event limit
alone does not bound discovery.

Reopen the DATA ROOT output. Require 48 x 6 run-resolved TH2 objects, exact run
labels, y axes identical to ordinary TH1 axes, empty x flows, correct folding,
TH2-to-TH1 integral and uncertainty closure, and exactly one metadata copy.
Require MC-only output to contain ordinary TH1 objects and no DATA auxiliary
hierarchy. Successful pilots do not prove full input completeness or physics
agreement.

## Compile and submit exact production identities

Require explicit submission authorization. Start from current source, never a
retained pickle or job directory. Source the selected batch wrapper after the
framework runtime, then reapply the analysis identity and unset sample/file
pilot filters. Use `lxplus_fnal_env.sh` for LXPLUS shared-checkout execution
with CERN XRootD input and FNAL EOS stage-out; use `lxplus_env.sh` for CERN
stage-out or `fnal_lpc_packaged_env.sh` for packaged FNAL execution. No `zzcr`
wrapper belongs to this leaf.

Require `configuration.py` to derive the early canonical tag only through the
pure profile and year loaders. Later shared execution must be exactly
year -> selection -> category -> samples -> luminosity -> aliases -> cuts ->
variables -> plot -> nominal nuisances -> structure -> contract -> payload.
Reject early execution of a materializer or a clone-era fallback identity.

First compile and expand with `--submit -dR 1`. Record the one new timestamped
pickle and inspect the full JDL and worker expansion. Reopen the pickle and
require its `YEAR`, tag, `JOB_CAMPAIGN`, `PRODUCTION_CAMPAIGN`, source hashes,
input inventory, axes, categories, luminosity sources, active binding, and
immutable audit identity to match the generated tag directory and payload.
Then submit only that exact snapshot with
`-c 0 --submit -dR 0 -config <exact-pickle>`.

Compile the five eras serially because the leaf-global pickle name has
one-second resolution. Never select `latest`, infer identity from a neighboring
era, or combine uncertain compilation and live submission. Use one
collision-resistant job campaign containing one intended tag per era. Record
exact schedd, cluster, expanded job count, input-file count, and destination.
Check the scheduler before retrying so uncertainty cannot create duplicates.

Submission, queueing, completion, stage-out, exact split-set equality, merge,
merged-file reopening, formula audit, visual audit, and promotion are separate
gates. A receipt, empty queue, or existing ROOT file proves only its own layer.

## Reproduce and validate plots

Prefer `reproduce_plots.py` for the retained campaign. Run `validate` first;
plot commands print by default and execute only with `--execute`. This wrapper
hash-checks all pinned pickles and merged ROOT files and always selects
category-aware `--luminosity-source auto`.

Use `plot_run_stability.py` directly only for advanced diagnostics with an
exact pickle, merged ROOT input, explicit output identity, and explicit source
selection. The supported renderer is Python/Matplotlib; ROOT is the scientific
container.

For a run or period, scale each era-normalized MC bin once by
`L_effective / L_MC_source` and its `Sumw2` by the square. DATA ratio bars are
Garwood-only; render MC uncertainty separately. Preserve same-era shared-MC
covariance in numerical outputs. For reduced chi-square use the half-width of
the Garwood interval and the scaled MC variance, no plotted point errors, a
reference at one, the approximate `1 +/- sqrt(2/ndf)` band, and explicit
out-of-range markers. Do not fabricate finite values for zero denominators.

Period stacks must derive exact `DY` membership from compiled `groupPlot`
metadata and group its disjoint complement as `Others`. Apply each compiled
process scale before aggregation, with variance scaled by its square.

Inspect output files, numerical receipts, and original-resolution PNGs. Use
computer vision when requested to check clipping, collisions, whitespace,
legibility, legend semantics, era labels/separators, and out-of-range markers.
Regenerate into a fresh identity after a failed audit; do not overwrite failed
evidence and call it promoted.

## Cancel and clean safely

Cancel only exact recorded clusters on the exact schedd and verify the queue
drains. Reconcile history and durable output before deleting task-owned local
directories. Remote-output deletion is separately destructive and requires
separate explicit scope.

After all workers are terminal, scan every retained tag directory for copied
X.509 proxies. Resolve exact regular-file targets, remove only task-created
copies, and verify that no proxy remains. Never remove the operator's source
proxy. Keep credential cleanup counts separate from scientific-artifact
cleanup. Do not place a credential in a runtime archive, manifest, log,
receipt, plot, or repository history.

Preserve production ledgers and copied luminosity provenance as historical
evidence, including their original paths and legacy identifiers.
