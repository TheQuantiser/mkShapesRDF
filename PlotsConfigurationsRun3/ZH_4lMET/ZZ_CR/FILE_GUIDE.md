# ZZ_CR file architecture and customization guide

This document explains the files that participate in the
`PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR` workflow, how mkShapesRDF consumes
them, which file is authoritative for each kind of change, and how to validate
customizations. It is a code-navigation guide rather than a replacement for:

- [`CONFIGURATION.md`](CONFIGURATION.md), which defines the current analysis
  contract and physics model;
- [`USAGE.MD`](USAGE.MD), which gives setup, submission, merge, and plotting
  commands;
- [`TRIGGER_SCALE_FACTORS.md`](TRIGGER_SCALE_FACTORS.md), which documents the
  exact selected-object TrigMaker adaptation and region weight placement;
- [`development/CATEGORY_DESIGN.md`](development/CATEGORY_DESIGN.md), which
  lists the exact category inventory and category algebra;
- [`development/SELECTION_SOURCE_NOTE.md`](development/SELECTION_SOURCE_NOTE.md),
  which records the physics sources behind the implemented selection.

All paths in this guide are relative to the `ZZ_CR` directory unless a path
starts with `mkShapesRDF/`.

## 1. The execution model

The most important fact about a mkShapesRDF configuration is that its Python
files do not behave like a collection of isolated modules during compilation.
The framework first executes `configuration.py`, then executes every entry in
`filesToExec` in order in one shared global namespace:

```text
configuration.py
  |
  +-- year_config.py
  +-- samples.py
  +-- selection_config.py
  +-- aliases.py
  +-- cuts.py
  +-- variables.py
  +-- plot.py
  +-- nuisances_nominal.py  (default) OR nuisances.py
  +-- structure.py
  +-- write_contract.py
  `-- worker_payload.py
          |
          +-- compiled config pickle and config.json
          +-- shared compressed worker payload
          `-- Condor split jobs through zz_cr_runner.py
```

Consequences of this design:

1. **Order is part of the interface.** For example, `aliases.py` consumes the
   selected era loaded by `year_config.py`; `cuts.py` consumes aliases and the
   selection contract; `variables.py` consumes the final category metadata.
2. **A name defined earlier is available later without an import.** This is
   normal for mkShapesRDF configuration files. Utility modules that are also
   imported directly by tests use explicit imports where needed.
3. **The compiled pickle is an executable snapshot.** A merge with `-c 0`
   reloads the serialized configuration; it does not re-read the current
   source files. Use the pickle produced for the jobs being merged.
4. **Absolute paths are serialized.** Merge and job-management commands should
   normally run from the site and checkout that compiled the configuration.
   The environment wrappers and packaged worker relocation address worker-side
   resources, but do not make an arbitrary copied pickle site-independent.
5. **The analysis contract is generated, not hand-written.** It records the
   resolved sources, categories, variables, samples, corrections, endpoints,
   profiles, and git state for the exact compiled job graph.

The relevant framework path is:

```text
mkShapesRDF/shapeAnalysis/mkShapesRDF.py
  -> ConfigLib.py                 execute and serialize the configuration
  -> BatchSubmission.py           split, package, and submit batch jobs
  -> zz_cr_runner.py              ZZ_CR-specific RunAnalysis subclass
       -> runner.py               core RDataFrame analysis implementation
  -> histo_utils.py               nuisance post-processing and merge support

samples.py
  -> mkShapesRDF/lib/search_files.py
  -> mkShapesRDF/lib/remote_io.py
```

## 2. Where should a change go?

Use this table before editing. It identifies the authoritative layer and avoids
duplicating a policy in a downstream adapter.

| Desired change | Primary file | Usually also inspect | Do not implement it in |
| --- | --- | --- | --- |
| Add an era or change era metadata | `year_config.json` | `year_config.py`, `tests/test_year_config.py` | `samples.py` |
| Add/remove a configured dataset or DATA run | `year_config.json` | `samples.py`, `plot_groups` in the same JSON | `plot.py` |
| Change a production campaign path | `year_config.json` | environment wrapper if site access changes | `aliases.py` |
| Change production run scope temporarily | environment variables | `configuration.py`, `USAGE.MD` | the sample catalog |
| Change lepton IDs or era-dependent thresholds | `year_config.json` | `selection_config.py` | `cuts.py` |
| Add a derived RDataFrame column | `aliases.py` | a macro under `macros/` for complex vector logic | `variables.py` |
| Change a physical region cut | `category_config.py` | `selection_config.py`, category tests | `cuts.py` |
| Add a category or profile | `category_config.py` | `histogram_config.py`, category tests | `cuts.py` |
| Add a histogram variable or change its bins/fold | `variables.py` | `histogram_config.py`, histogram tests | `plot.py` |
| Change which histograms a category receives | `histogram_config.py` | `variables.py`, `category_config.py` | `zz_cr_runner.py` |
| Change plot labels, colors, or process grouping | `plot_groups` in `year_config.json` | `plot.py` | `structure.py` |
| Add a nuisance | `nuisances.py` | `aliases.py`, branch availability, runner tests | `nuisances_nominal.py` |
| Change a category-specific correction factor | category metadata/weights in `category_config.py` | `zz_cr_runner.py`, weight tests | global sample weight |
| Change sparse booking or worker output semantics | `zz_cr_runner.py` | core `runner.py`, sparse-runner tests | category definitions |
| Change CERN/FNAL execution or destination | an environment wrapper | execution profiles in `configuration.py` | `samples.py` |
| Change provenance recorded for every production | `write_contract.py` | `contract_validation.py`, contract tests | generated JSON |

