# Trigger scale-factor calculation

This document describes the trigger-efficiency and trigger scale-factor
contract used by the `ZZ_CR` configuration. The central rule is simple:

- DY categories use exactly the two leptons selected as `Z0_idx`;
- FOURL, ZZCR, and SR use exactly the four leptons selected as
  `Z0_idx + X_idx`;
- the generic all-lepton event result and the stored leading-lepton branches
  are diagnostics only and are not nominal analysis weights.

The calculation reuses the canonical mkShapesRDF TrigMaker payload readers and
algebra. The local code adapts that calculation to the analysis-selected
indices; it does not maintain a second copy of the era payload.

## Implementation map

| File | Responsibility |
| --- | --- |
| `selected_trigger_adapter.py` | Declares the canonical TrigMaker C++ payload and functions for the selected era. |
| `macros/four_lepton_helpers.cc` | Recovers pre-LeptonScaleSmearing pT and PDG ID in the final `Lepton` index order. |
| `macros/selected_trigger_wrappers.cc` | Validates, compacts, pT-sorts, and evaluates exactly the selected lepton set. |
| `aliases.py` | Defines the RDataFrame result vectors and public efficiency/SF aliases. |
| `category_config.py` | Applies `TriggerSF_Z` or `TriggerSF_ZX` once in the appropriate region weight policy. |
| `samples.py` | Keeps the unified `ALL` sample weight free of a generic trigger SF; focused passes place the selected trigger SF at sample level. |
| `nuisances.py` | Uses the same selected-object trigger contract for nominal/up/down ratios in focused systematic passes. |
| `histogram_config.py` and `variables.py` | Expose the appropriate selected trigger SF as a region-specific diagnostic histogram. |

## 1. Declaring the canonical TrigMaker calculation

`selected_trigger_adapter.declare_canonical_trigger(era)` constructs the
standard mkShapesRDF `TrigMaker` module with:

```python
TrigMaker(
    era=era,
    isData=False,
    keepRunP=True,
    seeded=False,
    computeSF=True,
)
```

It runs the module on a declaration-only no-op dataframe. This asks TrigMaker
to declare its era-specific payload readers and canonical C++ functions in the
active ROOT interpreter without producing another run-period column or
changing framework source files.

Only one TrigMaker era may be declared in a process. Attempting to declare a
different era later fails explicitly because the generated C++ names are
process-global. The era comes from the resolved `l2tight_era` in
`year_config.json`.

The canonical functions used by the selected-object wrapper include:

- `get_eff`: data or MC single-/double-trigger leg efficiencies;
- `get_dz_eff`: the dilepton DZ efficiency, including its dependence on the
  number of good primary vertices;
- `get_gl_eff`: global trigger-efficiency terms for the flavor combination;
- `drll_sf`: the dilepton angular-separation correction;
- `get_w`: the canonical two-lepton event efficiency and SF algebra;
- `get_nlw`: the canonical four-lepton event efficiency and SF algebra;
- `get_sf` and `get_sf_unc`: the canonical efficiency-ratio and uncertainty
  helpers used by the diagnostic many-lepton path.

The local wrapper calls these declared functions; payload lookup and the
physics formula remain owned by TrigMaker.

## 2. Aligning selected indices with trigger-era kinematics

TrigMaker runs before `LeptonScaleSmearing`. The final `Lepton_*` collection
may therefore have a different pT order from the collection on which the
trigger payload was evaluated. Applying a final `Z0_idx` directly to an
unaligned pre-scale vector could select the wrong object.

The aliases solve this by constructing:

```text
ProductionLeptonPt
ProductionLeptonPdgId
```

`FourLepton::productionAlignedPt` and
`FourLepton::productionAlignedPdgId` match the final selected leptons to the
pre-scale `VetoLepton_*` source using the unchanged eta/phi coordinates, with
one-to-one matching and tight numerical tolerances. They return pre-scale pT
and PDG ID in final `Lepton` index order. Consequently, the same `Z0_idx` and
`X_idx` values consistently address:

- `ProductionLeptonPt` for trigger-payload pT;
- `Lepton_eta` and `Lepton_phi` for the selected directions;
- `ProductionLeptonPdgId` for the trigger flavor and charge convention.

Invalid, ambiguous, non-finite, or nonphysical alignment returns an empty
vector and is handled by the neutral-result path below.

## 3. Exact selected-Z calculation for DY

`aliases.py` defines:

```text
TriggerResult_Z = SelectedTrigger::selectedPairResult(
    ProductionLeptonPt,
    Lepton_eta,
    Lepton_phi,
    ProductionLeptonPdgId,
    Z0_idx,
    PV_npvsGood,
    run_period
)
```

`selectedPairResult` performs these steps:

1. Require at least two entries in `Z0_idx`.
2. Compact exactly `{Z0_idx[0], Z0_idx[1]}`—no other event lepton is
   considered.
3. Reject negative/out-of-range indices, duplicate indices, non-electron or
   non-muon flavors, non-finite kinematics, and nonpositive pT.
4. Sort those two selected leptons by production-aligned pT while applying the
   identical permutation to eta, phi, and PDG ID.
5. Compute their `deltaR`.
6. Evaluate canonical data and MC efficiencies with `get_eff`, the DZ term
   with `get_dz_eff`, the global term with `get_gl_eff`, and the angular term
   with `drll_sf`.
7. Pass those values to canonical `get_w` and expose its nominal/down/up
   efficiency and SF projections.

The public nominal DY correction is:

```text
TriggerSF_Z
```

