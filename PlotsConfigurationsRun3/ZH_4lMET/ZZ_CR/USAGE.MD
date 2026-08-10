# ZZ_CR compact Run-3 workflow

This configuration produces the inclusive DY validation region, physical ZZ
control region, and ZH four-lepton signal-reference region in one nominal job
graph. It supports `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`.

The normal commissioning contract is:

```text
ANALYSIS_PASS=ALL
CATEGORY_PROFILE=standard
HISTOGRAM_PROFILE=analysis
SAMPLE_PROFILE=commissioning
ENABLE_SYSTEMATICS=0
HISTOGRAMS=1
```

This resolves 36 bounded projections, 53 active registry variables, and 864
category-variable actions. `minimal` remains the fastest four-category,
150-action basic production. The persistent registry keeps all supported
definitions and binning even when variables are inactive. ZZ_CR is
histogram-only.

For a full plotting campaign, change only the sample scope to
`SAMPLE_PROFILE=presentation` and ensure `SAMPLE_FILTER`,
`LIMIT_FILES_PER_SAMPLE`, and `DATA_STREAM_FILTER` are unset. The category and
histogram graph remains the same 36-category, 864-action graph.

## Plan and profiles

Inspect the graph without discovering input files:

```bash
cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR
python inspect_plan.py --year 2024 \
  --analysis-pass ALL \
  --category-profile standard \
  --histogram-profile analysis \
  --sample-profile commissioning
```

Add `--write-profile-comparison` to regenerate
`development/category_profile_comparison.json`. The plan reports category and
action breakdowns by region and `view_type`, variables per category, and the
expected linear/log plot counts. It also records the selected sample profile,
plot groups, logical outputs, and whether `SAMPLE_FILTER` replaced the profile.

Sample profiles are:

- `commissioning` (default): quick development with `DATA` and the live DY
  and ZZ logical outputs only;
- `presentation`: every resolved prompt MC output assigned by the current
  `plot_groups`, including the target ZH/ggZH H→WW signal and other configured
  Higgs contamination, plus `DATA`.

The presentation profile includes DY, ZZ, WZ, Vg, VgS, WW, ggWW, top,
ttV/tZ, VVV, and the configured Higgs groups. It does not include a
nonprompt/fake background estimate. `SAMPLE_FILTER` remains the stronger exact
override for targeted runs:

```bash
export SAMPLE_PROFILE=presentation
export SAMPLE_FILTER=ZZ,DATA
```

Tags and `analysis_contract.json` record `SAMPLE_PROFILE`; the contract also
records its groups, complete profile inventory, actual active samples, and
whether the profile or `SAMPLE_FILTER` selected them.

Category profiles are:

- `minimal`: the three region inclusives plus `DY_ENRICHED` (4/150);
- `standard`: recommended DATA/MC commissioning projections (36/864);
- `flavor`: inclusive projections plus selected-pair flavor/topology partitions
  (16/498);
- `stream`: inclusive projections plus exclusive stream-priority marginals
  (13/351);
- `trigger`: inclusive projections plus exclusive `triggerFamilyPriority` views
  (19/485);
- `detailed`: standard plus six SR stream-by-X-flavor views (42/954);
- `debug`: the curated detailed/trigger union (57/1,289), requiring
  `ALLOW_LARGE_PLAN=1`.

`DY_ENRICHED` applies `abs(Z0_mass - 91.1876) < 15`, exactly the physical
ZZCR/SR Z window, and deliberately uses the same inclusive histogram tier as
`DY_ALL`. The standard profile also contains the full DY stream-by-Z-flavor
closure matrix, five curated ZZCR stream-by-topology intersections, and no SR
stream cross. It never generates an automatic Cartesian product. Each category
carries first-class view, partition, exclusivity, overlap, and
diagnostic-purpose metadata into `analysis_contract.json`.

## AN2019/238 v9 selection

