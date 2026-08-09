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

`category_config.py` is authoritative. The default `minimal` profile is:

```text
DY_ALL
ZZCR_ALL
SR_ALL
```

The `flavor` profile adds `DY_ZEE`, `DY_ZMM`, `ZZCR_4E`, `ZZCR_4MU`,
`ZZCR_2E2MU`, `SR_XSF`, and `SR_XDF`. ZZCR has no impossible XDF category.
The bounded `stream`, `trigger`, and `debug` profiles add diagnostics without
an implicit stream-by-flavor Cartesian product. Trigger family/path and DATA
stream priorities are ordinary default variables, so routine production does
not multiply every kinematic histogram by those axes.

Each category's metadata is generated from the same registry that materializes
`cuts.py`. It contains its parent and split expressions, full preselection and
cut, display label, weight domain, resolved MC weight, DATA rule, active
variables/binning/nuisances, profiles, year, and git state.

## Sparse histogram model

The persistent registry in `histogram_config.py` holds every supported
expression, title, binning, fold, tag, role, and applicability definition.
Activation is separate. For the 2024 `minimal + analysis` default there are
509 registry entries, 53 active variables, and only 125 actual
category-variable actions:

| Category | Booked variables |
| --- | ---: |
| `DY_ALL` | 25 |
| `ZZCR_ALL` | 50 |
| `SR_ALL` | 50 |

The previous graph had 46 categories by 509 variables, or 23,414 actions; the
default is reduced by a factor of 187.312. The local runner books only the
approved pairs and its conversion/save/merge paths support the resulting
non-rectangular dictionary. Missing pairs are absent, not empty histograms.

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

Operational setup, planning, local stage-in, packaged FNAL Condor, contract
inspection, status, and merge commands are in `USAGE.MD`.
