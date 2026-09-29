# RunStability usage

This leaf has one public workflow: nominal DY run stability. The default
production profile resolves the strict 35/35 GeV selected-lepton thresholds,
the strict `60 < m(Z0) < 120 GeV` window, six observables, and 48 categories
from declarative JSON. Do not reproduce that matrix with hand-written shell
selectors.

## Set up the source contract

Work from the writable `mkShapesRDF` checkout:

```bash
source start.sh
export YEAR=2024
export ANALYSIS_PASS=RUN_STABILITY
export RUN_STABILITY_PRODUCTION_PROFILE=dy
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
unset RUN_STABILITY_LUMI_DIR
```

Valid eras are `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`. With
`RUN_STABILITY_LUMI_DIR` unset, compilation validates
`lumi/run_stability_luminosity_binding.json` and resolves its immutable source
audit under `lumi/audits/`. An absolute `.../results` path is an advanced
override; it must still pass audit provenance, BRIL-input projection, exact
nominal-result, runtime-luminosity, run-set, and aggregate checks.

Inspect the nominal-only plan before discovery:

```bash
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/inspect_plan.py \
  --year 2024
```

Require one DY region, 48 categories, six active variables, 288 nominal
actions, `nominal_action_estimate: 288`, and
`systematic_action_estimate: 0`.

## Bounded local pilots

An event limit does not bound input discovery. Select one exact sample and
one file before running a finite event range:

```bash
export LIMIT_FILES_PER_SAMPLE=1
export FILES_PER_JOB=1
export EXECUTION_PROFILE=local_xrootd
export INPUT_ACCESS_MODE=xrootd
export OUTPUT_MODE=local

# DATA: choose an exact configured stream and run tag.
export SAMPLE_FILTER=DATA
export DATA_STREAM_FILTER=MuonEG
export DATA_RUN_FILTER=Run2024C-ReReco-v1
mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/RunStability -l 100

# MC: compile a separate snapshot after removing DATA-only filters.
export SAMPLE_FILTER=DYto2E-2Jets_MLL-50
unset DATA_STREAM_FILTER DATA_RUN_FILTER
mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/RunStability -l 100
```

Inspect the exact timestamped pickle and `analysis_contract.json`; never use
`latest` as a production identity. Reopen the DATA ROOT output and require
48 x 6 run-resolved TH2 objects, exact audited run labels, matching TH1/TH2
observable axes, empty run-axis flows, and one copy of the luminosity metadata.
The MC-only output must contain ordinary one-dimensional histograms and no
DATA run-resolved hierarchy.

## Pinned central NanoAOD producer diagnostic on LPC

`local_producer_diagnostic.py` is an opt-in, local diagnostic for the six-role
2024 paired low-pT input manifest. It applies the live processor `Steps_cfg`
DATA `__l2loose` or DY MC `__l2tight` chain to one manifest role and one
half-open range of original NanoAOD `Events` entries. The final snapshot is
written locally as `events.root`; it does not submit jobs or stage out files.
The output is an Events-only diagnostic tree, not a complete production
HWWNano file. The runner retains all nominal RDataFrame columns plus
`diagnostic_source_entry` and writes `entry_ledger.json.gz` with each input
`(source entry, run, luminosityBlock, event)` key and the surviving source
entries after each step. The `receipt.json` records source and output hashes,
ROOT UUID, event counts, chain, and per-step counts.

Use the frozen manifest whose LFNs have been independently matched to the
historical HWW parents. From the mkShapesRDF checkout:

```bash
cd /path/to/mkShapesRDF
source start.sh
sha256sum /path/to/coffea/docs/diagnostics/paired-2024-lowpt/inputs.json
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/local_producer_diagnostic.py \
  /path/to/coffea/docs/diagnostics/paired-2024-lowpt/inputs.json \
  --manifest-sha256 <exact-sha256> --role muon_c \
  --output-dir /absolute/new/local/diagnostic/muon_c
```

For `dy_ee` or `dy_mumu`, also supply `--normalization-receipt` and
`--normalization-sha256`. The hashed JSON receipt must name the same processor
sample and central dataset and have `schema_version: 1`,
`status: "verified"`, and a nonzero `gen_event_sumw`. Supported methods are:

- `Runs.genEventSumw`, with at least two complete source LFNs, matching
  per-file sums, and the pinned `source_file_inventory_hash`; or
- `retained_hww_baseW`, with `matched_input_lfn`,
  `historical_hww_part0_uri`, `historical_compiled_pickle_sha256`,
  `parent_pair_evidence_sha256`,
  `historical_hww_baseW`, and `cross_section_pb`.

The runner verifies receipt identity, hash, source membership or parent LFN,
catalog cross section, and the `baseW = 1000 * cross_section_pb /
gen_event_sumw` relation. The receipt's scientific verification, including
the historical HWW branch read and full-source denominator provenance, must
be completed independently before use. The runner never derives MC
normalization from the selected file's `Runs` tree. It rejects an existing
output directory, changed manifest SHA or producer-package tree relative to
the manifest's pinned mkShapesRDF revision, mismatched source
ROOT UUID or entry count, and a DATA Golden JSON hash mismatch. A real file
execution and comparison to retained HWW contents are still required before
claiming producer equivalence.

