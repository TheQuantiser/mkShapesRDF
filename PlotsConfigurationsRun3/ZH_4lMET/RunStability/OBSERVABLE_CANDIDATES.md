# Candidate observables for DY run stability

## Status and scope

This document is a researched proposal for expanding the DY RunStability
observable catalog. It is not the active production contract. The active
`dy` profile still contains exactly six observables:

```text
Z0_mass, Z0_pt, lZ1_pt, lZ2_pt, lZ1_eta, lZ2_eta
```

Those six observables and their axes remain owned by
[`run_stability_profiles.json`](run_stability_profiles.json). No retained
pickle, batch campaign, merged ROOT file, or promoted gallery contains the
additional candidates in this document.

The catalog below was reconstructed from three evidence layers:

1. the broader compatibility registries and selected-lepton dereferencing in
   [`../ZZ_CR/histogram_config.py`](../ZZ_CR/histogram_config.py),
   [`../ZZ_CR/variables.py`](../ZZ_CR/variables.py), and
   [`../ZZ_CR/aliases.py`](../ZZ_CR/aliases.py);
2. official CMS NanoAOD and CMSSW table documentation;
3. a bounded schema audit of ten real HWWNano files: one DATA and one DY MC
   input for each of `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`.

The ten-file audit demonstrates representative availability across all five
pinned production families. It is not an exhaustive all-file schema proof.
Before a future production, compilation must require every selected input and
component to satisfy the final branch and semantic contract.

## Recommended first expansion

The recommended general-purpose expansion keeps the current six observables
and adds the following twenty. Uniform axes use the compact declarative form
`[n_bins, start, stop]`. `fold=2` means overflow-only folding; `fold=0` means
no folding. These axes are provisional production candidates. They must be
checked with a bounded selected-event quantile and flow pilot before the JSON
profile and numerical identity are frozen.

| Observable | Definition | Uniform axis | Fold | Purpose |
| --- | --- | --- | ---: | --- |
| `Z0_eta` | Pseudorapidity of the selected dilepton system | `[50, -2.5, 2.5]` | 0 | Longitudinal acceptance and reconstruction |
| `Z0_phi` | Azimuth of the selected dilepton system | `[32, -3.2, 3.2]` | 0 | Detector-sector and azimuthal stability |
| `dPhi_lZ1_lZ2` | Wrapped absolute azimuthal separation of the selected leptons | `[32, 0.0, 3.2]` | 0 | Dilepton topology |
| `absDEta_lZ1_lZ2` | Absolute pseudorapidity separation of the selected leptons | `[30, 0.0, 6.0]` | 2 | Topology and acceptance |
| `dR_lZ1_lZ2` | Selected-lepton delta-R | `[30, 0.0, 6.0]` | 2 | Lepton topology and reconstruction |
| `phiEtaStar` | Dilepton phi-eta-star derived from the selected lepton directions | `[30, 0.0, 0.3]` | 2 | Low-`Z0_pt` recoil-sensitive observable |
| `PV_npvsGood` | Number of good reconstructed primary vertices | `[40, 0.0, 80.0]` | 2 | Primary DATA/MC pileup proxy |
| `rho` | `Rho_fixedGridRhoFastjetAll` | `[30, 0.0, 60.0]` | 2 | Event energy density and pileup |
| `PV_z` | Primary-vertex longitudinal position | `[40, -20.0, 20.0]` | 0 | Beamspot and vertex stability |
| `nJet30` | Number of clean jets with `pt > 30 GeV` | `[8, -0.5, 7.5]` | 2 | Jet multiplicity and radiation |
| `HT30` | Scalar `pt` sum of clean jets above 30 GeV | `[40, 0.0, 400.0]` | 2 | Hadronic activity |
| `leadJet30_pt` | Leading clean-jet `pt`, conditional on at least one jet above 30 GeV | `[27, 30.0, 300.0]` | 2 | Jet energy scale and radiation |
| `SoftActivityJetNjets5` | Number of soft-activity jets above 5 GeV | `[10, -0.5, 9.5]` | 2 | Underlying event and soft radiation |
| `lZ1_pfRelIso03_all` | PF relative isolation of the leading selected Z lepton | `[25, 0.0, 0.25]` | 2 | Lepton-isolation stability |
| `lZ2_pfRelIso03_all` | PF relative isolation of the subleading selected Z lepton | `[25, 0.0, 0.25]` | 2 | Lepton-isolation stability |
| `lZ1_miniPFRelIso_all` | Mini-isolation of the leading selected Z lepton | `[25, 0.0, 0.25]` | 2 | Boost-robust isolation stability |
| `lZ2_miniPFRelIso_all` | Mini-isolation of the subleading selected Z lepton | `[25, 0.0, 0.25]` | 2 | Boost-robust isolation stability |
| `PuppiMET_pt` | PUPPI missing transverse momentum | `[20, 0.0, 100.0]` | 2 | MET and pileup-mitigation stability |
| `dPhi_Z0_PuppiMET` | Wrapped absolute delta-phi between the selected Z and PUPPI MET | `[32, 0.0, 3.2]` | 0 | Recoil orientation |
| `recoil_ut` | Magnitude of `-(pTmiss vector + selected-Z pT vector)` | `[30, 0.0, 150.0]` | 2 | Hadronic recoil stability |