## 3. Entry point and era model

### `configuration.py`

**Purpose.** This is the mkShapesRDF entry point. It resolves the requested
analysis mode, constructs output and job-control locations, declares the
execution profile, selects the runner, and tells the framework which objects
must be serialized.

**How it works.** It reads and normalizes environment variables including:

- `YEAR`;
- `ANALYSIS_PASS`;
- `CATEGORY_PROFILE`;
- `HISTOGRAM_PROFILE`;
- `SAMPLE_PROFILE`;
- `ENABLE_SYSTEMATICS`;
- `EXECUTION_PROFILE`, `SITE_PRESET`, and `OUTPUT_MODE`;
- XRootD endpoints, LFNs, campaign names, packaging settings, and merge
  scratch locations.

It generates a UTC-stamped `tag`, selects `zz_cr_runner.py`, defines
`filesToExec`, and fills `varsToKeep` and `batchVars`. `varsToKeep` determines
what survives in the compiled configuration. `batchVars` is deliberately
small because large analysis dictionaries are put in one shared compressed
payload by `worker_payload.py`.

The configuration is histogram-only and fails closed for unsupported mode
combinations. In particular, the unified `ANALYSIS_PASS=ALL` path is nominal
only until the full nuisance behavior has been validated for that graph.

**Customize this file when:**

- introducing a new high-level execution/profile switch;
- changing output naming or directory policy;
- adding an item that workers or a later merge must receive;
- adding a supported execution profile;
- deliberately changing the ordered configuration file chain.

**Do not use it for:** era sample lists, physics cuts, variable expressions, or
plot grouping. Those policies already have dedicated authoritative files.

**Validate with:** `tests/test_configuration.py`,
`tests/test_fnal_io_defaults.py`, `inspect_plan.py`, and a compile-only or dry
run from every affected site wrapper.

### `year_config.json`

**Purpose.** This is the declarative source of truth for all supported Run 3
eras. It keeps physics/production data reviewable without embedding it in
control-flow code.

The file contains:

- the schema version and default era;
- luminosities and NanoAOD production identifiers;
- MC sample and DATA run/stream inventories;
- production normalization conventions;
- logical overlap components and source-set rules;
- plot groups and process presentation metadata;
- trigger paths and era mappings;
- lepton working points, 10/10 GeV Z0 pair-construction thresholds, and the
  separate ordered two-/four-lepton selection profiles;
- the official CVMFS `btagging.json.gz` path for each era;
- the FNAL EOS XRootD b-tag efficiency-map ROOT URL for each era;
- configured loose working-point audit values and era defaults.

The BTV JSON and efficiency ROOT file have different roles. The official
correctionlib JSON supplies the loose working point and heavy/light fixed-WP
scale-factor corrections. The ROOT file supplies `bjet_eff`, `cjet_eff`, and
`ljet_eff`, which are needed to calculate the untagged-jet veto factor. Both
are consumed by `macros/fixed_wp_btag_sf.cc` through aliases created in
`aliases.py`.

**Customize this file when:** adding an era, production, sample, DATA run,
trigger path, luminosity, b-tag payload, object working point, overlap rule,
normalization rule, or plot group.

**Important rules:**

- use full, explicit correction paths;
- keep remote efficiency maps as XRootD URLs when direct reads are intended;
- keep logical process names consistent across samples, overlap rules, plot
  groups, and structure generation;
- represent a persistent analysis choice here, but use `SAMPLE_FILTER` or a
  profile for a one-off production subset;
- do not hand-edit the configured loose b-tag value without checking it
  against the correctionlib payload—the runtime verifies that they agree.

**Validate with:** `tests/test_year_config.py`, `inspect_plan.py` for all five
eras, and `check_storage_paths_from_list.py` when storage inventories change.

### `year_config.py`

**Purpose.** This is the validation and materialization layer for
`year_config.json`.

**How it works.** It loads the JSON, validates its schema and cross-references,
selects the requested year, resolves directories and b-tag resources, reads
the official working point through correctionlib, expands DATA streams/runs,
selects sample profiles, and resolves logical overlap outputs and weights. Its
helpers are used by `configuration.py`, `samples.py`, `plot.py`, tests, and
inspection tools.

**Customize this file when:** the schema needs a new concept, an existing JSON
field needs new resolution logic, or a cross-field invariant must fail closed.
Prefer a JSON-only change when the existing schema already expresses the
desired configuration.

**Validate with:** `tests/test_year_config.py` for every era and any consumer
test affected by the new materialized fields.

