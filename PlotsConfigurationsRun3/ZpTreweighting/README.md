# Computing and applying Z-pT weights

This configuration supports **two separate passes**: compute a DY Z-pT
correction, then rerun the histograms using your reviewed or edited formulas.
You can stop between the passes or supply an existing correction JSON.

```text
Pass 1: event trees → baseline histograms → fitted correction JSON
                                             ↓ inspect / edit formulas
Pass 2: event trees + selected correction JSON → corrected histograms
```

Use `run.sh` for each step. It activates the installed framework, supplies the
settings and selects saved runs by name. **LPC and 2024 are the defaults.**
No manual environment exports are needed. The existing mkShapesRDF runner,
XRootD handling, runtime packaging and Condor transfers do the processing.

## Setup and a small test

The framework must already be installed using `./install.sh` from the
mkShapesRDF checkout root, and CERN EOS access needs your normal CMS proxy.
From the development workspace:

```bash
cd mkShapesRDF/PlotsConfigurationsRun3/ZpTreweighting
./run.sh smoke local_test
./run.sh plot local_test
```

All remaining commands run from this directory. `run.sh` sources `start.sh`
automatically. The smoke test processes **100 events from one fixed 2024 DY
file**, with systematics and the Z-pT correction off, and draws three dimuon
plots. It skips directory discovery. It is a software test, not a sample from
which to derive the correction.

For a one-job Condor preparation, use `./run.sh smoke batch_test --batch`.
This generates job files without submitting them; `./run.sh submit batch_test`
is the separate submission command. Use a fresh name for every new run.

## Automate the sequence

To run both passes without a pause for formula editing:

```bash
./run.sh auto zpt2024 --nominal-only --apply-fitted
```

This command **submits jobs**. It prepares the baseline, submits and waits for
its jobs, merges and plots the returned histograms, extracts the correction,
then prepares, submits, waits for, merges and plots the corrected pass. The
fitted JSON supplies the formulas directly; it does not edit analysis source.
Successful extraction is a software requirement, not a physics review of the fit.

To pause after computing the weights, omit `--apply-fitted`:

```bash
./run.sh auto zpt2024_review --nominal-only
# Inspect/edit runs/zpt2024_review/baseline/weights/dyZpTrw.json, then resume:
./run.sh auto zpt2024_review \
  --weights runs/zpt2024_review/baseline/weights/dyZpTrw.json
```

Automatic runs keep two independent configurations under
`runs/NAME/baseline/` and `runs/NAME/corrected/`. A resumed `auto NAME` loads the
saved settings and continues the existing jobs; it does not submit them twice.
Use `--era` and `--site` on the first invocation when changing the defaults.
An explicit `--weights` JSON can also replace a failed or externally performed
extraction once the baseline histograms are available.

Keep the controller running on the submit host, for example in an existing
persistent terminal session. If it stops, submitted jobs continue; rerun the
same `auto NAME` command to resume. By default it waits up to 72 hours per
histogram pass; change that with `--wait-hours`. It prints scheduler progress
when the state changes and stops on held/removed/failed jobs, missing outputs,
incomplete formulas or changes to the input list or analysis between passes.

On LPC, queries target the scheduler named in the native submission receipt.
Resume from the original site while its scheduler history remains available.
Existing merged histograms and plots are reopened before reuse. Incomplete
preparation, merge, plot or fit artifacts are preserved for diagnosis, and are
not automatically overwritten. Keep source stable during an automatic campaign;
use a new campaign name for changes to an already prepared correction.

The individual commands below remain available when you want to run each step
yourself. Their run directories are `runs/baseline/` and `runs/corrected/`,
independent of the nested directories used by `auto`.

## Pass 1 — compute the correction

First produce histograms for DATA, DY and the configured backgrounds, with
the Z-pT correction disabled. Normal event weights, scale factors and luminosity
normalization remain active.

```bash
./run.sh prepare baseline --nominal-only
# Review the printed submit.jdl and job population before submitting.
./run.sh submit baseline
./run.sh status baseline
```

`prepare` resolves all configured samples and files and builds the Condor
payload. `--nominal-only` omits systematic variations for this first nominal
comparison; omitting that option enables the configured systematics. It does
not limit samples or events. Discovery and packaging can take time.

After the jobs finish, inspect their errors and ensure the ROOT files have
returned. An empty queue alone does not establish success. Then:

```bash
./run.sh merge baseline
./run.sh plot baseline
./run.sh extract baseline
```

`plot` draws the baseline `ptll` DATA/MC comparisons. `extract` separately reads
the merged histograms, performs the existing background subtraction and fits,
and writes fit plots under `runs/baseline/weights/`. The formula file is:

```text
runs/baseline/weights/dyZpTrw.json
```

Extraction runs locally and does not submit another histogram campaign. It
fits the mm channel in 0/1/2-jet categories, or only the inclusive category for
an inclusive configuration. It requires a full run without an applied Z-pT
correction and checks that all requested formulas were written.

