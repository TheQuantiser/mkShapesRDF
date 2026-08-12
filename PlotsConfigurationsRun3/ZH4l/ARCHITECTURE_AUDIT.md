# ZH4l architecture audit

This audit was written before the `ZH4l` migration.  It describes the source
available on 2026-08-12 at starting commit
`3659c2e930d58b8a3df387ca9080c9443bb528e8`.  The worktree also contained an
untracked but complete `DY_ZZ_ClosureStudy`; it is treated as a current sibling
study rather than as generated output.  Existing `ZH_4lMET` files are an
immutable validation reference and are not changed by this refactor.

## Classification key

- **A — standard mkShapes leaf interface:** `configuration.py`, `samples.py`,
  `aliases.py`, `cuts.py`, `variables.py`, `plot.py`, `structure.py`, and
  `nuisances.py` in their ordinary public roles.
- **B — ZH4l-common physics:** era/process inventory, selected Z/X objects,
  common observables, selected-object corrections, and the physical b veto.
- **C — analysis-specific physics:** regions, study stages, truth matching,
  alternative algorithms, and a leaf's chosen histograms.
- **D — framework adapter:** minimum glue around an existing mkShapesRDF API.
- **E — execution/site infrastructure:** endpoints, runtime packaging, batch
  profiles, and stage-out.
- **F — diagnostics/testing/provenance:** tests, planning tools, contracts, and
  curated technical notes.
- **G — generated or historical artifact:** job products, receipts, caches,
  rendered reports, and campaign output.
- **H — redundant / compatibility-only:** duplicated implementation or an
  abstraction made unnecessary by the family split.

## Repository and public-style audit

The current public `latinos/PlotsConfigurationsRun3` tree was inspected at
`main`, including `HWW/ggH_DF/<era>` and `ControlRegions/DY/<era>`.  The useful
convention is the familiar eight-file leaf: orchestration in
`configuration.py`; inputs and base weights in `samples.py`; derived columns
and corrections in `aliases.py`; regions in `cuts.py`; histogram definitions
in `variables.py`; display grouping in `plot.py`; process bookkeeping in
`structure.py`; and uncertainties in `nuisances.py`.  Public configurations
also keep small analysis C++ helpers in `macros/`.  The public tree's repeated
era directories are not copied: this family resolves `ERA` centrally.

The relevant framework implementations were read without modification:

| Native concept | Implementation inspected | Reuse decision |
|---|---|---|
| file discovery | `mkShapesRDF.lib.search_files.SearchFiles` and remote-I/O helpers | Reuse directly. |
| analysis graph | `mkShapesRDF.shapeAnalysis.runner.RunAnalysis` | Use for ordinary rectangular leaves; retain a small adapter only when a study needs a different weight for the same event/cut or sparse non-rectangular booking. |
| trigger payload | `processor/modules/TrigMaker.py` and canonical `TrigMaker_cfg.py` | Reuse its declarations, payload readers, and formulae.  Native output is leading-object based, not selected-Z/ZX based. |
| lepton SF | `processor/modules/LeptonSF.py` | Reuse its per-lepton vectors; only selected-index multiplication is custom. |
| scale/smearing | `processor/modules/LeptonScaleSmearing.py` | Reuse produced branches; no local replacement. |
| MET filters | standard `METFilter_Common`/`METFilter_DATA` processor output | Reuse directly. |
| b tagging | `processor/modules/btagSFProducerLatinos.py` and public Run-3 aliases/macros | Similar but not identical: the native producer provides per-jet fixed-WP SF branches/shape SFs, not the exact veto-efficiency event ratio using the validated map and the same CleanJet acceptance. |
| nuisances/variations | core runner variation loading and existing nuisance dictionaries | Reuse directly. |
| histogram output | core `histo_utils` and runner post-processing | Reuse; custom runners delegate conversion/folding wherever possible. |
| batch execution | `ConfigLib`, `BatchSubmission`, runtime package and remote-I/O support | Reuse; site values live outside physics definitions. |

## Current source ownership

### `ZZ_CR`

