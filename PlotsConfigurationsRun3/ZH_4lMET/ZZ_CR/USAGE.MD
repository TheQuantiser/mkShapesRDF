# ZZ_CR usage

Run-3 `ZH_4lMET` four-lepton control/reference configuration for
`mkShapesRDF`. The supported eras are `2022`, `2022EE`, `2023`, `2023BPix`,
and `2024`.

## Setup

From the `mkShapesRDF` repository root:

```bash
source start.sh
cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR
```

The important runtime controls are environment variables:

| Variable | Values / default |
| --- | --- |
| `YEAR` | Five eras above; default `2024` |
| `ANALYSIS_PASS` | Optional focused-mode override: `ZPARENT`, `FOURL_BASE`, or `CONTROL`; unset means unified `ALL` |
| `ENABLE_SYSTEMATICS` | `1` loads `nuisances.py`; default `0` |
| `HISTOGRAM_DETAIL` | `core`, `trigger`, `objects`, `quality`, `weights`, or `all` |
| `EXECUTION_PROFILE` | Default `local`; site wrappers select production profiles |

ZZ_CR is histogram-only. Its common, physics-aware axes are defined directly
in `variables.py` and apply to every era and category.

The execution modes are:

- `ALL`: one nominal job set containing all 46 output categories with the
  appropriate correction weight applied independently to each parent cut.
- `ZPARENT`: inclusive Z/DY baseline with the complete two-lepton category
  matrix.
- `FOURL_BASE`: four-lepton preselection without a b veto.
- `CONTROL`: AN2019/238 ZZ control and XSF/XDF signal regions; includes the
  fixed-WP b-veto correction.

The hierarchy is incremental: `FOURL_BASE` extends the Z/DY baseline, and the
`CONTROL` selections extend the same physical four-lepton requirements.
Run all five eras and the passes needed by the analysis. Nominal and systematic
modes receive distinct timestamped tags.

The retained output categories are:

| Pass and cut | Matrix | Count |
| --- | --- | ---: |
| `ZPARENT / inclusive_z_dy` | (`Inclusive` + 3 streams) × 2 Z flavours × `X_NA` | 8 |
| `FOURL_BASE / four_lepton_base` | (`Inclusive` + 3 streams) × 2 Z flavours × (`XSF` or `XDF`) | 16 |
| `CONTROL / zz_control_region` | (`Inclusive` + 3 streams) × 2 Z flavours × (`XSF` or `XDF`) | 16 |
| `CONTROL / signal_region` | Stream-inclusive × 2 Z flavours × (`XEE`, `XMM`, or `XDF`) | 6 |
| Unified `ALL` execution-pass total | Four parent cuts | 46 |

For `inclusive_z_dy`, `four_lepton_base`, and `zz_control_region`, the stream
axis contains the stream-integrated `Inclusive` projection alongside the three
mutually exclusive stream-priority classes `MuonEG`, `Muon`, and `EGamma`.
The `Inclusive` entries intentionally overlap the corresponding three
per-stream entries; the per-stream entries remain mutually exclusive.
`signal_region` deliberately drops the per-stream categories and retains only
the six stream-integrated combinations of `ZEE`/`ZMM` with `XEE`/`XMM`/`XDF`.
The `ALL` identifier selects the unified execution pass and is never a category
key.

The category identifiers are
`STR_<Inclusive|MuonEG|Muon|EGamma>__Z_<ZEE|ZMM>__X_<NA|XSF|XDF>` for the
first three parents, subject to the applicable X values above. Signal uses only
`STR_Inclusive__Z_<ZEE|ZMM>__X_<XEE|XMM|XDF>`.
The `inclusive_z_dy` leaves use `X_NA`; `four_lepton_base` and
`zz_control_region` use `X_XSF`/`X_XDF`; `signal_region` uses
`X_XEE`/`X_XMM`/`X_XDF`. All leaves are explicitly enumerated in `cuts.py`.
Concrete HLT-path and path-priority aliases remain available as trigger
diagnostics, but they are not category axes.

For `zz_control_region`, the `XSF` cells are the nominal AN2019/238 ZZ control
region. The parallel `XDF` cells are retained validation slices under the same
X-mass and MET sideband. For `signal_region`, the parent is the union of the
two physical branches: XSF uses 10 < m(X) < 65 GeV, PuppiMET > 35 GeV, and
m4l > 140 GeV, while XDF uses 10 < m(X) < 70 GeV and PuppiMET > 20 GeV. The
signal matrix projects that union into disjoint XEE, XMM, and XDF branches;
XEE and XMM together exhaust the physical XSF branch.