The expanded profile would have 26 observables and therefore
`48 * 26 = 1248` category-observable products per era, approximately 4.33
times the current 288-product matrix.

For a smaller first campaign, prioritize these ten additions:

1. `PV_npvsGood`;
2. `rho`;
3. `nJet30`;
4. `HT30`;
5. `lZ1_pfRelIso03_all`;
6. `lZ2_pfRelIso03_all`;
7. `PuppiMET_pt`;
8. `dPhi_Z0_PuppiMET`;
9. `recoil_ut`;
10. `dR_lZ1_lZ2`.

Together with the current six, this reduced profile would contain 16
observables and `48 * 16 = 768` products per era.

## Complete candidate catalog

### Selected-Z and dilepton geometry

Derive these from the same selected `Z0_idx` object used by the mass and
ordered-lepton-`pt` cuts:

- `Z0_eta`, `Z0_absEta`, `Z0_phi`, `Z0_rapidity`, and `Z0_absRapidity`;
- `lZ1_phi` and `lZ2_phi`;
- `dPhi_lZ1_lZ2`, `absDEta_lZ1_lZ2`, and `dR_lZ1_lZ2`;
- `phiEtaStar`;
- the lepton-`pt` asymmetry
  `(lZ1_pt - lZ2_pt) / (lZ1_pt + lZ2_pt)` with an explicit denominator
  guard.

The compatibility leaf already contains selected-Z eta/phi and pair-separation
machinery. RunStability should derive these from its current selected Z rather
than consume an old generic `ptll`, `dphill`, or `drll` branch whose pair
selection has not been proven identical.

### Pileup, primary vertices, beamspot, and event density

The following candidates were present in all ten representative HWWNano
files:

- `PV_npvs` and `PV_npvsGood`;
- `PV_x`, `PV_y`, and `PV_z`;
- `PV_chi2`, `PV_ndof`, and the guarded ratio `PV_chi2 / PV_ndof`;
- `PV_score`, preferably after a range study and a monotonic transform such as
  `log10(1 + PV_score)`;
- `BeamSpot_z` and `BeamSpot_sigmaZ`;
- `Rho_fixedGridRhoAll`;
- `Rho_fixedGridRhoFastjetAll`;
- `Rho_fixedGridRhoFastjetCentral`;
- `Rho_fixedGridRhoFastjetCentralNeutral`;
- `Rho_fixedGridRhoFastjetCentralCalo`;
- `Rho_fixedGridRhoFastjetCentralChargedPileUp`.

The different rho definitions are not interchangeable. The official
[CMSSW global-variable table](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/globals_cff.py)
documents their distinct collection and detector-region semantics.

The representative 2024 DATA and MC files also contained `PV_sumpt2`,
`PV_sumpx`, and `PV_sumpy`; the representative earlier-era files did not.
Those variables require a 2024-specific profile or an explicit missing-era
contract.

The following are MC-only truth or simulation-state quantities and are not
normal DATA/MC distribution candidates:

- `Pileup_nTrueInt`;
- `Pileup_nPU`;
- `Pileup_pudensity`;
- `Pileup_gpudensity`.

Use reconstructed `PV_npvsGood` and rho for common DATA/MC pileup stability.

### Jets and hadronic activity

