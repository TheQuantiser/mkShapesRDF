# ZZ_CR configuration summary

This configuration builds Run-3 two- and four-lepton control/reference
histograms for `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`. The active
DY+ZZ plotting production retains recorded DATA and enables only the `DY` and
`ZZ` MC plot groups; the complete sample catalog remains in
`year_config.json`.

## Eras and inputs

| Era | Luminosity | NanoAOD schema | Fixed-WP tagger and loose WP |
| --- | ---: | --- | --- |
| 2022 | 8.000 fb^-1 | v12 | PNetB, 0.0470 |
| 2022EE | 26.700 fb^-1 | v12 | PNetB, 0.0499 |
| 2023 | 17.794 fb^-1 | v12 | PNetB, 0.0358 |
| 2023BPix | 9.451 fb^-1 | v12 | PNetB, 0.0359 |
| 2024 | 109.080 fb^-1 | v15 | UParTAK4B, 0.0246 |

MC and DATA are read from the configured HWWNano productions. DATA uses the
MuonEG, Muon/Muon0/Muon1, and EGamma/EGamma0/EGamma1 streams available in each
era. Stream-trigger weights make those streams exclusive. The active MC
processes are ordinary DY samples and the overlap-resolved inclusive `ZZ`
sample; DYG is not part of the DY plot group.

## Physics objects

- Leptons are the HWWNano merged `Lepton` collection. The common production
  gate requires at least two leptons and the production-order
  `L2TightLeading2` decision. Pre-scale `VetoLepton` coordinates recover the
  exact ordering used by the upstream l2tight step.
- Pair IDs require both leptons to pass
  `mvaWinter22V2Iso_WP90_tthMVA_Run3` for electrons or
  `cut_TightID_pfIsoTight_HWW_tthmva_67` for muons. Z leptons require
  leading/subleading pT > 25/10 GeV, while X leptons require > 10/10 GeV.
  These thresholds come from `year_config.json`.
- `Z0` is the opposite-sign, same-flavor pair closest to 91.1876 GeV. `X` is
  the highest-pT non-overlapping opposite-sign pair; it may be same- or
  different-flavor unless a region says otherwise.
- Four-lepton observables (`m4l`, `pT4l`, angular separations, recoil, and MET
  angles) are constructed from the selected `Z0` and `X` indices.
- Jets use `CleanJet`; the common detector-quality veto rejects events with a
  30 < pT < 50 GeV jet at 2.5 < |eta| < 3.0 (`nJetInHorn == 0`).
- The physical b veto considers CleanJets with pT > 20 GeV and |eta| < 2.5.
  A separate diagnostic `bVeto` uses pT > 30 GeV.
- Trigger objects are flavor-matched to leptons by nearest delta-R < 0.1,
  with NanoAOD-v12/v15 filter-bit decoding kept era-specific.

## Common event selection

All passes require the OR of the configured e-mu, single-muon, double-muon,
single-electron, and double-electron triggers, `nLepton >= 2`, the production
l2tight gate, and the forward-horn jet veto.

| Pass | Cuts and purpose |
| --- | --- |
| `ALL` | Default nominal production containing every category below. It applies declarative per-category weights in the configuration-local runner. |
| `ZPARENT` | The inclusive Z/DY two-lepton baseline with the complete stream × Z flavour × `X_NA` matrix. |
| `FOURL_BASE` | Adds `nLepton >= 4`, valid and distinct `Z0/X` indices, `m(X) > 4 GeV`, `m4l > 0`, and total selected-lepton charge zero. No b veto or ordered four-lepton pT requirement is applied. |
| `CONTROL` | Implements the AN2019/238 ZZ-control and signal regions. It adds ordered selected-lepton pT > 25/15/10/10 GeV, the fifth-lepton veto, `m(Z0) > 12 GeV`, physical b veto, and `|m(Z0)-91.1876| < 15 GeV`. |

The `CONTROL` children are:

- ZZ control region: 75 < m(X) < 105 GeV and PuppiMET pT < 35 GeV. Its XSF
  cells are the nominal AN2019/238 ZZ control region; XDF cells are explicit
  validation slices under the same sideband selection.
