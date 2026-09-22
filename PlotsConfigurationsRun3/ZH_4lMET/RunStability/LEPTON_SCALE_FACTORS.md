# Lepton-selection scale-factor inventory

This document identifies the raw correction components that feed the lepton
selection weights used by the DY-only `RunStability` configuration and by the
compatibility `ZH_4lMET/ZZ_CR` configuration. It deliberately starts from the
processor payloads and producers, rather than treating a final branch such as
`SelectedLeptonSF_Z` as one indivisible scale factor.

The active RunStability implementation is the authority for its selected-Z
composition. `ZZ_CR` is inspected here only to document how the same
processor-level corrections are consumed by its selected-Z and selected-Z+X
objects; this document does not make `ZZ_CR` an implementation dependency.
The selected-pair trigger mechanics are described in more detail in
[TRIGGER_SCALE_FACTORS.md](TRIGGER_SCALE_FACTORS.md).

## Scope and terminology

The following terms have distinct meanings in this inventory:

| Term | Meaning |
| --- | --- |
| Raw component | One correction or efficiency map read from one named payload correction |
| Derived per-lepton product | A product or uncertainty combination built by `LeptonSF.py` from raw components |
| Derived event product | A product or efficiency ratio evaluated for the selected leptons |
| Retained branch | A column written by HWWNano and available to the shape configuration |
| Active nominal weight | A factor actually multiplied into the current nominal MC event weight |
| Diagnostic/inactive | Available payload content or a branch not used in the active nominal weight |

Electron and muon ID/isolation/reconstruction corrections are direct MC scale
factors. Trigger leg payloads are different: they contain separate DATA and MC
efficiencies. The selected-pair trigger scale factor is derived only after
combining those efficiencies into an event efficiency.

This inventory covers scale factors associated with the selected leptons. It
does **not** classify the following as lepton-selection scale factors:

- electron or muon momentum scale and smearing, which alter kinematics rather
  than multiply event weights;
- fake/nonprompt transfer factors, which belong to a different background
  estimation contract;
- pileup and b-tagging weights;
- HLT decisions, stream de-duplication expressions, trigger-object matching,
  or filter bits, which are selections or matching decisions rather than
  efficiency corrections.

## Active eras and working points

Both configurations select the same processor working points for the five
supported analysis eras:

| Analysis era | Processor era | Electron working point | Muon working point |
| --- | --- | --- | --- |
| 2022 | `Full2022v12` | `mvaWinter22V2Iso_WP90_tthMVA_Run3` | `cut_TightID_pfIsoTight_HWW_tthmva_67` |
| 2022EE | `Full2022EEv12` | same | same |
| 2023 | `Full2023v12` | same | same |
| 2023BPix | `Full2023BPixv12` | same | same |
| 2024 | `Full2024v15` | same | same |

The active names are declared in [`year_config.json`](year_config.json).
Their cuts and payload assignments are owned by
[`LeptonSel_cfg.py`](../../../mkShapesRDF/processor/data/LeptonSel_cfg.py), and
the correction branches are produced by
[`LeptonSF.py`](../../../mkShapesRDF/processor/modules/LeptonSF.py).

For 2022 through 2023BPix, the prompt-lepton discriminator in these working
points is `Electron_tthMVA > 0.90` or `Muon_tthMVA > 0.67`. The 2024 working
points use `Electron_promptMVA > 0.90` and `Muon_promptMVA > 0.67`. The payload
correction names remain the Run-3 tthMVA-labelled names shown below.

## Electron components

For one selected electron, the nominal correction is

\[
  SF_e^{\mathrm{Tot}}
  = SF_e^{\mathrm{Reco}}
    SF_e^{\mathrm{WP90Iso}}
    SF_e^{\mathrm{promptMVA}}.
\]

The producer first combines the two selection-efficiency components into
`IdIsoSF`, then multiplies that result by the reconstruction component to form
`TotSF`.

### Reconstruction/tracking component

