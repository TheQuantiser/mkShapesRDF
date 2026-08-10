# Run 3 ZZ control-region configuration

`ZZ_CR` is a histogram-only mkShapesRDF configuration for the Run 3 Z/DY
validation region, physical ZZ control region, and ZH four-lepton
signal-reference region. It supports `2022`, `2022EE`, `2023`, `2023BPix`,
and `2024` NanoAOD productions.

See [`TRIGGER_SCALE_FACTORS.md`](TRIGGER_SCALE_FACTORS.md) for the exact
selected-lepton trigger-efficiency calculation and weight-placement contract.

## Essentials

- `Z0` is the opposite-sign same-flavor pair closest to the Z mass, built from
  a pair whose two leptons each exceed 10 GeV.
- `X` is the non-overlapping opposite-sign pair with the highest leading
  lepton pT, breaking ties with the subleading lepton pT.
- ZZCR requires same-flavor X, `75 < X_mass < 105 GeV`, and
  `PuppiMET_pt < 35 GeV`.
- SR uses the AN2019/238 v9 XSF/XDF selections and the same 15 GeV Z window.
- ZZCR/SR require `minSelectedPairMass > 12 GeV` over all six selected-lepton
  pairs; DY deliberately does not.
- `DY_ENRICHED` applies the SR Z window and mirrors every ordinary DY
  subcategory.
- DY and all Enriched DY mirrors require the two selected Z0 leptons, sorted
  by pT, to exceed 25 and 15 GeV. This DY-registry requirement is not applied
  to FOURL, ZZCR, or SR.
- The nominal MC weight combines luminosity normalization, MET filters,
  pileup, selected-lepton, trigger, and region-appropriate b-veto factors.
  DY evaluates `TriggerSF_Z` from exactly the two selected `Z0_idx` leptons;
  four-lepton regions evaluate `TriggerSF_ZX` from the selected Z0+X quartet.
- Official BTV correctionlib JSON files are read from CVMFS. Fixed-WP
  efficiency histograms are read directly from the configured FNAL EOS XRootD
  ROOT files.
- Underflow and overflow are folded into the first and last visible bins for
  the primary Z/X mass and pT observables.
- Unified `ANALYSIS_PASS=ALL` production is nominal-only; enabling systematics
  with this pass fails closed.

## Standard modes

| Use | Category profile | Sample profile | Categories | Actions |
| --- | --- | --- | ---: | ---: |
| Quick commissioning | `standard` | `commissioning` | 47 | 1,043 |
| Full presentation | `detailed` | `presentation` | 53 | 1,133 |

The commissioning sample profile selects DATA plus the configured DY and ZZ
groups. The presentation profile selects the complete configured prompt MC
model, target ZH/ggZH signal, and DATA. It does not include a nonprompt/fake
estimate. `SAMPLE_FILTER` is the exact override for a targeted run.

The normal environment contract is:

```bash
export YEAR=2024
export ANALYSIS_PASS=ALL
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=commissioning
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
```

For full presentation production, change to:

```bash
export CATEGORY_PROFILE=detailed
export SAMPLE_PROFILE=presentation
export FILES_PER_JOB=10
unset SAMPLE_FILTER LIMIT_FILES_PER_SAMPLE DATA_STREAM_FILTER
```

For a complete production submission, source `start.sh`, source exactly one
site wrapper from the table below, and only then export the analysis settings
above plus an era-specific `PRODUCTION_CAMPAIGN`. Compile and submit the
current configuration explicitly:

```bash
mkShapesRDF -c 1 --submit \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -l -1 -q workday
```

`-c 1` is required for a fresh production compile. Calling `--submit` without
it may reuse the selected or latest pickle, including stale profiles, filters,
event limits, payload paths, endpoints, or output settings.

## Inspect before running

From the repository root:

```bash
source start.sh
cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR

python inspect_plan.py \
  --year 2024 \
  --analysis-pass ALL \
  --category-profile standard \
  --histogram-profile analysis \
  --sample-profile commissioning
```

The plan resolves categories, variables, actions, samples, and expected plots
without discovering input files.

## Execution presets

Source one site wrapper before setting campaign-specific analysis variables:

| Wrapper | Submission site | Input | Output | Packaging |
| --- | --- | --- | --- | --- |
| `zzcr_lxplus_env.sh` | CERN | CERN XRootD | CERN CMS Store | no |
| `zzcr_lxplus_fnal_env.sh` | CERN | CERN XRootD | FNAL CMS Store | no |
| `fnal_lpc_packaged_env.sh` | FNAL | CERN XRootD | FNAL CMS Store | yes |

The wrappers force their full site/I/O contract so stale variables do not
leak from a previously sourced setup. Set identity inputs such as `FNAL_USER`
or `CERN_USER` before sourcing; set year, profiles, filters, campaign name,
and other deliberate overrides afterward. Direct XRootD reads are the
default. Whole-file stage-in remains an explicit fallback.

For a bounded local XRootD validation:

```bash
source start.sh

export YEAR=2024
export ANALYSIS_PASS=ALL
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=commissioning
export SAMPLE_FILTER=ZZ
export LIMIT_FILES_PER_SAMPLE=1
export FILES_PER_JOB=1
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export EXECUTION_PROFILE=local_xrootd
export INPUT_ACCESS_MODE=xrootd
export OUTPUT_MODE=local

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR -l 100
```

For Condor, first compile a bounded dry run with `-b 1 -dR 1` and inspect the
generated JDL and worker script. For full production, run the exact
`-c 1 --submit ... -l -1` command above; never reuse an event-limited pilot
JDL or submit a moving/latest pickle implicitly.

## Merge contract

Use the exact timestamped pickle created for the submitted jobs:

```bash
mkShapesRDF -c 0 --check -b 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -config PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/configs/config_<exact>.pkl

mkShapesRDF -c 0 --histoadd -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -config PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/configs/config_<exact>.pkl
```

The merge reconstructs the split-file plan and reads outputs directly through
XRootD. A compiled pickle retains absolute checkout and scratch paths, so run
management and merge from the checkout/site that created it whenever possible.

Every compile also writes a self-digested `analysis_contract.json` containing
the exact categories, cuts, weights, variables, binning, samples, input hashes,
payloads, profiles, endpoints, output locations, and git state.

## Documentation

- [`USAGE.MD`](USAGE.MD): complete setup, pilot, submission, status, merge,
  and plotting commands.
- [`CONFIGURATION.md`](CONFIGURATION.md): current physics, sample, category,
  histogram, weight, payload, and reproducibility contract.
- [`FILE_GUIDE.md`](FILE_GUIDE.md): file-by-file architecture and guidance on
  where and how to customize the configuration.
- [`skills/submit-zzcr-production/SKILL.md`](skills/submit-zzcr-production/SKILL.md):
  reusable safeguards for fresh site-aware Condor production submissions.
- [`development/CATEGORY_DESIGN.md`](development/CATEGORY_DESIGN.md): exact
  category inventory and algebra.
- [`development/SELECTION_SOURCE_NOTE.md`](development/SELECTION_SOURCE_NOTE.md):
  source-to-code traceability for the physical selections.

## Validation

After source changes, run:

```bash
source start.sh
pytest -q PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/tests
```

Follow selection, alias, payload, or C++ changes with bounded DATA and MC jobs;
Python plan inspection alone cannot validate ROOT expressions or NanoAOD
branch availability. Do not commit generated pickles, job controls, ROOT
files, plots, caches, or local receipts.