Portable clean-jet candidates are:

- `nCleanJet`, `nJet30`, and `nJet50`;
- `nCentralJet30` for `abs(eta) < 2.5` and `nForwardJet30` for the complement;
- `HT30`;
- leading and subleading clean-jet `pt`, `eta`, and `phi`;
- dijet mass and absolute delta-eta, conditional on two selected jets;
- `SoftActivityJetNjets2`, `SoftActivityJetNjets5`, and
  `SoftActivityJetNjets10`;
- `SoftActivityJetHT2`, `SoftActivityJetHT5`, and `SoftActivityJetHT10`.

All ten representative files contained `CleanJet_pt`, `CleanJet_eta`,
`CleanJet_phi`, `CleanJet_mass`, and `CleanJet_jetIdx`. The clean-jet
collection should define analysis-level kinematics. `CleanJet_jetIdx` may
dereference the owning NanoAOD `Jet` entry for detector-quality quantities:

- `Jet_area`, `Jet_rawFactor`, `Jet_jetId`, and `Jet_nConstituents`;
- `Jet_chHEF`, `Jet_neHEF`, `Jet_chEmEF`, `Jet_neEmEF`, and `Jet_muEF`.

Their official definitions are in the
[CMSSW AK4 PUPPI jet table](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/jetsAK4_Puppi_cff.py).

`Jet_puIdDisc`, charged/neutral multiplicities, and HF energy fractions were
only present in the representative 2024 inputs. `Jet_puIdDisc` is also
version-dependent. Do not put these into one cross-era profile without a
pinned per-era semantic contract.

B-tag variables are intentionally not recommended for the first DY expansion.
They require an explicit era-dependent algorithm, discriminator, working
point, and correction contract that the current streamlined DY leaf does not
otherwise need.

### Common selected-lepton isolation and quality

The common electron/muon fields present in all ten representative files
support these flavor-aware selected-lepton observables:

- `lZ1_pfRelIso03_all` and `lZ2_pfRelIso03_all`;
- `lZ1_pfRelIso03_chg` and `lZ2_pfRelIso03_chg`;
- `lZ1_miniPFRelIso_all` and `lZ2_miniPFRelIso_all`;
- `lZ1_miniPFRelIso_chg` and `lZ2_miniPFRelIso_chg`;
- leading/subleading `absDxy`, `absDz`, `ip3d`, and `sip3d`;
- leading/subleading `jetRelIso` and `jetPtRelv2`;
- selected-lepton `tightCharge` where it is not already degenerate after
  selection.

Useful provisional axes are:

| Quantity | Uniform axis | Fold |
| --- | --- | ---: |
| `pfRelIso03_all` | `[25, 0.0, 0.25]` | 2 |
| `pfRelIso03_chg` | `[20, 0.0, 0.20]` | 2 |
| `miniPFRelIso_all` | `[25, 0.0, 0.25]` | 2 |
| `absDxy` | `[25, 0.0, 0.05]` cm | 2 |
| `absDz` | `[25, 0.0, 0.10]` cm | 2 |
| `ip3d` | `[25, 0.0, 0.10]` cm | 2 |
| `sip3d` | `[25, 0.0, 10.0]` | 2 |
| `jetPtRelv2` | `[30, 0.0, 60.0]` GeV | 2 |

Choose `jetRelIso` binning only after checking its selected-event signedness
and range in every production.

The official [electron](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/electrons_cff.py)
and [muon](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/muons_cff.py)
tables document PF isolation, mini-isolation, displacement, 3D impact
parameters, and jet-related isolation. Similarly named electron and muon
fields do not imply one identical producer. The implementation must first map

```text
Z0_idx -> merged Lepton index -> Lepton_electronIdx or Lepton_muonIdx
       -> Electron_* or Muon_*
```

as the compatibility aliases do.

### Electron-specific observables

Candidates for ZEE-applicable products are:

- `Electron_hoe`, `Electron_sieie`, and `Electron_r9`;
- `Electron_scEtOverPt`;
- relative energy uncertainty such as `Electron_energyErr / Electron_pt`;
- `Electron_lostHits`, `Electron_convVeto`, and `Electron_tightCharge`;
- `Electron_eInvMinusPInv` when it is present in the exact production;
- electron MVA-ID outputs and working-point decisions only with a pinned
  producer and version.

