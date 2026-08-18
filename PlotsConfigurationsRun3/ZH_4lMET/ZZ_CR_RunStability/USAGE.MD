# DY run-stability usage

This leaf supports bounded local validation and full packaged FNAL Condor
production of the `RUN_STABILITY` pass. Workers read CERN inputs through
XRootD and stage outputs to FNAL EOS. The ordinary one-dimensional hierarchy
can be plotted with `mkPlot` after merging. `plot_run_stability.py` separately
provides validated, luminosity-scaled, on-demand per-run DY plots and a
multi-era Data/MC ratio-vs-run product; it does not pre-render all runs.

## Runtime and fixed profile

Work from the writable `mkShapesRDF` checkout and source the framework
runtime. Use the local XRootD execution profile; do not source one of the
batch/remote-output wrappers for these pilots.

```bash
source start.sh

export ANALYSIS_PASS=RUN_STABILITY
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export LIMIT_FILES_PER_SAMPLE=1
export FILES_PER_JOB=1
export EXECUTION_PROFILE=local_xrootd
export INPUT_ACCESS_MODE=xrootd
export OUTPUT_MODE=local
```

`RUN_STABILITY` rejects incompatible category, histogram, sample, or
systematic settings. `RUN_STABILITY_LUMI_DIR` may point at another validated
copy of `lumi/results`; otherwise the configuration uses the explicit
workspace-relative fallback documented in `README.md`.

## Select the target matrix and compile an era

This run-stability pass is DY-only. Use either `all_dy` or exact
comma-separated DY names:

```bash
export RUN_STABILITY_REGION=DY
export RUN_STABILITY_OBSERVABLES=all_dy
export RUN_STABILITY_CATEGORIES=all_dy
```

Choose one of `2022`, `2022EE`, `2023`, `2023BPix`, or `2024`, clear all pilot
filters, and compile a fresh configuration:

```bash
export YEAR=2024
unset SAMPLE_FILTER DATA_STREAM_FILTER DATA_RUN_FILTER

mkShapesRDF -c 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability
```

Compilation performs real input discovery but returns only the first file per
physical source because `LIMIT_FILES_PER_SAMPLE=1`. Inspect the exact
timestamped pickle and its `analysis_contract.json`; do not rely on an
ambiguous `latest` configuration for reproducibility.

The `run_stability` contract must contain the selected era and region, exact
selectors, ordered run map, resolved category/observable matrix and one path
per pair, all 14 luminosity definitions and category mappings, all consumed paths and hashes,
validation/provenance references, the exact configuration luminosity used for
MC, and the DATA split-zero metadata policy.

## One-file DATA pilot

Use an exact stream and run tag present in `year_config.json`. These filters
make the compiled DATA inventory contain one physical file; unknown values
fail during compilation.

```bash
export YEAR=2024
export SAMPLE_FILTER=DATA
export DATA_STREAM_FILTER=MuonEG
export DATA_RUN_FILTER=Run2024C-ReReco-v1

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability \
  -l 100
```

With `all_dy`, the output must contain ordinary DATA TH1 objects plus exactly
1,200 DATA TH2 objects under `run_stability/`. An exact subset must contain its
category/observable product. The output must also contain exactly one copy of the
28 per-run luminosity TH1D objects and the one-bin `mc_source_lumi_fb`
object. Reopen the ROOT file and check classes, axes, exact run labels, y-axis
edges, `Sumw2`, empty x flows, y-only folding, and TH2-to-TH1 integral and
uncertainty closure.

## One-file DY MC pilot

Clear the DATA filters before compiling the MC-only configuration:

```bash
export SAMPLE_FILTER=DYto2E-2Jets_MLL-50
unset DATA_STREAM_FILTER DATA_RUN_FILTER

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability \
  -l 100
```

The output must contain ordinary DY MC TH1 objects and no auxiliary TH2 or
run-stability metadata objects. The MC reference remains era-inclusive and
one-dimensional.

## Tests

```bash
source start.sh
python -m pytest -q \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/tests
python -m pytest -q \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/tests
```

The copied suite includes fail-closed luminosity cases, unknown-run rejection,
nonzero weighted TH1/TH2 closure, core variable-remap coverage, the unchanged
`hadd2` merge behavior, metadata single-writer behavior, MC role isolation,
and a check that the configured plotting namespace enumerates only ordinary
one-dimensional cuts and variables.