| Current source | Class | What it owns now | Final disposition |
|---|---:|---|---|
| `configuration.py` | A/D/E | Leaf orchestration mixed with site presets, packaging, campaigns, contracts, and a custom runner | Replace with a compact `ZZCR/configuration.py`; move sites/runtime to `common/runtime.py` and `env/`. |
| `samples.py` | A/B | SearchFiles discovery, all-era process materialization, overlap/stitching, base weights, DATA stream de-duplication | Keep leaf-facing `samples`; centralize process/profile resolution in `common/catalog.py` and era materialization in `common/eras.py`. |
| `aliases.py` lines 1–317 | B/H | production-order reconstruction, lepton WPs, selected Z/X, pT predicates | Move authoritative object graph to `common/objects.py`; expose concise public names and reserve `ZH4l_` for mechanics. |
| `aliases.py` lines 318–716 | B/F | common kinematics plus extensive trigger-object, stream, and matching diagnostics | Common observables go to `common/observables.py`; nominal leaves retain only trigger/stream quantities they actually cut on. |
| `aliases.py` lines 717–914 | B/D/F | selected-index lepton and trigger corrections plus stored-leading oracles | Move selected-domain products to `common/corrections.py`; oracles/raw vectors become private `ZH4l_` columns or tests. |
| `aliases.py` lines 915–1270 | B/F/G | recoil, flavors, per-lepton quality maps, fixed-WP b tagging, DATA fallbacks, generator/jet diagnostics | Retain common flavor/charge/veto/recoil physics; isolate b tagging in corrections; omit broad nominal diagnostics. |
| `selection_config.py` | B/H | analysis passes, selected-pair WPs, trigger path metadata, diagnostic suffix registries | Selected object/trigger metadata belongs in common builders; pass multiplexing and suffix registries are not a nominal-leaf API. |
| `category_config.py` | C/H | DY, four-lepton, ZZCR/SR regions plus seven diagnostic projection profiles | Replace with legible physical cuts in `ZZCR/cuts.py`; DY/closure projections belong in `Closure`. |
| `histogram_config.py` | C/D/H | 500-variable registry tagging, profile activation, sparse policy, hashes | Replace with common observable definitions and explicit leaf opt-in; retain sparse booking only for Closure. |
| `variables.py` | A/B/C/F | axes plus an exceptionally broad diagnostic registry | Split reusable binnings into `common/observables.py`; keep a compact ZZCR list. |
| `plot.py` | A/B | plot groups and labels | Generate from `common/catalog.py` metadata, avoiding independent membership lists. |
| `structure.py` | A/B | signal/background/DATA bookkeeping derived from plot groups | Keep as a small leaf, sourced from catalog metadata. |
| `nuisances.py` | A/B | luminosity, selected-object SFs, b veto, theory and friend variations | Keep leaf interface; source era/process domains from common. |
| `nuisances_nominal.py` | A/H | empty nuisance set | Keep only in studies needing an explicitly nominal run; ordinary ZZCR uses `nuisances.py`. |
| `year_config.json` | B | era luminosities, productions, WPs, samples, overlap, streams, trigger and b-tag payloads | Rename to the single family `common/eras.json` source. |
| `year_config.py` | B/D | materialization, validation, process/profile, path and payload resolution | Rename/refocus as `common/eras.py`; process grouping moves to catalog. |
| `selected_trigger_adapter.py` | D | declares canonical TrigMaker code once without running a second event graph | Retain once as a private common adapter; it changes object domain only. |
| `macros/selected_trigger_wrappers.cc` | D/B | evaluates canonical TrigMaker functions on selected Z or ZX leptons | Retain as `common/macros/trigger.cc`; canonical payload/formula code remains owned by TrigMaker. |
| `macros/four_lepton_helpers.cc` | B/F/H | selected objects and observables mixed with trigger-object diagnostics, recoil, generator helpers, and b-veto compatibility functions | Retain the validated physics in `common/macros/objects.cc`, exposing only the small analyst API; diagnostics are not leaf aliases. |
| `macros/fixed_wp_btag_sf.cc` | B/D | exact fixed-WP veto and veto event-SF with cached efficiency/SF payloads | Retain as `common/macros/btag.cc`; no inspected native utility has identical event semantics. |
| `zz_cr_runner.py` | D/E | sparse category-variable booking, per-category weights, compact worker samples, remote mkdir, custom sparse output | ZZCR no longer contains DY/diagnostic mixed domains and uses one ZX correction domain, so native `runnerFile = "default"` is sufficient. |
| `worker_payload.py` | D/E/H | relocatable compressed worker dictionary | Native runtime packaging is sufficient for compact ZZCR; family runtime helpers replace it. |
| `contract_validation.py`, `write_contract.py` | F/E | runtime contract hashing and provenance | Consolidate as one small common provenance utility; generated contracts go to ignored output. |
| `inspect_plan.py`, `inspect_category_occupancy.py` | F | category/action and real-event occupancy diagnostics | Tests or Closure-specific planning; not nominal physics. |
| `check_storage_paths_from_list.py`, `make_sample_catalog.py` | E/F | site inventory/catalog crawling and verification | Useful standalone infrastructure but not family physics; normal leaf discovery uses SearchFiles. |
| `*_env.sh` | E/H | overlapping CERN/FNAL endpoint and runtime presets | Consolidate into `env/lxplus.sh`, `env/lxplus_fnal.sh`, and `env/fnal.sh`. |
| `tests/*.py` | F | contracts, categories, pT/low-mass/b-veto/weight semantics, runner and era resolution | Preserve relevant physics assertions in common/ZZCR tests; runner-profile tests retire with their abstraction. |
| `development/*.md` | F/G | historical selection/category/FNAL audits | Summarize useful decisions here and in architecture docs; do not migrate as active configuration. |
| `development/*.json`, `filesToMerge*.txt` | G | generated plans, occupancy, contracts, receipts and merge lists | Do not migrate or track. |
| `skills/submit-zzcr-production/**` | E/F | an operational Codex skill tied to the legacy application | Not physics and not migrated; documented shell commands are sufficient. |