The active electron reconstruction correction is the `tkSF` declaration in
`LeptonSel_cfg.py`:

| Property | Active value |
| --- | --- |
| Payload correction | `Electron-ID-SF` |
| Working-point categories | `RecoBelow20`, `Reco20to75`, `RecoAbove75` |
| Nominal/variations | `sf`, `sfup`, `sfdown` |
| Coordinates in 2022, 2022EE, 2024 | era label, variation, reconstruction category, `Lepton_eta`, `Lepton_pt` |
| Coordinates in 2023, 2023BPix | the same plus `Lepton_phi` |
| Producer domain | `10.001 <= pT <= 199.99 GeV`, `-2.4999 <= eta <= 2.4999`, followed by the reconstruction-category boundary guards |

The reconstruction category is selected at 20 and 75 GeV. The code uses
19.9999 below 20, 20.0001--74.99 in the middle category, and at least 75.001
in the high-pT category to avoid payload-edge ambiguity.

The retained aligned vectors are:

- `Lepton_RecoSF`: nominal scale factor;
- `Lepton_RecoSF_Up`: the absolute positive displacement `sfup - sf`;
- `Lepton_RecoSF_Down`: the absolute negative displacement `sf - sfdown`.

The latter two are uncertainty magnitudes, not complete varied scale factors.
The final electron `TotSF_Up/Down` branches turn them into complete variations.

### Official WP90Iso component

The active `wpSF` component uses the same official `Electron-ID-SF` payload
with working-point category `wp90iso` and variation categories `sf`, `sfup`,
and `sfdown`.

Its eta coordinate is the electron supercluster eta,
`Lepton_eta + Electron_deltaEtaSC`, not the track eta used by the
reconstruction component. The 2023 and 2023BPix official payloads additionally
consume `Lepton_phi`; the other three active payloads do not. The producer
clamps pT and eta to the same 10.001--199.99 GeV and +/-2.4999 bounds used by
the electron correction machinery.

### Local prompt/tthMVA residual component

The active `tthMvaSF` component is a local correction in
`processor/data/scale_factor/<processor-era>/electron.json`:

| Property | Active value |
| --- | --- |
| Payload correction | `Electron-ID-SF` |
| Working-point category | `cut_mvaWinter22V2Iso_WP90_tthMVA_Run3` |
| Nominal/variations | `sf`, `sfup`, `sfdown` |
| Coordinates | processor-era label, variation, working point, `Lepton_eta`, `Lepton_pt` |

Unlike the official WP90Iso component, this local residual uses ordinary
`Lepton_eta` and has no phi coordinate in any active era.

### Electron derived and retained branches

The two selection components are combined internally as

\[
  SF_e^{\mathrm{IdIso}}
  = SF_e^{\mathrm{WP90Iso}} SF_e^{\mathrm{promptMVA}}.
\]

The producer retains:

- `Lepton_tightElectron_<WP>_IdIsoSF` and its complete `Up`/`Down` variants;
- `Lepton_tightElectron_<WP>_TotSF` and its complete `Up`/`Down` variants;
- the separate `Lepton_RecoSF` vectors described above.

It does **not** retain the official WP90Iso and local prompt-MVA values as two
separate public vectors. Their individual values live only in the internal
`ElewpSF_<WP>` calculation, which is dropped after the derived branches are
defined. Plotting the two raw maps must therefore evaluate their payloads
directly rather than pretending they are separately retained NanoAOD columns.

### Electron uncertainty caveat

The current source constructs the combined WP90Iso-plus-prompt-MVA variation
by adding the two squared relative shifts, but without taking the outer square
root before applying that shift to the nominal product. The final
reconstruction combination does use a square root when combining the derived
`IdIsoSF` displacement with the reconstruction displacement.

This is a verified description of the executable source, not an endorsement
of that uncertainty prescription and not a silent correction to it. Any
future change to the prescription is a physics/weight change requiring its own
source modification, nuisance review, tests, and yield/shape validation.