- Same-flavor signal region: 10 < m(X) < 65 GeV, PuppiMET pT > 35 GeV,
  and m4l > 140 GeV.
- Different-flavor signal region: 10 < m(X) < 70 GeV and PuppiMET pT >
  20 GeV.

The `signal_region` parent is the union of those XSF and XDF signal
expressions. Its X-flavour matrix predicates project that union into disjoint
XEE, XMM, and XDF cells. XEE and XMM are the two atomic components of the
physical XSF branch, and together the three leaf families exhaust the parent
union.

The fifth-lepton veto rejects a fifth lepton with pT >= 10 GeV.

The selections are deliberately incremental: `four_lepton_base` extends
`inclusive_z_dy`; the common physical four-lepton requirements extend that
base; and `zz_control_region` and `signal_region` are the final mutually
distinct physical selections. No independent selection bypasses the DY baseline.

```text
inclusive_z_dy
└── four_lepton_base
    └── physical common selection
        ├── zz_control_region (XSF nominal, XDF validation)
        └── signal_region (XSF/XDF union)
```

## Category matrices

For `inclusive_z_dy`, `four_lepton_base`, and `zz_control_region`, the source
contract books the stream-integrated `Inclusive` projection alongside the
three mutually exclusive stream-priority classes (`MuonEG`, `Muon`, and
`EGamma`). The `Inclusive` entries intentionally overlap the corresponding
three per-stream entries; the per-stream entries remain mutually exclusive.

Crossing those four stream labels with `ZEE`/`ZMM` yields eight categories for
`inclusive_z_dy`, with the non-applicable X axis encoded as `X_NA`. Crossing
them additionally with `XSF`/`XDF` yields 16 categories each for
`four_lepton_base` and `zz_control_region`.

`signal_region` deliberately has no per-stream categories. It books only six
stream-integrated categories: two Z flavours crossed with `XEE`, `XMM`, and
`XDF`. `XEE` and `XMM` atomically split its physical XSF branch.

The first three parents use the axis-explicit identifier
`STR_<Inclusive|MuonEG|Muon|EGamma>__Z_<ZEE|ZMM>__X_<NA|XSF|XDF>`, subject to
the applicable X values for each parent. Signal uses only
`STR_Inclusive__Z_<ZEE|ZMM>__X_<XEE|XMM|XDF>`.
`inclusive_z_dy` uses `X_NA`; `four_lepton_base` and `zz_control_region` use
`X_XSF`/`X_XDF`; and `signal_region` uses `X_XEE`/`X_XMM`/`X_XDF`. The `ALL`
identifier selects the unified execution pass and is not a category key.
All category dictionaries are explicitly enumerated in `cuts.py`; they are not
generated at configuration load time. Concrete HLT-path and path-priority
aliases remain available as trigger diagnostics, but they are not category
axes.

The unified execution contract is thus `8 + 16 + 16 + 6 = 46` categories.
With 509 variables this gives 23,414 category-variable cells, rendered as
23,414 linear plus 23,414 logarithmic plots (46,828 PNGs). For eight enabled
samples, the nominal merged output contains 187,312
sample-category-variable histograms.

## Corrections and nominal weights

The MC event weight is

```text
XSWeight * METFilter_Common * puWeight
* SelectedLeptonSF_<Z or ZX> * TriggerSF_event
[* BTagVetoSF for CONTROL]
```

`ZPARENT` applies selected-lepton efficiencies only to `Z0`; `FOURL_BASE` and
`CONTROL` apply them to all four selected `Z0+X` leptons. Trigger efficiencies
are evaluated for the selected event contract. DATA receives only
`METFilter_DATA` and the per-run exclusive stream-trigger weight; MC
corrections never target DATA.

In unified `ALL` mode, the common MC weight ends at `TriggerSF_event`; each
flattened category then multiplies its configured correction expression. A
cut's `*` policy supplies the default and an exact category key may override
it, so future categories can use distinct weights without runner changes.