## 4. Inputs, processes, and event weights

### `samples.py`

**Purpose.** This file turns the selected era and logical process model into
the mkShapesRDF `samples` dictionary.

**How it works.** It:

- resolves `SAMPLE_PROFILE` or the stronger exact `SAMPLE_FILTER` override;
- discovers files through `mkShapesRDF.lib.search_files.SearchFiles` using the
  configured discovery and read endpoints;
- applies `LIMIT_FILES_PER_SAMPLE` and `FILES_PER_JOB`;
- builds logical overlap components and component-specific weights;
- constructs common MC normalization and analysis weights;
- expands DATA run/stream components;
- applies exclusive stream trigger de-duplication rules;
- honors `DATA_STREAM_FILTER` for bounded tests;
- checks variation-branch availability before enabling supported systematic
  paths.

Input discovery and event reading are separate concepts: an `xrdfs` endpoint
may list files while an XRootD redirector supplies the URLs read by ROOT. In
the direct-read profiles, files are not copied wholesale before analysis.

**Customize this file when:** changing file-discovery mechanics, the mapping
from declarative logical components into mkShapesRDF sample tuples, or the
common event-weight construction.

**Prefer another mechanism when:**

- adding a dataset or DATA run: edit `year_config.json`;
- selecting a temporary subset: use `SAMPLE_FILTER`;
- limiting development input: use `LIMIT_FILES_PER_SAMPLE`;
- changing job granularity: use `FILES_PER_JOB`;
- changing plot membership: edit `plot_groups` in `year_config.json`.

**Validate with:** `tests/test_year_config.py`, `tests/test_weights.py`, a
bounded compile, and the analysis contract's resolved file/sample hashes.

### `structure.py`

**Purpose.** It creates the mkShapesRDF `structure` dictionary used to label
samples as DATA, signal, or background for statistical/output conventions.

**How it works.** It validates that every active sample belongs to a resolved
plot group and derives `isSignal` and `isData` consistently from the active
process model.

**Customize this file when:** the structure-building mechanics themselves
change. Most additions require only `year_config.json`; this file should stay
generic and complete.

### `plot.py`

**Purpose.** It materializes `groupPlot`, `plot`, and `legend` for mkPlot.

**How it works.** It consumes the active samples, selected luminosity,
category display labels, and declarative `plot_groups` from `year_config.json`.
Only active processes are emitted.

**Customize this file when:** changing the algorithm that translates
declarative plot metadata into mkPlot dictionaries. Change process labels,
colors, stack order, signal/background classification, and memberships in the
JSON instead.

## 5. Selected objects, triggers, corrections, and derived columns

### `selection_config.py`

**Purpose.** This file defines the shared selection vocabulary and the
analysis-pass contract used by aliases and categories.

It resolves:

- supported passes (`ALL`, `ZPARENT`, `FOURL_BASE`, and `CONTROL`);
- production-aligned lepton working points and pT thresholds;
- selected-lepton scale-factor suffixes;
- configured trigger paths and aggregate expressions;
- raw trigger-family and stream-priority metadata;
- human-readable cut labels;
- the era's named selection profile.

**Customize this file when:** changing how selection-profile fields become
expressions, adding a high-level pass, or changing common trigger/object
contract mechanics. Put era-dependent values in `year_config.json` when
possible.

**Validate with:** configuration, category, algebra, and weight tests. A
selection-contract change should also be reflected in `CONFIGURATION.md` and,
when physics-sourced, `development/SELECTION_SOURCE_NOTE.md`.

### `aliases.py`

**Purpose.** This is the central RDataFrame derived-column graph. It constructs
the `aliases` dictionary consumed by the runner.

Major responsibilities include:

- loading the configured LeptonSel working points;
- declaring the local C++ helper macros;
- constructing production-aligned selected leptons;
- selecting the Z candidate and the non-overlapping X pair;
- exposing selected indices, flavor/charge predicates, and pair/four-lepton
  kinematics;
- computing `minSelectedPairMass` over all six unordered pairs made from the
  selected Z+X leptons;
- implementing fifth-lepton, distinct-index, charge, horn-jet, and b-jet veto
  diagnostics;
- declaring canonical TrigMaker calculations and selected-lepton trigger
  wrappers;
- resolving trigger-family and DATA stream priorities;
- composing selected-lepton, trigger, recoil, b-tag, and generator-level
  corrections and diagnostics;
- providing safe fallbacks when an optional branch is absent.

Aliases form a dependency graph. Define a prerequisite before an alias that
uses it, restrict MC-only aliases with their `samples` field, and make invalid
physics inputs fail closed rather than quietly selecting an event.

**Customize this file when:** adding or modifying a derived physics column,
event correction, diagnostic, or selected-object computation. Add a histogram
definition separately in `variables.py` if the new alias should be plotted;
add a category expression in `category_config.py` if it should select events.

**Validate with:** the closest focused tests, a bounded ROOT compile, and the
category occupancy tool for selection-affecting aliases. Pure Python plan
inspection cannot validate C++ expressions against a NanoAOD schema.