## Muon components

For one selected muon, the nominal correction is

\[
  SF_\mu^{\mathrm{Tot}}
  = SF_\mu^{\mathrm{TightID}}
    SF_\mu^{\mathrm{TightPFIso}}
    SF_\mu^{\mathrm{promptMVA}}.
\]

All three raw components come from the local
`processor/data/scale_factor/<processor-era>/muonSF_latinos_HWW.json` payload.
Each correction consumes `(eta, pt, scale_factors)`. The active producer reads
only `nominal`, `stat`, and `syst`; payload categories such as `AltSig`,
`massBin`, `massRange`, `tagIso`, and, in 2024, `AltBkg`, are present but are
not active inputs to the nominal RunStability or `ZZ_CR` weights.

| Raw component | Correction name | Meaning of denominator transition |
| --- | --- | --- |
| Tight identification | `NUM_TightID_HWW_DEN_TrackerMuons` | tracker muon to HWW tight-ID muon |
| Tight PF isolation | `NUM_TightPFIso_DEN_TightID_HWW` | HWW tight-ID muon to tight-PF-isolated muon |
| Prompt/tthMVA | `NUM_TightID_HWW_TightIso_tthMVA_DEN_TightPFIso` | tight-PF-isolated muon to the active prompt-MVA selection |

The producer clamps the local corrections to
`10.001 <= pT <= 199.99 GeV` and `-2.3999 <= eta <= 2.3999`.

### Muon retained branches

Unlike the electron producer, the muon producer retains every raw component:

| Component | Nominal branch suffix | Variation branches |
| --- | --- | --- |
| Tight ID | `_idSF` | `_idSF_Up`, `_idSF_Down`, `_idSF_Syst` |
| Tight PF isolation | `_isoSF` | `_isoSF_Up`, `_isoSF_Down`, `_isoSF_Syst` |
| Prompt/tthMVA | `_tthSF` | `_tthSF_Up`, `_tthSF_Down`, `_tthSF_Syst` |

Each complete branch begins with
`Lepton_tightMuon_<WP>`. For a raw component, `Up/Down` are nominal +/- the
payload's `stat` value, while `Syst` is nominal plus the payload's `syst`
value.

The branch called `Lepton_tightMuon_<WP>_IdIsoSF` is broader than its name: its
nominal value is the product of **all three** raw components, including the
prompt/tthMVA component. Its `Up/Down` variants use the quadrature sum of the
three `stat` values, and its `Syst` variant uses the quadrature sum of the
three `syst` values. `TotSF` has the same nominal product; its `Up/Down`
variants combine the aggregate statistical and systematic magnitudes in
quadrature.

### No active standalone muon reconstruction scale factor

There is no `tkSF`, tracker-to-reconstruction payload, or separate muon
reconstruction branch configured for the active muon working point in any of
the five eras. The first active muon efficiency transition is
`DEN_TrackerMuons -> NUM_TightID_HWW`.

This statement is specific to these working points and payload assignments. It
does not claim that CMS has no muon reconstruction/tracking measurements, nor
does it authorize treating the tight-ID component as a separately defined
reconstruction scale factor.

## Trigger efficiency components

The trigger leg files are correctionlib efficiency maps, not direct scale
factor maps. For each processor era, `TrigMaker_cfg.py` declares ten logical
leg aliases for DATA and ten for MC, backed by seven unique DATA files and
seven unique MC files.

Every active leg file contains correction `TriggerEff` with coordinates
`(eta, pt, systematic)`. `TrigMaker.py` evaluates these categories and rounds
each result to four decimal places:

- `nominal`;
- `stat_down`, `stat_up`;
- `syst_down`, `syst_up`.

The returned seven-element variation vector is nominal, combined down/up,
statistical down/up, and systematic down/up. Electron legs are clamped to
`9.999 <= pT <= 79.9 GeV` and `-2.4999 <= eta <= 2.4999`. Muon legs are
clamped to `9.999 <= pT <= 149.9 GeV` and
`-2.3999 <= eta <= 2.3999`.