For `CONTROL`, `BTagVetoSF = btagSFbc * btagSFlight`. Official fixed-WP BTV
scale factors and working points are loaded directly from
`/cvmfs/cms-griddata.cern.ch/cat/metadata/BTV/<campaign>/latest/btagging.json.gz`.
The process-dependent ttbar efficiencies are read from the shared
`PlotsConfigurationsRun3/utils/data/btag/<era>` maps.

## Systematic model

When `ENABLE_SYSTEMATICS=1`, the configuration books:

- era-specific luminosity and a correlated 1.5% CP5 underlying-event
  normalization;
- pileup, selected-electron efficiency, selected-muon efficiency, and event
  trigger shape weights;
- correlated and era-uncorrelated heavy-flavor and light-flavor b-tag shape
  weights in `CONTROL` only;
- JER, unclustered MET, lepton scale, and lepton resolution suffix shapes;
- JES sources: Absolute, era-Absolute, FlavorQCD, BBEC1, EC2, HF,
  era-BBEC1, era-EC2, RelativeBal, era-RelativeSample, and era-HF;
- ISR/FSR weights when at least four PS weights exist;
- six-point QCD-scale envelopes and 102-replica PDF RMS shapes, grouped by
  physics process, only when the required vectors are present;
- automatic finite-MC statistical uncertainties.

DATA is excluded from every nuisance. The current optimized plotting campaign
is nominal-only (`ENABLE_SYSTEMATICS=0`).

## Histogram and optimized-binning contract

`HISTOGRAM_DETAIL=all` books all compact physics, object, trigger, quality, and
weight diagnostics. `variables.py` resolves one physics-aware axis per
variable, shared by all eras, categories, and nominal/systematic variations.
The axes incorporate the completed DY+ZZ optimization catalog, variable
definitions, and explicit selection thresholds while folding sparse or
nonphysical tails into sensible display boundaries. No runtime binning JSON or
category-specific event-loop mode is used.

Every parent cut uses the explicitly enumerated category matrices above. The
one two-lepton cut exposes eight categories; `four_lepton_base` and
`zz_control_region` expose 16 each; and `signal_region` exposes six. Stream
splits are retained for the first three parents, while signal is intentionally
stream-integrated. Trigger-path information remains a separate diagnostic
rather than a category split.

## Extension and production lifecycle

The internal `ALL` contract is the default nominal operating mode; users do
not need to export `ANALYSIS_PASS=ALL`. It exposes every parent cut in
one compiled payload; the configuration-local runner branches the same
dataframe once per flattened category and redefines only that branch's nominal
weight. Core `mkShapesRDF` and `BatchSubmission` remain unchanged.

The FNAL profile keeps that implementation analysis-local as well.  During
compilation, `worker_payload.py` registers the compressed payload and the
year-selected b-tag efficiency map as runtime includes, replaces their source
paths with package tokens, and rejects a packaged payload that still contains
an AFS dependency.  On the worker, `zz_cr_runner.py` expands those tokens after
deserialization and creates the configured remote campaign/tag directory
before processing.  `fnal_lpc_packaged_env.sh` selects FNAL XRootD endpoints
and injects a 4096 MB HTCondor memory request while preserving any existing
submit attributes.  These are configuration contracts; they do not require a
fork or modification of the framework core.

Category-weight policy is declarative:

```python
"cut_weights": {
    "parent_cut": {
        "*": "defaultCorrection",
        "special_category": "specialCorrection",
    },
}
```

To add a category, add its expression under the parent's `categories` mapping,
add a compact display label, and add an exact weight override only if it must
differ from `*`. `cuts.py` rejects weight entries for unknown categories, and
the runner has no hard-coded category names. Common axes in `variables.py`
apply automatically. A category requiring a new physics object or correction
must define that alias before its selection or weight references it.

The production lifecycle is: compile and submit one immutable receipt;
reconcile Condor job IDs with nonempty EOS split files; merge using that exact
receipt; verify all top-level ROOT directories; then render and count every
linear/log plot pair. Commands, recovery rules, and expected counts are in
`USAGE.MD`.
