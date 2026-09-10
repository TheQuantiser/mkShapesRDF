# Scientific definitions and advanced configuration

mkShapesRDF has two distinct pipelines. `mkPostProc` produces processed event
trees from NanoAOD. This analysis consumes those existing `Events` trees through
the shape-analysis pipeline; it does not run post-processing.

Each era directory is a complete configuration selected with `mkShapesRDF -f`.
The framework executes `configuration.py`, then its `filesToExec` in a shared
Python namespace, and saves the resolved configuration as a compressed pickle.
Here the execution order is:

1. `configuration.py` retains the upstream luminosity and file ordering and
   loads the family's `runtime.py` site/input settings.
2. `samples.py` declares the upstream processes, component datasets, nominal
   weights and DATA trigger precedence. It selects requested samples/components
   before calling the framework's file discovery.
3. `aliases.py` defines lepton requirements, generator Z pT, jet categories,
   correction helpers and optional DY reweighting.
4. `variables.py`, `cuts.py`, `plot.py`, `nuisances.py`, and `structure.py`
   define histograms, selections, presentation, uncertainties and process roles.
5. `finalize.py` restricts plot/model dictionaries to selected samples and applies
   the explicit systematics switch.

The native `RunAnalysis` builds ROOT RDataFrame graphs, applies aliases,
preselections and event weights, and books histograms. MC weights include the
configured luminosity in inverse femtobarns; DATA is not luminosity-scaled.
Outputs have paths such as `Zmm_0j/ptll/histo_DY`. Condor splits inputs using
`FilesPerJob`; `-o 2` merges those outputs. `extract_Zptrw.py` consumes merged
DATA and MC histograms to subtract backgrounds and fit a pT-dependent ratio.

| Directory | Upstream population / luminosity retained | Jet categories |
| --- | --- | --- |
| `2022_v12` | Summer22 and Run2022 C–D; 8.0 fb⁻¹ | 0, 1, ≥2 jets |
| `2022_v12_incl` | Same | `0j` means inclusive; 1j/2j also remain |
| `2023_v12` | Summer23 / Run2023 C `_OLD` products; 17.794 fb⁻¹ | 0, 1, ≥2 jets |
| `2024_v15` | Summer24 and Run2024 C–I; 109.08 fb⁻¹ | 0, 1, ≥2 jets |
| `2024_v15_incl` | Same | `0j` means inclusive; 1j/2j also remain |

The inclusive `0j` overlaps the other categories; do not add them together.
The configured luminosities are inherited denominators, not new luminosity
measurements or a certification/coverage audit. The 2023 `_OLD` MC directory
returned “No such file or directory” on 2026-09-10. Updating that campaign
requires checking its changed lepton/schema contract; the port does not
silently substitute newer trees.

## Advanced settings

These environment variables are for direct native framework use. `run.sh` clears inherited `ZPT_*` settings and supplies its own command options; do not combine the two interfaces.
`ZPT_RUN_DIR` and `ZPT_RUN_MODE` are wrapper-owned settings: they place generated
state under one run directory and record whether it is smoke or production in
the native pickle. Leave them unset for direct framework use.

| Setting | Meaning / default |
| --- | --- |
| `ZPT_SITE` | `lpc` or `cern`; default `lpc` |
| `ZPT_CAMPAIGN` | Tag suffix; default `nominal`; use a fresh explicit value for runs |
| `ZPT_OUTPUT` | Local path or complete XRootD destination; default local, per tag |
| `ZPT_SAMPLE` | One exact process key, e.g. `DY`, `DATA`, `Fake`; unset means all |
| `ZPT_DATASET` | One exact component of `ZPT_SAMPLE`; required with a pinned file |
| `ZPT_INPUT_FILE` | One explicit processed-tree URI/path for that component |
| `ZPT_LIMIT_FILES` | Per component: positive count or `-1`; upstream default 2 in 2022, all in 2023/2024 |
| `ZPT_FILES_PER_JOB` | Positive override; 0 keeps the upstream process setting |
| `ZPT_SYSTEMATICS` | `0` or `1`; default `1` retains upstream nuisances |
| `ZPT_TREE_BASE` | Base namespace for the same campaign/subdirectories; default CERN CMS `/store/group/phys_higgs/cmshww/amassiro/HWWNano` |
| `ZPT_APPLY_REWEIGHT` | `0` for derivation, `1` for application; default `0` |
| `ZPT_REWEIGHT_JSON` | Explicit reviewed fitted JSON required for application |