On 2026-09-29, one bounded `muon_c` pass failed before creating an Events
output: the live DATA step requests `Regrouped_*` JES uncertainties under
`Summer24Prompt24_V2_DATA`, while the configured 2025-12-02
`jet_jerc.json.gz` payload (SHA-256
`ff3f656858d24f349438cc67c4bea0ea32f2bd89fb8d8e18b0b1e7667640ab2a`)
has those keys only under the MC tag. An empty JES list allows the nominal
calculator to construct, but that would depart from
the configured chain and was not used for this diagnostic. Two DY MC passes
over the frozen first 80,000 entries did complete: 34,538 ee and 31,989
mumu Events survived. Every output event key occurred in its independently
matched historical HWW part0. On the first 20 matched keys per role,
`baseW` and `CleanJet_pt` agreed in all 20 within `rtol=atol=1e-6`, while
`Lepton_pt` agreed in none; `mll` agreed in 8 ee cases (including sentinel
values) and 0 mumu cases. The live MC lepton smearing source draws random
values, which plausibly contributes to the difference; historical producer
version and payload differences remain unexcluded. The historical HWW
producer Git revision is not recorded by this diagnostic. Preserve the
historical HWW product as the authority for the original campaign's lepton
values.

## Validate the leaf

```bash
python -m pytest -q \
  PlotsConfigurationsRun3/ZH_4lMET/RunStability/tests
python -m black --check --config pyproject.toml \
  PlotsConfigurationsRun3/ZH_4lMET/RunStability
```

The bounded pilots and tests establish software behavior for their inputs.
They do not establish complete DATA coverage, scheduler success, luminosity
validity, or physics agreement for a full campaign.

## Prepare a future batch campaign

Future campaigns are source-first. Change the owning JSON, validate the
resolved contract, and compile a fresh exact snapshot. Do not build a new
campaign from retained pickles or generated job directories.

Before compilation, independently reconcile the exact DATA components and
files with the processor sample catalog, the analysis-aligned read-only
configuration family, and live materialization. For 2022 the required
transition matrix is:

```text
MuonEG:     B, C, D
SingleMuon: B, C
Muon:          C, D
EGamma:     B, C, D
```

There is no `Muon` B component and no `SingleMuon` D component. Catalog
discovery must preserve the part0-else-part1 rule per exact identity; a
part0-only crawl drops valid `MuonEG_Run2022B-ReReco-v1` and
`MuonEG_Run2022F-Prompt-v1` inputs.

For an independent all-parts inventory check, use
`check_storage_paths_from_list.py` and retain its deterministic optional JSON
receipt. Require receipt kind `run_stability_all_parts_storage_audit` and
`complete: true`; an older ZZ_CR receipt kind is not the active contract.

After a valid proxy is already initialized on LXPLUS, source the shared-checkout
CERN-input/FNAL-stage-out wrapper, then reapply the analysis identity because
wrappers own site and I/O settings:

```bash
source PlotsConfigurationsRun3/ZH_4lMET/RunStability/lxplus_fnal_env.sh
export YEAR=2024
export ANALYSIS_PASS=RUN_STABILITY
export RUN_STABILITY_PRODUCTION_PROFILE=dy
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export FILES_PER_JOB=10
export JOB_CAMPAIGN=DYRS_PT35_M60TO120_OBS6_<unique-id>
export PRODUCTION_CAMPAIGN=DYRS_2024_PT35_M60TO120_OBS6_<unique-id>
unset SAMPLE_FILTER LIMIT_FILES_PER_SAMPLE DATA_STREAM_FILTER DATA_RUN_FILTER
unset RUN_STABILITY_LUMI_DIR

# Compile and expand only; no scheduler submission.
mkShapesRDF -c 1 --submit -dR 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/RunStability \
  -l -1 -q workday

# After reopening and auditing config_<exact>.pkl, submit that snapshot only.
mkShapesRDF -c 0 --submit -dR 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/RunStability \
  -config PlotsConfigurationsRun3/ZH_4lMET/RunStability/configs/config_<exact>.pkl \
  -l -1 -q workday
```

Live submission is a separate authorized action. Compile the five eras
serially because the leaf-global pickle name has one-second resolution.
Before each submission, deserialize the exact pickle and require `YEAR`, tag,
`JOB_CAMPAIGN`, `PRODUCTION_CAMPAIGN`, input inventory, axes, luminosity
sources, and hashes to agree one-to-one with the generated tag directory and
JDL. Record the exact schedd and cluster. Check live state before retrying so
uncertainty cannot create a duplicate submission.

Completion, stage-out, exact split-set equality, merge, ROOT reopening,
formula audit, visual audit, promotion, and cleanup are separate gates. Remove
jobs only by exact schedd and cluster, verify that the queue drains, and treat
remote deletion as separately authorized. Copied X.509 proxies are temporary
credentials: exclude them from runtime archives and remove only exact
task-created copies after all workers are terminal.

## Reproduce the retained plots

`plot_reproduction.json` pins the promoted historical campaign's five exact
pickles and merged ROOT files by SHA-256. It is a reproduction input, not a
future production source.

```bash
cd PlotsConfigurationsRun3/ZH_4lMET/RunStability
python reproduce_plots.py validate

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

Plot commands print without running by default. Review the resolved command,
then add `--execute`. `plot_run_stability.py` is the lower-level interface for
advanced diagnostics; provide it an exact compiled pickle, exact merged ROOT
input, explicit output identity, and `--luminosity-source auto`.

See [README.md](README.md) for the public contract,
[ARCHITECTURE.md](ARCHITECTURE.md) for ownership, and
[LUMINOSITY_PROPAGATION.md](LUMINOSITY_PROPAGATION.md) for the formulas.