### `selected_trigger_adapter.py`

**Purpose.** This is a thread-safe, declaration-only bridge to the canonical
mkShapesRDF `TrigMaker` module.

**How it works.** A no-op dataframe lets `TrigMaker` declare its C++ payload
readers and exact event formulae without producing a random run period or
mutating the real analysis dataframe. The module records the single era
declared in the process and rejects loading a second era into the same ROOT
interpreter because the generated C++ names are process-global.

**Customize this file when:** the canonical `TrigMaker` declaration interface
changes. Analysis trigger selection belongs in `selection_config.py` and
selected-pair wrapper behavior belongs in the corresponding macro.

### `macros/four_lepton_helpers.cc`

**Purpose.** It contains compiled C++ helpers for vector and combinatorial
operations that would be cumbersome or unsafe as long expression strings.

The helpers cover pair construction/ranking, production alignment, selected
index validation, trigger matching and priority, selected scale-factor
products, fifth-lepton checks, minimum selected-pair mass, pair/four-lepton
kinematics, recoil, and related masking utilities.

**Customize this file when:** a new derived operation needs loops over ROOT
vectors, careful bounds checking, or reusable numerical logic. Keep the macro
side-effect free, return neutral values for diagnostics where appropriate,
and use fail-closed values for selections. Declare its use in `aliases.py` and
add a compiled focused test for boundary cases.

### `macros/selected_trigger_wrappers.cc`

**Purpose.** It adapts the canonical TrigMaker calculation to the selected Z
and X leptons rather than relying on stored leading-lepton scalar weights.

It assembles and orders the selected leptons, invokes the canonical trigger
payload, and exposes the relevant central/variation projections with guarded
fallback behavior. `TriggerSF_Z` compacts exactly `Z0_idx[0:2]` for DY;
`TriggerSF_ZX` compacts exactly the selected Z0+X quartet for four-lepton
regions. These factors are applied in the corresponding region registry
weight policies, not as a generic event-level correction.

The complete data flow, result-vector schema, fallback behavior, nuisance
contract, and duplication safeguards are documented in
[`TRIGGER_SCALE_FACTORS.md`](TRIGGER_SCALE_FACTORS.md).

**Customize this file when:** the selected-object interface or canonical
TrigMaker result schema changes. Do not reproduce the underlying trigger
payload or its formulae here.

### `macros/fixed_wp_btag_sf.cc`

**Purpose.** It implements the physical loose b veto and the corresponding
fixed-working-point event scale factor.

**How it works.** A process-wide, mutex-protected cache loads:

- the official correctionlib BTV JSON;
- `bjet_eff`, `cjet_eff`, and `ljet_eff` from the efficiency ROOT map.

For each selected CleanJet in the physical pT/eta range it resolves the raw
jet index and hadron flavor. Tagged jets contribute their correctionlib scale
factor. Untagged jets contribute `(1 - efficiency * SF) / (1 - efficiency)`;
an efficiency of exactly one is handled explicitly because the analytic ratio
is undefined. The code verifies that the correctionlib loose working point
matches the configured audit value, clamps efficiency-map pT at the map edge,
rejects invalid efficiencies or non-finite factors, and counts map-overflow
jets for diagnostics.

**Customize this file when:** changing the fixed-WP event formula, supported
map schema, jet acceptance, or correctionlib input contract. Change only
payload paths or era WPs in `year_config.json`.

**Validate with:** correctionlib/ROOT payload-opening checks, weight tests, and
a bounded MC run containing heavy- and light-flavor jets.

## 6. Regions and categories

### `category_config.py`

**Purpose.** This is the authoritative physical-region and category registry.
It is the correct place for cuts, category metadata, split families, and
category profiles.

It defines:

- the inclusive DY, enriched DY, physical ZZ control, and signal-reference
  parent selections;
- the shared signal-region Z window;
- the physical common four-lepton requirements, including
  `minSelectedPairMass > 12 GeV` for ZZCR/SR but not DY;
- selected-pair flavor, four-lepton topology, DATA stream, and exclusive
  trigger-family projections;
- the one-to-one enriched-DY mirrors of ordinary DY subcategories;
- `minimal`, `standard`, `flavor`, `stream`, `trigger`, `detailed`, and
  guarded `debug` profiles;
- category labels, view types, partition families, overlap/exclusivity
  declarations, diagnostic purpose, histogram tier, and weight domain;
- category/action budgets and the `build_categories` materializer.

Parent regions may overlap intentionally. A category family marked exclusive
must be proved exclusive within its declared parent; cross-family projections
are diagnostic overlaps unless metadata says otherwise.

**Customize this file when:** changing a region boundary, adding a category,
adding a split family, changing a profile, or changing category-specific
metadata/weights.

When adding a category:

1. define it from an existing parent and a clear split expression;
2. declare its metadata rather than encoding meaning only in its name;
3. place it in the intended profiles explicitly;
4. decide whether it is a partition, an intersection, or an overlapping view;
5. assign a histogram tier/view type that `histogram_config.py` understands;
6. update the category inventory and algebra tests;
7. run `inspect_plan.py` and, for a physics change, bounded occupancy.