### Ten aliases and seven unique maps

| Logical alias or aliases | Unique payload map | Physical leg represented |
| --- | --- | --- |
| `SingleEle` | `Ele30_pt_eta_efficiency.json` | single-electron Ele30 leg |
| `SingleMu` | `IsoMu24_pt_eta_efficiency.json` | single-muon IsoMu24 leg |
| `DoubleEleLegHigPt`, `EleMuLegHigPt` | `Ele23_Ele12_leg1_pt_eta_efficiency.json` | electron Ele23/high leg |
| `DoubleEleLegLowPt`, `MuEleLegLowPt` | `Ele23_Ele12_leg2_pt_eta_efficiency.json` | electron Ele12/low leg |
| `DoubleMuLegHigPt` | `Mu17_Mu8_leg1_pt_eta_efficiency.json` | muon Mu17/high leg |
| `DoubleMuLegLowPt`, `EleMuLegLowPt` | `Mu17_Mu8_leg2_pt_eta_efficiency.json` | muon Mu8/low leg |
| `MuEleLegHigPt` | `Mu23_pt_eta_efficiency.json` | muon Mu23/high leg |

The same alias-to-file pattern is used in all five active eras, with separate
DATA and MC files under each era. Mu12 efficiency files exist in the trigger
payload tree, but none is referenced by the active Run-3 `TrigMaker_cfg.py`
entries. The mixed-flavor event algebra therefore reuses the seven maps above;
it does not read a separate active Mu12 map.

### Angular, DZ, and global terms

Four shared angular corrections are read from the top-level trigger payload
directory:

| Flavor/order | File | Inputs used by the active code |
| --- | --- | --- |
| electron-electron | `DRll_SF_ee.json` | `dRll`, `nominal` |
| muon-muon | `DRll_SF_mm.json` | `dRll`, `nominal` |
| electron-muon | `DRll_SF_em.json` | `dRll`, `nominal` |
| muon-electron | `DRll_SF_me.json` | `dRll`, `nominal` |

The payload schema also has a `systematic` coordinate, but the active
`drll_sf` function requests only `nominal`. The same angular factor is applied
inside the DATA and MC event-efficiency expressions. When it is finite and
nonzero, that common multiplicative factor cancels from their nominal ratio,
although it remains part of the individual efficiencies.

All active Run-3 DZ entries are constant `[1.0, 0.0]` for DATA and MC, for
`DoubleEle`, `DoubleMu`, `MuEle`, and `EleMu`. All active global-efficiency
entries are likewise `[1.0, 0.0]` for the four double/cross families and the
two single-lepton families. The TrigMaker interface supports nontrivial
vertex-, pT-, and global-efficiency terms, but those interfaces do not imply a
current non-unity correction in these five configurations.

### Derived selected-pair trigger scale factor

For the selected Z pair, the wrapper evaluates the canonical TrigMaker
single- and double-leg OR algebra separately for DATA and MC, including the
active angular, DZ, and global terms. It then forms

\[
  SF_{\mathrm{trigger}}^{Z}
  = \frac{\epsilon_{\mathrm{event}}^{\mathrm{DATA}}
          (\ell_1,\ell_2)}
         {\epsilon_{\mathrm{event}}^{\mathrm{MC}}
          (\ell_1,\ell_2)}.
\]

The nominal selected-pair result is therefore a function of both selected
leptons' flavors, pT, and eta; their phi values enter through `DeltaR`; and the
configured run-period selector chooses the payload set. `PV_npvsGood` is
passed through the general DZ interface, but the active constant DZ entries
remove any present numerical NPV dependence.

The selected wrapper exposes DATA efficiency, MC efficiency, nominal/down/up
SF, and a validity flag. On DATA, the public `TriggerSF_Z` correction is
explicitly one. Stored leading-lepton trigger branches and generic all-lepton
results are diagnostics, not the active RunStability selected-Z weight.