## Validate before production

```bash
python tests/validate_contracts.py --output-dir /tmp/zzcr_contracts
pytest -q tests/test_check_storage_paths_from_list.py
```

The trigger and b-tag regressions require a representative real input file:

```bash
python tests/trigger_regression.py \
  --year 2024 --era Full2024v15 --file root://.../nanoLatino_....root \
  --output /tmp/trigger_2024.json

python tests/btag_regression.py \
  --year 2024 --file root://.../nanoLatino_....root \
  --output /tmp/btag_2024.json
```

## B-tag payloads

The fixed-working-point evaluator follows the current Run-3 configuration
layout and uses two payload types:

- Official BTV scale factors and loose working points are read directly from
  `/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/<campaign>/latest/btagging.json.gz`.
- Process-dependent ttbar MC efficiencies are not part of that CVMFS JSON.
  They are resolved from the single shared
  `PlotsConfigurationsRun3/utils/data/btag/<era>/` area used by the external
  Run-3 control-region configurations. ZZ_CR does not keep a private copy.

The standard sibling-checkout layout is discovered automatically. For another
layout, point `BTAG_EFFICIENCY_BASE` at the shared
`PlotsConfigurationsRun3/utils/data/btag` directory before compiling the
configuration. A missing CVMFS JSON or efficiency map is a fatal validation
error rather than a silently omitted b-tag correction.

## Bounded local run

Limit both sample discovery and events. This exercises the normal catalog path
without maintaining a second manual-file execution mode.

```bash
export YEAR=2024
export ENABLE_SYSTEMATICS=0 HISTOGRAM_DETAIL=all
export EXECUTION_PROFILE=local_xrootd OUTPUT_MODE=local
export SAMPLE_FILTER=ZZ LIMIT_FILES_PER_SAMPLE=1 FILES_PER_JOB=1
unset ANALYSIS_PASS

mkShapesRDF -c 1 -o 0 -b 0 -f . -l 1000
```

## Operations

Use one exact timestamped `configs/config_*.pkl` as the immutable receipt for
status checks, recovery, merging, and plotting. Do not use `latest` after a
newer configuration has been compiled.

### Submit one all-region production

No full production is currently active. Condor cluster `12246746` was stopped
after the category contract changed and must not be used for merging or
plotting. The commands below describe how to create a fresh immutable receipt
for the finalized 46-category contract.

```bash
source ../../../start.sh
source lxplus_env.sh
voms-proxy-init --voms cms -valid 192:00

export YEAR=2024 ENABLE_SYSTEMATICS=0
export HISTOGRAM_DETAIL=all
export FILES_PER_JOB=10
export PRODUCTION_CAMPAIGN=ZZCR_DYZZ_DATA_2024_ALLREGIONS
unset ANALYSIS_PASS SAMPLE_FILTER LIMIT_FILES_PER_SAMPLE

mkShapesRDF -c 1 -o 0 -b 1 -f . -l -1
```

Each split job fills all 46 categories. `samples.py` enables only DY, ZZ, and
DATA by default. The receipt in `jobs/<tag>/condor/<tag>/submit.receipt.txt`
records the Condor cluster; the compiled receipt is the newly created
timestamped pickle. Confirm that the job tree is compact, the JDL queues the
expected split count, and the compiled cuts contain 46 flattened categories.
Set `ANALYSIS_PASS` only to request one of the focused modes; ordinary nominal
operation leaves it unset and therefore uses the unified contract.
Run production from a clean shell so diagnostic sample/file limits cannot leak
into the catalog production.

For FNAL packaged execution, source `fnal_lpc_packaged_env.sh` instead.  That
profile reads through `root://eoscms.cern.ch`, stages output through
`root://cmseos.fnal.gov`, enables the self-contained Condor runtime archive,
and requests 4096 MB per single-core job.  The archive includes both the
compressed analysis payload and the exact fixed-working-point b-tag efficiency
map selected for the requested year; a packaged worker must not retain an AFS
path to either resource.  Before the event loop, the configuration-local
runner idempotently creates the campaign/tag output directory with
`xrdfs <write-endpoint> mkdir -p <output-LFN>`, so first-job stage-out does not
depend on a manually prepared directory.

To audit FNAL packaging without submitting, keep `-o 0` and omit `--submit`:

```bash
source ../../../start.sh
source fnal_lpc_packaged_env.sh
export YEAR=2024 ENABLE_SYSTEMATICS=0 HISTOGRAM_DETAIL=all
export SAMPLE_FILTER=ZZ LIMIT_FILES_PER_SAMPLE=1 FILES_PER_JOB=1
export PRODUCTION_CAMPAIGN=FNAL_PACKAGE_AUDIT
mkShapesRDF -c 1 -o 0 -b 1 -dR 1 -f . -l 1
```

Inspect the resulting JDL and archive before submission.  The submit ad must
contain `RequestMemory = 4096`; the archive must contain the generated payload
and b-tag map under `runtime_includes/`; and the serialized payload must contain
runtime-include tokens rather than CERN AFS paths.  The full 2024 nominal audit
books 46 categories and 509 variables per category.  The environment variable
`MKSHAPESRDF_SKIP_REMOTE_OUTPUT_PREPARE=1` exists only for an isolated
no-remote-write worker test and must not be set for submitted jobs.

### Monitor and recover

```bash
condor_q <cluster-id>
mkShapesRDF -c 0 --check -b 1 -f . \
  -configs configs -config configs/<exact-config>.pkl
```

Require zero held jobs and one nonempty EOS ROOT file per job ID. Ordinary
`err.txt` files contain ROOT's missing EDM-dictionary warnings and timing; a
nonzero Condor return value, traceback, stage-out failure, or absent ROOT file
is actionable. Resubmit only failed split IDs through the exact compiled
configuration. Never launch a second full cluster over a partially completed
output directory.

To stop a mistaken submission, run `condor_rm <cluster-id>`, verify that
`condor_q` returns no jobs, and move its job tree and configuration receipt to
the archive. Remove remote contents only when they have been explicitly
declared disposable.

### Merge

After expected job IDs and actual nonempty split files match exactly:

```bash
mkShapesRDF -c 0 --histoadd -b 0 -f . \
  -configs configs -config configs/<exact-config>.pkl
```

For CERN production profiles, the local merged file is written below
`/eos/user/<initial>/<user>/mkShapesRDF_merge_scratch/<campaign>/<tag>/` and
staged to the split-output EOS directory. Require all 46 top-level categories
in `rootls` before plotting.

### Plot and verify

```bash
mkPlot \
  --inputFile /eos/user/<initial>/<user>/mkShapesRDF_merge_scratch/<campaign>/<tag>/mkShapes__<tag>.root \
  --onlyPlot cratio \
  --showIntegralLegend 1 \
  --fileFormats png
```

Plots are written to `jobs/<tag>/plots`. With 509 variables and 46 categories,
the complete contract contains 23,414 category-variable cells. Rendering one
linear and one logarithmic view per cell produces 23,414 linear plus 23,414
logarithmic PNGs: 46,828 nonempty files. Across the eight enabled samples,
the nominal merged ROOT contract contains 187,312 sample-category-variable
histograms.

### Add a category or weight

Per-category weights are declarative. In `ANALYSIS_PASS_CONTRACT["ALL"]`, each
cut's `cut_weights` mapping uses `*` as its default expression and an exact
category key as an optional override:

```python
{"*": "defaultCorrection", "new_category": "specialCorrection"}
```

Add the category expression in `cuts.py`, its display label in
`selection_config.py`, and only then an optional weight override. `cuts.py`
rejects misspelled category keys; the runner resolves the metadata without
hard-coded region names.

## Samples and storage

`year_config.json` is the authoritative era/sample/trigger/luminosity/storage
configuration; do not duplicate those values in Python. To make and verify a
fresh all-parts catalog without retaining it here:

```bash
python make_sample_catalog.py crawl --help
python check_storage_paths_from_list.py /absolute/path/all_parts.txt \
  --config year_config.json --receipt /tmp/zzcr_storage_receipt.json
```

## Histogram binning

`variables.py` resolves one common axis per variable, shared by every category,
era, and nominal/systematic variation. The choices combine the completed DY+ZZ
binning catalog with variable semantics and analysis thresholds; nonphysical
or sparsely populated tails are folded into sensible plotting boundaries.
There is no runtime category-binning JSON and no category-by-category job mode.

Historical campaigns, reports, Condor trees, catalog snapshots, and the
completed DY+ZZ proxy-binning products were moved to:

```text
/afs/cern.ch/work/m/mwadud/private/2026_ZH_4l2nu/devel/zz_cr_codex_archive_20260809
```

Those products are provenance/reference material, not active full-release
inputs.