`Electron_fbrem` and electron prompt MVA were found only in the representative
2024 files. The strongest initial ZEE additions are leading/subleading
`sieie`, `hoe`, `r9`, and relative energy uncertainty. Selection-required
boolean decisions may be nearly degenerate and should not be promoted merely
because their branches exist.

### Muon-specific observables

Candidates for ZMM-applicable products are:

- `Muon_pfRelIso04_all` and `Muon_tkRelIso`;
- `Muon_dxybs`;
- relative momentum uncertainty `Muon_ptErr / Muon_pt`;
- `Muon_segmentComp`;
- `Muon_nStations` and `Muon_nTrackerLayers`;
- `Muon_tightCharge`;
- muon-ID decisions that are not already fixed by selection.

Muon prompt MVA was only present in the representative 2024 files. The
strongest initial ZMM additions are leading/subleading `pfRelIso04_all`,
relative momentum uncertainty, `segmentComp`, and `nTrackerLayers`.

### MET, balance, and recoil

All ten representative files contained:

- `PuppiMET_pt`, `PuppiMET_phi`, and `PuppiMET_sumEt`;
- `TkMET_pt` and `TkMET_phi`;
- `CaloMET_pt`, `CaloMET_phi`, and `CaloMET_sumEt`;
- `DeepMETResolutionTune_pt` and `DeepMETResponseTune_pt`.

Selected-Z derived candidates are:

- `dPhi_Z0_PuppiMET` and the corresponding selected-lepton/MET delta-phi
  quantities;
- the guarded ratio `PuppiMET_pt / Z0_pt`;
- recoil Cartesian components from
  `u vector = -(PuppiMET vector + selected-Z pT vector)`;
- `recoil_ut`, `recoil_upar`, and `recoil_uperp`;
- a guarded recoil response such as `-recoil_upar / Z0_pt`.

The [CMSSW MET table](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/met_cff.py)
distinguishes PUPPI MET, track MET, calorimeter MET, DeepMET response and
resolution tunes, covariance/significance, and unclustered components. They
are not interchangeable estimators.

PUPPI MET significance, covariance components, and unclustered-`pt`
information were found only in the representative 2024 inputs. They require a
2024-specific profile or a deliberate optional-observable contract.

Compatibility recoil expressions are useful implementation references, but
RunStability definitions must use the selected `Z0_idx`. An old HWW branch
named `recoil`, `upara`, or `uperp` is not equivalent without a proven
candidate-selection contract.

### FSR

All ten representative files contained:

- `nFsrPhoton` and `FsrPhoton_pt`, `eta`, and `phi`;
- `FsrPhoton_relIso03` and `FsrPhoton_dROverEt2`;
- `Electron_fsrPhotonIdx` and `Muon_fsrPhotonIdx`.

Candidate selected-Z products are:

- number of selected-Z leptons with an associated FSR photon;
- leading associated FSR-photon `pt`;
- associated-photon `relIso03` and `dROverEt2`;
- selected-lepton/photon delta-R;
- the FSR-corrected versus uncorrected selected-Z mass difference.

The last item is valid only after establishing whether the current `Z0_mass`
already includes FSR recovery.

### Trigger objects and matching

All ten representative files contained:

- `nTrigObj`;
- `TrigObj_pt`, `TrigObj_eta`, and `TrigObj_phi`;
- `TrigObj_id` and `TrigObj_filterBits`.

Useful derived diagnostics are:

- numbers of all, electron-like, and muon-like trigger objects;
- minimum delta-R from each selected lepton to a compatible trigger object;
- matched trigger-object `pt` and lepton/object `pt` response;
- number of compatible matches and an unambiguous/ambiguous/unmatched state;
- path- or family-specific match efficiency versus run;
- fired trigger-family/path counts and resolved path priority.

Raw `TrigObj_filterBits` must not be plotted as a generic scalar. Its meaning
depends on object type and NanoAOD/CMSSW version. Decode it through an explicit
era/version-bound trigger-object contract.

The [CMS NanoAOD WorkBook](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookNanoAOD)
also explains that HLT branch availability can vary by file and missing bits
can be zero-filled when files are merged. A zero bit is therefore interpreted
only in its pinned file/menu context.