### `PairingStudy`

| Current source | Class | What it owns now | Final disposition |
|---|---:|---|---|
| `configuration.py` | A/E | compact study orchestration and packaged batch setup | Migrate to `Pairing/configuration.py`, sourcing era/runtime centrally. |
| `samples.py` | A/B | ZH/ZZ inventory and SearchFiles discovery | Reuse common era/catalog resolution. |
| `aliases.py` | A/C | one cached study event, truth/algorithm projections, study weights | Keep locally; baseline selected-object inputs come from common. |
| `cuts.py` | A/C | truth-domain study cuts | Keep locally. |
| `variables.py` | A/C | pairing algorithm/status/response cubes | Keep locally and explicit. |
| `plot.py`, `structure.py` | A/B | ZH/ZZ display and process bookkeeping | Source memberships/colors from common catalog. |
| `pairing_config.py` | B/C/H | era inventory adapter plus topology/region codes | Era logic moves to common; pairing codes remain local. |
| `macros/pairing_study.cc` | C | candidate enumeration, alternative scores, truth matching, summaries | Retain locally as `Pairing/macros/pairing.cc`. |
| `local_runner.py` | D | per-variable diagnostic weights (raw/signed/absolute and vector weights) | Retain a minimal study runner: native RunAnalysis has one `weight` column per graph and cannot book the same cut/observable under these domains. |
| `make_summary.py`, `make_plots.py` | C/F | pairing-specific aggregation and report plots | Retain locally. |
| `run_all_years.sh` | E | all-era batch front end | Rename terminology to eras and source family environments. |
| `tests/*.py` | F | candidate, truth, sample and summary decoding equivalence | Migrate and update paths/names. |
| `README.md`, `PAIRING_STUDY.md`, `IMPLEMENTATION_AUDIT.md` | F | user guide and detailed scientific/audit record | Consolidate quick use in README; retain scientific detail where useful. |
| `.gitignore`, `*.aux`, `*.log`, `*.out`, rendered PDF and campaign logs | G | generated report/campaign output | Ignore; source Markdown/TeX may remain user-owned in the untouched legacy tree. |

### `DY_ZZ_ClosureStudy` found in the worktree

| Current source | Class | What it owns now | Final disposition |
|---|---:|---|---|
| `configuration.py` | A/E | closure orchestration and packaged runtime | Migrate to `Closure/configuration.py`; use common runtime. |
| `samples.py` | A/B/H | nearly duplicated ZZCR discovery plus closure inventory | Replace duplicated materializer with common catalog/sample builder. |
| `aliases.py` | A/B/C/H | duplicated full ZZCR graph plus closure stage aliases | Consume common objects/corrections; retain closure-only stage quantities locally. |
| `cuts.py`, `study_config.py` | A/C | audited DY→ZZ ladder, N−1 stages, partitions and weight domains | Retain as closure-specific physical/study definitions. |
| `variables.py` | A/C/D | explicit sparse stage booking and counter weights | Retain locally with bounded action count. |
| `plot.py`, `structure.py`, `nuisances_nominal.py` | A/B | standard presentation/bookkeeping, nominal-only study | Keep compact and source process metadata centrally. |
| `year_config.json`, `year_config.py`, `selection_config.py`, `selected_trigger_adapter.py` | B/D/H | byte-identical copies of ZZCR common configuration/adapters | Remove from the new leaf; consume `common`. |
| `macros/four_lepton_helpers.cc`, `fixed_wp_btag_sf.cc`, `selected_trigger_wrappers.cc` | B/D/H | byte-identical copies of ZZCR helpers | Remove from the new leaf; consume common macros. |
| `macros/closure_helpers.cc` | C | closure-only vector/counter helpers | Retain locally. |
| `closure_runner.py` | D | sparse non-rectangular booking and stage/variable-specific weights | Retain minimally; native runner cannot express several simultaneous weight domains in one cut graph. |
| `inspect_plan.py`, `make_summary.py`, `make_plots.py` | C/F | closure planning, metrics and report figures | Retain locally. |
| `tests/*.py` | F | frozen reference expressions, ladder algebra, trigger/stream partitions, sample and histogram budgets | Migrate and point reference checks at common. |
| `README.md`, `CLOSURE_STUDY.md`, `IMPLEMENTATION_AUDIT.md` | F | study documentation and limitations | Consolidate under `Closure/`. |
| `configs/`, `condor/`, `rootFiles/`, caches and proxies | G | generated jobs, products, runtime archives and credentials | Never migrate or track. |

