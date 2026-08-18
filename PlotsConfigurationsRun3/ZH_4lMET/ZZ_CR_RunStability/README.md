# DY run stability

`ZZ_CR_RunStability` is an independent copy of the established
`ZH_4lMET/ZZ_CR` configuration. It preserves the ordinary one-dimensional
mkShapesRDF histogram hierarchy and adds a DATA-only run-resolved hierarchy.
The original `ZZ_CR`, the `ZH4l` successor, and mkShapesRDF core are not part
of this leaf's implementation surface.

## DY run-stability profile

The default and supported run-stability production contract is:

```bash
export YEAR=2024
export ANALYSIS_PASS=RUN_STABILITY
export CATEGORY_PROFILE=standard
export HISTOGRAM_PROFILE=analysis
export SAMPLE_PROFILE=presentation
export ENABLE_SYSTEMATICS=0
export HISTOGRAMS=1
export RUN_STABILITY_REGION=DY
export RUN_STABILITY_OBSERVABLES=all_dy
export RUN_STABILITY_CATEGORIES=all_dy
```

Run stability in this leaf is DY-only; any non-DY region fails during
compilation. The default `all_dy` selectors resolve 25 supported
one-dimensional DY observables in all 48 standard run-stability categories,
or 1,200 DATA TH2 objects. The category inventory includes the ordinary DY
views, their enriched-Z-window mirrors, five positive trigger-family views,
and seven positive concrete-HLT-path views. `presentation` supplies DATA
and the complete configured prompt MC denominator; it does not define a
nonprompt/fake estimate. A smaller
production can use exact comma-separated names, for example:

```bash
export RUN_STABILITY_REGION=DY
export RUN_STABILITY_OBSERVABLES=Z0_mass,lZ1_pt,lZ2_pt,Z0_pt,Z0_eta
export RUN_STABILITY_CATEGORIES=DY_ALL,DY_ZEE,DY_ZMM
```

The maintained focused trigger-stability production uses `Z0_mass` and this
exact 16-category selector:

```bash
export RUN_STABILITY_OBSERVABLES=Z0_mass
export RUN_STABILITY_CATEGORIES=DY_ALL,DY_STREAM_MUONEG,DY_STREAM_MUON,DY_STREAM_EGAMMA,DY_TRGFAM_ELMU,DY_TRGFAM_SINGLEMU,DY_TRGFAM_DOUBLEMU,DY_TRGFAM_SINGLEEL,DY_TRGFAM_DOUBLEEL,DY_HLT_MU23_ELE12,DY_HLT_MU12_ELE23,DY_HLT_MU8_ELE23,DY_HLT_MU17_MU8,DY_HLT_ISOMU24,DY_HLT_ELE23_ELE12,DY_HLT_ELE30
```

Unknown, empty, or non-DY names fail during compilation. The
resolved names, the original selectors, the target region, and the complete
expected path matrix are serialized in the compiled contract and encoded in
the production tag. `VARIABLE_INCLUDE` and `VARIABLE_EXCLUDE` are not a
second selector path for DY run stability. Use the `list` command below to
inspect the exact supported and produced matrix from a compiled configuration.

## DATA dataset completeness

"All configured files" means the exact compiled catalog was processed; it is
not by itself proof that the catalog contains every intended recorded-DATA
dataset. Before compilation or submission, form a sample-specific component
matrix containing primary dataset, run tag, logical stream, and trigger
weight. Compare that matrix and the exact compiled file URIs against all of:

1. the live leaf `year_config.json`;
2. the processor sample catalog selected by the DATA production;
3. an analysis-aligned configuration in the read-only sibling
   `PlotsConfigurationsRun3` checkout; and
4. the exact materialized HWWNano directory selected by the production and
   processing step.

The external analysis configuration is comparison evidence, not permission to
ignore a processor-catalogued and materialized component that it omitted.
Require the compiled campaign to contain every component and file expected by
the reconciled union, and require every discrepancy or unexpected component to
be resolved before submission. Missing configured, reference, processor, or
materialized membership is a submission veto. Keep primary-dataset coverage
distinct from MC sample coverage.

Do not form a blind Cartesian product of one primary-dataset list and every run
period. Primary-dataset names can change within an analysis era. Encode each
sample's eligible run tags and its logical stream explicitly, so renamed
datasets inherit the correct stream de-duplication weight.