A ratio of one DATA leg map to one MC leg map can be useful for payload
inspection, but it is **not** interchangeable with the final event SF: OR
terms, high/low-leg permutations, double-trigger overlap, and flavor ordering
are combined before taking the event-level ratio.

### Trigger source-audit caveat

The specialized component-level ElMu uncertainty block in `TrigMaker.py`
contains an assignment that writes an MC variation into `effs_data` instead
of `effs_mc`. The selected-Z wrapper used by RunStability calls the canonical
two-lepton `get_w` result and does not consume that specialized component
branch for its nominal SF. This remains a source-level caveat for anyone who
plots or interprets the specialized `TriggerEffWeight_ElMu` uncertainty
output; it should be fixed and validated as a separate producer change rather
than hidden by documentation.

## Configuration consumers

### RunStability

[`aliases.py`](aliases.py) selects the electron or muon `TotSF` value for each
of the two `Z0_idx` leptons and multiplies them into `SelectedLeptonSF_Z`.
It independently recomputes `TriggerSF_Z` for that exact selected pair using
the canonical TrigMaker payload readers and local selected-pair adapter.

The nominal RunStability MC correction fragment is

```text
puWeight * SelectedLeptonSF_Z * TriggerSF_Z
```

The configured common MC factor `XSWeight * METFilter_Common` and the runtime
luminosity normalization are applied outside this fragment. DATA uses its DATA
filter and stream-trigger rules; its lepton and trigger correction aliases are
unity. RunStability has `ENABLE_SYSTEMATICS=0`, so the public production uses
the nominal correction and does not book separate lepton/trigger nuisance
variations.

### Compatibility ZZ_CR

[`../ZZ_CR/aliases.py`](../ZZ_CR/aliases.py) consumes the same processor
electron and muon `TotSF` vectors. Its Z-parent pass uses
`SelectedLeptonSF_Z * TriggerSF_Z`. Its four-lepton passes use the product for
the selected Z+X leptons and the corresponding selected-four-lepton trigger
result; regions that require a b-veto multiply a separate b-tag correction.

When systematic production is enabled there, the nuisance layer exposes
combined selected-electron, selected-muon, and event-trigger variations. It
does not expose every raw electron WP90Iso/prompt-MVA/reconstruction component
as an independent nuisance. The raw-component inventory in this document must
not be mistaken for the current nuisance-factorization contract.

## Payload and source organization

| Component family | Source |
| --- | --- |
| Official electron reconstruction and WP90Iso | `/cvmfs/cms-griddata.cern.ch/cat/metadata/EGM/<campaign>/2025-12-15/electron.json.gz` |
| Local electron prompt/tthMVA residual | `mkShapesRDF/processor/data/scale_factor/<processor-era>/electron.json` |
| Local muon ID, isolation, and prompt/tthMVA | `mkShapesRDF/processor/data/scale_factor/<processor-era>/muonSF_latinos_HWW.json` |
| DATA/MC trigger leg efficiencies | `mkShapesRDF/processor/data/trigger/<processor-era>/{data,mc}/...` |
| Shared angular trigger maps | `mkShapesRDF/processor/data/trigger/DRll_SF_{ee,mm,em,me}.json` |

The exact official electron campaign and payload-era labels are:

| Processor era | Official campaign | Official era label | Local residual era label |
| --- | --- | --- | --- |
| `Full2022v12` | `Run3-22CDSep23-Summer22-NanoAODv12` | `2022Re-recoBCD` | `2022Re-recoBCD` |
| `Full2022EEv12` | `Run3-22EFGSep23-Summer22EE-NanoAODv12` | `2022Re-recoE+PromptFG` | same |
| `Full2023v12` | `Run3-23CSep23-Summer23-NanoAODv12` | `2023PromptC` | same |
| `Full2023BPixv12` | `Run3-23DSep23-Summer23BPix-NanoAODv12` | `2023PromptD` | same |
| `Full2024v15` | `Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15` | `2024Prompt` | `2024PromptCDE+Re-recoFGHI` |

