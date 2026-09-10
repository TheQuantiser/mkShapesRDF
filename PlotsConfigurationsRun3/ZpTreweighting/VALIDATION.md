# Validation record

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
