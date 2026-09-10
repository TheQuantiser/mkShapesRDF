# Z-pT weight computation and application

This configuration computes DY Z-pT weights from DATA and MC histograms, then
reruns the event trees with those weights. Both passes can run automatically,
or you can stop after computation, edit the formulas, and start application
separately. **LPC and the 2024 jet-binned configuration are the defaults.**

```text
Pass 1: event trees → baseline histograms → fit → weights JSON
                                                   ↓ review / edit
Pass 2: same event trees + selected weights JSON → corrected histograms
```

## Start here: run one year

Use a checkout with the framework installed through its `./install.sh`, a valid
CMS proxy, and access to CERN EOS. On LPC, run from a login node with compatible
site Condor clients; see [LPC versus CERN](#lpc-versus-cern) if submission fails.

From the development workspace:

```bash
cd mkShapesRDF/PlotsConfigurationsRun3/ZpTreweighting
./run.sh auto zpt2024 --nominal-only --apply-fitted
```

That is the full sequence. `run.sh` activates the framework and supplies the
settings; no analysis environment exports are needed. **The command submits
Condor jobs.** Keep it running in a persistent terminal on the submit host.
Use a fresh campaign name for a new computation.

The controller performs:

1. Prepare and submit the baseline with the Z-pT correction disabled.
2. Wait for successful jobs and returned ROOT files, then merge and plot.
3. Subtract the configured backgrounds and fit the dimuon correction.
4. Prepare a second pass using the fitted JSON, submit it, then wait, merge
   and plot again.

`--nominal-only` uses every configured sample, file and event, with systematic
variations disabled. Omitting it enables the configured systematics.
`--apply-fitted` applies the fit without a review pause; a successful fit
execution does not establish that its model describes the data adequately.

For a small installation/I/O test before production:

```bash
./run.sh smoke local_test
./run.sh plot local_test
```

This reads the first 100 events of one fixed 2024 DY file, skips directory
listing, and produces three linear dimuon plots. It cannot determine weights.
`./run.sh smoke batch_test --batch` prepares the same one-job test for Condor;
`./run.sh submit batch_test` submits it.

## Stop to edit weights, or resume a campaign

Omit `--apply-fitted` to compute the weights and stop:

```bash
./run.sh auto zpt2024_review --nominal-only
```

Inspect the fit PDFs and edit the formula strings in
`runs/zpt2024_review/baseline/weights/dyZpTrw.json`, or make an edited copy.
For 2024, the keys are `2024_v15/LO_0j`, `LO_1j` and `LO_2j`.
Then continue with the selected JSON:

```bash
./run.sh auto zpt2024_review \
  --weights runs/zpt2024_review/baseline/weights/dyZpTrw.json
```

The formula variable `x` is evaluated as `gen_Zpt` in the DY event weight.
`--weights` adds that factor once; enabling it requires no `samples.py` edit.
**Preparation captures the formulas.** Later JSON edits cannot change an
already prepared pass. Use a new run name for another formula revision.
Bundled `dyZpTrw.json` files are upstream placeholders, not approved corrections.

If the controller stops, the submitted jobs continue. Rerun its original
`auto NAME` command from the same source checkout and site to resume; it uses
the saved configuration, recorded scheduler and existing jobs. It does not
submit a second copy. The default wait is 72 hours per pass, adjustable with
`--wait-hours`.

Held, removed or failed jobs, missing history or outputs, incomplete formulas,
and changed inputs between passes stop the controller. An empty queue alone
is not completion. Failed artifacts are preserved for diagnosis. Keep source
stable during a campaign, retain the original run paths, and resume while the
scheduler history is still available. An explicit `--weights` file can also
replace a failed or externally performed fit once baseline histograms exist.

## Find the outputs

For `auto NAME`, the two independent passes are under `runs/NAME/`:

| Output | Location |
| --- | --- |
| Baseline merged histograms | `baseline/rootFiles/mkShapes__ZpTreweighting_2024_v15_baseline.root` |
| Computed formulas | `baseline/weights/dyZpTrw.json` |
| Fit diagnostics | `baseline/weights/*.pdf` |
| Corrected merged histograms | `corrected/rootFiles/mkShapes__ZpTreweighting_2024_v15_corrected.root` |
| Before/after DATA–MC plots | `baseline/plots/` and `corrected/plots/` |
| Exact configurations, job files and logs | Each pass's `configs/` and `condor/` directories |

The ROOT names above are for the default era. Each standard 2024 pass contains
19 observables in 12 categories for 14 processes; `plot` draws `ptll`, with
linear and logarithmic versions. Fit-plot luminosity comes from the saved
configuration, and the event-axis label uses the actual histogram bin width.

The full nominal 2024 campaign executed on 2026-09-10 is retained locally at
`runs/zpt2024_20260910_1705_r2/`: both passes completed, with 2,788 successful
jobs each, two merged ROOT files, 48 comparison PNGs and the three fitted
formulas. For this campaign, use the relabeled fit PDFs in
`baseline/fit_plots/`; the original PDFs beside the JSON retain the old labels.
The corrected shapes improve below 50 GeV, but the 0- and 1-jet fits require
physics review. [The validation record](VALIDATION.md#full-nominal-2024-computation-and-application-2026-09-10)
gives the numerical comparisons, exact configurations and limitations.

To put generated runs elsewhere, place `--runs-dir /absolute/output/path`
before `auto` or any other command on every invocation. On a development tree
with large generated directories, use a source-only checkout and an external
run directory: the native runtime packager traverses the source checkout.

## LPC versus CERN

Choose `--era` and `--site` when starting a campaign. Resumed `auto` commands
inherit saved settings.

```bash
./run.sh auto zpt2022_cern --era 2022 --site cern --nominal-only --apply-fitted
```

| Setting | Supported choices |
| --- | --- |
| `--era` | `2022`, `2022-inclusive`, `2023`, `2024` (default), `2024-inclusive` |
| `--site` | `lpc` (default), `cern` |
| `--weights PATH` | Use selected formulas; mutually exclusive with `--apply-fitted` in `auto` |

| Concern | LPC | CERN |
| --- | --- | --- |
| Worker code | Native framework package extracted into worker scratch | Shared checkout visible to workers |
| Python/ROOT | Existing package shipping and CVMFS LCG setup; no worker installation | Checkout's `start.sh` |
| Discovery and event reads | `root://eoscms.cern.ch` | `root://eoscms.cern.ch` |
| Output return | Native Condor transfer to each pass's `rootFiles/` | Shared run directory |
| CMS proxy | Separate native transfer; CVMFS VOMS trust directory for validation | Separate native transfer |
| Optional native remote write endpoint | `root://cmseos.fnal.gov` | `root://eoscms.cern.ch` |

The scripts use returned ROOT files; they do not publish them to a remote EOS
output directory. Selecting LPC does not move the CERN inputs, and no CERN
`/eos` mount is assumed. The framework's `+JobFlavour` is a CERN attribute, not
an LPC runtime guarantee. Packaging, XRootD access, authentication and transfers
all use the existing framework mechanisms.

If LPC submission reports missing `classad2` or `htcondor2`, its site wrapper
and system Python bindings are mismatched. Installing packages in the analysis
environment cannot fix that wrapper. On 2026-09-10, `cmslpc374` had compatible
bindings; `cmslpc-el9-heavy01` did not. The LPC worker setup supplies the same
CVMFS VOMS trust directory as the established RunStability preset, before native
proxy validation. Queue/history queries use the scheduler in the submission
receipt and accept a successful empty response as zero records.

See the [framework Condor/I/O guide](../../docs/condor_remote_io.rst) and
[LPC batch documentation](https://www.uscms.org/uscms_at_work/computing/setup/batch_systems.shtml).

## Run the stages separately

These commands are useful when you already have weights or want direct control
over each stage. Run them from this configuration directory. `prepare` builds
jobs without submitting them; inspect the printed JDL and job population.

```bash
# Compute weights.
./run.sh prepare baseline --nominal-only
./run.sh submit baseline
./run.sh status baseline
# After successful jobs and returned outputs:
./run.sh merge baseline
./run.sh plot baseline
./run.sh extract baseline

# Apply the selected weights in a new histogram pass.
./run.sh prepare corrected --nominal-only \
  --weights runs/baseline/weights/dyZpTrw.json
./run.sh submit corrected
./run.sh status corrected
# After successful jobs and returned outputs:
./run.sh merge corrected
./run.sh plot corrected
```

These manual runs live at `runs/baseline/` and `runs/corrected/`. To inspect a
pass created by `auto`, point the command at its parent directory, for example:

```bash
./run.sh --runs-dir runs/zpt2024 status corrected
```

With existing compatible weights, skip the first block. Set matching era,
site and systematics options on both manual `prepare` commands; manual runs
do not inherit one another's settings. `extract` requires an unweighted full
baseline and runs locally. It fits the mm 0/1/2-jet regions, or only the
inclusive region for an inclusive leaf. It does not submit histogram jobs or
fit an additional correction from an already corrected pass.

New manual preparations need fresh names. Merge, plot and fit commands preserve
existing results rather than overwriting them. `./run.sh --help` lists commands.
There is no added hash-check, logging or manifest layer: state is held by native
pickles, submission receipts, normal job logs and outputs.

## Configuration and architecture map

```text
ZpTreweighting/
├── run.sh                  activate the framework; invoke workflow.py
├── workflow.py             CLI, named runs, submit/merge/plot/extract commands
├── automation.py           two-pass sequence, scheduler waits and resume checks
├── runtime.py              site presets, sample resolution, worker dependencies
├── finalize.py             align plot/model dictionaries with selected samples
├── data/                   shared fake-rate and b-tag calibration inputs
├── 2022_v12/               complete era leaves
├── 2022_v12_incl/
├── 2023_v12/
├── 2024_v15/               default leaf; files described below
├── 2024_v15_incl/
├── tests/                  focused software tests
└── runs/                   generated artifacts, ignored by Git
```

Each leaf is compiled in **one shared Python namespace**, in this order:

```text
configuration.py → runtime.py → samples.py → aliases.py → variables.py
  → cuts.py → plot.py → nuisances.py → structure.py → finalize.py
  → saved pickle → native RDataFrame runner → per-job ROOT files
  → native merge → mkPlot / extract_Zptrw.py
```

| To change… | Owning file |
| --- | --- |
| Formulas used for application | JSON passed to `--weights`, before preparation |
| Datasets, tree campaigns, nominal weights, files per job | Leaf `samples.py` |
| Objects, scale factors, derived quantities, DY correction expression | Leaf `aliases.py`; C++ helpers in `macros/` where present |
| Preselection and jet categories | Leaf `cuts.py`, with object definitions in `aliases.py` |
| Histogram expressions and binning | Leaf `variables.py` |
| Colors, groups and DATA/MC presentation | Leaf `plot.py` |
| Systematic variations | Leaf `nuisances.py` |
| Process roles for datacards/model consumers | Leaf `structure.py` |
| Luminosity, execution order and saved variables | Leaf `configuration.py` |
| Background subtraction, fit model and normalization | Leaf `extract_Zptrw.py` |
| Site endpoints and packaged dependencies | Shared `runtime.py` |
| Smoke input, command defaults and stage operations | Shared `workflow.py` |
| Automatic sequencing and scheduler handling | Shared `automation.py` |

Prepare a fresh run after changing source to update histogram jobs and saved
plot settings. Extraction reads the leaf's current `extract_Zptrw.py`; review
method changes before fitting an existing baseline. For CERN shared-checkout
jobs, keep both source and runtime stable until the jobs finish.

## Method and interpretation

This adapts [CodexForster's configuration](https://github.com/CodexForster/PlotsConfigurationsRun3/tree/482bac950792bf2056a414b8759576177ec0a282/ZpTreweighting)
and consumes processed event trees; it does not run `mkPostProc`.

The standard extraction normalizes DY to DATA minus the retained MC backgrounds
below 50 GeV, then fits their reconstructed `ptll` ratio with the inherited
error-function-plus-quadratic model. The formula is constant above 50 GeV and
is applied at generator Z pT, using reconstructed jet categories. The fitted
shape weights do not include the overall DATA/DY normalization factor. Inspect
both fit residuals and the new event-level histograms before accepting a result.

- The retained 2022/2024 subtraction omits the configured `Fake` histogram.
- Inclusive `0j` contains every jet multiplicity and overlaps `1j`/`2j`.
- Luminosities and selections are inherited; software completion does not audit
  certification coverage, global duplicate events or physics acceptance.
- The upstream 2023 `_OLD` MC directory was unavailable on 2026-09-10 and needs
  a reviewed input update before production.

[REFERENCE.md](REFERENCE.md) describes scientific definitions and native options.
[VALIDATION.md](VALIDATION.md) records executed workflows, output evidence and
limitations, including the full nominal 2024 campaign.