**Do not edit `cuts.py` directly to add a category.** That bypasses the
registry, metadata, profile budgets, contract, and algebra checks.

### `cuts.py`

**Purpose.** This is the thin compatibility adapter expected by mkShapesRDF.

It calls `build_categories`, exports `preselections`, `cuts`,
`CATEGORY_METADATA`, the selected `CATEGORY_PROFILE`, display labels, and the
final category IDs.

**Customize this file when:** the adapter contract with mkShapesRDF changes.
Normal category and selection work belongs in `category_config.py`.

## 7. Histogram registry and rendering

### `variables.py`

**Purpose.** This is the authoritative registry of supported histogram
expressions and axes.

It builds the persistent raw variable definitions, including branch-level,
selected-object, trigger, correction, quality, and generator diagnostics. It
also defines shared presentation axes and masks invalid X-dependent values so
sentinel values do not populate physical bins. At the end it asks
`histogram_config.py` to materialize only the approved category-variable
pairs.

The exported objects include:

- `VARIABLE_REGISTRY`: all supported variable definitions;
- `VARIABLE_REGISTRY_HASHES`: immutable definition hashes for provenance;
- `CATEGORY_VARIABLES`: the resolved sparse booking map;
- `variables`: the active subset in mkShapesRDF format.

Each variable definition carries an expression, axis title, binning, fold
policy, tags/role, and any applicability information required by the
materializer. For `fold`, use mkShapesRDF's convention deliberately: underflow
is folded into the first visible bin when the low-side bit is enabled, and
overflow is folded into the final visible bin when the high-side bit is
enabled.

**Customize this file when:** adding/removing a supported observable, changing
an expression, title, bin edges, or underflow/overflow handling.

For a new variable:

1. ensure its expression is a real branch or an alias defined earlier;
2. choose explicit bin edges where the analysis needs nonuniform bins;
3. set fold behavior intentionally;
4. assign tags and role;
5. define applicability if it is invalid outside some physics region;
6. update `histogram_config.py` if the variable should enter an existing
   profile or view;
7. run registry and plan tests.

**Do not put category cuts here.** Masking an undefined observable and
selecting an event are distinct operations.

### `histogram_config.py`

**Purpose.** This file separates the persistent variable registry from the
histograms actually booked for each category.

**How it works.** It combines variable tags/roles, physics region, category
`view_type`, histogram tier, and `HISTOGRAM_PROFILE`. It applies
`VARIABLE_INCLUDE` and `VARIABLE_EXCLUDE`, enforces action budgets, records
category-variable mappings, and checks registry hashes so definitions cannot
mutate silently during materialization.

Available histogram profiles are `analysis`, `trigger`, `objects`, `weights`,
`quality`, and `all`. A category can receive a different approved subset from
another category even though both draw from the same registry. This sparse
mapping is why action count is the sum of category-specific variable counts,
not `number of categories * number of variables`.

**Customize this file when:** deciding which existing variables belong in a
profile, view type, physics region, or tier; adding an activation policy; or
changing an action-budget guard.

**Use `variables.py` instead when:** the expression, title, binning, fold, or
definition tags themselves change.

**Validate with:** `tests/test_histogram_registry.py`, `inspect_plan.py`, and
the action-count comparison for all affected profiles.

## 8. Nuisances

### `nuisances_nominal.py`

**Purpose.** It exports an empty `nuisances` dictionary for the supported
nominal production path. Keeping this as a real config file lets the ordered
execution chain remain identical while avoiding accidental nuisance booking.

**Customize this file only when:** the definition of “nominal” itself changes.
Ordinary uncertainty definitions belong in `nuisances.py`.

### `nuisances.py`

**Purpose.** It defines the available experimental and theoretical
uncertainties, including luminosity components, pileup, underlying event,
lepton/trigger/b-tag corrections, detector branch suffixes, parton shower,
QCD scales, PDF, and statistical nuisances.

It filters definitions by analysis pass, sample type, and available branch or
alias support. Suffix nuisances rely on the core runner's varied-column
machinery; weight nuisances rely on valid up/down weight expressions.

**Customize this file when:** adding or changing a validated uncertainty.
Before enabling it, confirm the variation exists for every intended sample,
the affected aliases are recomputed correctly, the category-variable sparse
mapping survives variations, and the merged naming is compatible with
downstream tools.

The current production contract rejects `ANALYSIS_PASS=ALL` together with
`ENABLE_SYSTEMATICS=1`. Treat this file as an available uncertainty model, not
authorization to bypass that fail-closed guard.

## 9. Custom runner and worker payload

### `zz_cr_runner.py`

**Purpose.** This is the ZZ_CR-specific subclass of the framework's
`RunAnalysis`. It exists because the configuration needs sparse
category-variable booking and category-specific event-weight factors.

It:

- rejects tree-output variables because ZZ_CR is histogram-only;
- creates result slots only for resolved category-variable pairs;
- flattens category weight policies;
- books each cut on an RDataFrame branch whose `weight` is redefined only for
  that category;