For the 2022EE v12 production, the established DATA contract is the Cartesian
product of primary datasets `MuonEG`, `Muon`, and `EGamma` with
`Run2022E-Prompt-v1`, `Run2022F-Prompt-v1`, and `Run2022G-Prompt-v1`, read
from `Run2022EE_Prompt_nAODv12_Full2022v12` after
`DATAl2loose2022EEv12__l2loose`. The exact 2026-08-17 production audit is
recorded in `production_history/20260817_dy_zmass_ratio_production.md`.

Run2022 exposes the failure mode. The processor catalog contains both
`SingleMuon_Run2022C-ReReco-v1` and `Muon_Run2022C-ReReco-v1`; `Muon` continues
into Run2022D, while `SingleMuon` does not. The required analysis matrix is
therefore seven components, not the historical six-component Cartesian
product:

| Primary dataset | Logical stream | Eligible run tags |
| --- | --- | --- |
| `MuonEG` | `MuonEG` | Run2022C, Run2022D |
| `SingleMuon` | `Muon` | Run2022C only |
| `Muon` | `Muon` | Run2022C, Run2022D |
| `EGamma` | `EGamma` | Run2022C, Run2022D |

The logical stream does not imply one universal component weight.
`SingleMuon_Run2022C` uses the sample-specific
`!Trigger_ElMu && Trigger_sngMu` weight, while `Muon` uses
`!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)`. A sample-level run list is
mandatory to prevent the nonexistent `SingleMuon_Run2022D` component from
being invented, and a sample-level trigger expression is mandatory to preserve
the primary dataset's acceptance contract.

The historical leaf, aligned DY reference, exact compiled pickle, and pinned
luminosity inventory all omitted `SingleMuon_Run2022C-ReReco-v1`. Their mutual
agreement and the old 672-file count therefore did not establish completeness.
The existing TH2 has nonzero early-run rows because other primary datasets
survived; that does not prove the missing muon stream was present. Omitting it
removes early dimuon DATA while MC is still normalized to the available
positive trigger exposure, producing artificially low inclusive and especially
muon-channel Data/MC ratios. Adaptive tick labels were a separate presentation
issue, not the cause of those low ratios. The corrected evidence and failed
pre-submission gate are recorded in
`production_history/20260818_dy_trigger_stability_production.md`.

## ROOT output contract

Ordinary DATA and MC remain one-dimensional and keep the standard paths:

```text
<selected category>/<observable>/histo_<sample>
```

The additional DATA-only two-dimensional objects are:

```text
run_stability/<selected category>/<observable>/histo_DATA
```

Their x axis has one ordinal bin per audited run, labelled with the exact run
number. Their y axis has the same edges, title, and fold policy as the public
one-dimensional observable. Folding acts on y only. An unknown run throws
during the event loop, and nonempty x underflow or overflow is rejected. No
two-dimensional MC object is booked.

The ordinary hierarchy is therefore still compatible with `mkPlot`; the
auxiliary hierarchy is not passed to the standard one-dimensional plotter.

## Luminosity inputs and metadata

At compilation, `run_stability_config.py` reads the validated nominal,
positive-combination, and concrete-path products in the workspace
`lumi/results/` directory. Override that location only with an explicit
results directory:

```bash
export RUN_STABILITY_LUMI_DIR=/absolute/path/to/lumi/results
```

The compiler validates every source's run set, finite and nonnegative values,
era/year aggregates, validation receipt, provenance hashes, and deterministic
run order. It serializes the complete run map, source definitions, and
category-to-source routing into the compiled analysis contract and worker
payload. Workers do not reopen the workspace luminosity files.

Hash-valid result files are insufficient when their DATA membership was built
from a different configuration. Before compilation or submission, require the
luminosity dataset-inventory manifest to name this live leaf's
`year_config.json` and require its recorded `year_config.sha256` to equal the
current file's SHA-256. Rebuild and revalidate the luminosity products after
any DATA component, run-tag, stream, or trigger-weight change. Never submit by
accepting a manifest that still points to the original `ZZ_CR` configuration
or an older RunStability copy, even if every result hash is internally
consistent.

The source keys are `nominal`, `trigger_any`, the five positive trigger-family
keys `trigger_{elmu,sngmu,dblmu,sngel,dblel}`, and the seven concrete-path keys
`hlt_{mu23_ele12,mu12_ele23,mu8_ele23,mu17_mu8,isomu24,ele23_ele12,ele30}`.
Ordinary DY reference, flavor, and stream categories route to `trigger_any`;
`DY_TRGFAM_*` categories route to the matching family; and `DY_HLT_*`
categories route to the matching concrete path. Enriched mirror categories
inherit their unprefixed category's source.

