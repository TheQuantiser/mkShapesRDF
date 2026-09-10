# Validation record

## Full nominal 2024 computation and application, 2026-09-10

**Both passes completed on LPC.** This is a real DATA/MC campaign using every
configured `2024_v15` sample/file and no event limit, with systematic variations
disabled. It supersedes the earlier software-only execution limits below; those
sections remain historical records of their respective changes.

The campaign is `runs/zpt2024_20260910_1705_r2/` in this configuration family.
Its `EXECUTION.md`, `resume.sh`, native configurations, job logs, output files and
inspection scripts are local generated artifacts, excluded from Git. The full
path starts at
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/mkShapesRDF/PlotsConfigurationsRun3/ZpTreweighting/`.

The automatic command was `auto zpt2024_20260910_1705_r2 --nominal-only
--apply-fitted`, with the absolute family `runs/` passed to `--runs-dir`.
`resume.sh` records the exact invocation and environment. A source-only worktree
at `codex_analysis/zpt2024-production-source-r2` avoided traversing the large
generated development tree during native packaging. Its base revision was
`05648c4`, plus the controller's empty-query fix included with this record.
The framework core and histogram physics definitions were unchanged.

Runtime: `cmslpc374.fnal.gov`, native Condor 25.0.12, the existing framework
`start.sh`, Python 3.13.11, ROOT 6.38.00 and LCG 109 / EL9 / GCC 13. No dependency
installation or upgrade was needed. Workers used the existing package builder,
CVMFS runtime and separate proxy transfer. Inputs were discovered/read through
`root://eoscms.cern.ch`; ROOT files returned through Condor to the shared run
directories. No remote EOS output publication was performed.

| Pass | Exact pickle in its `configs/` directory | Cluster on `lpcschedd6.fnal.gov` | Result |
| --- | --- | --- | --- |
| Real worker pilot | `config_26-09-10_17_23_35.pkl` | `85436867.0` | Successful exit and transfer; 100 fixed DY events |
| Baseline | `config_26-09-10_17_24_41.pkl` | `85436884.0–2787` | All 2,788 jobs successful; merged and plotted |
| Corrected | `config_26-09-10_18_02_27.pkl` | `85436965.0–2787` | All 2,788 jobs successful; merged and plotted |

Independent final queue/history queries found no queued jobs and exactly the
expected process IDs, working directories, JobStatus 4, ExitCode 0 and
ExitBySignal false for all three clusters. All task-created proxy copies were
removed after terminal-state and output verification; the original proxy was
preserved. Retained JDLs require a current proxy before any new submission.

The full population contains 14 processes, 19 observables and 12 categories,
including all 35 configured DATA components for Run C–I. The saved input list
has 9,965 distinct DATA file URLs and 9,002 DY files, plus all configured
backgrounds. Some file populations are intentionally reused for different
process definitions, such as DATA/Fake and WZ/WZS. The configured luminosity is
109.08 fb^-1; this is not an independent full-year luminosity audit.

### Output and numerical checks

- Both merged ROOT files were independently reopened and contained exactly
  3,192 expected TH1 objects with finite contents/errors, including flow bins.
  Each pass had exactly 2,788 expected returned worker files, without missing
  or extra job outputs, and 24 readable comparison PNGs.
- All 2,964 DATA/background histograms were **exactly identical** between passes
  in bin contents and errors. All histogram entries and axes were unchanged,
  including DY; all 228 DY histograms changed in contents/errors.
- The compiled configurations had identical input ordering, base sample weights,
  selections, variables, nuisances, luminosity and unaffected aliases. The DY
  event weight gained `DY_NLO_ZpTrw` exactly once.
- For each pass, all 336 `events`/`ptll` histograms were independently summed
  from every worker file and compared with the merge, including flow bins and
  sum-of-squared-weight uncertainties. Entries matched exactly. With relative
  tolerance 1e-9 and absolute tolerance 1e-8 for floating-point accumulation,
  all sums agreed. Maximum absolute content/variance differences were
  4.47e-8 / 1.30e-8 for baseline and 1.49e-8 / 3.35e-8 for corrected.
- Every worker stderr was inspected. The only non-timing lines were the five
  known unused EDM metadata dictionary warnings, repeated in every job.
- The worker pilot's 228 histograms exactly matched the earlier local execution
  on the same first 100 DY events. Bounded DATA and Fake pilots are retained in
  the initial attempt directory; they test their actual event/weight paths.

