# ZZ_CR compact Run-3 workflow

This configuration produces the inclusive DY validation region, physical ZZ
control region, and ZH four-lepton signal-reference region in one nominal job
graph. It supports `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`.

The normal contract is:

```text
ANALYSIS_PASS=ALL
CATEGORY_PROFILE=minimal
HISTOGRAM_PROFILE=analysis
ENABLE_SYSTEMATICS=0
HISTOGRAMS=1
```

This resolves three categories (`DY_ALL`, `ZZCR_ALL`, and `SR_ALL`), 53 active
variables, and 125 category-variable actions. The persistent registry keeps
all supported definitions and binning even when variables are inactive.
ZZ_CR is histogram-only.

## Plan and profiles

Inspect the graph without discovering input files:

```bash
cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR
python inspect_plan.py --year 2024 \
  --analysis-pass ALL \
  --category-profile minimal \
  --histogram-profile analysis
```

Category profiles are `minimal`, `flavor`, `stream`, `trigger`, and `debug`.
`flavor` adds `DY_ZEE`, `DY_ZMM`, `ZZCR_4E`, `ZZCR_4MU`, `ZZCR_2E2MU`,
`SR_XSF`, and `SR_XDF`. Stream and trigger profiles add bounded diagnostic
splits; they do not create stream-by-flavor Cartesian products.

Histogram profiles are `analysis`, `trigger`, `objects`, `weights`, `quality`,
and `all`. Exact overrides select existing registry entries:

```bash
export VARIABLE_INCLUDE=Z0_mass,X_mass,PuppiMET_pt
export VARIABLE_EXCLUDE=PuppiMET_pt
```

An include never creates or changes a definition. Re-enabling a variable later
restores the same expression, fold, and binning. `MAX_CATEGORIES` and
`MAX_HISTOGRAM_ACTIONS` are fail-closed safety budgets;
`ALLOW_LARGE_PLAN=1` is the explicit debug override.

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
export CATEGORY_PROFILE=minimal
export HISTOGRAM_PROFILE=analysis
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export EXECUTION_PROFILE=local_stagein
export INPUT_ACCESS_MODE=stage-in
export XRD_READ_ENDPOINT=root://eoscms.cern.ch
export XRD_DISCOVERY_ENDPOINT=root://eoscms.cern.ch
export OUTPUT_MODE=local
export SAMPLE_FILTER=ZZ
export LIMIT_FILES_PER_SAMPLE=1
export FILES_PER_JOB=1

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR -l 100
```

This copies the CERN input with `xrdcp` into task-owned scratch, reads the
local copy, and removes it on success. Do not use a packaged production profile
with `-b 0`.

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
export CATEGORY_PROFILE=minimal
export HISTOGRAM_PROFILE=analysis
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export FILES_PER_JOB=1
export PRODUCTION_CAMPAIGN=ZH4lMET_COMPACT_PILOT
```

The wrapper selects `packaged_fnal_stagein_eos_production`: CERN XRootD
discovery/read, `xrdcp` stage-in to worker scratch, and stage-out only to FNAL
EOS. It transfers the checkout package and a worker-local CMS proxy. The FNAL
efficiency-map URL remains remote and is authenticated with that proxy.

Create a bounded dry-run first:

```bash
export SAMPLE_FILTER=ZZ
export LIMIT_FILES_PER_SAMPLE=1

mkShapesRDF -c 1 -o 0 -b 1 -dR 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR -l 100
```

Inspect `jobs/<tag>/condor/<tag>/submit.jdl`, `run.sh`, the per-job
`script.py`, and `mkshapesrdf_runtime.tgz`. A worker expression must not refer
to `/uscms_data` or `/afs`; absolute paths in `transfer_input_files` are
submit-side sources and are expected.

For a pilot, submit the inspected JDL with the empirically validated memory
request (currently 2048 MB):

```bash
cd jobs/<tag>/condor/<tag>
condor_submit -append 'request_memory = 2048MB' submit.jdl
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

Use the exact compiled configuration, not a moving `latest` alias:

```bash
mkShapesRDF -c 0 --check -b 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -configs jobs/<tag>/configs \
  -config jobs/<tag>/configs/config_<exact>.pkl

mkShapesRDF -c 0 --histoadd -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -configs jobs/<tag>/configs \
  -config jobs/<tag>/configs/config_<exact>.pkl
```

Remote split outputs live below:

```text
root://cmseos.fnal.gov//store/user/<user>/mkShapesRDF_rootfiles/
  <campaign>/<tag>/
```

A minimal-analysis MC split contains 25 variable directories under `DY_ALL`
and 50 each under `ZZCR_ALL` and `SR_ALL`. For example, `DY_ALL/X_mass` must
not exist, while `ZZCR_ALL/X_mass` and `SR_ALL/X_mass` must exist.

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
