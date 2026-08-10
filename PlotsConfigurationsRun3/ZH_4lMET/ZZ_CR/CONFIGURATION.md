# ZZ_CR configuration contract

For a file-by-file map of the implementation, execution order, authoritative
customization points, and validation expectations, see
[`FILE_GUIDE.md`](FILE_GUIDE.md).

This Run-3 configuration produces compact DY, ZZ-control, and ZH
four-lepton signal-reference histograms for `2022`, `2022EE`, `2023`,
`2023BPix`, and `2024`. `SAMPLE_PROFILE=commissioning` selects DATA plus the
DY and ZZ MC plot groups for quick development. `SAMPLE_PROFILE=presentation`
selects the complete configured prompt process model and target ZH/ggZH
signal for presentation production.

The live default and the latest full-production contract are independent
choices along the category and sample axes:

| Use | Category profile | Sample profile | Categories | Actions |
| --- | --- | --- | ---: | ---: |
| Ordinary commissioning | `standard` | `commissioning` | 47 | 1,043 |
| Full detailed presentation | `detailed` | `presentation` | 53 | 1,133 |

Both use `ANALYSIS_PASS=ALL`, `HISTOGRAM_PROFILE=analysis`, nominal-only
histograms, and the same physics selections, weights, and variable
definitions. The six categories added by `detailed` are the SR
stream-by-`XSF`/`XDF` projections; changing the sample profile never changes
the category graph.

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
  Candidate construction requires both Z0 leptons to exceed 10 GeV.
- `X` is the non-overlapping opposite-sign pair with the highest leading
  lepton pT, breaking ties with the subleading lepton pT.
- Every DY category, including the Enriched DY mirrors, requires the two
  selected Z0 leptons after pT sorting to exceed 25 and 15 GeV. This DY-only
  requirement is attached directly to the `DY` entry in `REGION_REGISTRY`;
  it is not inherited by FOURL, ZZCR, or SR.
- The four selected indices must be distinct and their total charge must be
  zero. A fifth lepton with pT at least 10 GeV is vetoed.
- The ordered Z0+X four-lepton pT thresholds used by ZZCR/SR are 25, 15, 10,
  and 10 GeV.
- The common physical ZZCR/SR selection requires
  `minSelectedPairMass>12 GeV`, where the minimum is evaluated over all six
  unordered pairs formed from exactly the selected Z0+X leptons. Invalid,
  duplicate, or non-finite selected inputs fail closed. This veto is not part
  of the DY selection. The value is an executable alias used by the cuts, not
  an additional histogram action. The 15 GeV Z window remains independent,
  followed by the loose physical b veto for CleanJets above 20 GeV and |eta|
  below 2.5.
- ZZCR explicitly requires `X_isSF`, 75 < m(X) < 105 GeV, and PuppiMET below
  35 GeV.
- The XSF signal reference requires 10 < m(X) < 65 GeV, PuppiMET above
  35 GeV, and m4l above 140 GeV.
- The XDF signal reference requires 10 < m(X) < 70 GeV and PuppiMET above
  20 GeV.

These numerical region definitions reproduce AN2019/238 v9. Table 37 on PDF
page 120 (document page 118) explicitly gives the XSF upper edge as 65 GeV;
Section 7.4 and Table 39 on PDF page 132 (document page 130) define the ZZ
control region. The complete source record, including the rendered Table 37
low-mass row and the explicit six-pair Run-3 implementation, is in
`development/SELECTION_SOURCE_NOTE.md`.

The common preselection is the configured trigger-family OR, at least two
leptons, the production-order `L2TightLeading2` decision, and the Run-3
forward-horn jet veto. Selected-index trigger efficiencies are reconstructed
from the canonical TrigMaker payload. DY evaluates `TriggerSF_Z` from exactly
the two selected `Z0_idx` leptons after sorting that pair by pT; ZZCR/SR
evaluate `TriggerSF_ZX` from exactly the selected Z0+X quartet. Stored
leading-lepton scalar trigger weights are regression oracles, not the nominal
correction.

The resolved `trigger_paths` for each era are checked fail-closed against the
complete DATA/MC HLT-path union in that era's canonical mkShapesRDF
`TrigMaker_cfg.py` entry. The five current Run 3 eras genuinely share the same
seven paths, so they inherit one `year_defaults.trigger_paths` definition;
future era-specific differences must be supplied as per-year overrides.

## Declarative category model

`category_config.py` is authoritative. The recommended/default `standard`
profile is a declared set of diagnostic projections, not a Cartesian product:

```text
DY:   1 inclusive + 2 Z flavors + 3 streams + 6 stream-by-Z-flavor,
      plus a signal-Z-window enriched mirror of all 12 projections
ZZCR: 1 inclusive + 3 topologies + 3 streams + 5 curated intersections
SR:   1 inclusive + 2 X flavors + 5 topologies + 3 streams
```

This gives 47 categories. `DY_ENRICHED` is an overlapping projection defined
by `abs(Z0_mass - 91.1876) < 15`, the same Z window used by ZZCR/SR. Every
ordinary DY subcategory has a corresponding `DY_ENRICHED_*` projection with
the same histogram tier and DY weight. `minimal` preserves
exactly `DY_ALL`, `DY_ENRICHED`, `ZZCR_ALL`, and `SR_ALL`. `flavor`, `stream`,
and `trigger` isolate their named use cases;
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
registry entries, 53 active variables, and 1,043 actual category-variable
actions after mirroring every DY subcategory in the enriched window:

| View | DY | ZZCR/SR |
| --- | ---: | ---: |
| inclusive | 25 | 50 |
| flavor/topology | 19 | 31 |
| stream/trigger priority | 17 | 25 |
| stream-flavor | 15 | 15 |