The merged files are
`baseline/rootFiles/mkShapes__ZpTreweighting_2024_v15_baseline.root`
(2,677,523 bytes) and
`corrected/rootFiles/mkShapes__ZpTreweighting_2024_v15_corrected.root`
(2,677,499 bytes). The fitted JSON is `baseline/weights/dyZpTrw.json`.
Before/after plots are under each pass's `plots/` directory.

`inspect_outputs.py` and `compare_passes.py` retain the independent inspection
code. Run them from the framework checkout after sourcing `start.sh`;
`INSPECT_ZPT_PASS=baseline` or `corrected` selects the first script's input.
The resulting records are `baseline-inspection.log`, `corrected-inspection.log`
and `comparison.log`; scheduler and stderr summaries are beside them.

### Fit results and interpretation

The inherited extraction used dimuon `ptll`, normalization method 2, and the
error-function-plus-quadratic fit below 50 GeV with a constant tail. It wrote
`2024_v15/LO_0j`, `LO_1j` and `LO_2j`; the second pass applied those exact
formulas at `gen_Zpt`. Numerical checks found positive finite weights on a
0.01 GeV grid from 0 to 50 GeV and at selected tail points through 10 TeV.

| Dimuon region | DATA-minus-background / DY normalization below 50 GeV | Reported fit chi2/ndf |
| --- | --- | --- |
| 0 jets | 0.919457675 | 159.153 |
| 1 jet | 0.783756423 | 11.162 |
| At least 2 jets | 0.732999114 | 1.275 |

**The 0- and 1-jet fits are poor descriptions at the available precision.**
Automatic application was executed as requested, but these are candidate
corrections requiring method review. The overall normalization factors above
are not part of the shape-weight formulas, so corrected native DATA/MC plots
retain normalization offsets. The 0-jet high-pT discrepancy also remains.

For a descriptive shape comparison, each pass was independently normalized to
DATA minus the extractor's MC backgrounds in `0 <= ptll < 50 GeV`. The table
shows the unweighted RMS of `(DATA-BG)/(normalized DY) - 1` across those 25 bins.
It is not a chi-square test or an uncertainty-calibrated acceptance criterion;
both passes share the same events and the dimuon data also determined the fits.

| Region | Baseline RMS | Corrected RMS |
| --- | --- | --- |
| Zee, 0 jets | 7.209% | 1.109% |
| Zee, 1 jet | 6.785% | 0.897% |
| Zee, at least 2 jets | 7.592% | 0.898% |
| Zmm, 0 jets | 7.061% | 1.304% |
| Zmm, 1 jet | 6.613% | 1.121% |
| Zmm, at least 2 jets | 7.799% | 0.853% |

All three fitted dimuon plots and representative before/after dimuon and
electron comparison plots were visually inspected. That inspection exposed
inherited fit labels claiming 8.2 fb^-1 and 5 GeV bins. All five extractors now
accept the luminosity supplied from the saved configuration and derive the
bin-width label from the histogram. Six PDFs were regenerated for this campaign
under **`baseline/fit_plots/`**, showing 109.08 fb^-1 and 2 GeV bins. Original
PDFs in `baseline/weights/` remain as evidence of the old labels. Refitting for
those regenerated plots reproduced the same normalizations and chi2/ndf;
the JSON and formulas already used by the corrected pass were preserved.

Physics limitations remain: the inherited subtraction omits Fake; the fit uses
reconstructed pT but application uses generator pT; no systematic variation
campaign or uncertainty calibration was performed. The DATA producer source
includes the repository-owned Golden JSON filter and the sample definitions
retain trigger precedence. Certification coverage, global duplicate-event
handling and the configured luminosity were not independently audited on the
external processed trees. This is successful software execution and a measured
shape comparison, not physics acceptance.

### Operational fixes and focused tests

The initial attempt on `cmslpc-el9-heavy01` could not submit because the site's
wrapper required missing system `classad2`/`htcondor2` bindings. The next attempt
submitted cluster 85436866, whose workers failed VOMS issuer validation; all
2,788 jobs were removed and terminal state was verified. Their configs/logs are
preserved under the initial and `_r1` campaign names, and their task-created
proxy copies were removed. The replacement campaign used the existing
RunStability LPC CVMFS VOMS trust setting before native proxy validation.
Authentication checks and framework shipping/I/O code were preserved.

Real successful empty queue responses then exposed the controller's assumption
that native JSON output always contained `[]`. It now accepts empty stdout only
when the client exits successfully, while still requiring complete successful
history and readable outputs. A focused regression checks that empty queue and
empty history cannot establish completion.

