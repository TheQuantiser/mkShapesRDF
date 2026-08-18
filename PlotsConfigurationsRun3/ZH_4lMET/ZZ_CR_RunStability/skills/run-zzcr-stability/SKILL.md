---
name: run-zzcr-stability
description: Compile, run, inspect, plot, or validate the DY-only ZH_4lMET ZZ_CR_RunStability leaf with selectable DATA run-resolved TH2 matrices, one-dimensional prompt MC, dynamically routed nominal/trigger-family/concrete-path luminosity sources, category-aware plotting, and campaign-local job control.
---

# Run DY stability safely

## Read the live contract

Work from the writable `mkShapesRDF` checkout. Read the leaf `README.md`,
`USAGE.md`, `LUMINOSITY_PROPAGATION.md`, `run_stability_config.py`, and
`zz_cr_runner.py` before acting. Also apply the workspace plot-configuration
inspection and validation skills and the CMS luminosity-audit skill.

Never modify mkShapesRDF core, `include/`, `utils/`, the original
`ZH_4lMET/ZZ_CR`, or `ZH4l` for this workflow. Do not submit Condor jobs,
stage out output, commit, or push unless a later request separately authorizes
that action.

## Compile-time contract

Use exactly:

```bash
export ANALYSIS_PASS=RUN_STABILITY
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
```

Set `YEAR` to one of `2022`, `2022EE`, `2023`, `2023BPix`, or `2024`.
`RUN_STABILITY_LUMI_DIR`, when set, must name an absolute or resolvable copy of
the validated `lumi/results` directory with its sibling `provenance.json`.
Compilation must fail rather than infer missing run or luminosity data.

Run stability is DY-only. Set `RUN_STABILITY_REGION=DY` and set both
`RUN_STABILITY_OBSERVABLES` and
`RUN_STABILITY_CATEGORIES` to `all_dy` or exact comma-separated names. Inspect
the compiled `analysisContract.run_stability` block. Require the expected run
count for the selected era, the exact selected matrix and path product, both
the complete dynamic luminosity-source registry, category-to-source map, input
hashes, exact MC source luminosity, selector provenance, and the DATA
split-zero metadata policy. Require nominal, `Trigger_Any`, all five positive
trigger-family sources, and all seven concrete-path sources. Each source must
have the exact nominal run order, independently checked era/year aggregates,
and recorded/delivered ROOT metadata paths.

Before compilation or submission, audit recorded DATA separately from MC.
Construct the live sample-specific primary-dataset/run-tag/logical-stream/
trigger-weight matrix. Compare it and every exact compiled DATA file URI with
the matching processor sample catalog, an analysis-aligned era configuration
in the read-only sibling `PlotsConfigurationsRun3` checkout, and the
materialized HWWNano directory selected by the production and step. Treat the
aligned configuration as comparison evidence, not authority to suppress a
processor-catalogued and materialized component. Reconcile the expected union;
require zero unresolved missing or unexpected components and files. Never
submit if any configured, reference, processor, or materialized member is
absent from the compiled campaign. Record per-component counts. Do not turn a
DATA completeness question into an MC sample comparison.

Do not assume a Cartesian primary-dataset list across periods. Encode
primary-dataset transitions with per-sample run tags and the owning logical
stream's trigger weight. For 2022 require exactly: MuonEG C/D as stream
MuonEG; SingleMuon C only as stream Muon; Muon C/D as stream Muon; and EGamma
C/D as stream EGamma. Preserve the sample-specific expressions:
`!Trigger_ElMu && Trigger_sngMu` for SingleMuon and
`!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)` for Muon. Reject an
invented SingleMuon D component or a stream-wide weight that erases this
distinction.

Before compilation, inspect the luminosity dataset-inventory manifest. Require
its `year_config` to name this live RunStability `year_config.json` and its
`year_config.sha256` to equal the current file hash. Treat a hash-valid
manifest for the original ZZ_CR or an older leaf copy as stale. After any DATA
component, run-tag, stream, or trigger-weight change, rebuild and validate the
luminosity artifacts before submission.

For early-2022 coverage questions, especially runs below 356434, never infer
completeness from sparse adaptive tick labels or from nonzero inclusive TH2
rows. The historical six-component/672-file campaign omitted
SingleMuon_Run2022C even though other streams populated every early run. Its
inclusive and muon-channel ratios are biased low because DATA lost early muon
events while MC retained positive normalization exposure. Its early muon-path
zero luminosities came from incomplete owning-stream coverage and are not a
physical inactivity result. Require the corrected seven-component contract
and regenerated luminosity products before interpreting those ratios.

## Bounded real-input pilot

Source `start.sh`, select `EXECUTION_PROFILE=local_xrootd`, local output, one
exact sample, one file per sample, and a finite event limit. Run DATA and one DY MC
as separate bounded pilots so each input role is explicit. `-l` alone does not
bound discovery. For the DATA pilot, use exact `DATA_STREAM_FILTER` and
`DATA_RUN_FILTER` values from the selected year's configured catalog so the
compiled input inventory contains one physical file. Unknown filters must fail
during compilation. Unset both DATA filters before compiling the DY MC pilot.

Do not use a site production wrapper for this local pilot: those wrappers can
select packaged batch execution and remote output. Never reuse a pilot pickle
or generated job description for production.