Minimal is 150 actions. Standard is 6.953 times that basic plan and
22.449 times smaller than the previous 23,414-action graph. `flavor`,
`stream`, `trigger`, and `detailed` use 536, 402, 570, and 1,133 actions. The
local runner books only approved pairs and its conversion/save/merge paths
support the resulting non-rectangular dictionary. Missing pairs are absent,
not empty histograms. Definition hashes and binning never depend on view.

The fail-closed default budgets leave a small explicit margin above each live
plan:

| Profile | Categories | Category budget | Actions | Action budget |
| --- | ---: | ---: | ---: | ---: |
| `minimal` | 4 | 6 | 150 | 200 |
| `standard` | 47 | 50 | 1,043 | 1,100 |
| `flavor` | 18 | 20 | 536 | 700 |
| `stream` | 16 | 20 | 402 | 500 |
| `trigger` | 24 | 30 | 570 | 700 |
| `detailed` | 53 | 60 | 1,133 | 1,200 |
| `debug` | 73 | 50 | 1,553 | 1,200 |

`debug` intentionally exceeds both defaults and therefore requires
`ALLOW_LARGE_PLAN=1`; the other profiles run without that override.

The current presentation axes keep five-GeV mass bins across 80--100 GeV:

```text
Z0_mass, X_mass: 30, 40, 60, 80, 85, 90, 95, 100, 120 GeV
Z0_pt, X_pt:     0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40,
                  50, 60, 70, 80, 100, 120 GeV
```

All four axes use `fold=3`, so underflow enters the first visible bin and
overflow enters the last. `Z0_pt` and `X_pt` deliberately share the same
progressive 2/5/10/20 GeV-width axis.

## Nominal weights

The common sample-level MC weight is:

```text
XSWeight * METFilter_Common * puWeight
```

After each category filter, the local runner applies:

```text
DY_*:          SelectedLeptonSF_Z * TriggerSF_Z
ZZCR_* / SR_*: SelectedLeptonSF_ZX * TriggerSF_ZX * BTagVetoSF
```

The selected trigger factors use the adapted TrigMaker algebra described
above. Keeping them branch-local permits overlapping regions to receive the
correct object-domain factors exactly once in one event graph. DATA uses
`METFilter_DATA` and the exclusive per-run stream trigger rule, never MC scale
factors.

## Samples and overlap

The resolved `Vg`, `VgS`, `WZ`, and `ZZ` partitions are constructed from
disjoint source/phase-space components in `year_config.json`. Validation
requires each physical source to be consumed exactly once or passed through,
unique output names, and production-normalization aliases that belong to an
active source.

`SAMPLE_PROFILE=commissioning` is the default and activates only the live DY
and ZZ plot-group members plus `DATA`. `SAMPLE_PROFILE=presentation` derives
its inventory from all live `plot_groups` and requires complete, unique
coverage of every resolved logical MC output. That includes DY, ZZ, WZ, Vg,
VgS, WW, ggWW, top, ttV/tZ, VVV, the target ZH/ggZH H→WW signal, and other
configured Higgs contamination. Nonprompt/fake background is not included in
this configuration. `SAMPLE_FILTER` is the stronger exact override for
targeted runs. `DATA_STREAM_FILTER` can restrict the logical DATA process to
MuonEG, Muon, and/or EGamma inputs.

`SAMPLE_PROFILE`, its groups, the profile inventory, the actual selection
source, and active samples are recorded in `analysis_contract.json`. The
output tag includes the profile name, so commissioning and presentation
outputs cannot collide.

The current resolved sample counts are:

| Era | Commissioning outputs | Presentation outputs |
| --- | ---: | ---: |
| 2022 | 4 | 53 (52 MC + DATA) |
| 2022EE | 4 | 53 (52 MC + DATA) |
| 2023 | 4 | 53 (52 MC + DATA) |
| 2023BPix | 4 | 53 (52 MC + DATA) |
| 2024 | 8 | 55 (54 MC + DATA) |

The 2024 commissioning scope is six DY outputs, ZZ, and DATA. The earlier
eras resolve fewer commissioning DY aliases but the same group-based rule.
All counts are derived checks, not a second hard-coded sample list.

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

Operational setup, planning, CERN shared-checkout submission, direct packaged
FNAL XRootD reads, optional local or worker stage-in, contract inspection,
status, and merge commands are in `USAGE.MD`.

Direct CERN XRootD reads are the ordinary FNAL mode for both local validation
(`local_xrootd`) and packaged Condor production
(`packaged_fnal_xrootd_eos_production`). Whole-file stage-in remains an
explicit diagnostic/fallback mode and is never selected implicitly.

The site environment scripts are reset scripts. Each one unconditionally
replaces its execution profile, I/O modes, packaging mode, include base, proxy
policy, endpoints, site preset, output user, and default campaign so values
from a previously sourced site cannot leak into a new submission. Identity
inputs such as `CERN_USER` or `FNAL_USER` may be set before sourcing; deliberate
analysis or profile overrides must be set afterward. Re-sourcing resets them.

`zzcr_lxplus_env.sh` selects the non-packaged
`shared_xrootd_eos_production` profile for CERN input and CERN CMS Store
output. `zzcr_lxplus_fnal_env.sh` selects the non-packaged
`shared_xrootd_fnal_eos_production` profile for CERN input and FNAL CMS Store
output. `fnal_lpc_packaged_env.sh` forcibly selects
`packaged_fnal_xrootd_eos_production`; the explicit
`packaged_fnal_stagein_eos_production` profile remains available when selected
after sourcing the wrapper.
