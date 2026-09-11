# Run-3 ZH four-lepton analysis family

`ZH4l` contains the shared Run-3 four-lepton object and correction contract
and four independent mkShapesRDF leaves:

- `ZZCR/` — nominal four-lepton ZZ control and ZH signal-region production;
- `Pairing/` — comparison of nominal and alternative Z/X pairing algorithms;
- `Closure/` — the DY-to-ZZ selection, trigger, flavor, and weight closure
  ladder found in the working tree when the migration began.
- `Example/` — a small runnable configuration demonstrating distinct Z/X WPs,
  composed weights, inherited regions, vector histograms and event trees.

The leaves never import one another.  They consume the one authoritative
implementation in `common/`.  `ZH_4lMET/` remains the production compatibility authority until an explicit
cutover. ZH4l development does not retire it.

## Where things are

| Question | Owner |
|---|---|
| Inputs, logical processes, stitching | `common/eras.json`, `common/catalog.py`, then each leaf's `samples.py` |
| Flexible sources, views, candidates and weight recipes | `common/definitions.py`, `common/presets.py`, `common/selections.py` |
| Complete nominal Z/X preset | `common/objects.py`, `common/macros/objects.cc` |
| Common kinematics and binnings | `common/observables.py` |
| Lepton/trigger/b-veto weights | `common/corrections.py` and `common/macros/` |
| Physical regions | `<leaf>/cuts.py` |
| Histograms and selected event trees | `<leaf>/variables.py`, `common/outputs.py`, `common/runner.py` |
| Process display/bookkeeping | `common/presentation.py`, `<leaf>/plot.py`, `<leaf>/structure.py` |
| Uncertainties | `<leaf>/nuisances.py` |
| Site and batch settings | `common/runtime.py`, `env/` |

## Setup and quick start

For a complete example of the flexible toolkit, start with
[Example/README.md](Example/README.md) and [Example/analysis.py](Example/analysis.py).
It pins one real 2024 ZZ file and one ZH file, supports every nominal output
mode, and provides a bounded run plus histogram/tree verification commands.

Run from the repository root. `ERA` is the preferred selector; supported
values are `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`. `YEAR` is accepted
only as a checked compatibility alias. Conflicting `ERA` and `YEAR` values
fail immediately.

```bash
source start.sh
source PlotsConfigurationsRun3/ZH4l/env/lxplus.sh   # or fnal.sh

export ERA=2024
export SAMPLE_FILTER=ZZ
export LIMIT_FILES_PER_SAMPLE=1
export ENABLE_SYSTEMATICS=0
export ZH4L_CAMPAIGN=zzcr_smoke

mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH4l/ZZCR -l 100
```

Use `ENABLE_SYSTEMATICS=1` for the full ZZCR nuisance model. `SAMPLE_PROFILE`
has two documented scopes:

- `full` (default): every configured signal/background process plus `DATA`;
- `quick`: the bounded DY+ZZ+DATA scope for compilation and smoke tests.

The old names `presentation` and `commissioning` remain compatibility aliases
for `full` and `quick`. `SAMPLE_FILTER` is an exact comma-separated override,
so the quick-start command runs only `ZZ`. Generated `configs/`, `condor/`,
`rootFiles/`, plots, caches, and rendered reports are ignored.

For the studies:

```bash
PlotsConfigurationsRun3/ZH4l/Pairing/run_all_eras.sh pilot
PlotsConfigurationsRun3/ZH4l/Closure/run_all_eras.sh compile
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the supported API and a compact
Z-only configuration example, [NAMING.md](NAMING.md) for the naming contract, the leaf
READMEs for analysis commands, [ARCHITECTURE_AUDIT.md](ARCHITECTURE_AUDIT.md)
for the reuse decision record, and [MIGRATION_REPORT.md](MIGRATION_REPORT.md)
for validation evidence and limitations.

## Event trees and verification

Set `ZH4L_OUTPUT_MODE=trees` or `both` before compiling a leaf. ZZCR tree
output requires `ENABLE_SYSTEMATICS=0`; Pairing and Closure are nominal
studies. The default remains `histograms`. Trees appear at
`trees/<region>/<sample>/Events` and retain event/source identity, selected
object information and the actual total output weight. Pairing keeps candidate
information in vectors on each event row. Branch groups and explicit additions
are configured in each leaf's `variables.py`.

The naming migration changes derived columns and histogram keys to lower-case
snake_case (`z_mass`, `zx_mass`, `sf_lepton_zx`, for example). Recompile before
running; existing pickles and outputs keep their old schema. Upstream branches,
sample names and established region labels retain their original spelling.

Run the focused suite from the framework checkout after sourcing `start.sh`:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  python -m pytest -q -p no:cacheprovider PlotsConfigurationsRun3/ZH4l
```

The plugin override avoids unrelated site-wide pytest plugins. The tests
include synthetic ROOT mechanics and preserved compatibility oracles. A real
input smoke is still needed for source/schema and physics-domain claims.
No new persistent validation logs or manifest system is required.

### Bounded implementation checks, 2026-09-10

On `cmslpc-el9-heavy01.fnal.gov`, the supported runtime used Python 3.13.11
and ROOT 6.38.00 (LCG 109). All three leaves executed freshly materialized
nominal configurations in `both` mode over entries 0–99 of this processed
2024 signal file:

```text
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/nanoLatino_ZH_Zto2L_Hto2Wto2L2Nu_M125__part0.root
```

The checks used `ConfigLib.loadConfig`, its ordinary serialized dictionaries,
and the selected `RunAnalysis` adapter with one pinned file and `limit=100`.
ZZCR tree refills reproduced Z-mass bins/errors. A fresh Closure pickle/run
reproduced all 48 booked Z-pT projections from its trees, including errors;
36 of 54 regions were populated (443 rows across overlapping regions).
The flexible preset matched the established preset's selected indices on all
100 events and its lepton/trigger/b-veto corrections on seven valid
veto-passing events, with relative/absolute numerical tolerance 1e-6.
The source's signed 64-bit event type was retained; separate synthetic tests
cover unsigned identities above 2^63, zero/signed weights and file/chunk merges.

A bounded archive containing actual framework code, ZZCR and common passed
relocated imports and an isolated DATA snapshot check. Building an archive
from the entire development checkout exceeded the 180-second cap before
producing an archive; full Condor packaging/execution is not established by
that bounded test. No jobs were submitted. These checks do not establish
all-era physics or nuisance-production equivalence. Outputs used for these
implementation checks were temporary; historical campaign outputs were not
rewritten.