## Mandatory custom-feature decision record

| Custom feature | Purpose / current owner | Users | Existing concept | Semantic comparison | Recommended owner and public name |
|---|---|---|---|---|---|
| Era catalogue/materializer | `year_config.json/.py` resolves five eras, processes, overlap, streams, WPs and payloads | all leaves | Public configs and SearchFiles cover pieces, not this combined validated inventory | Similar interfaces; ZH4l content is analysis-specific | `common/eras.json`, `common/eras.py`; preferred selector `ERA`, checked `YEAR` fallback |
| Selected Z/X | `selection_config.py`, `aliases.py`, `four_lepton_helpers.cc` | ZZCR, Pairing baseline, Closure | standard kinematic modules provide leading systems, not this selected OSSF Z plus complement | Different object domain | `common/objects.py` + `common/macros/objects.cc`; `Z_idx`, `X_idx`, `validZX` |
| Common observables | aliases/variables | all leaves | some native leading-object names exist (`mll`, etc.) | Different where selected indices differ | `common/observables.py`; `mZ`, `mX`, `m4l`, `pt4l`, `minMll4l`, `q4l` |
| Selected lepton SF | selected products in aliases | ZZCR, Closure | LeptonSF produces aligned per-lepton vectors | Native vectors identical inputs; multiplication domain differs | `common/corrections.py`; `LepSF_Z`, `LepSF_ZX` |
| Selected trigger SF | adapter + trigger wrapper | ZZCR, Closure | TrigMaker owns payload readers/formulae | Formulae identical; selected-object domain intentionally differs from native leading 2l/4l | `common/corrections.py`, private adapter, `common/macros/trigger.cc`; `TriggerSF_Z`, `TriggerSF_ZX` |
| Fixed-WP b veto/SF | two C++ helpers plus aliases | ZZCR, Closure | Run-3 btag producer/public helpers | Similar correction payload, but no exact validated veto-efficiency event ratio and shared selection acceptance | `common/corrections.py`, `common/macros/btag.cc`; `bVeto`, `bVetoSF` |
| Category profiles | `category_config.py` | legacy ZZCR diagnostics | native cuts/categories | Native is sufficient once scientific questions are separate leaves | Physical cuts in ZZCR; stage projections in Closure; no profile manager |
| Histogram profiles | `histogram_config.py` | legacy ZZCR | native variables and optional cut restriction | Native is sufficient for compact ZZCR; Closure remains sparse | `common/observables.py` plus explicit leaf `variables.py` |
| ZZCR custom runner/payload | `zz_cr_runner.py`, `worker_payload.py` | legacy ZZCR | RunAnalysis, batch packaging | Becomes unnecessary after DY/diagnostics split and one ZX weight domain | `runnerFile = "default"` |
| Pairing custom runner | `local_runner.py` | Pairing | RunAnalysis | Insufficient: variable-specific scalar/vector raw/signed/absolute weights | `Pairing/runner.py`; no public physics alias introduced |
| Closure custom runner | `closure_runner.py` | Closure | RunAnalysis | Insufficient: sparse cut-variable matrix and variable/stage correction factors | `Closure/runner.py`; local adapter |
| Runtime/site wrappers | five overlapping shell files/config blocks | all leaves | native batch/remote-I/O APIs | APIs sufficient; values remain site-specific | `common/runtime.py`, `env/{fnal,lxplus,lxplus_fnal}.sh` |
| Contracts/provenance | contract scripts, receipts | all leaves operationally | git plus config dictionaries | Existing implementation is broader than needed | one `common/provenance.py`; generated JSON ignored |

## Collision audit conclusions

Repository-wide searches show that native/public `mll` cannot be repurposed for
the selected Z, and native `TriggerSFWeight_2l/4l` cannot name the selected
domain.  `bVeto` is accepted because the validated physical loose 20 GeV veto
matches the conventional meaning; the implementation remains centralized.
Public aliases use concise physics names.  Technical source-order recovery,
trigger result vectors and declaration sentinels use `ZH4l_...`.  A test in
`common/tests` will fail on accidental native collisions and on leaf
redefinitions of common public aliases.

## Resulting dependency rule

```text
common <- ZZCR
common <- Pairing
common <- Closure
```

No leaf imports another leaf.  New configurations never import `ZH_4lMET`;
the old tree remains untouched solely because the user explicitly required it
to remain unchanged and because it provides an old/new validation oracle.