The audited run counts are:

| Era | Run bins |
| --- | ---: |
| 2022 | 151 |
| 2022EE | 190 |
| 2023 | 126 |
| 2023BPix | 43 |
| 2024 | 456 |

Exactly one DATA worker—the logical `DATA` split with index zero—writes, for
every compiled source key:

```text
run_stability/metadata/<source>_delivered_lumi_fb
run_stability/metadata/<source>_recorded_lumi_fb
run_stability/metadata/mc_source_lumi_fb
```

The 28 per-run luminosity objects are TH1D histograms with the same run labels
as the TH2 x axis and zero bin errors. `mc_source_lumi_fb` is the exact configured
`lumi` constant already included in the MC event weight; it is deliberately
not replaced with a sum from the extracted luminosity tables.

## On-demand MC scaling and comparison plots

`plot_run_stability.py` validates an exact compiled pickle against an exact
merged ROOT file and produces plots only when requested. It never guesses a
latest pickle and never pre-renders one plot per run. The implemented rule for
process `p`, run `r`, and resolved source `s` is:

A merged production is usable only when its compiled `run_stability`
contract and ROOT auxiliary hierarchy contain the requested DY category and
observable. Historical files containing only `run_stability/ZZCR_*` are not
valid inputs for DY run-ratio plots, even if their ordinary one-dimensional
hierarchy also contains DY categories. Produce a fresh, narrowly selected DY
matrix rather than relabelling or projecting an incompatible campaign.

```text
H_MC^(p,r)(y) = H_MC^(p,era)(y)
                * L_recorded_run^(s) / L_MC_source
```

Use `--luminosity-source auto` for category-aware propagation. `auto` resolves
the compiled category mapping and requires the same source key in every input
era. An exact compiled source key may be supplied as an explicit diagnostic
override, but it changes the normalization interpretation and is recorded in
the output identity. Variances scale by the square of the factor, and every
configured prompt process is scaled before the total is formed. A
zero-luminosity run is marked invalid in the run-ratio output and is never
silently replaced by another luminosity definition. An era/category with a
nonpositive total prompt-MC template fails before writing a ratio; absence
under that guard is not converted to zero or silently dropped from the era
sequence.

The complete normalization, Sumw2, asymmetric ratio-error, and shared-template
covariance equations are documented in `LUMINOSITY_PROPAGATION.md`.

List or validate the exact available matrix:

```bash
python PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/plot_run_stability.py \
  list --config /path/to/config_<exact>.pkl \
  --input root://cmseos.fnal.gov//store/user/.../mkShapes__<tag>.root
```

Create one observable plot for one chosen run:

```bash
python PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/plot_run_stability.py \
  plot --config /path/to/config_<exact>.pkl \
  --input root://cmseos.fnal.gov//store/user/.../mkShapes__<tag>.root \
  --category DY_ALL --observable Z0_mass --run <run> \
  --luminosity-source auto --output-dir /path/to/output
```

The DATA points use central 68.2689% Garwood intervals. The MC error comes
from the ordinary histogram `Sumw2`, including the luminosity scale. The
bin-by-bin Data/MC interval propagates both contributions.

Create one ratio-vs-run product across the five analysis eras by repeating
the three-argument dataset option in the desired axis order:

```bash
python PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/plot_run_stability.py \
  ratio-vs-run \
  --dataset 2022 /path/to/2022.pkl root://.../2022.root \
  --dataset 2022EE /path/to/2022EE.pkl root://.../2022EE.root \
  --dataset 2023 /path/to/2023.pkl root://.../2023.root \
  --dataset 2023BPix /path/to/2023BPix.pkl root://.../2023BPix.root \
  --dataset 2024 /path/to/2024.pkl root://.../2024.root \
  --category DY_ALL --observable Z0_mass \
  --luminosity-source auto --output-dir /path/to/output
```

That command writes PNG, PDF, CSV, JSON, and ROOT outputs. The ROOT file keeps
the asymmetric ratio graph and both MC-only and total covariance matrices.
Because one finite era-level MC template is reused for all runs in that era,
the MC statistical covariance is fully correlated within an era and zero
between distinct era templates. The symmetric total covariance adds
`D/M^2` on its diagonal; the graph remains the authoritative asymmetric
Poisson presentation.