- preserves ROOT variations during conversion;
- writes the non-rectangular result dictionary without empty directories;
- compacts split-sample metadata to keep generated worker scripts small;
- prepares authenticated remote output directories;
- loads the shared compressed worker payload in batch execution.

**Customize this file when:** changing booking, result conversion, sparse
output, split-job serialization, or worker startup semantics.

**Do not use it for:** category selection, variable activation, or the physics
definition of a correction. The runner should execute resolved metadata, not
invent it.

**Validate with:** `tests/test_sparse_runner.py`, weight tests, a bounded local
run, and a small batch pilot when serialization or remote output changes.

### `worker_payload.py`

**Purpose.** It creates one compressed shared payload containing the large
analysis dictionaries instead of repeating them in every Condor process
script.

For packaged jobs it registers runtime includes and replaces local absolute
resource paths with relocation tokens. Stable remote b-tag efficiency maps
remain XRootD URLs and are read directly; a local map can still be packaged as
a development fallback. Packaged payload creation rejects unresolved `/afs/`
dependencies.

**Customize this file when:** adding a large worker-side object, adding a
relocatable local resource, or changing packaged-resource policy. If a small
scalar merely needs to reach a worker, first consider `batchVars` in
`configuration.py`.

### `write_contract.py`

**Purpose.** It writes the self-digested `analysis_contract.json` that records
what the compiled production means.

The contract includes the git SHA/dirty state, era and profiles, execution and
remote-I/O settings, selected samples and file hashes, logical process model,
category expressions/weights/metadata, variable definitions and binning,
nuisances, correction resources, action counts, and output locations. It is
written beside job controls and to the configured output provenance location
where appropriate.

**Customize this file when:** a new runtime choice is needed to reproduce or
audit results. Update `contract_validation.py` and contract tests with every
schema change. Never hand-edit a generated contract to describe different
jobs.

### `contract_validation.py`

**Purpose.** It independently checks that an analysis contract is internally
consistent and agrees with executable configuration objects.

**Use it when:** writing tests, auditing a compiled job, or adding a contract
schema field. Keep it independent enough to catch a writer mistake rather
than merely repeating `write_contract.py` line for line.

## 10. Environment wrappers

Source exactly one site wrapper before compiling a job. These scripts force
the site-sensitive variables rather than retaining stale values from a
previous setup.

### `zzcr_lxplus_env.sh`

Shared-filesystem CERN execution with CERN EOS output. Use it for lxplus
submission when results should remain at CERN. It does not require Condor
runtime packaging.

### `lxplus_env.sh`

The generic lxplus preset retained for compatibility. Its role is equivalent
to the shared CERN-to-CERN workflow; prefer the explicitly named
`zzcr_lxplus_env.sh` in new instructions because the source/destination is
clear at a glance.

### `zzcr_lxplus_fnal_env.sh`

Shared-filesystem CERN execution with FNAL `/store/user/...` output through
XRootD. Use it when compiling/submitting on lxplus while shipping ROOT results
to FNAL. No Condor code package is needed because the CERN worker can use the
shared checkout/environment.

### `fnal_lpc_packaged_env.sh`

Packaged FNAL LPC execution with FNAL output and direct XRootD input reads.
Use it when workers must receive the checkout/runtime payload instead of
seeing a shared source tree. It configures runtime packaging, proxy use,
remote endpoints, and production output defaults.

### Wrapper customization rules

- Site/destination variables should be assigned unconditionally so sourcing a
  new wrapper genuinely changes modes.
- Analysis-scope variables such as year, sample profile, and file limits may
  be exported after sourcing the wrapper for an individual campaign.
- Keep CERN and FNAL usernames explicit when they differ.
- Compile a fresh pickle after changing wrappers; an existing pickle retains
  the old resolved paths and endpoints.
- Do not combine assumptions from two wrappers in one compiled configuration.

## 11. Inspection and storage utilities

These programs are tools; they are not executed by `filesToExec`.

### `inspect_plan.py`

Builds the category/sample/histogram plan without discovering input files. It
reports categories and actions by region/view, variables per category, sample
profile resolution, and expected plot counts. It can regenerate
`development/booking_plan.json` and the profile-comparison receipt.

**Use it:** immediately after changes to profiles, categories, samples, or
histogram activation. It is the fastest structural validation step.

### `inspect_category_occupancy.py`

Runs a bounded selection-only occupancy check on real input. It stages only
the requested input files, slices the alias graph to needed dependencies, and
books category counts rather than the full histogram plan.

**Use it:** after a physics-selection or alias change, when deciding whether a
diagnostic category is populated, or when zero-event behavior needs to be
localized. It is not a replacement for a weighted full production.

### `make_sample_catalog.py`

Independently crawls EOS production layouts and creates/audits sample catalog
information. It is intentionally outside normal configuration compilation.

**Use it:** when discovering a new production or rebuilding an inventory from
storage. Review its output before transferring persistent choices into
`year_config.json`.

### `check_storage_paths_from_list.py`