Thus the selected Z need not be the production-leading pair. The calculation
follows the actual `Z0_idx` choice exactly.

## 4. Exact selected-four-lepton calculation

`TriggerResult_ZX` calls `SelectedTrigger::selectedFourResult` with the same
aligned inputs and both selected index vectors. It compacts exactly:

```text
{Z0_idx[0], Z0_idx[1], X_idx[0], X_idx[1]}
```

The wrapper rejects invalid or duplicate indices, sorts exactly those four
objects by production-aligned pT, and calls canonical `get_nlw`. Its public
nominal correction is:

```text
TriggerSF_ZX
```

This is the trigger SF used by FOURL, ZZCR, and SR. It is not used by DY.

`TriggerResult_event` can evaluate the complete aligned production-source
lepton set, including a generalized path for more than four leptons. It is
retained for diagnostics and regression studies; `TriggerSF_event` is not a
nominal region weight.

## 5. Result-vector and public-alias contract

Every selected trigger result is normalized to this eight-element layout:

| Index | Public alias suffix | Meaning |
| ---: | --- | --- |
| 0 | `TriggerEffData_*` | Data efficiency, nominal. |
| 1 | `TriggerEffData_*_Down` | Data efficiency, down variation. |
| 2 | `TriggerEffData_*_Up` | Data efficiency, up variation. |
| 3 | `TriggerEffMC_*` | MC efficiency corresponding to the nominal result. |
| 4 | `TriggerSF_*` | Nominal data/MC scale factor. |
| 5 | `TriggerSF_*_Down` | Down scale-factor projection. |
| 6 | `TriggerSF_*_Up` | Up scale-factor projection. |
| 7 | `TriggerSF_*_Valid` | One for a finite canonical result; zero for a neutral fallback. |

Here `*` is `Z`, `ZX`, or `event`. `SelectedTrigger::expose` converts the
canonical TrigMaker result layout into this stable local layout and checks all
public values for finiteness.

If the selected inputs or canonical result are invalid, the wrapper returns:

```text
data efficiencies = 1
MC efficiency      = 1
scale factors      = 1
validity           = 0
```

This keeps diagnostic columns finite while making loss of trigger-payload
coverage visible through `TriggerSF_*_Valid`.

For DATA, every public `TriggerSF_*`, variation, and validity alias is forced
to one. DATA event weights use the DATA MET filter and exclusive stream
trigger de-duplication; no MC trigger correction is applied.

## 6. Nominal weight placement and duplication prevention

For unified nominal production (`ANALYSIS_PASS=ALL`), the common MC weight is:

```text
lumi * XSWeight * METFilter_Common * puWeight
```

The local runner then applies one region policy after the corresponding
region filter:

| Region | Branch-local correction |
| --- | --- |
| DY, including Enriched DY and all DY subcategories | `SelectedLeptonSF_Z * TriggerSF_Z` |
| FOURL | `SelectedLeptonSF_ZX * TriggerSF_ZX` |
| ZZCR and SR | `SelectedLeptonSF_ZX * TriggerSF_ZX * BTagVetoSF` |

The generic `TriggerSF_event` is deliberately absent from the common weight.
Therefore the selected trigger SF is applied exactly once, and overlapping DY
and four-lepton regions can use different selected-object domains in the same
event graph.

For focused passes (`ZPARENT`, `FOURL_BASE`, or `CONTROL`), `samples.py` moves
the same complete selected-object correction into the sample weight and
`build_categories` sets the runner factor to `1.f`. The two placements are
mutually exclusive. The same rule prevents duplication of `BTagVetoSF`:
ZZCR/SR receive one SF, DY receives none, and the boolean
`physicalBtagVeto` cut is an event selection rather than a second weight.

## 7. Trigger variations

Unified `ANALYSIS_PASS=ALL` production is nominal-only and fails closed if
systematics are enabled because branch-local weight redefinition cannot be
safely combined with the current variation graph.

Focused systematic passes use the trigger contract declared by the pass:

- `ZPARENT`: `TriggerSF_Z_{Up,Down} / TriggerSF_Z`;
- `FOURL_BASE` and `CONTROL`:
  `TriggerSF_ZX_{Up,Down} / TriggerSF_ZX`.

The ratio helper returns one when the nominal SF is zero, avoiding a division
by zero while leaving the validity histogram available for diagnosis.

## 8. Regression oracles and validation

The stored NanoAOD-style branches `TriggerSFWeight_2l`,
`TriggerSFWeight_4l`, and their variations are retained as regression oracles.
The `TriggerResult_storedLeading2Oracle` and
`TriggerResult_storedLeading4Oracle` aliases reconstruct the corresponding
production-leading calculations. They are not forwarded into nominal DY,
ZZCR, or SR weights.

Relevant automated checks include:

- `tests/test_weights.py`: verifies exact `Z0_idx` routing, selected trigger
  weight placement, absence of `TriggerSF_ZX` from DY, and zero/one b-tag-SF
  multiplicity;
- `tests/test_categories.py`: verifies focused and unified region correction
  contracts;
- `tests/test_histogram_registry.py`: verifies DY exposes `TriggerSF_Z` while
  four-lepton regions expose `TriggerSF_ZX`;
- `tests/test_year_config.py`: verifies every era resolves a canonical
  TrigMaker trigger-path contract.

When modifying this machinery, run:

```bash
source start.sh
python -m pytest -q PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/tests
```

Any change to the selected-object interface, TrigMaker result layout, weight
placement, or DATA fallback should be accompanied by a focused regression
test before production submission.