The authoritative signal selection is Table 37 on PDF page 120 (document page
118) of `AN2019_238_v9.pdf`. XSF requires `X_isSF`, `10 < X_mass < 65 GeV`,
`PuppiMET_pt > 35 GeV`, and `m4l > 140 GeV`. XDF requires `X_isDF`,
`10 < X_mass < 70 GeV`, and `PuppiMET_pt > 20 GeV`, with no m4l threshold.
Both use ordered lepton pT thresholds `25, 15, 10, 10 GeV`, the 10 GeV
fifth-lepton veto, the 15 GeV Z window, zero selected-lepton charge, and the
loose b veto above 20 GeV.

Section 7.4 and Table 39 on PDF page 132 (document page 130) define ZZCR with
the same-flavor second-Z candidate, `75 < X_mass < 105 GeV`, and
`PuppiMET_pt < 35 GeV`. The physical ZZCR/SR common selection additionally
requires `minSelectedPairMass > 12 GeV` over all six pairs formed from exactly
the selected Z0+X leptons; DY does not use this requirement. The precise source
and implementation record is `development/SELECTION_SOURCE_NOTE.md`. The XSF
edge remains 65 GeV because that is the value in the authoritative AN; no
claim is made that later public material uses an identical edge.

Histogram profiles are `analysis`, `trigger`, `objects`, `weights`, `quality`,
and `all`. Exact overrides select existing registry entries:

```bash
export VARIABLE_INCLUDE=Z0_mass,X_mass,PuppiMET_pt
export VARIABLE_EXCLUDE=PuppiMET_pt
```

An include never creates or changes a definition. Re-enabling a variable later
restores the same expression, fold, and binning. `MAX_CATEGORIES` and
`MAX_HISTOGRAM_ACTIONS` are fail-closed safety budgets;
`ALLOW_LARGE_PLAN=1` is the explicit debug override. Normal category/action
budgets are profile-aware: standard fails above 40 categories or 1,000
actions, and detailed fails above 50 categories or 1,200 actions.

Run the selection-only occupancy tool on a bounded staged input with:

```bash
python inspect_category_occupancy.py \
  --year 2024 --kind MC --label 2024_ZZ \
  --events 10000 --input root://eoscms.cern.ch//store/.../nanoLatino_ZZ__part0.root \
  --output occupancy_2024_ZZ.json
```

It dependency-slices the normal aliases and books only `Filter/Count` actions.
The combined five-era evidence and keep/omit decisions are in
`development/category_occupancy.json` and `development/CATEGORY_DESIGN.md`.

## Weight and b-tag contract

The common MC weight is:

```text
lumi * XSWeight * METFilter_Common * puWeight * TriggerSF_event
```

The local runner independently multiplies that weight on each category branch:

```text
DY_*:          SelectedLeptonSF_Z
ZZCR_* / SR_*: SelectedLeptonSF_ZX * BTagVetoSF
DATA:          METFilter_DATA and stream trigger de-duplication; no MC SF
```

Categories may overlap; their branch-local factors do not contaminate each
other. `DATA_STREAM_FILTER=MuonEG`, `Muon`, or `EGamma` restricts a targeted
DATA pilot while the logical output process remains `DATA`.

Fixed-WP b tagging uses two authoritative inputs:

- official BTV working points and flavor/systematic scale factors from the
  full absolute CVMFS `btagging.json.gz` path in `year_config.json`;
- process-dependent MC efficiencies (`bjet_eff`, `cjet_eff`, `ljet_eff`) from
  the full `root://cmseos.fnal.gov//store/user/mwadud/ZH4lMET/btag/...` URL in
  `year_config.json`.

The correctionlib payload does not contain those three efficiency histograms,
so neither input substitutes for the other. Missing payloads, corrections,
working-point mismatches, or ROOT histograms are fatal.

## FNAL local development

From the repository root:

```bash
source start.sh

export YEAR=2024
export ANALYSIS_PASS=ALL
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=commissioning
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export EXECUTION_PROFILE=local_xrootd
export INPUT_ACCESS_MODE=xrootd
export XRD_READ_ENDPOINT=root://eoscms.cern.ch
export XRD_DISCOVERY_ENDPOINT=root://eoscms.cern.ch
export OUTPUT_MODE=local
export SAMPLE_FILTER=ZZ
export LIMIT_FILES_PER_SAMPLE=1
export FILES_PER_JOB=1

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR -l 100
```