All **50 focused tests passed**, including the luminosity argument supplied to
extraction. Syntax checks passed for all five extractors; Black and Flake8 passed
for the changed orchestration/test sources, and `auto --help` was checked.
No broad framework test suite was run. The controller and these output
inspections use no hash-based checks. Generated ROOT files, plots, job payloads,
logs and credentials are not committed. The sections below describe earlier,
narrower validation only.

## Automatic two-pass controller, 2026-09-10

The controller adds `auto`, with an optional formula-review pause and explicit
`--apply-fitted` mode. The leaf physics sources and framework core are unchanged.
Validation used the same LPC host and supported Python/ROOT runtime as below.

- **Software: passed within the tested scope.** All 49 focused tests passed.
  New cases cover both automatic passes, review/edit/resume, duplicate-controller
  exclusion, repeated completion, changed options and input lists, incomplete
  extraction, missing ROOT members, missing history/output, held/removed/failed
  jobs, unknown exits, and scheduler/directory mismatches. Scheduler responses,
  full-campaign stages and fitting are fixtures, not actual submissions or fits.
- **Numerical: passed for the identity-correction test.** A fresh native run
  applied deliberately synthetic `1.0` formulas to the same real 100-event 2024
  DY input. All 228 histogram contents, errors, entries and axes exactly matched
  the earlier baseline. The saved configuration explicitly enables reweighting
  and adds `DY_NLO_ZpTrw` once. This checks application plumbing, not fitted
  correction quality.
- **Statistical and physics: not assessed.** No full DATA/MC fit or acceptance
  study was run. Automatically applying a successful fit does not establish
  physics validity.
- **Reproducibility: passed for the bounded identity comparison and fixture
  resume tests.** Real scheduler completion/transfer, long-lived controller
  recovery and a complete two-pass production campaign remain unverified.

Black, Flake8 and CLI help passed for the changed Python sources. The controller
also reopened the earlier real smoke ROOT file and found all 228 nominal members.
No hash or checksum comparisons were used.

Installed LPC client source inspection established that `condor_submit` chooses
a scheduler and prints `Attempting to submit jobs to NAME`, while the history
wrapper requires `-name`. Queue/history now use that target from the existing
native receipt. The wrappers lack a shebang, so the controller invokes them
through argument-preserving Bash execution. A shell-wrapper regression test
checks that spaces and literal command-substitution text remain arguments.

Both native queue and history clients returned the expected two fixture job
records through the controller's JSON query code. Initial hand-written history
fixtures lacked the native offset/identity record delimiters and produced empty,
combined or malformed output. The corrected fixture uses the native record
format; the production query logic was not relaxed to accept malformed history.
These are file-backed client tests, not live scheduler queries or job completion.

Evidence is under
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/zpt-auto-20260910_164029/`:
`identity/` contains the compiled configuration and ROOT output; `identity.json`
is explicitly a synthetic identity formula fixture; `identity.log` and
`identity-comparison.txt` record the run and comparison. The `scheduler-fixture`
and `history-*` files retain the client-format investigation. The native identity
run used the existing smoke input, one DY component/file, systematics off,
`ZPT_APPLY_REWEIGHT=1`, the fixture JSON and `-c 1 -o 0 -b 0 -l 100`.

No Condor job was submitted, no remote output was written, and no full automated
DATA/MC campaign or real extraction fit was executed during this change.

## Named-run scripts, 2026-09-10

The script redesign was tested on `cmslpc-el9-heavy01.fnal.gov` with this
checkout's `start.sh` (Python 3.13.11, ROOT 6.38.00). It changes orchestration
and generated paths; the leaf physics sources and framework core are unchanged.

| Dimension | Status | Evidence and limits |
| --- | --- | --- |
| Software | passed | 28 focused tests; Bash syntax and CLI help; actual `smoke`, one-job preparation, local packaged worker, `merge`, `plot`, and unsubmitted `status` paths |
| Numerical | passed | All 228 histograms exactly match the earlier real-input result and the newly merged local-worker result, including entries, contents, errors and X-axis edges |
| Statistical | not assessed | Fit orchestration uses software fixtures in tests; no DATA fit or uncertainty calibration |
| Physics | not assessed | No new physics definitions, full DATA/MC campaign or source certification audit |
| Reproducibility | passed | The same fixed 100 events agree between interactive and packaged local execution; scheduler transfer, full campaigns and remote writes are outside this result |

From the framework checkout, the small software test command was:

```bash
source start.sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q PlotsConfigurationsRun3/ZpTreweighting/tests
```

The tests cover stale environment exports, full versus bounded presets,
one-pickle selection, run-directory mismatch, duplicate submission and submission
timeout handling, missing merge inputs, era-specific extraction keys, incomplete
fit output and the smoke plot selection. Submission and fitting are mocked:
these tests establish command/state handling, not scheduler or fit success.
Black and Flake8 passed on the new Python files; Bash syntax and wrapper help
also passed. No broad framework test suite was run for this analysis-local change.

Evidence is retained outside Git at
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/zpt-workflow-20260910_145450/`.
The following commands used that absolute directory as `EVIDENCE`; the ordinary
user workflow needs no such variable:

```bash
./run.sh --runs-dir "$EVIDENCE/runs" smoke local
./run.sh --runs-dir "$EVIDENCE/runs" plot local
./run.sh --runs-dir "$EVIDENCE/runs" merge batch
./run.sh --runs-dir "$EVIDENCE/runs" plot batch
./run.sh --runs-dir "$EVIDENCE/runs" status batch
```

The smoke command ran from `/tmp` using the absolute path to `run.sh`, with
deliberately stale `ZPT_SAMPLE=DATA`, `ZPT_LIMIT_FILES=999`, and
`ZPT_SYSTEMATICS=1`. Its compiled configuration retained only the fixed DY file
and no nuisances. The exact pickle is
`runs/local/configs/config_26-09-10_14_54_54.pkl`; `smoke.log` and `comparison.txt`
record the run and numerical comparison. There were 74 preselected events and
the same 46/20/8 ordinary dimuon jet-bin entries as the initial port.

As in the initial port below, batch preparation used the existing lean framework
snapshot to avoid another large-checkout recursive scan. After sourcing this
checkout's `start.sh`, the previous evidence directory's `framework-snapshot/`
was prepended to the inherited `PYTHONPATH`. The new script was invoked directly:

```bash
python /absolute/path/to/ZpTreweighting/workflow.py \
  --runs-dir "$EVIDENCE/runs" smoke batch --batch
```

This tested the new orchestration and external configuration with the unchanged
native package builder. It did not establish packaging speed in the full
development checkout. The pickle is
`runs/batch/configs/config_26-09-10_14_56_28.pkl`; the JDL and package are in
`runs/batch/condor/ZpTreweighting_2024_v15_batch/`. The JDL has one `DY_0` job
and the expected run-directory output remap. The archive contains 661 members,
including the calibration dependencies, with the proxy transferred separately.

The declared job inputs were copied to fresh `worker-scratch/`, and
`bash run.sh DY_0` ran there with no inherited `STARTPATH`, `PYTHONPATH` or
virtual environment and an initial `/usr/bin:/bin` PATH. After it completed,
its ROOT output was copied locally to the JDL's return destination. Thus the
subsequent `merge batch` exercised a real worker output, but **did not test
Condor transfer**. `worker.log`, `merge.log`, and the ROOT files retain this
evidence. All 228 merged histograms match the interactive output exactly.

The first plot call made native linear/log plots for all regions. ROOT reported
log-axis errors on this small DY-only population; those files and `plot.log`
are preserved. The smoke preset was then narrowed to linear `Zmm_0j/1j/2j`
plots. A fresh `plot batch` produced exactly those three PNGs; rendered 0j and
2j plots were inspected. `plot-batch.log` has no log-axis errors. Existing
PyROOT null-comparison deprecation warnings remain in the native plotter.

No hash or checksum comparisons were used for the script tests or output
comparisons. No Condor submission, remote stage-out, full-sample run,
2022/2023 live processing, systematic friends or real extraction fit was run.
The `status batch` command reported no recorded submission, as expected.
Task-created proxy copies were removed after the local worker test; the
original proxy was untouched. The retained dry-run JDL must be prepared again
with a current proxy before use. Generated runs, ROOT files and logs remain
outside the committed source.

## Initial LPC port, 2026-09-10

The bounded port validation uses framework revision
`6a1df5017113c464e8aef672eea6d533829a7687` on `cmslpc-el9-heavy01.fnal.gov`,
Python 3.13.11 and ROOT 6.38.00. On 2026-09-10:

| Dimension | Status | Evidence and scope |
| --- | --- | --- |
| Software | passed | Installer runtime check; 15 offline checks; all five configurations loaded with a discovery stub; real 2024 DY execution; generated one-job Condor dry-run and isolated local worker execution |
| Numerical | passed | 228 finite histograms in 12 regions; interactive and packaged worker bin contents, errors, entries and X-axis edges exactly equal on the same 100 events |
| Statistical | not assessed | No fit or uncertainty calibration executed |
| Physics | not assessed | No full DATA/MC comparison, certification/coverage or global duplicate audit; source-contract comparison preserves upstream definitions apart from the documented changes |
| Reproducibility | passed | Independent scratch execution of the same bounded input reproduces all histograms exactly; full campaigns and future mutable BTV recompiles remain outside this check |