## Pass 2 — edit the formulas and recompute histograms

**Inspect the fits and edit the formula strings before preparing the next run.**
For the default 2024 configuration, edit `LO_0j`, `LO_1j` and `LO_2j` under
the `2024_v15` key in the extracted JSON. Keep the JSON keys and ROOT/C++ formula
syntax; the formula variable `x` is evaluated as `gen_Zpt` when applied to DY.
You can edit the JSON directly or pass an edited copy.

If the derivation method itself needs changing, edit the selected leaf's
`extract_Zptrw.py`; it owns the fit function, subtraction and normalization.
If you already have compatible formulas, skip Pass 1 and supply that JSON here.
Bundled leaf `dyZpTrw.json` files contain placeholders, not approved corrections.

```bash
./run.sh prepare corrected --nominal-only \
  --weights runs/baseline/weights/dyZpTrw.json
# Review the prepared jobs, then submit this separate histogram pass.
./run.sh submit corrected
./run.sh status corrected
```

After the corrected jobs finish and their outputs return:

```bash
./run.sh merge corrected
./run.sh plot corrected
```

`--weights` reads the selected JSON and includes its Z-pT factor once in the DY
event weight. No manual change to `samples.py` is needed to enable it. This
pass rereads the event trees and fills new histograms for the full configured
sample set; the additional correction affects DY. Baseline and corrected
outputs remain separate under `runs/baseline/` and `runs/corrected/`.

**Preparation captures the formulas in the saved configuration.** Editing the
JSON afterward does not update prepared or submitted jobs. For another formula
revision, prepare a fresh name such as `corrected_v2` with the edited JSON.
The wrapper's `extract` command is for the baseline pass; it does not fit an
additional correction from a run that already applied Z-pT weights.

## Other eras and LPC versus CERN

Set `--era` and `--site` on each new `prepare` command. Status, merge, plotting
and extraction then use that run's saved settings. **Use matching era, site and
systematics options in both passes**; a new `prepare` does not inherit options
from the run that produced the JSON.

| Option | Choices / behavior |
| --- | --- |
| `--era` | `2022`, `2022-inclusive`, `2023`, `2024` (default), `2024-inclusive` |
| `--site` | `lpc` (default) or `cern`; also accepted by `smoke` |
| `--nominal-only` | Omit systematic variations; used in both walkthrough passes above |
| `--weights PATH` | Apply the selected correction JSON; omit for the baseline pass |

For example, begin a nominal CERN 2022 pass with
`./run.sh prepare baseline2022 --era 2022 --site cern --nominal-only`.

| Concern | LPC: `--site lpc` (default) | CERN: `--site cern` |
| --- | --- | --- |
| Worker software | Framework runtime package extracted in worker scratch | Shared checkout, visible to workers |
| Python and ROOT | Existing package shipping plus CVMFS LCG setup; no worker installation | Checkout's `start.sh` |
| Input discovery and reading | CERN EOS through `root://eoscms.cern.ch` | Same explicit XRootD endpoint |
| Output from these scripts | Condor returns ROOT files to `runs/NAME/rootFiles/` | ROOT files in the shared run directory |
| Optional native remote write endpoint | `root://cmseos.fnal.gov` | `root://eoscms.cern.ch` |
| CMS proxy | Existing separate proxy transfer; CVMFS VOMS trust directory for worker validation | Existing separate proxy transfer |

