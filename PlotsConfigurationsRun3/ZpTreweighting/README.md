# Z-pT reweighting on LPC and CERN

This family adapts [CodexForster/PlotsConfigurationsRun3/ZpTreweighting](https://github.com/CodexForster/PlotsConfigurationsRun3/tree/482bac950792bf2056a414b8759576177ec0a282/ZpTreweighting)
at commit `482bac950792bf2056a414b8759576177ec0a282` for this mkShapesRDF checkout.
LPC is the default site. It uses the **existing framework implementation** of
`SearchFiles`, remote I/O, packaged Condor execution, path relocation, proxy
transfer and output return. There is no new runner, package builder, storage
client, submission service or campaign manifest system.

## How the configuration works

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

## LPC versus CERN

| Concern | `ZPT_SITE=lpc` (default) | `ZPT_SITE=cern` |
| --- | --- | --- |
| Submit/login host | LPC; checkout may be under `/uscms_data` | LXPLUS; shared checkout must be worker-visible |
| Worker software | Existing `condorRuntimePackage=True`; extracted in worker scratch | Existing shared-checkout mode; sources `STARTPATH` |
| Worker runtime | CVMFS LCG 109, EL9, GCC 13; no worker pip/install | Runtime selected by the checkout's `start.sh` |
| Input discovery and reading | CERN EOS via `root://eoscms.cern.ch` | Same explicit XRootD endpoint |
| Default output | Local `rootFiles/<tag>`; batch files returned by Condor | Local `rootFiles/<tag>` on the shared checkout |
| Optional remote write endpoint | `root://cmseos.fnal.gov` | `root://eoscms.cern.ch` |
| Authentication | Existing separately transferred CMS proxy | Same explicit proxy transfer |

Changing execution site does **not** move these CERN-owned inputs to FNAL.
An LPC `/eos` spelling is not a CERN mount. LPC workers cannot read the submit
host's `/uscms_data` directly; the framework package and transfer mechanisms
already address this. See the [framework I/O guide](../../docs/condor_remote_io.rst),
[LPC batch documentation](https://www.uscms.org/uscms_at_work/computing/setup/batch_systems.shtml),
and [LPC EOS documentation](https://www.uscms.org/uscms_at_work/computing/LPC/usingEOSAtLPC.shtml).

Set `MKSHAPESRDF_LCG_VIEW` before compilation only if the installation also uses
that compatible alternate view. Framework CLI I/O options override the
configuration, for example `--input-access-mode stage-in`,
`--xrd-discovery-endpoint`, `--xrd-read-endpoint`, and `--output-folder`.

## Setup and one-file smoke run

From the **framework checkout**, use its installed environment:

```bash
./install.sh --check
source start.sh
voms-proxy-info -timeleft
# If needed, obtain a CMS proxy using the site's normal voms-proxy-init procedure.

export ZPT_SITE=lpc
export ZPT_CAMPAIGN="smoke_$(date +%Y%m%d_%H%M%S)"
export ZPT_SAMPLE=DY
export ZPT_DATASET=DYto2Mu-2Jets_MLL-50
export ZPT_LIMIT_FILES=1
export ZPT_FILES_PER_JOB=1
export ZPT_SYSTEMATICS=0
export ZPT_APPLY_REWEIGHT=0
export ZPT_INPUT_FILE='root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/nanoLatino_DYto2Mu-2Jets_MLL-50__part0.root'

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZpTreweighting/2024_v15 -l 100
```

The explicit file was discovered and read on LPC during this port. It bypasses
directory discovery. Without `ZPT_INPUT_FILE`, the selected component is found
using `SearchFiles`; file limits apply after one directory listing. `-l` alone
does not limit discovery, files or jobs. The reduced MC population is only a
software check and cannot supply a measured DATA/MC correction.

## Condor preparation and production

With the same bounded sample settings, choose a fresh campaign and dry-run:

```bash
export ZPT_CAMPAIGN="batch_smoke_$(date +%Y%m%d_%H%M%S)"
mkShapesRDF -c 1 -o 0 -b 1 -dR 1 \
  -f PlotsConfigurationsRun3/ZpTreweighting/2024_v15 -l 100
```

Inspect `2024_v15/condor/<tag>/submit.jdl`, `run.sh`, the one job's `script.py`,
and the framework-generated runtime archive/manifest. For LPC, confirm scratch
extraction, separately transferred proxy, calibration inputs, and ROOT output
remapping. The framework emits a CERN `+JobFlavour` attribute; it is not an LPC
runtime guarantee. Use the current LPC scheduler policy when planning resources.

Compilation produces a timestamped `configs/config_*.pkl`. Record that exact
path and use `-config /absolute/path/to/config_TIMESTAMP.pkl` with `-c 0` for
submission, status (`-o 1`) and merge (`-o 2`). To submit after reviewing the
dry-run, rerun with the exact pickle and `-dR 0`; submission was not performed
as part of this port. The framework regenerates its batch directory on that
operation. Never regenerate a tag whose jobs are active.

For a full campaign, first unset `ZPT_SAMPLE`, `ZPT_DATASET`, `ZPT_INPUT_FILE`
and set `ZPT_LIMIT_FILES=-1`; restore the intended `ZPT_SYSTEMATICS` and choose
a fresh campaign before compiling. File/component completeness and systematic
friend-tree availability must be established for that campaign. An empty
discovery result is an error rather than an omitted process. Preserve the exact
pickle used by the jobs; do not manage production using an ambiguous `latest`.

For large remote outputs, set an explicit destination before compilation:

```bash
export FNAL_USER=your_fnal_username
export ZPT_OUTPUT="root://cmseos.fnal.gov//store/user/${FNAL_USER}/ZpTreweighting/${ZPT_CAMPAIGN}/2024_v15"
```

That enables the existing framework stage-out and disables duplicate Condor ROOT
return. The default remote existing-output policy is `fail`. Remote writes
were not tested here. Use a new campaign identity for local reruns as well;
local output creation is not protected by the remote overwrite policy.

## Settings and deriving weights

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

The original extraction scripts are retained for method compatibility. After
a complete unweighted DATA+background+DY campaign has been merged and inspected,
run the selected leaf's extractor in a fresh result directory. For example,
with absolute shell variables `leaf`, `merged`, and `result` pointing to the
2024 leaf, its verified merged ROOT file, and a new result directory:

```bash
mkdir "$result"
cd "$result"
for njet in 0 1 2; do
  python "$leaf/extract_Zptrw.py" -f -n 2 -c mm -nj "$njet" \
    --input "$merged" --write-json "$result/dyZpTrw.json" \
    --year 2024_v15 --sample-type LO
done
```

Use `--year 2022_v12 --sample-type LO` for 2022, and
`--year 2023 --sample-type NLO` for 2023. For an inclusive leaf, derive only
`-nj 0`. Inspect fit convergence, plots and the populated JSON entries before
setting `ZPT_APPLY_REWEIGHT=1` and `ZPT_REWEIGHT_JSON` to that result and compiling
a **new** campaign. The native runner applies the selected DY alias once.
Formula values are compiled into the pickle.

The extractor still follows the upstream fitting, normalization and background
subtraction choices; in particular, the 2022/2024 extractor does not subtract
the configured `Fake` histogram. No fit, uncertainty calibration or physics
acceptance is claimed by this port. The upstream `automate.py` (which edits
source and couples submission, waiting, fitting and rerunning) and the optional
mounted-path `twoDhists.cc` diagnostic are not included. Use the explicit native
framework steps above.

`mkPlot` in this checkout reads `./configs` using its latest pickle. Run it in
a directory whose `configs` contains only the intended compiled campaign;
`--inputFile` selects a ROOT file, not a configuration. This avoids mixing a
smoke configuration with production plots. `--onlyVariable ptll --onlyPlot
cratio --fileFormats png` is the upstream-style ratio plot selection.

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

## Validation

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

The real input is the exact `DYto2Mu-2Jets_MLL-50__part0.root` URL in the smoke
command above. Of the first 100 entries, 74 passed preselections: the ordinary
`Zmm` 0j/1j/2j event histograms contain 46/20/8 entries, with weighted integrals
24.4389223063469 / 8.937465707484202 / 3.12376314239049. These are observed smoke
results, not expected production yields. Electron-channel histograms were empty.
The ROOT read reported unused EDM metadata dictionary warnings; no missing
analysis columns, JIT errors or non-finite histogram values were observed.

All 18 calibration files were reopened, and their Git blob hashes match the
pinned upstream tree. The 2024 fake-rate adapter was also JIT-compiled and its
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
family is uncommitted.

The small offline checks run with:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q PlotsConfigurationsRun3/ZpTreweighting/tests
```

No extra logging or manifest layer is added. Native compiled configs, Condor
stdout/stderr and the framework's package manifest provide the runtime record.