All active era entries in the bundled `dyZpTrw.json` files contain upstream
placeholder formulas. The 2022 and 2023 upstream samples enabled these by default;
this port deliberately disables application until a JSON is selected explicitly.
The alias name `DY_NLO_ZpTrw` and the 2022/2024 JSON key prefix `LO` are inherited
names; neither is evidence of the generator's perturbative order.

Use `./run.sh extract RUN` for the retained upstream fitting method. It fits the mm channel with `-f -n 2`, using jets 0/1/2 (only 0 for inclusive leaves). The JSON keys are `2022_v12/LO_*`, `2023/NLO_*`, and `2024_v15/LO_*`.

The extractor still follows the upstream fitting, normalization and background
subtraction choices; in particular, the 2022/2024 extractor does not subtract
the configured `Fake` histogram. No fit, uncertainty calibration or physics
acceptance is claimed by this port. The upstream `automate.py` (which edits
source and couples submission, waiting, fitting and rerunning) and the optional
mounted-path `twoDhists.cc` diagnostic are not included. Use the named-run commands in the README.

## Source changes and calibration ownership

The five leaves retain upstream sample catalogs, lepton working points, cuts,
histogram binning, luminosities, plot groups, nuisances and extraction methods,
apart from the explicit changes documented above. Jet-eta expressions now use
`Alt(CleanJet_pt, index, 0)` in their threshold guards so 0/1-jet events do not
index nonexistent jets; valid-index values are unchanged. Nuisance friend paths
are full XRootD URLs, and unused plot-group and nuisance sample keys (such as the separate `ggWW`
key when its files are already in `WW`) are removed.

`data/` contains 18 small ROOT calibration files (148,429 bytes total), copied
byte-for-byte from the same upstream revision's `utils/data/`: the selected
2022 PNet and 2024 UParT b-tag efficiency maps, plus the eight fake/prompt-rate
maps required by each era. They are source inputs, not generated output.
The aliases declare exact files through `condorRuntimeIncludes`; the fake-rate
constructor accepts those exact paths so the existing relocator can move them.
The b-tag helpers no longer dereference the unused `STARTPATH` environment
variable, and receive the BTV JSON path explicitly. Correctionlib initialization
uses its existing PyROOT binding. BTV JSONs are read from the upstream CVMFS
location at compilation/package preparation and included in the worker archive;
`latest` remains mutable for future recompiles. Retain the existing archive and
its built-in manifest to reproduce a batch result.

Upstream authorship, including the Danush Shekar attribution in the extraction
scripts, is preserved. No repository license file was present in the inspected
upstream tree; this port does not assign a new license to that source.

## Direct framework use

For custom input selection, another smoke era, different plot variables or remote stage-out, use the configuration directly with the settings above and the [framework I/O guide](../../docs/condor_remote_io.rst). The simple wrapper keeps outputs local and lets Condor return them. It does not expose every native option.

`auto` composes the same preparation, submission, merge, plot and extraction
functions. It stores no separate campaign manifest; the two native compiled
configurations and their normal artifacts identify progress. A file lock prevents
two controllers from advancing the same campaign concurrently. Before applying
weights it compares the resolved input lists, base weights, cuts, variables,
nuisances, luminosity and aliases, allowing the intended DY factor to change.
These are direct comparisons of configuration values, not hash checks.

For completion, the queue must be empty and history must contain every submitted
job with `JobStatus=4`, `ExitCode=0`, and `ExitBySignal=false`; see the
[HTCondor job attribute definitions](https://htcondor.readthedocs.io/en/24.x/classad-attributes/job-classad-attributes.html).
Returned ROOT files must also be readable. The LPC client selects a scheduler
at submission and reports it in stdout. The controller takes that name from the
native receipt and passes `-name` to both queue and history queries. It clears
`FERMIHTC_SCHEDD_OVERRIDE` only in those child processes so a later shell setting
cannot redirect a recorded campaign. CERN uses the original submit context.
Scheduler history expiration prevents automatic proof of completion; inspect
and manage such old campaigns with the individual native steps.

Keep one exact compiled pickle for the campaign and pass it with `-config` for native status/merge operations. Native batch execution regenerates the job directory; never regenerate one with active jobs. `mkPlot` reads `./configs`, so run it where that directory contains only the intended pickle. For the wrapper, that is `runs/RUN/`.