Selecting LPC does not relocate the CERN datasets. No CERN `/eos` mount is
assumed. The framework's `+JobFlavour` setting is a CERN attribute, not an LPC
runtime guarantee. Details: [framework Condor/I/O guide](../../docs/condor_remote_io.rst)
and [LPC batch documentation](https://www.uscms.org/uscms_at_work/computing/setup/batch_systems.shtml).

Use an LPC login node with a compatible site Condor installation. If submission
reports a missing `classad2` or `htcondor2`, the site wrapper and system Python
bindings are mismatched; installing packages in the analysis environment cannot
fix that wrapper. On 2026-09-10, `cmslpc374` had compatible bindings while
`cmslpc-el9-heavy01` did not. The worker preset uses the same CVMFS VOMS trust
directory as the existing RunStability LPC configuration, before the framework
checks the separately transferred proxy.

## Saved runs and command behavior

| Command | Result |
| --- | --- |
| `auto NAME` | Run/resume the sequence, pausing for formula review by default; `--apply-fitted` enables both passes without a pause |
| `prepare NAME` | Compile one configuration and generate the native Condor payload; no submission |
| `submit NAME` | Submit the prepared JDL once, preserving the native receipt and stderr |
| `status NAME` | Query the recorded cluster with `condor_q` and `condor_history` |
| `merge NAME` | Require all expected returned ROOT files to be readable, merge them, and reopen the result |
| `plot NAME` | Draw `ptll` using that run's saved configuration |
| `extract NAME` | Fit corrections from a baseline run and write its weights JSON |

New manual runs need fresh names; `auto` reuses its name to resume. Existing
merged outputs and plot/fit directories are preserved, and failed submissions
are not automatically retried. Keep runs
at their original paths. To store them elsewhere, put `--runs-dir /absolute/path`
before the command on every invocation. `./run.sh --help` lists the options.

There are **no hash/checksum-based checks and no extra logging or manifest
layer** in these scripts. The native pickle and normal framework/Condor
artifacts hold the run state.

## Configuration and architecture map

```text
ZpTreweighting/
├── run.sh                  activate the framework and call workflow.py
├── workflow.py             CLI defaults and named-run operations
├── automation.py           two-pass controller, scheduler waits and resume checks
├── runtime.py              site settings, sample selection, payload declarations
├── finalize.py             restrict plot/model dictionaries to selected samples
├── data/                   shared fake-rate and b-tag calibration inputs
├── 2022_v12/               complete era configurations
├── 2022_v12_incl/
├── 2023_v12/
├── 2024_v15/               default leaf; each leaf has the files below
│   ├── configuration.py    luminosity, execution order, serialized variables
│   ├── samples.py          datasets, tree directories, weights, job splitting
│   ├── aliases.py          objects, derived quantities, correction expressions
│   ├── cuts.py             preselection and event categories
│   ├── variables.py        observables and histogram binning
│   ├── plot.py             groups, colors, labels, DATA/MC presentation
│   ├── nuisances.py        systematic variations and their sample mappings
│   ├── structure.py        process roles for model/datacard consumers
│   ├── dyZpTrw.json         upstream reference formulas
│   ├── extract_Zptrw.py    background subtraction, normalization and fitting
│   └── macros/             era-specific C++ helpers, where needed
├── 2024_v15_incl/
├── tests/                  small software tests
└── runs/NAME/              generated state, ignored by Git
    ├── configs/            exactly one native compiled pickle, plus config.json
    ├── condor/TAG/         native JDL, scripts, package, submission receipt, job logs
    ├── rootFiles/          returned job files and merged ROOT output
    ├── plots/              ptll PNGs
    └── weights/            extracted JSON and fit plots
```

For `auto`, the same run layout appears twice: under `runs/NAME/baseline/`
and `runs/NAME/corrected/`.

The execution order is part of the interface. The framework runs these files
in **one shared Python namespace**:

```text
configuration.py → runtime.py → samples.py → aliases.py → variables.py
  → cuts.py → plot.py → nuisances.py → structure.py → finalize.py
  → compiled pickle → native RDataFrame runner → ROOT histograms
  → native merge → mkPlot / extract_Zptrw.py
```

| To change… | Edit… |
| --- | --- |
| The correction formulas used in the second pass | The JSON passed to `--weights`, before preparation |
| Samples, processed-tree campaign, nominal weights or files per job | The selected leaf's `samples.py` |
| Lepton/jet definitions, scale factors or DY correction application | `aliases.py`; nominal weight composition also lives in `samples.py` |
| Selection thresholds or jet regions | `cuts.py`, and the relevant definitions in `aliases.py` |
| Observable expressions, ranges or bin widths | `variables.py` |
| Plot grouping, labels or colors | `plot.py` |
| Systematics | `nuisances.py`; use `--nominal-only` to disable them for a run |
| Luminosity or configuration execution order | `configuration.py` |
| Fit function, subtraction or normalization method | `extract_Zptrw.py` |
| Default smoke file or command presets | `workflow.py` |
| Automatic stage order, scheduler waiting or resume behavior | `automation.py` |
| Site I/O endpoints or declared worker dependencies | `runtime.py` |

Source changes require a fresh preparation to affect histogram jobs and saved
plot settings. For CERN shared-checkout jobs, keep source and runtime stable
until the jobs finish. Extraction uses the leaf's current `extract_Zptrw.py`;
review changes to that method before fitting an existing baseline run.

## Analysis notes and further reading

This adapts [CodexForster's ZpTreweighting configuration](https://github.com/CodexForster/PlotsConfigurationsRun3/tree/482bac950792bf2056a414b8759576177ec0a282/ZpTreweighting)
and consumes processed event trees; it does not run `mkPostProc`.

- The upstream 2023 `_OLD` MC directory was unavailable on 2026-09-10 and needs
  a reviewed input update before production.
- In inclusive leaves, `0j` includes all jet multiplicities and overlaps
  `1j`/`2j`; do not add those categories together.
- The retained 2022/2024 extractor does not subtract the configured `Fake`
  histogram. Review that method choice and fit quality before applying weights.
- Luminosities and selections are inherited. The bounded software tests do not
  establish full dataset coverage, fit validity or physics acceptance.

[REFERENCE.md](REFERENCE.md) covers scientific definitions and direct native
framework options. [VALIDATION.md](VALIDATION.md) records the executed small
tests and their limits.