Successful bounded pilots establish software behavior for the inspected
inputs. They do not establish full-production completeness, per-run
statistical power, physics-level Data/MC agreement, nonprompt modeling, or a
validated luminosity-scaling choice.

## Full packaged FNAL production

Verify an already initialized proxy, then source the leaf-local FNAL wrapper:

```bash
source start.sh
voms-proxy-info -identity -path -timeleft
source PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/fnal_lpc_packaged_env.sh
```

The wrapper selects direct `root://eoscms.cern.ch` input, packaged Condor
workers, `root://cmseos.fnal.gov` stage-out, and the worker-visible CVMFS VOMS
trust directory. Select one era and a fresh campaign identity after sourcing
the wrapper:

```bash
export YEAR=2024
export ANALYSIS_PASS=RUN_STABILITY
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export FILES_PER_JOB=10
export JOB_CAMPAIGN=DY_TRIGGER_STABILITY_<unique-id>
export PRODUCTION_CAMPAIGN=DY_RUN_STABILITY_2024_<unique-id>
unset SAMPLE_FILTER LIMIT_FILES_PER_SAMPLE DATA_STREAM_FILTER DATA_RUN_FILTER

mkShapesRDF -c 1 --submit \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability \
  -l -1 -q workday
```

Repeat with a new compile and campaign identity for `2022`, `2022EE`, `2023`,
`2023BPix`, and `2024`. Do not submit an existing pilot JDL or a moving/latest
pickle. The validated 2026-08-17 campaign manifest is in
`production_history/20260817_vomsfix_full_production.md`.

Before submission, audit recorded DATA independently of MC. Compare the live
sample-specific dataset/run-tag/stream/trigger-weight matrix and the exact
compiled component/file inventory against the processor catalog, the
analysis-aligned read-only `PlotsConfigurationsRun3` family, and the selected
live HWWNano directory. Treat the aligned configuration as one reference, not
as an override of a processor-catalogued and materialized component. Require
the compiled inventory to cover the reconciled union with no unresolved
missing or unexpected components or files. Any discrepancy is a submission
veto.

Also inspect `lumi/inputs/dataset_run_inventory/dataset_run_inventory.json`.
Its `year_config` must resolve to this live RunStability leaf, and its
`year_config.sha256` must match the current `year_config.json`. Internally
consistent luminosity tables generated from an older or different
configuration are stale. Regenerate and validate the luminosity artifacts
before compiling after a DATA membership change.

For 2022EE, require all nine `MuonEG`/`Muon`/`EGamma` × E/F/G Prompt-v1
components and exact file-set equality. The Z-mass campaign's 1,507-file
2022EE DATA audit is recorded in
`production_history/20260817_dy_zmass_ratio_production.md`.

For 2022, do not use the historical six-component/672-file inventory as a
completeness oracle. Require this period-dependent seven-component matrix:

```text
MuonEG:     Run2022C, Run2022D -> logical stream MuonEG
SingleMuon: Run2022C only      -> logical stream Muon
Muon:       Run2022C, Run2022D -> logical stream Muon
EGamma:     Run2022C, Run2022D -> logical stream EGamma
```

Use the sample-specific trigger/de-duplication weights from the live contract:
`SingleMuon` takes `!Trigger_ElMu && Trigger_sngMu`, while `Muon` takes
`!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)`. The processor catalog and
materialized HWWNano inventory exposed the missing
`SingleMuon_Run2022C-ReReco-v1` component that the leaf and aligned DY reference
had both omitted. Positive early-run TH2 rows from other streams do not close
this gap. That omission removes early single-muon-accepted DATA, including
affected dimuon events, and makes the old inclusive and muon-channel Data/MC
ratios artificially low. Do not classify the old muon-path zero exposures as
physical inactivity; their owning-stream coverage was incomplete. The
corrected audit is in
`production_history/20260818_dy_trigger_stability_production.md`.

For a complete Z-mass ratio-versus-run campaign without booking unused DY
observables, add these selectors before each fresh compile:

```bash
export RUN_STABILITY_REGION=DY
export RUN_STABILITY_OBSERVABLES=Z0_mass
export RUN_STABILITY_CATEGORIES=DY_ALL,DY_STREAM_MUONEG,DY_STREAM_MUON,DY_STREAM_EGAMMA,DY_TRGFAM_ELMU,DY_TRGFAM_SINGLEMU,DY_TRGFAM_DOUBLEMU,DY_TRGFAM_SINGLEEL,DY_TRGFAM_DOUBLEEL,DY_HLT_MU23_ELE12,DY_HLT_MU12_ELE23,DY_HLT_MU8_ELE23,DY_HLT_MU17_MU8,DY_HLT_ISOMU24,DY_HLT_ELE23_ELE12,DY_HLT_ELE30
```

Keep `SAMPLE_PROFILE=presentation` and clear all sample, stream, run, and file
limits: observable/category narrowing must not silently narrow the DATA or
prompt-MC input population. The resulting contract has 16 auxiliary DATA
TH2 paths per era. A completed historical production with
`run_stability/ZZCR_*` paths is not a DY input and must not be reused for this
plot.

The one shared `JOB_CAMPAIGN` creates exactly one top-level local folder,
`jobs/<JOB_CAMPAIGN>/`, containing a distinct tag subdirectory for every era.
It does not replace the fresh era-specific remote `PRODUCTION_CAMPAIGN`.

When expanding the requested category ratio matrix, resolve each category with
`--luminosity-source auto`. A nonpositive era-level MC denominator is an
undefined ratio: preserve the fail-closed result, write no partial stem, and
continue the other combinations. Do not manufacture a zero ratio or remove
the affected era from the run axis.

## Status and merge

Use the recorded cluster and schedd to distinguish queued, completed, and
failed jobs. Then check and merge with the exact timestamped pickle produced
for that submission:

```bash
condor_q -name <schedd> <cluster-id>
condor_history -name <schedd> <cluster-id> -af JobStatus ExitCode

mkShapesRDF -c 0 --check -b 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability \
  -config PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/configs/config_<exact>.pkl

mkShapesRDF -c 0 --histoadd -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability \
  -config PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/configs/config_<exact>.pkl
```

Independently list the exact FNAL EOS campaign directory after merging. It
must contain the complete split-output set and one merged
`mkShapes__<tag>.root` file.

## Ordinary one-dimensional plots

`mkPlot` loads the latest pickle from `./configs`, while the compiled
`plotPath` is relative to the process working directory. To plot a specific
production without selecting another era's latest pickle, make an isolated
campaign runtime directory containing only the exact pickle and route its
compiled plot path to the campaign plot directory:

```bash
repo=/absolute/path/to/mkShapesRDF
tag=<exact-tag>
job="$repo/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/jobs/$tag"
runtime="$job/plot_runtime"

mkdir -p "$runtime/configs" "$runtime/jobs/$tag" "$job/plots"
cp "$repo/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/configs/config_<exact>.pkl" \
  "$runtime/configs/"
ln -s "$job/plots" "$runtime/jobs/$tag/plots"

cd "$runtime"
mkPlot \
  --inputFile "$job/$tag/mkShapes__$tag.root" \
  --outputDirPlots "$job/plots" \
  --fileFormats png \
  --showIntegralLegend 1
```

For the validated standard profile, 311 category-variable actions and the
default three plot types in linear and log form produce 1,866 PNGs plus
`plotter.html` per era. These plots use the ordinary era-level 1D hierarchy.
The auxiliary DATA TH2 hierarchy is intentionally excluded from `mkPlot`;
use the separate validated on-demand tool below for per-run comparisons.

## On-demand run plots and ratio summaries

Use the exact merged ROOT file and exact pickle with the commands documented
in `README.md`. Every plotting command first verifies the full expected DATA
TH2 matrix, run labels and flows, all delivered/recorded luminosity histograms, the MC
source luminosity, and every expected ordinary prompt-MC TH1. The luminosity
source is mandatory. Plot outputs are separate derived artifacts and do not
alter the merged input.

See `LUMINOSITY_PROPAGATION.md` for the exact per-run MC scale, Sumw2 and
ratio-uncertainty propagation, within-era MC covariance, zero-luminosity
policy, and interpretation boundary. Ratio summaries use the bounded
Matplotlib publication view (`0.5-1.5`) with directional outlier triangles;
presentation clipping never changes the CSV or ROOT values.