## Inspect the ROOT output

For DATA, require exactly `categories × observables` TH2 objects below
`run_stability/`, exact run labels,
empty x flows, y edges/folding matching ordinary TH1 objects, and one copy of
all 29 metadata histograms: delivered and recorded values for 14 luminosity
sources plus `mc_source_lumi_fb`. Compare the visible TH2 integral summed over
run bins to the matching ordinary DATA TH1 integral.

For the DY MC-only output, require ordinary TH1 objects and no
auxiliary TH2 or run metadata. Merge validation must use the unchanged
`utils/bin/hadd2`; metadata is present in only DATA split zero so it must not
be multiplied.

Successful bounded execution establishes software behavior and selected
numerical invariants. It does not establish full-production completeness,
physics-level DATA/MC agreement, nonprompt modeling, or validated per-run MC
normalization for a production that has not been independently inspected.

## Produce a full ratio campaign

Require explicit user authorization before submission. Do not reuse a merged
campaign merely because it contains ordinary DY TH1 objects: its exact pickle
and `run_stability/` hierarchy must contain every requested DY auxiliary DATA
path. A historical `run_stability/ZZCR_*` matrix is incompatible.

For the focused Z-mass trigger-stability production, set
`RUN_STABILITY_REGION=DY`, `RUN_STABILITY_OBSERVABLES=Z0_mass`, and use this
exact 16-category selector:

```bash
export RUN_STABILITY_CATEGORIES=DY_ALL,DY_STREAM_MUONEG,DY_STREAM_MUON,DY_STREAM_EGAMMA,DY_TRGFAM_ELMU,DY_TRGFAM_SINGLEMU,DY_TRGFAM_DOUBLEMU,DY_TRGFAM_SINGLEEL,DY_TRGFAM_DOUBLEEL,DY_HLT_MU23_ELE12,DY_HLT_MU12_ELE23,DY_HLT_MU8_ELE23,DY_HLT_MU17_MU8,DY_HLT_ISOMU24,DY_HLT_ELE23_ELE12,DY_HLT_ELE30
```

Keep the presentation sample profile and unset every sample, DATA stream,
DATA run, and per-sample file limit. Source the packaged FNAL wrapper first,
then apply these selectors. Set one collision-resistant `JOB_CAMPAIGN`
directory name for the related five-era production; require every tag's
contract, worker payload, Condor material, and plots below
`jobs/<JOB_CAMPAIGN>/<tag>/`. `JOB_CAMPAIGN` must not contain path separators,
`.` or `..`, and it does not alter the remote output campaign. Compile and
submit every era separately only after explicit authorization, using the exact
README command. Record the exact timestamped pickle in the leaf-global
`configs/` directory, tag, cluster, schedd, expanded job count, input-file count, and
destination before monitoring.

Treat submission, queueing, completion, stage-out, exact split-set equality,
merge, merged-file reopening, plot generation, and plot inspection as
separate gates. Merge only with each recorded exact pickle. Generate both
`--luminosity-source auto` for category-aware production plots. Allow an
explicit compiled source key only as a recorded diagnostic override; never
replace a zero source value with another source.

Attempt every requested category/source plot independently. Preserve a
nonpositive-MC guard as a scientifically undefined result, create no partial
artifacts for that stem, continue other independent combinations, and record
the exact era and category that failed. Disable ROOT's ordinary histogram
statistics box in the stored labelled ratio histogram. Render the stability
summary with the analysis-local Matplotlib implementation adapted from the
maintained mkshapes-analysis-lab publication-light theme: use the semantic
`0.5-1.5` ratio range, directional boundary triangles for out-of-range
central values, adaptive run labels, era lanes, and explicit invalid-run
markers. Inspect both an inclusive and a sparse full-size plot after
generation. Read `LUMINOSITY_PROPAGATION.md` before changing the scale,
uncertainty, or covariance implementation.

## On-demand comparison products

Use `plot_run_stability.py` only with the exact compiled pickle and exact
merged ROOT file. Run `list` or `validate` first. Require
`--luminosity-source auto` for the standard category-aware workflow. Verify
that ordinary categories resolve `trigger_any`, `DY_TRGFAM_*` resolves the
matching `trigger_*` source, `DY_HLT_*` resolves the matching `hlt_*` source,
and enriched mirrors preserve the unprefixed source. For multi-era inputs,
require identical resolved keys across eras. Never replace a zero value with
another source. The tool must validate the full selected matrix and prompt-MC
inventory before plotting. Its per-run plots use Garwood DATA intervals and
scaled MC Sumw2. Its ratio-vs-run ROOT product must retain the within-era
shared-MC covariance, zero covariance across independent era templates, run
labels, CSV values, and a JSON provenance receipt. Generated comparison
artifacts are derived outputs and are not production validation by themselves.

Treat family/path categories as direct positive, overlapping projections, not
exclusive delivered-time partitions. DATA primary-dataset de-duplication is
owned by the per-component sample weights, not by these category cuts. The
current MC weight retains aggregate
selected-Z `TriggerSF_Z`; no concrete-path trigger scale factor is implemented
or validated. Report `DY_HLT_*` results only as path-selection stability
diagnostics, never as path-SF measurements.