### DATA-quality and event-filter monitors

Event-quality flags are candidates for a separate DATA-only per-run failure
rate product, not ordinary post-selection DATA/MC distributions. Examples
include:

- good-vertex, beam-halo, HBHE noise, and HBHE isolation filters;
- ECAL dead-cell and bad-calibration filters;
- bad-PF-muon and bad-PF-muon-dz filters;
- supported HF noisy-hit filters.

The appropriate statistic is the failing-event numerator over a documented
pre-filter denominator, with a binomial interval and explicit absent/not-
applicable states. A flag required by the main preselection is identically
true after selection and is not a useful post-selection histogram.

## Exclusions from the common profile

Do not promote the following as general cross-era DATA/MC observables:

- MC-only pileup truth and generator-level quantities;
- `puWeight`, lepton scale factors, or trigger scale factors presented as
  event observables, because DATA commonly receives a unit fallback;
- 2024-only MET-significance, covariance, prompt-MVA, or jet-PU-ID quantities
  without an explicit era-specific contract;
- booleans already forced by selection;
- `nJetInHorn` when the preselection already requires zero;
- four-lepton X, pairing, or four-lepton-mass quantities;
- old generic dilepton or recoil branches unless their selected-pair semantics
  are proven identical to `Z0_idx`.

## Configuration and implementation design

The expanded catalog belongs in `run_stability_profiles.json`. Python must
validate and materialize that JSON rather than repeat observable names, axes,
or binning. A future entry should carry an explicit applicability and source
contract, for example:

```json
{
  "id": "lZ1_pfRelIso03_all",
  "expression": "lZ1_pfRelIso03_all",
  "axis": [25, 0.0, 0.25],
  "fold": 2,
  "applicability": "all_dy",
  "source_contract": "selected_lepton_flavor_dereference"
}
```

Useful applicability classes are:

- `all_dy`;
- `zee_only` and `zmm_only`;
- `requires_jet30` and `requires_two_jets30`;
- `requires_fsr_match`;
- `data_quality_only`;
- `era_specific`.

If flavor- or condition-specific observables are adopted, the current dense
assumption that every observable is booked in every category must be replaced
deliberately by a validated sparse category-observable matrix. Its exact
ordered pairs, count, and hash must be serialized. Do not emit meaningless
electron-quality outputs for ZMM categories or muon-quality outputs for ZEE
categories merely to preserve a rectangular matrix.

Reusable derived aliases should cover selected-lepton flavor dereferencing,
selected-Z geometry, jet-threshold summaries, selected-Z recoil, FSR
association, and trigger-object matching. No numerical definition or axis
should be duplicated between Python and JSON.

## Production gates for any adopted subset

Before changing the active profile or requesting batch jobs:

1. choose the exact ordered observable subset and applicability rules;
2. perform an all-configured-input branch/schema audit, not only the ten-file
   representative check recorded here;
3. trace every derived quantity from producer through retained fields and the
   selected-object mapping;
4. run a bounded DATA and DY MC pilot to inspect finite values, quantiles,
   flows, and conditional denominators;
5. freeze compact axes in `run_stability_profiles.json` and extend its
   validator without duplicating them in Python;
6. require exact ordinary-TH1/DATA-TH2 axis identity, integer DATA `Sumw2`,
   and TH2-to-TH1 closure;
7. compile a fresh pickle and require its ordered matrix, count, hash,
   expressions, axes, folds, luminosity binding, and payload to match;
8. submit only after separate authorization, then independently validate
   split outputs, merge, numerical formulas, and rendered plots.

## Official CMS references

- [CMS NanoAOD WorkBook](https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookNanoAOD)
- [CMSSW electron table](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/electrons_cff.py)
- [CMSSW muon table](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/muons_cff.py)
- [CMSSW global-variable table](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/globals_cff.py)
- [CMSSW AK4 PUPPI jet table](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/jetsAK4_Puppi_cff.py)
- [CMSSW MET table](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/met_cff.py)
- [CMSSW NanoAOD DQM reference](https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/nanoDQM_cfi.py)

The official sources document intended current NanoAOD semantics and useful
reference monitoring ranges. They do not prove identical branch availability
or meaning in every HWWNano v12-v15 production. The exact configured input
schemas and producers remain the authority for production acceptance.