The real input is the exact `DYto2Mu-2Jets_MLL-50__part0.root` URL now stored in `workflow.py` as `SMOKE_INPUT`. Of the first 100 entries, 74 passed preselections: the ordinary
`Zmm` 0j/1j/2j event histograms contain 46/20/8 entries, with weighted integrals
24.4389223063469 / 8.937465707484202 / 3.12376314239049. These are observed smoke
results, not expected production yields. Electron-channel histograms were empty.
The ROOT read reported unused EDM metadata dictionary warnings; no missing
analysis columns, JIT errors or non-finite histogram values were observed.

All 18 calibration files were reopened. The 2024 fake-rate adapter was also JIT-compiled and its
eight expected maps checked; that checks initialization, not fake-rate physics.
The source comparison executed both upstream and local configurations with
stubbed discovery, comparing samples, selections, binning, luminosities and
presentation. It is a software comparison, not a live full-input inventory.

The first dry-run from the large development checkout was bounded at 80 seconds;
a diagnostic retry reached 300 seconds while the **existing framework** was
recursively enumerating the source checkout (`runtime_package.py`,
`_iter_source_files`). Neither submitted a job. A lean snapshot of its unchanged
648 tracked package files plus the existing `utils/bin/hadd2` completed the
same native dry-run with this analysis as an external configuration. The first
snapshot invocation omitted the inherited CVMFS Python search path and could
not import ROOT; preserving that path fixed the validation environment.
No framework code or package mechanism was changed.

The inspected archive is 3,972,357 bytes with 661 members, including the selected
configuration, b-tag helpers, efficiency map and BTV JSON, and excluding proxy
credentials. The JDL contains one `DY_0` job and local ROOT return remapping.
The generated worker was then run with `/usr/bin:/bin` as its initial PATH,
no inherited `STARTPATH` or `PYTHONPATH`, and the archive/proxy transferred into
a fresh scratch directory. It sourced its configured LCG view and completed.
This tests local worker mechanics; **Condor scheduling/transfer and remote
stage-out were not executed**, nor were merge, plotting, extraction fits,
2022/2023 live inputs or systematic friend trees.

Evidence is retained outside the Git checkout at
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/zpt-lpc-tuaqp150/`:

- `configs-local/config_26-09-10_12_26_13.pkl`, `local.log` and the ROOT output
  under `local/` identify the interactive 100-event run.
- `batch.log` and `batch-retry.log` retain the bounded attempts/diagnostic;
  `snapshot.log` retains the isolated environment import failure.
- `configs-snapshot-runtime/config_26-09-10_12_38_37.pkl`,
  `snapshot-runtime.log` and `framework-snapshot/` identify the successful dry-run.
- `worker.log` and `worker-scratch/` retain the isolated worker and matching ROOT
  output. The native JDL/archive/manifest are under this leaf's ignored
  `condor/ZpTreweighting_2024_v15_zpt-lpc-tuaqp150_snapshot_runtime/` directory.

The interactive invocation used the smoke command with campaign
`zpt-lpc-tuaqp150_local`, `ZPT_OUTPUT=<evidence>/local` and
`-configs <evidence>/configs-local`. The successful dry-run used the same sample
settings, campaign `zpt-lpc-tuaqp150_snapshot_runtime`, output
`<evidence>/returned`, and `-configs <evidence>/configs-snapshot-runtime`, with
`-b 1 -dR 1 -l 100`. It invoked the unchanged framework entry point via
`python -c 'from mkShapesRDF.shapeAnalysis.mkShapesRDF import main; main()'`
from `framework-snapshot/`, prepending that directory to the supported runtime's
inherited `PYTHONPATH`. The worker command was `bash run.sh DY_0` in its fresh
scratch directory with the JDL's declared input files copied there.

Task-created proxy copies were removed after validation; the user's original
proxy was left untouched. The generated JDL is retained as evidence and must
be regenerated with a current proxy before submission. No jobs remain from
this task, because no scheduler submission occurred. Framework core and
pre-existing RunStability documentation changes were left unchanged; the new
family was committed in the initial port.

The small offline checks run with:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q PlotsConfigurationsRun3/ZpTreweighting/tests
```

No extra logging or manifest layer is added. Native compiled configs, Condor
stdout/stderr and the framework's package manifest provide the runtime record.