Compares the storage expectations in `year_config.json` with an external file
or directory inventory and can write an audit receipt.

**Use it:** when production locations or catalogs change, especially before a
multi-era campaign. It checks configuration-to-storage agreement; it does not
prove that every ROOT file is readable or physically valid.

## 12. Tests and what each one protects

Run the suite from the repository root:

```bash
pytest -q PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/tests
```

| Test file | Contract protected | Run especially after |
| --- | --- | --- |
| `tests/conftest.py` | isolated config loading, environment cleanup, shared fixtures | changing how files are loaded |
| `tests/test_year_config.py` | JSON schema, all eras, payloads, profiles, overlap model, paths | era/sample/JSON changes |
| `tests/test_configuration.py` | mode/profile normalization and fail-closed combinations | entry-point changes |
| `tests/test_fnal_io_defaults.py` | forced wrapper values and FNAL/CERN remote-I/O defaults | wrapper or execution-profile changes |
| `tests/test_categories.py` | exact category inventories, metadata, profiles, and budgets | category/profile changes |
| `tests/test_category_algebra.py` | partition truth tables, topology completeness, enriched-DY relations | selection or split-expression changes |
| `tests/test_histogram_registry.py` | immutable registry, applicability, actions, bins, and folds | variables or histogram-policy changes |
| `tests/test_weights.py` | logical overlap and category-weight composition | samples, overlap, correction changes |
| `tests/test_selected_pair_mass.py` | compiled six-pair minimum-mass helper and invalid-input behavior | four-lepton helper changes |
| `tests/test_sparse_runner.py` | sparse booking, variations, category weights, and output writing | custom-runner changes |
| `tests/test_analysis_contract.py` | contract completeness, digest, and executable agreement | writer/schema/provenance changes |

A pure unit test cannot replace a real ROOT schema check. For changes to
aliases, payloads, branches, or C++ helpers, follow the unit suite with a
bounded compile/run against representative DATA and MC.

## 13. Generated, operational, and historical files

The following are products or evidence, not normal customization inputs:

- `configs/config_*.pkl`: compiled configuration snapshots used to execute,
  inspect, or merge the exact job graph;
- `configs/config.json`: human-readable form of the most recently compiled
  snapshot;
- `jobs/<tag>/`: local job controls, logs, contracts, worker payloads, merge
  state, and plots;
- `rootFiles/` or remote campaign directories: split/merged ROOT products;
- `plots/` and plot ZIP files: rendering products;
- `lxplus_jobs/`: locally collected external job configuration snapshots;
- `development/*.json`: generated plan, occupancy, comparison, example
  contract, or pilot receipts;
- `filesToMerge_*.txt`: a merge list artifact. The framework can reconstruct
  merge inputs from the serialized split plan; do not treat a historical list
  as current configuration.

Do not commit new job controls, pickles, ROOT files, caches, plots, or local
test receipts. Existing tracked development evidence should be regenerated by
its producing tool when intentionally updating the documented reference
state, not edited to make it look consistent.

The Markdown files under `development/` have distinct roles:

- `CATEGORY_DESIGN.md`: current category inventory and algebra;
- `SELECTION_SOURCE_NOTE.md`: current source-to-code selection traceability;
- `CATEGORY_REFINEMENT_AUDIT.md`: historical category refinement evidence;
- `PHYSICS_SELECTION_AUDIT.md`: historical physics-selection audit;
- `FNAL_REFACTOR_AUDIT.md`: historical execution/storage refactor audit;
- `FINAL_AUDIT.md`: historical completion snapshot.

When historical audit text disagrees with executable code or the current
top-level docs, inspect the git revision it describes. Do not use an old audit
as a live configuration override.

## 14. Relevant mkShapesRDF core files

These files are outside `ZZ_CR` and normally should not be edited for an
analysis-specific customization. They are useful when tracing behavior.

### `mkShapesRDF/shapeAnalysis/mkShapesRDF.py`

The CLI orchestrator. With `-c 1` it executes and serializes the configuration;
with `-c 0` it reloads a pickle. It resolves remote I/O, selects local/batch
execution, loads `runnerFile`, creates batches, runs locally, and drives merge
or nuisance post-processing modes.

### `mkShapesRDF/shapeAnalysis/ConfigLib.py`

Executes configuration files in a shared namespace and serializes selected
objects to zlib-compressed cloudpickle/pickle plus JSON. This explains both
`filesToExec` ordering and why `varsToKeep` is a persistence API.

### `mkShapesRDF/shapeAnalysis/BatchSubmission.py`

Splits the resolved sample work, generates process scripts/JDLs, assembles any
runtime package and explicit includes, transfers worker inputs, and submits
Condor jobs.

### `mkShapesRDF/shapeAnalysis/runner.py`

The stock RDataFrame engine. It creates sample dataframes, aliases, cuts,
variables, variations, result objects, and output ROOT files. `zz_cr_runner.py`
subclasses it only where the sparse/category-weight contract differs.

### `mkShapesRDF/shapeAnalysis/histo_utils.py`

