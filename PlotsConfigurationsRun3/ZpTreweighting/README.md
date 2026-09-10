# Z-pT reweighting at FNAL LPC

Use `run.sh` for the complete workflow. It activates this checkout's installed
runtime, supplies the settings and keeps each named run in its own directory.
**Defaults: LPC, 2024, and no applied DY reweighting.** No manual environment
exports are needed. The scripts use the existing mkShapesRDF runner, XRootD
handling, Python/runtime shipping and Condor file transfer.

This is a port of [CodexForster's ZpTreweighting configuration](https://github.com/CodexForster/PlotsConfigurationsRun3/tree/482bac950792bf2056a414b8759576177ec0a282/ZpTreweighting).
It consumes processed event trees; it does not produce NanoAOD or run `mkPostProc`.

## Start with a small run

The framework must already be installed with `./install.sh` from the checkout
root. CERN EOS access also requires your normal CMS proxy. `run.sh` sources
`start.sh` automatically and leaves the calling shell unchanged.

```bash
cd mkShapesRDF/PlotsConfigurationsRun3/ZpTreweighting
./run.sh smoke
```

This processes **100 events from one fixed 2024 DY file**, with systematics and
DY reweighting off. It skips directory discovery and prints the output path.
The automatic run name contains the date and time. For a named run and plots:

```bash
./run.sh smoke local_test
./run.sh plot local_test
```

To prepare the same one-file, 100-event job for Condor:

```bash
./run.sh smoke batch_test --batch
```

Preparation creates the job files without submitting. Review the printed
`submit.jdl` and adjacent `run.sh`, then use `./run.sh submit batch_test` when
ready. A smoke run is a software check; it cannot supply a DATA/MC correction.

## Run the analysis

Use a new name for each campaign. These commands select the saved run by name:

```bash
./run.sh prepare baseline
./run.sh submit baseline
./run.sh status baseline
# After the jobs have completed and their outputs have returned:
./run.sh merge baseline
./run.sh plot baseline
```

- **prepare** resolves all configured samples and files, compiles the configuration,
  and generates the native Condor payload. Systematics are on by default. Review
  the JDL and input/job population before submission. This is a full preparation
  and can take time for discovery and runtime packaging.
- **submit** submits that prepared JDL once. It preserves the framework's normal
  submission receipt and stderr. It does not regenerate the job directory.
- **status** queries the recorded cluster with `condor_q` and `condor_history`.
  An empty queue alone does not mean success; inspect the per-job errors too.
- **merge** requires every expected returned ROOT file to be present and readable,
  then invokes the native merger and reopens its output.
- **plot** draws `ptll` using this run's saved configuration: DATA/MC ratio plots
  for a full run, or linear DY-only plots in the three dimuon regions for smoke.

To derive and then apply a correction:

```bash
./run.sh extract baseline
# Inspect the fitted plots and formulas in runs/baseline/weights/ first.
./run.sh prepare corrected --weights runs/baseline/weights/dyZpTrw.json
./run.sh submit corrected
```

`extract` runs the existing mm-channel fits for 0/1/2 jets (only 0 for an
inclusive configuration). It requires a full unweighted run and checks that
all requested formulas were written. Fit quality and the subtraction model
still need physics review. Bundled `dyZpTrw.json` files contain placeholders;
they are not approved corrections. The upstream 2022/2024 extractor does not
subtract the configured `Fake` histogram; see [the scientific reference](REFERENCE.md).

## Choose an era or site

Options belong on `prepare` (or `smoke --site ...`); subsequent commands use
the choice saved in the run.

```bash
./run.sh prepare run2022 --era 2022 --nominal-only
./run.sh prepare inclusive2024 --era 2024-inclusive
./run.sh prepare cern2024 --site cern
```

Supported era names are `2022`, `2022-inclusive`, `2023`, `2024` and
`2024-inclusive`. The upstream 2023 `_OLD` MC directory was unavailable on
2026-09-10, so that campaign needs a reviewed input update before production.
For inclusive leaves, the category named `0j` includes all jet multiplicities
and overlaps `1j`/`2j`. Luminosities and selections are inherited from upstream;
this port does not establish full dataset coverage or physics acceptance.

| Concern | LPC: `--site lpc` (default) | CERN: `--site cern` |
| --- | --- | --- |
| Worker software | Framework runtime package extracted in worker scratch | Shared checkout, visible to workers |
| Python and ROOT | Existing package shipping plus CVMFS LCG setup; no worker installation | Checkout's `start.sh` |
| Input discovery and reading | CERN EOS through `root://eoscms.cern.ch` | Same explicit XRootD endpoint |
| Output from these scripts | Condor returns ROOT files to `runs/NAME/rootFiles/` | ROOT files in the shared run directory |
| Optional native remote write endpoint | `root://cmseos.fnal.gov` | `root://eoscms.cern.ch` |
| CMS proxy | Existing separate proxy transfer | Existing separate proxy transfer |

Selecting LPC does not relocate the CERN datasets. No CERN `/eos` mount is
assumed. The framework's `+JobFlavour` setting is a CERN attribute, not an LPC
runtime guarantee. Details: [framework Condor/I/O guide](../../docs/condor_remote_io.rst)
and [LPC batch documentation](https://www.uscms.org/uscms_at_work/computing/setup/batch_systems.shtml).

## Configuration and architecture map

```text
ZpTreweighting/
├── run.sh                  activate the framework and call workflow.py
├── workflow.py             CLI defaults and named-run operations
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
| Samples, processed-tree campaign, nominal weights or files per job | The selected leaf's `samples.py` |
| Lepton/jet definitions, scale factors or DY correction application | `aliases.py`; nominal weight composition also lives in `samples.py` |
| Selection thresholds or jet regions | `cuts.py`, and the relevant definitions in `aliases.py` |
| Observable expressions, ranges or bin widths | `variables.py` |
| Plot grouping, labels or colors | `plot.py` |
| Systematics | `nuisances.py`; use `--nominal-only` to disable them for a run |
| Luminosity or configuration execution order | `configuration.py` |
| Fit function, subtraction or normalization method | `extract_Zptrw.py` |
| Default smoke file or command presets | `workflow.py` |
| Site I/O endpoints or declared worker dependencies | `runtime.py` |

Edit source, then prepare a **new run name**. A compiled pickle is a snapshot;
editing source does not update existing jobs or saved plot settings. Keep runs
at their original paths and, for CERN shared-checkout jobs, keep the source and
runtime stable until the jobs finish.
Extraction uses the selected leaf's current `extract_Zptrw.py`; review changes
to that method before fitting an existing run.

Run names cannot be reused. Existing merged outputs and plot/fit directories
are preserved; failed submissions are not automatically retried. There are
**no hash/checksum-based checks and no extra logging or manifest layer**.
The native pickle and normal framework/Condor artifacts hold the run state.
To store runs elsewhere, put `--runs-dir /absolute/path` before the command
on every invocation. `./run.sh --help` lists the commands.

For custom native options and scientific caveats, see [REFERENCE.md](REFERENCE.md).
Executed small tests and their limits are recorded in [VALIDATION.md](VALIDATION.md).