## Plotting the raw components

The minimum scientifically interpretable component gallery is:

| Family | Required views |
| --- | --- |
| Electron reconstruction | central, up/down displacement, and relative displacement for each of the three reconstruction categories |
| Electron WP90Iso | central and up/down maps |
| Electron prompt-MVA residual | central and up/down maps |
| Electron derived products | `IdIsoSF` and `TotSF`, constructed with the executable producer convention and labelled as derived |
| Muon ID, isolation, prompt-MVA | separate nominal, statistical, and systematic maps for all three raw corrections |
| Muon derived total | nominal and combined variations, labelled as derived |
| Trigger legs | DATA efficiency, MC efficiency, and diagnostic DATA/MC ratio for each of the seven unique maps, with stat/syst views kept separate |
| Trigger angular terms | the four one-dimensional `DeltaR` functions |
| DZ/global terms | tables showing the active unity values rather than empty or misleading heat maps |
| Selected-pair trigger SF | explicit benchmark slices in pair flavor and the two leptons' kinematics; never an undeclared two-dimensional projection |

The official electron payloads for 2023 and 2023BPix are functions of phi as
well as eta and pT. Any two-dimensional plot must therefore specify a phi
slice or a documented weighted projection. Averaging or dropping phi without
recording that operation would change the quantity being shown.

Each plot should record the era, payload path and hash, correction key,
working-point/category value, coordinates held fixed, clamp policy, and
whether it is a raw map, a derived per-lepton product, or an event-level
quantity.

## Audit snapshot and limitations

This inventory was reconstructed on 2026-08-20 from checkout revision
`6a1df5017113c464e8aef672eea6d533829a7687`. The principal source identities
at that revision are:

| Source | SHA-256 |
| --- | --- |
| `processor/modules/LeptonSF.py` | `b120dc4791d974f74cc0f4fd8bdacb31711a77c7d2f2fdee4fc84d4e54fc1401` |
| `processor/data/LeptonSel_cfg.py` | `dfe253af96dfa5a1caaff5c6f5e78ce9fc14dc466a7abb6d07db58d8c1d754b2` |
| `processor/modules/TrigMaker.py` | `6d5e5248fa111709674bf6cfac05d73d20e63264a6983452ddf1118f3fce76fd` |
| `processor/data/TrigMaker_cfg.py` | `094e5a421ccd5ad630b2ab6e8c931bdc77e760becedf168cc6207b091cdc0747` |
| `RunStability/aliases.py` | `62fa572c58f8e6355c5997bc7b8b70335f64d76cc79ea5a32ae1095e9508f9d8` |
| `RunStability/selection_config.py` | `39e5dd2e28f243a5731bc500fdd38f9939ee8768df622c2d4b2acfb262bf204b` |
| `RunStability/selected_trigger_adapter.py` | `eb187fac7d384e227f63d8da3bd086ed92041bcea3bf80f596846c9c6492cee0` |
| `RunStability/macros/selected_trigger_wrappers.cc` | `0b6558b380bd6ba8a79ced32cf224ff09bc50ff9900c701c65faaa8861b3100e` |
| `ZZ_CR/aliases.py` | `b7858b127dc6e82f4480b99d7fe9fd6c4609e53e1f0f2d304de7f20937298e29` |
| `ZZ_CR/samples.py` | `c89e7c50d3ffe581e52f3a23d9b053bc619f03c52e5cef020f3e539c0f6e91af` |

Static source and payload-schema inspection establishes component identity,
input coordinates, branch composition, and active weight placement. It does
not establish that the payload measurements are scientifically correct, that
their uncertainties have calibrated coverage, or that real-event yields agree
with DATA. Those claims require direct payload evaluation, representative
event-level distributions, nuisance/yield comparisons, and an approved
physics reference.