Contains histogram/nuisance post-processing used by framework merge flows.
Change it only for behavior that should apply to all configurations.

### `mkShapesRDF/lib/search_files.py`

Discovers files from local or remote production directories and applies the
configured discovery/read endpoints. `samples.py` is the analysis-facing
consumer.

### `mkShapesRDF/lib/remote_io.py`

Centralizes XRootD URI construction, remote commands, stage-in/output policy,
and remote file operations. Execution profiles feed it through
`configuration.py` and CLI overrides.

## 15. Common customization recipes

### Add a new era

1. Add the full era block to `year_config.json`.
2. Add/verify luminosity, production steps, MC, DATA runs/streams, triggers,
   lepton IDs, normalization, and plot group coverage.
3. Add explicit BTV correctionlib and efficiency-map paths.
4. Extend schema materialization in `year_config.py` only if the era requires
   a genuinely new concept.
5. Run year/configuration/weight tests and `inspect_plan.py`.
6. Perform bounded DATA and MC compilation/execution before full submission.

### Add a sample or logical process

1. Add its dataset/production definition to `year_config.json`.
2. Assign it to the correct overlap source set and logical output.
3. Add it to a declarative plot group or create a new group.
4. Confirm `structure.py` resolves it completely.
5. Inspect the presentation profile and contract sample inventory.
6. Run a bounded job before full production.

### Change a physical selection

1. Put era-dependent object values in `year_config.json`.
2. Add any new derived quantity in `aliases.py` or a macro.
3. Change the parent/split expression in `category_config.py`.
4. Update the physics source note and configuration contract.
5. Update truth-table/boundary tests.
6. Run plan inspection, bounded occupancy, then representative DATA and MC.

### Add a category

1. Define it and its complete metadata in `category_config.py`.
2. Add it only to the intended category profiles.
3. Define its histogram view/tier policy in `histogram_config.py` if not
   already covered.
4. Update exact inventory and algebra tests.
5. Check action/category budgets with `inspect_plan.py`.

### Add a variable or change binning

1. Edit only the definition in `variables.py`.
2. Ensure any derived expression exists in `aliases.py` first.
3. Select intentional underflow/overflow folding.
4. Add/update activation in `histogram_config.py`.
5. Run registry tests and inspect the bin edges/action plan.
6. Use a bounded ROOT job to catch expression type/schema failures.

### Change which plots appear in a category

1. Leave definitions in `variables.py` unchanged.
2. Modify the profile/view/region policy in `histogram_config.py`.
3. Inspect category-variable counts and both linear/log plot expectations.

### Add or change an event correction

1. Resolve payload paths and era metadata in `year_config.json`.
2. Implement the derived nominal/variation aliases in `aliases.py` and, for
   complex vector logic, a macro.
3. Decide whether the correction belongs in common sample weight or a
   category-specific weight domain.
4. Add nuisance definitions only after nominal behavior is validated.
5. Add focused numerical and integration tests.
6. Confirm paths, names, and resolved weights in `analysis_contract.json`.

### Change submission site or output destination

1. Source the one matching environment wrapper.
2. Export campaign-specific analysis variables after it.
3. Compile a fresh configuration on that site.
4. Submit and later merge using that campaign's own pickle and checkout.
5. Use XRootD/EOS tools appropriate to the destination for operational files;
   do not rewrite analysis source to point at one completed campaign.

## 16. Recommended validation ladder

Use the least expensive check that can catch the class of mistake, then move
down the ladder for changes that affect execution:

1. **Syntax and focused unit tests** for the edited layer.
2. **Full ZZ_CR unit suite** for cross-layer invariants.
3. **Plan inspection** for category/sample/action changes.
4. **Storage/payload checks** for new paths and correction files.
5. **Bounded occupancy** for selection and category changes.
6. **Bounded local or batch ROOT job** for aliases, macros, branch schemas,
   weights, and remote I/O.
7. **Contract inspection** before scaling out.
8. **Small merge and plot smoke test** before a multi-era production when
   histogram/output behavior changed.

Typical structural commands are:

```bash
cd PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR

python inspect_plan.py \
  --year 2024 \
  --analysis-pass ALL \
  --category-profile standard \
  --histogram-profile analysis \
  --sample-profile commissioning

cd ../../..
pytest -q PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/tests
```

Use the exact compile, submit, status, merge, and plotting commands in
`USAGE.MD`; they encode the current CLI and site-specific workflow more
precisely than duplicating them here.

## 17. Review checklist

Before committing a customization, confirm:

- the change is in the authoritative file listed in this guide;
- no generated job, pickle, ROOT, plot, cache, or local receipt is staged;
- selection meaning and metadata still agree;
- every active sample resolves to a plot and structure group;
- every active category resolves at least one valid variable;
- category and action counts remain within their declared budgets;
- underflow and overflow folding are intentional for changed axes;
- correction paths are explicit and available from the execution site;
- the contract records every new choice needed to reproduce the result;
- focused and full tests were run, or any environment-dependent limitation is
  recorded clearly;
- documentation describing the live contract was updated with the code.