This streams the bounded CERN input directly through XRootD and writes only
the small result locally. It is the default local validation mode. Do not use
a packaged production profile with `-b 0`.

Whole-file stage-in remains available for an explicit transfer diagnostic:

```bash
export EXECUTION_PROFILE=local_stagein
export INPUT_ACCESS_MODE=stage-in
```

That opt-in mode copies the input into task-owned scratch and removes it on
success; it is not the ordinary validation path.

## CERN shared-checkout Condor

The historical CERN wrapper name is available for jobs that read and write
through CERN CMS Store:

```bash
source start.sh
source PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/zzcr_lxplus_env.sh

export YEAR=2024
export ANALYSIS_PASS=ALL
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=commissioning
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export FILES_PER_JOB=1
export PRODUCTION_CAMPAIGN=ZH4lMET_CERN_PRODUCTION
```

This selects `shared_xrootd_eos_production`: CERN Condor workers use the
shared checkout without a runtime package, read directly through
`root://eoscms.cern.ch`, and write to `root://eoscms.cern.ch` beneath
`/store/user/${EOS_USER}/mkShapesRDF_rootfiles`.

To submit on CERN Condor but write the result to FNAL CMS Store, select the
FNAL-output wrapper instead:

```bash
source start.sh

# Set this before the wrapper only when the FNAL and CERN usernames differ.
export FNAL_USER=<fnal-username>
source PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/zzcr_lxplus_fnal_env.sh

export YEAR=2024
export ANALYSIS_PASS=ALL
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export FILES_PER_JOB=1
export PRODUCTION_CAMPAIGN=ZH4lMET_CERN_TO_FNAL_PRODUCTION
```

This selects `shared_xrootd_fnal_eos_production`. It retains the CERN
shared-checkout, non-packaged execution contract and direct CERN XRootD input,
but changes stage-out to `root://cmseos.fnal.gov` beneath the FNAL
`/store/user/${EOS_USER}` namespace.

The site wrappers are reset scripts, not default-value helpers. Sourcing one
unconditionally replaces `EXECUTION_PROFILE`, input and output modes, runtime
packaging, include-base, proxy, endpoints, site, `EOS_USER`, and the default
campaign. Export `FNAL_USER` or `CERN_USER` before sourcing when it is an
identity input. Apply analysis settings and deliberate site/profile overrides
after sourcing. Re-sourcing a wrapper resets those overrides.

## FNAL packaged Condor

Check the proxy without initializing one interactively:

```bash
voms-proxy-info -identity -path -timeleft
```

Set the normal production environment:

```bash
source start.sh
source PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/fnal_lpc_packaged_env.sh

export YEAR=2024
export ANALYSIS_PASS=ALL
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=commissioning
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export FILES_PER_JOB=1
export PRODUCTION_CAMPAIGN=ZH4lMET_COMPACT_PILOT
```

The wrapper now selects `packaged_fnal_xrootd_eos_production`: workers read
CERN inputs directly through `root://eoscms.cern.ch` and stage output only to
FNAL EOS through `root://cmseos.fnal.gov`. It transfers the checkout package
and a worker-local CMS proxy. The FNAL efficiency-map URL also remains remote
and is authenticated with that proxy. Direct reads avoid whole-file scratch
copies and the partial-file retry failure mode seen in the first full campaign.
The wrapper forcibly resets its complete FNAL site contract every time it is
sourced, so stale values from another site cannot leak into the submission.

Whole-file stage-in remains available when deliberately wanted:

```bash
source PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/fnal_lpc_packaged_env.sh
export EXECUTION_PROFILE=packaged_fnal_stagein_eos_production
export INPUT_ACCESS_MODE=stage-in
```

Set deliberate overrides after sourcing the wrapper. The stage-in profile
copies each CERN file with `xrdcp` into task-owned worker scratch, while the
direct profile lets ROOT/XRootD perform streamed range reads. Both profiles
keep packaged workers and FNAL EOS stage-out. Re-sourcing the FNAL wrapper
returns the environment to direct-read packaged production.

For the full all-sample 2024 plotting campaign, use:

```bash
export SAMPLE_PROFILE=presentation
export FILES_PER_JOB=10
export PRODUCTION_CAMPAIGN=ZH4lMET_2024_PRESENTATION
unset SAMPLE_FILTER LIMIT_FILES_PER_SAMPLE DATA_STREAM_FILTER
```

`presentation` means every logical output resolved from the 2024
`year_config.json` and live plot groups—currently 54 MC outputs plus DATA.
It does not add a nonprompt/fake estimate.

Create a bounded dry-run first:

```bash
export SAMPLE_FILTER=ZZ
export LIMIT_FILES_PER_SAMPLE=1

mkShapesRDF -c 1 -o 0 -b 1 -dR 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR -l 100
```

After the dry-run command returns, inspect
`jobs/<tag>/condor/<tag>/submit.jdl`, `run.sh`, the per-job
`script.py`, and `mkshapesrdf_runtime.tgz`. A worker expression must not refer
to `/uscms_data` or `/afs`; absolute paths in `transfer_input_files` are
submit-side sources and are expected.

For a pilot, submit the inspected JDL with the empirically validated resource
requests (currently 2048 MB memory and 8 GB disk):

```bash
cd jobs/<tag>/condor/<tag>
condor_submit -terse \
  -append 'request_memory = 2048MB' \
  -append 'request_disk = 8GB' \
  submit.jdl | tee submit.receipt.txt
```

For an ordinary submission through the application, use `--submit` after the
same dry-run review. Keep `FILES_PER_JOB=1` for commissioning; tune it only
from completed pilot timing, memory, input-size, and output-size evidence.

## Status, merge, and output checks

Monitor a submitted cluster and inspect resource use:

```bash
condor_q <cluster-id>
condor_history -name <schedd> <cluster-id> \
  -af ClusterId ProcId ExitCode RemoteWallClockTime MemoryUsage ResidentSetSize
```

Use the exact timestamped pickle written by the compile, not a moving `latest`
alias. The pickle is under the configuration's `configs/` directory; the
campaign-local `analysis_contract.json` records the immutable runtime state:

```bash
mkShapesRDF -c 0 --check -b 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -config PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/configs/config_<exact>.pkl

mkShapesRDF -c 0 --histoadd -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -config PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/configs/config_<exact>.pkl
```

Remote split outputs live below:

```text
root://cmseos.fnal.gov//store/user/<user>/mkShapesRDF_rootfiles/
  <campaign>/<tag>/
```

A standard-analysis split contains 25 variable directories under `DY_ALL`, 50
under each four-lepton inclusive, 19/31 under flavor views, 17/25 under stream
views, and 15 under curated intersections. For example,
`DY_STREAM_MUON_ZEE/X_mass` must not exist, while
`ZZCR_STREAM_EGAMMA_4E/X_mass` must exist. Minimal outputs retain their
original 25/50/50 directory contract.

## Exact analysis contract

Every compile writes the same generated `analysis_contract.json` beside the
durable job controls and in `configs/`. It is derived from the executable
runtime dictionaries and records the full preselection, mechanically resolved
category cuts, base/category/full weights, active samples and files, exact
variable expressions/binning/folds/applicability, nuisances, overlap model,
site endpoints, profiles, payload hashes, git state, and its own SHA-256.

Inspect it with:

```bash
python -m json.tool jobs/<tag>/analysis_contract.json | less

python - <<'PY'
import json
c = json.load(open('jobs/<tag>/analysis_contract.json'))
for name, item in c['categories'].items():
    print(name)
    print(' cut   =', item['full_cut_expression'])
    print(' weight=', item['full_nominal_mc_weight'])
    print(' vars  =', len(item['active_variables']))
PY
```

The focused tests independently compare the contract with executable cuts,
runner factors, and variable definitions:

```bash
source start.sh
pytest -q PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/tests
```

## Systematics limitation

Sparse booking preserves ROOT variations and the sparse conversion/save/merge
paths are regression-tested. Unified `ANALYSIS_PASS=ALL` plus
`ENABLE_SYSTEMATICS=1` is deliberately rejected: ROOT cannot redefine the
already-varied `weight` column for different category factors. Use the compact
nominal workflow now; focused systematic campaigns remain available only after
their exact category-weight interaction is separately validated.
