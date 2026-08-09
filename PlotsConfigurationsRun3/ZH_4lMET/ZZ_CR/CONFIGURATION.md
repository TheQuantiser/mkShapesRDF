# ZZ_CR configuration contract

This Run-3 configuration produces compact DY, ZZ-control, and ZH
four-lepton signal-reference histograms for `2022`, `2022EE`, `2023`,
`2023BPix`, and `2024`. The ordinary plotting sample scope is recorded DATA
plus the DY and ZZ MC plot groups. The full source catalog remains available
in `year_config.json` for explicit targeted runs.

## Eras and b tagging

| Era | Luminosity | NanoAOD | Tagger | Loose WP |
| --- | ---: | ---: | --- | ---: |
| 2022 | 8.000 fb^-1 | v12 | PNetB | 0.0470 |
| 2022EE | 26.700 fb^-1 | v12 | PNetB | 0.0499 |
| 2023 | 17.794 fb^-1 | v12 | PNetB | 0.0358 |
| 2023BPix | 9.451 fb^-1 | v12 | PNetB | 0.0359 |
| 2024 | 109.080 fb^-1 | v15 | UParTAK4B | 0.0246 |

The loose WP is read with correctionlib from each era's official, explicit
CVMFS `btagging.json.gz`; the duplicated JSON value is a fail-closed audit
check. The same payload supplies the heavy- and light-flavor fixed-WP scale
factors. Separate process-dependent MC efficiency histograms
`bjet_eff`, `cjet_eff`, and `ljet_eff` are read from the explicit FNAL EOS
XRootD ROOT-file URL. The official correctionlib files do not contain those
histograms.

## Selected objects and physics regions

- `Z0` is the opposite-sign same-flavor pair closest to 91.1876 GeV.
- `X` is the highest-pT non-overlapping opposite-sign pair.
- The four selected indices must be distinct and their total charge must be
  zero. A fifth lepton with pT at least 10 GeV is vetoed.
- The ordered selected-lepton pT thresholds are 25, 15, 10, and 10 GeV.
- The common physical selection requires `m(Z0)>12 GeV`, a 15 GeV Z window,
  and the loose physical b veto for CleanJets above 20 GeV and |eta| below
  2.5.
- ZZCR explicitly requires `X_isSF`, 75 < m(X) < 105 GeV, and PuppiMET below
  35 GeV.
- The XSF signal reference requires 10 < m(X) < 65 GeV, PuppiMET above
  35 GeV, and m4l above 140 GeV.
- The XDF signal reference requires 10 < m(X) < 70 GeV and PuppiMET above
  20 GeV.

The common preselection is the configured trigger-family OR, at least two
leptons, the production-order `L2TightLeading2` decision, and the Run-3
forward-horn jet veto. Selected-index trigger efficiencies are reconstructed
from the canonical TrigMaker payload; stored leading-lepton scalar trigger
weights are regression oracles, not the nominal correction.

## Declarative category model

`category_config.py` is authoritative. The recommended/default `standard`
profile is a declared set of diagnostic projections, not a Cartesian product:

```text
DY:   1 inclusive + 2 Z flavors + 3 streams + 6 stream-by-Z-flavor
ZZCR: 1 inclusive + 3 topologies + 3 streams + 5 curated intersections
SR:   1 inclusive + 2 X flavors + 5 topologies + 3 streams
```

This gives 35 categories. `minimal` preserves exactly `DY_ALL`, `ZZCR_ALL`,
and `SR_ALL`. `flavor`, `stream`, and `trigger` isolate their named use cases;
the trigger views filter on the exclusive `triggerFamilyPriority`, never on
overlapping raw trigger bits. `detailed` adds only six SR
stream-by-`XSF`/`XDF` views. `debug` is the curated detailed/trigger union and
requires `ALLOW_LARGE_PLAN=1`. ZZCR has no impossible XDF category.

The selected-object SR topology map is `4E=ZEE+XEE`, `4MU=ZMM+XMM`,
`2E2MU=(ZEE+XMM)|(ZMM+XEE)`, `3E1MU=ZEE+XDF`, and
`1E3MU=ZMM+XDF`. Tests prove these five leaves exclusive and exhaustive, and
prove all DY/ZZCR partition/intersection identities.

Every category has controlled `view_type`, `partition_family`, within-family
exclusivity, cross-family overlap, and diagnostic-purpose fields. The contract
copies those fields directly, so downstream code never needs to parse IDs.

Each category's metadata is generated from the same registry that materializes
`cuts.py`. It contains its parent and split expressions, full preselection and
cut, display label, weight domain, resolved MC weight, DATA rule, active
variables/binning/nuisances, profiles, year, and git state.

## Sparse histogram model

The persistent registry in `histogram_config.py` holds every supported
expression, title, binning, fold, tag, role, and applicability definition.
Activation is separate and resolved declaratively from
`(physics_region, view_type)`. For 2024 `standard + analysis` there are 509
registry entries, 53 active variables, and 839 actual category-variable
actions:

| View | DY | ZZCR/SR |
| --- | ---: | ---: |
| inclusive | 25 | 50 |
| flavor/topology | 19 | 31 |
| stream/trigger priority | 17 | 25 |
| stream-flavor | 15 | 15 |

Minimal remains 125 actions. Standard is 6.712 times that basic plan and
27.907 times smaller than the previous 23,414-action graph. `flavor`,
`stream`, `trigger`, and `detailed` use 473, 326, 460, and 929 actions. The
local runner books only approved pairs and its conversion/save/merge paths
support the resulting non-rectangular dictionary. Missing pairs are absent,
not empty histograms. Definition hashes and binning never depend on view.

## Nominal weights

The common sample-level MC weight is:

```text
XSWeight * METFilter_Common * puWeight * TriggerSF_event
```

After each category filter, the local runner applies:

```text
DY_*:          SelectedLeptonSF_Z
ZZCR_* / SR_*: SelectedLeptonSF_ZX * BTagVetoSF
```

This permits overlapping regions to receive independent factors in one event
graph. DATA uses `METFilter_DATA` and the exclusive per-run stream trigger
rule, never MC scale factors.

## Samples and overlap

The resolved `Vg`, `VgS`, `WZ`, and `ZZ` partitions are constructed from
disjoint source/phase-space components in `year_config.json`. Validation
requires each physical source to be consumed exactly once or passed through,
unique output names, and production-normalization aliases that belong to an
active source. The default plotting activation then selects only DY, ZZ, and
DATA. `SAMPLE_FILTER` is an explicit targeted override; `DATA_STREAM_FILTER`
can restrict the logical DATA process to MuonEG, Muon, and/or EGamma inputs.

## Reproducibility and systematics

Every compile writes a self-digested `analysis_contract.json` beside the job
controls and in the durable configs directory. It records exact cuts, weights,
variables/binning, active inputs, overlap model, nuisances, endpoints,
profiles, hashes, timestamp, and git state.

Sparse ROOT variations are retained by the local runner. Unified
`ANALYSIS_PASS=ALL` with systematics is nevertheless fail-closed because ROOT
does not permit redefining a weight column that already depends on variations.
The commissioned one-graph workflow is therefore nominal-only. This explicit
limitation avoids silently incorrect systematic histograms.

Operational setup, planning, direct packaged FNAL XRootD reads, optional local
or worker stage-in, contract inspection, status, and merge commands are in
`USAGE.MD`. The FNAL wrapper defaults to
`packaged_fnal_xrootd_eos_production`; the explicit
`packaged_fnal_stagein_eos_production` profile remains available.
