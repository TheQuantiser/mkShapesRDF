# ZH4l architecture

## Dependency and physics model

```text
common ─────► ZZCR
   │
   ├────────► Pairing
   │
   └────────► Closure

event → eligible leptons → selected Z → selected X → Z+X quartet
      → observables → predicates → region → correction weight
```

`ZZCR`, `Pairing`, and `Closure` are complete mkShapesRDF leaves.  A leaf may
choose common definitions but cannot own or modify them, and it must never
import another leaf.  `common` cannot import a leaf.

The directory follows the familiar public `PlotsConfigurationsRun3` mental
model: `samples.py` owns processes and base weights; `aliases.py` derived
columns; `cuts.py` regions; `variables.py` histogram axes; `plot.py` display;
`structure.py` signal/data/background bookkeeping; `nuisances.py`
uncertainties; and `configuration.py` orchestration.  Multi-era content is
shared rather than cloning five leaf directories.

## Ownership

| Concept | Authoritative owner | Leaf responsibility |
|---|---|---|
| Era metadata, luminosity, productions, WPs, payload locations, raw inventory | `common/eras.json`, materialized by `common/eras.py` | Select `ERA` only |
| Logical processes, overlap/stitching, sample scopes | `common/catalog.py` using native `SearchFiles` | State correction domain and optional scope |
| Nominal selected Z and complementary X | `common/objects.py` + `common/macros/objects.cc` | Consume aliases |
| Shared kinematics | `common/objects.py`, `common/observables.py` | Opt into a short explicit variable list |
| Selected-index lepton and trigger SFs | `common/corrections.py`; canonical payload code declared through TrigMaker | Choose `Z` or `ZX` domain visibly |
| Loose 20-GeV b veto and exact event SF | `common/corrections.py` + `common/macros/btag.cc` | Use `bVeto`, `bVetoSF` |
| Process colors/groups/structure | era catalog + `common/presentation.py` | Instantiate standard dictionaries |
| Physics regions and study questions | each leaf's `cuts.py`/study config | Keep local |
| Pairing truth and alternative scores | `Pairing/macros/pairing.cc` | Pairing only |
| DY→ZZ stages and sparse axes | `Closure/study_config.py`, `Closure/variables.py` | Closure only |
| Endpoints, package mode, proxy/stage-out | `common/runtime.py`, `env/*.sh` | No physics values |

## Analyst-facing alias contract

Public physics names are concise and unprefixed. Implementation-only columns
begin with `ZH4l_`. Functions/values, predicates, regions, and weights remain
separate: weights do not occur in cuts and cuts do not occur in variables.

| Legacy name | Public name | Meaning |
|---|---|---|
| `Z0_idx` | `Z_idx` | selected OSSF pair closest to the Z mass under validated ID/pT rules |
| `X_idx` | `X_idx` | validated complementary selected pair |
| `hasValidZ0`, `hasValidX`, `selectedIndicesDistinct` | `validZ`, `validX`, `validZX` | fail-closed object predicates |
| `Z0_mass`, `Z0_pt`, `Z0_eta`, `Z0_phi` | `mZ`, `ptZ`, `etaZ`, `phiZ` | selected-Z kinematics |
| `X_mass`, `X_pt`, `X_eta`, `X_phi` | `mX`, `ptX`, `etaX`, `phiX` | selected-X kinematics |
| `m4l`, `pT4l`, `phi4l` | `m4l`, `pt4l`, `phi4l` | quartet kinematics |
| `minSelectedPairMass`, `sumLeptonCharge` | `minMll4l`, `q4l` | all-pair minimum and quartet charge |
| `Passes2lOrderedPt`, `Passes4lOrderedPt` | `passZPt`, `pass4lPt` | strict ordered pT predicates |
| `fifthLeptonVeto`, `physicalBtagVeto` | `veto5l`, `bVeto` | fifth-lepton and loose 20-GeV b vetoes |
| `Z0_isEE`, `Z0_isMM` | `isZee`, `isZmm` | selected-Z flavor |
| `X_isEE`, `X_isMM`, `X_isSF`, `X_isDF` | `isXee`, `isXmm`, `isXSF`, `isXDF` | selected-X flavor |
| `SelectedLeptonSF_Z`, `SelectedLeptonSF_ZX` | `LepSF_Z`, `LepSF_ZX` | selected lepton correction domain |
| `TriggerSF_Z`, `TriggerSF_ZX` | unchanged | selected trigger correction domain |
| `BTagVetoSF` | `bVetoSF` | fixed-WP event correction |
| `dataStreamPriority`, `triggerFamilyPriority` | `streamPriority`, `triggerPriority` | Closure-only partitions |

Never redefine native `mll` as selected-Z mass and never repurpose
`TriggerSFWeight_2l/4l`; those names have native leading-object semantics.
`bVeto` is an intentional identical-semantic reuse of the conventional loose
20-GeV physical veto. A diagnostic threshold is explicitly `bVeto30`.
`common/alias_contract.py` and its tests classify and enforce these decisions.

Recommended case:

- scalars: `mZ`, `pt4l`, `minMll4l`, `q4l`;
- booleans: `validZX`, `pass4lPt`, `veto5l`, `bVeto`;
- corrections: `LepSF_ZX`, `TriggerSF_ZX`, `bVetoSF`;
- configuration constants: `UPPER_SNAKE_CASE`;
- official sample identifiers: unchanged.

## Runner decisions

| Leaf | Runner | Decision |
|---|---|---|
| ZZCR | native `default` | Once DY/closure projections are separated, every category has the same selected-ZX correction domain and the compact 6×9 booking is rectangular. Native RunAnalysis is sufficient. |
| Pairing | local `runner.py` | Retained because the same graph/observable must be booked with per-variable scalar/vector raw, signed, and absolute study weights. The adapter subclasses native RunAnalysis and delegates normal processing. |
| Closure | local `runner.py` | Retained because 54 stages use a sparse 295-action cut-variable matrix and stage/variable-specific factors. Native RunAnalysis has a single normal weight path and rectangular booking. |

The selected-trigger adapter is also retained narrowly: it declares canonical
TrigMaker payload readers/formulae once and changes only the object domain from
native leading leptons to the explicitly selected Z/ZX indices.  The b-tag
helper is retained because inspected native utilities do not implement the
exact validated veto-efficiency event ratio with the same CleanJet acceptance.

## Adding a study

1. Create one sibling leaf with the standard eight files; do not add an empty
   era directory.
2. Put the family directory on `sys.path`, resolve `ERA` through
   `common.eras`, and instantiate common object/correction/observable builders.
3. Keep the scientific question—truth logic, stages, regions, or special
   histograms—in the new leaf.
4. Add only aliases that are genuinely study-local. Extend `common` only for a
   channel definition, a service needed by the family, or physics used by at
   least two leaves.
5. Add the leaf to the collision test and prove any custom runner is necessary.
6. Add bounded tests, a README, and ignored campaign output paths.