The PNG/PDF stability summary uses Matplotlib and the maintained
`notebooks/mkshapes_analysis_lab` publication-light visual grammar. Its
semantic ratio window is `0.5-1.5`; filled upward/downward triangles preserve
central values outside the window, and an `x` marks a zero-luminosity invalid
run. The fixed `1500 x 840` canvas shows every point but only an adaptive
selection of run-number labels. The first and last run of every era are always
labelled. Exact ratios, uncertainties, run labels, and outlier inventories
remain in the CSV, ROOT, and JSON products; tick labels are presentation, not
a run-coverage inventory.

The trigger-family and path categories select the positive family or concrete
HLT decision directly. DATA primary-dataset copies are already de-duplicated
by the per-component sample weights; this de-duplication is not repeated in
the category expression and does not define a luminosity subtraction. The
categories are overlapping and each is normalized by its matching positive
family/path exposure. The nominal MC weight still uses the selected-Z
aggregate `TriggerSF_Z`; no concrete-path-specific trigger scale factor is
implemented or validated. Concrete-path plots are therefore trigger-modeling
diagnostics, not path-SF measurements. See `LUMINOSITY_PROPAGATION.md` for the
complete source map and interpretation boundary.

## Campaign-local job layout

Set one `JOB_CAMPAIGN` directory name before compiling any era in a related
campaign:

```bash
export JOB_CAMPAIGN=DY_TRIGGER_STABILITY_20260818T000000Z
```

It must be one nonempty name without `/`, `\\`, `.` or `..`. Every freshly
generated era/tag is then contained below:

```text
jobs/<JOB_CAMPAIGN>/<tag>/
  analysis_contract.json
  zz_cr_worker_payload.pkl.zlib
  configs/
  condor/
  plots/
```

Use the exact timestamped pickle in the leaf-global `configs/` directory for
status and merge operations; the tag-local `configs/` directory contains the
analysis contract rather than the framework pickle. `JOB_CAMPAIGN` groups local control artifacts; it does not
replace the configured remote output campaign or authorize submission,
stage-out, merge, or cleanup. `USAGE.MD` gives the complete compile, exact
pickle, plotting, and campaign-layout examples.

## Bounded local validation

From the repository root:

```bash
source start.sh

export YEAR=2024
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

Compile a DATA-only or DY-only pilot by adding the corresponding exact
`SAMPLE_FILTER`, then run with a finite event limit:

```bash
export SAMPLE_FILTER=DATA
export DATA_STREAM_FILTER=MuonEG
export DATA_RUN_FILTER=Run2024C-ReReco-v1
mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability -l 100
```

The exact stream and run-tag filters make this a genuine one-file DATA pilot;
an unknown run tag fails at compilation. Before the MC pilot, unset both
`DATA_STREAM_FILTER` and `DATA_RUN_FILTER`, then repeat with an exact DY output
name such as `SAMPLE_FILTER=DYto2E-2Jets_MLL-50` for the one-dimensional MC
reference. A finite event limit does not bound input discovery, so the file
limit is mandatory.
These are local XRootD pilots: no Condor submission or remote stage-out is
part of this validation contract.

Run the focused tests with:

```bash
source start.sh
python -m pytest -q \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability/tests
```

## Architecture boundary

The copied `zz_cr_runner.py` subclasses the unchanged core `RunAnalysis`.
Ordinary TH1 booking and conversion still delegate to core. The copied runner
alone owns auxiliary DATA TH2 booking, y-only folding, run-flow checks,
metadata writing, and the extra ROOT directories. Any need to modify
`mkShapesRDF/`, `include/`, `utils/`, the original `ZZ_CR`, or `ZH4l` is a
design failure for this leaf.

See `CONFIGURATION.md` and `FILE_GUIDE.md` for the inherited four-lepton
selection, samples, weights, and file ownership. The local
`skills/run-zzcr-stability/SKILL.md` owns the bounded execution procedure.

The FNAL packaged wrapper preserves the established `ZZ_CR` transport:
CERN XRootD input and FNAL EOS output. It additionally serializes
`X509_VOMS_DIR=/cvmfs/grid.cern.ch/etc/grid-security/vomsdir` into the worker
launcher before proxy validation. This is worker trust configuration, not
proxy creation; operators must still create a valid CMS VOMS proxy before
submission. A worker error stating that the CMS AC issuer certificate cannot
be found means the payload did not reach the analysis and must not be merged.
