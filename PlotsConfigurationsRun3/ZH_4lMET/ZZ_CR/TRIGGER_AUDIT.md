# ZZ_CR Run 3 Trigger Audit

This note documents the trigger diagnostics added to the local
`PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR` configuration.  The active
`zz_cr` selection in `cuts.py` is unchanged.  The additions are diagnostic
aliases and tree-snapshot branches that make trigger-path, trigger-family,
and per-lepton trigger-object matching auditable in the postprocessed
mkShapesRDF output.

The trigger-object bit interpretation below is tied to the NanoAOD producer
code, not to an inferred convention.  The local ZZ_CR configuration now assumes
the CMSSW 15_0_X/NanoAODv15 trigger-object bit map for all supported year
profiles.  This assumption is independent of historical 2022-2023 profile
names or input campaign paths that still contain `nAODv12`.

## Local Processing Flow

The ZZ_CR configuration follows the standard mkShapesRDF flow:

1. `zzcr_year.py` selects one year block from `zzcr_year_config.json` using
   `ZZCR_YEAR`.
2. `samples.py` builds MC and data samples.  For data, stream
   de-duplication weights are read from `zzcr_year_config.json`: MuonEG
   events are kept first, then Muon/SingleMuon, then EGamma.
3. `TrigMaker.py` defines the aggregate trigger branches
   `Trigger_ElMu`, `Trigger_sngMu`, `Trigger_dblMu`, `Trigger_sngEl`,
   and `Trigger_dblEl` by OR-ing the configured `HLT_*` branches for the
   selected run period.
4. `zzcr_selection_config.py` fixes the trigger-object schema assumption to
   NanoAODv15; it no longer infers v12/v15 from `l2tight_era`.
5. `aliases.py` defines Z/X pair indices, trigger-object matching vectors,
   decoded v15 trigger-object bits, event trigger priorities, and four-lepton
   diagnostic categories.
6. `variables.py` expands `variables["tree"]["tree"]` into the set of
   branches to snapshot for the `zz_cr` cut.
7. `mkShapesRDF/shapeAnalysis/runner.py` defines or aliases the tree
   branches, books lazy `Events` snapshots for each cut/category/sample, and
   `saveResults()` writes the final trees under
   `trees/<cut>_<category>/<sample>/Events`.  For the current active cut the
   category is `ALL`, so the diagnostic tree is
   `trees/zz_cr_ALL/<sample>/Events`.

Important local entry points:

| Purpose | Local source |
|---|---|
| Year trigger paths and data stream de-duplication | `ZZ_CR/zzcr_year_config.json` |
| Aggregate trigger ORs | `mkShapesRDF/processor/modules/TrigMaker.py` |
| Trigger branch suffix lists, priority order, and NanoAODv15 trigger-object schema assumption | `ZZ_CR/zzcr_selection_config.py` |
| Per-lepton matching and decoded bit aliases | `ZZ_CR/aliases.py` |
| Event trigger-category aliases | `ZZ_CR/aliases.py` |
| Tree branch persistence | `ZZ_CR/variables.py` |
| Matching/packing helper code | `ZZ_CR/macros/zh4lmet_zzcr_helpers.cc` |
| Snapshot definition/final output writing | `mkShapesRDF/shapeAnalysis/runner.py` |

When `ZZCR_PINNED_FILES` is set, `aliases.py` and `variables.py` inspect the
input `Events` branches.  Missing optional branches are replaced with explicit
defaults, and missing configured HLT branches are saved as `false` rather than
creating invalid self-definitions.

## Upstream NanoAOD Evidence

### Event-Level HLT Branches

NanoAOD event-level `HLT_*` branches are not trigger-object bits.  They are
boolean branches produced from `edm::TriggerResults`.

Primary CMSSW sources:

- CMSSW_13_0_X:
  [`TriggerOutputBranches.h`](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/plugins/TriggerOutputBranches.h#L15-L20),
  [`TriggerOutputBranches.cc`](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/plugins/TriggerOutputBranches.cc#L8-L60),
  [`fillColumn`](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/plugins/TriggerOutputBranches.h#L48-L53).
- CMSSW_15_0_X:
  [`TriggerOutputBranches.h`](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/plugins/TriggerOutputBranches.h#L15-L20),
  [`TriggerOutputBranches.cc`](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/plugins/TriggerOutputBranches.cc#L8-L64),
  [`fillColumn`](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/plugins/TriggerOutputBranches.h#L48-L53).

Short upstream code snippets used for this interpretation:

| Meaning | Source snippet |
|---|---|
| The writer only handles trigger results | `can only write out edm::TriggerResults objects` |
| Version suffixes are stripped from HLT names | `name.replace(vfound, name.size() - vfound, "");` |
| HLT branches are boolean ROOT branches | `(brname + "/O").c_str()` |
| The branch value is the trigger accept decision | `triggers.accept(nb.idx)` |

Therefore a branch such as
`HLT_Ele30_WPTight_Gsf` means that the event fired that HLT path, after
NanoAOD removed the `_vN` suffix.  It does not say which offline lepton
matched the path.  The per-lepton diagnostics in this audit add that
object-level information separately.

### Trigger Object Table and `TrigObj_filterBits`

The NanoAOD trigger-object collection is produced by
`triggerObjectTable` with the collection name `TrigObj`.

Primary CMSSW sources:

- CMSSW_13_0_X:
  [`triggerObjects_cff.py`](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/python/triggerObjects_cff.py#L45-L126),
  [`TriggerObjectTableProducer.cc`](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/plugins/TriggerObjectTableProducer.cc#L101-L124),
  [`TriggerObjectTableProducer.cc` table columns](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/plugins/TriggerObjectTableProducer.cc#L268-L327),
  [`nano_cff.py`](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/python/nano_cff.py#L85-L90).
- CMSSW_15_0_X:
  [`triggerObjects_cff.py`](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/python/triggerObjects_cff.py#L55-L140),
  [`TriggerObjectTableProducer.cc`](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/plugins/TriggerObjectTableProducer.cc#L101-L124),
  [`TriggerObjectTableProducer.cc` table columns](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/plugins/TriggerObjectTableProducer.cc#L268-L328),
  [`nano_cff.py`](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/python/nano_cff.py#L75-L80).

Short upstream code snippets used for this interpretation:

| Meaning | Source snippet |
|---|---|
| The table is named `TrigObj` | `name= cms.string("TrigObj")` |
| Electron trigger objects carry id 11 | `id = cms.int32(11)` |
| Muon trigger objects carry id 13 | `id = cms.int32(13)` |
| Bit number defaults to quality-bit order | `unsigned int bit = i;` |
| v12 set bits contribute `2^bit` | `int(pow(2, bit))` |
| v15 set bits contribute `2^bit` | `1UL << bit` |
| The id branch is saved as unsigned 16-bit | `addColumn<uint16_t>("id", id` |
| v12 saves `filterBits` as int | `addColumn<int>("filterBits", bits` |
| v15 saves `filterBits` as uint64 | `addColumn<uint64_t>("filterBits", bits` |

The key consequence is that `TrigObj_filterBits` is an integer mask whose bit
positions are the ordered `qualityBits` entries in `triggerObjects_cff.py`,
unless a `qualityBits` entry explicitly sets a `bit`.  No relevant electron
or muon entry used here sets a custom bit, so the row order fixes the bit
numbers.

Local aliases read `TrigObj_filterBits` through `valueAtULL`, so integer input
masks are represented by the same unsigned 64-bit diagnostic branch in the
saved ZZ_CR tree.  The bit meanings decoded by ZZ_CR are the NanoAODv15
electron and muon meanings documented below.

`l*_trigObj_pdgId` and `l*_trigObj_id` are both copied from `TrigObj_id`.
For this collection, that value is the NanoAOD trigger-object category id
from the table producer, not a signed offline PDG id.  The inspected electron
and muon trigger objects have id `11` and `13`.

## Local Trigger Menu

The same configured HLT paths are used for all supported ZZ_CR years
2022, 2022EE, 2023, 2023BPix, and 2024:

| Aggregate branch | Trigger family | Concrete event-level HLT branches saved |
|---|---|---|
| `Trigger_ElMu` | electron-muon | `HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL`, `HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ`, `HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ` |
| `Trigger_dblMu` | double muon | `HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8` |
| `Trigger_sngMu` | single muon | `HLT_IsoMu24` |
| `Trigger_dblEl` | double electron | `HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL` |
| `Trigger_sngEl` | single electron | `HLT_Ele30_WPTight_Gsf` |

`TrigMaker.py` builds each aggregate branch as an OR of the configured paths
for the active run period.  The `HLT_*` branches are the original NanoAOD
TriggerResults booleans; the `Trigger_*` branches are mkShapesRDF aggregate
booleans.

`HLT_Ele35_WPTight_Gsf` exists in some inspected inputs, but it is not part
of the ZZ_CR trigger menu above and is not saved by this audit.

## NanoAOD Trigger-Object Bit Map

The following tables show the exact NanoAOD bit evidence used by the local
decoded branches.  The source snippets are short fragments from the linked
CMSSW files; the bit number comes from the `qualityBits` entry order.

### Legacy CMSSW 13_0_X / NanoAODv12 Electron Bits

Source: [`triggerObjects_cff.py` electron quality bits](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/python/triggerObjects_cff.py#L54-L76).

This table is retained as provenance for older HWWNano files.  It is not the
active local ZZ_CR assumption.

| Local decoded branch | `TrigObj_id` | NanoAOD bit | Upstream snippet | Meaning used locally |
|---|---:|---:|---|---|
| `<lep>_trigObj_bit_ele_CaloIdLTrackIdLIsoVL` | 11 | 0 | `*CaloIdLTrackIdLIsoVL*TrackIso*Filter` | electron object passed the CaloIdL/TrackIdL/IsoVL trigger-object filter family |
| `<lep>_trigObj_bit_ele_1eWPTight` | 11 | 1 | `hltEle*WPTight*TrackIsoFilter*` | broad one-electron WPTight object bit |
| `<lep>_trigObj_bit_ele_1eWPLoose` | 11 | 2 | `hltEle*WPLoose*TrackIsoFilter` | broad one-electron WPLoose object bit |
| `<lep>_trigObj_bit_ele_DoubleEle` | 11 | 4 | `hltEle*Ele*CaloIdLTrackIdLIsoVL*Filter` | double-electron object bit, without split leg information in v12 |
| `<lep>_trigObj_bit_ele_DoubleEleLeg1` | 11 | none | no v12 split-leg bit | unavailable in the legacy v12 bit map |
| `<lep>_trigObj_bit_ele_DoubleEleLeg2` | 11 | none | no v12 split-leg bit | unavailable in the legacy v12 bit map |
| `<lep>_trigObj_bit_ele_EleMu` | 11 | 5 | `hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*` | electron leg of electron-muon paths |
| `<lep>_trigObj_bit_ele_Ele30WPTight` | 11 | none | no v12 Ele30-specific bit | unavailable in the legacy v12 bit map |

### CMSSW 15_0_X / NanoAODv15 Electron Bits

Source: [`triggerObjects_cff.py` electron quality bits](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/python/triggerObjects_cff.py#L58-L86).

| Local decoded branch | `TrigObj_id` | NanoAOD bit | Upstream snippet | Meaning used locally |
|---|---:|---:|---|---|
| `<lep>_trigObj_bit_ele_CaloIdLTrackIdLIsoVL` | 11 | 0 | `*CaloIdLTrackIdLIsoVL*TrackIso*Filter` | electron object passed the CaloIdL/TrackIdL/IsoVL trigger-object filter family |
| `<lep>_trigObj_bit_ele_1eWPTight` | 11 | 1 | `hltEle*WPTight*TrackIsoFilter*` | broad WPTight bit; upstream doc notes possible X-trigger contribution |
| `<lep>_trigObj_bit_ele_1eWPLoose` | 11 | 2 | `hltEle*WPLoose*TrackIsoFilter` | broad one-electron WPLoose object bit |
| `<lep>_trigObj_bit_ele_DoubleEleLeg1` | 11 | 4 | `TrackIsoLeg1Filter` | higher-threshold double-electron leg bit |
| `<lep>_trigObj_bit_ele_DoubleEleLeg2` | 11 | 5 | `TrackIsoLeg2Filter` | lower-threshold double-electron leg bit |
| `<lep>_trigObj_bit_ele_DoubleEle` | 11 | 4 or 5 | leg1 or leg2 snippets above | local OR of the two split double-electron bits |
| `<lep>_trigObj_bit_ele_EleMu` | 11 | 6 | `hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*` | electron leg of electron-muon paths |
| `<lep>_trigObj_bit_ele_Ele30WPTight` | 11 | 18 | `hltEle30WPTightGsfTrackIsoFilter` | explicit Ele30/WPTight object bit, used for exact v15 single-electron matching |

### Legacy CMSSW 13_0_X / NanoAODv12 Muon Bits

Source: [`triggerObjects_cff.py` muon quality bits](https://github.com/cms-sw/cmssw/blob/CMSSW_13_0_X/PhysicsTools/NanoAOD/python/triggerObjects_cff.py#L105-L125).

This table is retained as provenance for older HWWNano files.  It is not the
active local ZZ_CR assumption.

| Local decoded branch | `TrigObj_id` | NanoAOD bit | Upstream snippet | Meaning used locally |
|---|---:|---:|---|---|
| `<lep>_trigObj_bit_mu_TrkIsoVVL` | 13 | 0 | `RelTrkIsoVVLFiltered` | muon object passed TrkIsoVVL trigger filter family |
| `<lep>_trigObj_bit_mu_Iso` | 13 | 1 | `IsoFiltered` | muon object passed isolated-muon filter family |
| `<lep>_trigObj_bit_mu_SingleMu` | 13 | 3 | `SingleMu*IsoFiltered` | single-muon trigger-object bit |
| `<lep>_trigObj_bit_mu_DoubleMu` | 13 | 4 | `hltDiMuon*Filtered*` | double-muon trigger-object bit |
| `<lep>_trigObj_bit_mu_EleMu` | 13 | 5 | `hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*` | muon leg of electron-muon paths |

### CMSSW 15_0_X / NanoAODv15 Muon Bits

Source: [`triggerObjects_cff.py` muon quality bits](https://github.com/cms-sw/cmssw/blob/CMSSW_15_0_X/PhysicsTools/NanoAOD/python/triggerObjects_cff.py#L118-L140).

| Local decoded branch | `TrigObj_id` | NanoAOD bit | Upstream snippet | Meaning used locally |
|---|---:|---:|---|---|
| `<lep>_trigObj_bit_mu_TrkIsoVVL` | 13 | 0 | `RelTrkIsoVVLFiltered` | muon object passed TrkIsoVVL trigger filter family |
| `<lep>_trigObj_bit_mu_Iso` | 13 | 1 | `IsoFiltered` | muon object passed isolated-muon filter family |
| `<lep>_trigObj_bit_mu_SingleMu` | 13 | 3 | `SingleMu*IsoFiltered` | single-muon trigger-object bit |
| `<lep>_trigObj_bit_mu_DoubleMu` | 13 | 4 | `hltDiMuon*Filtered*` | double-muon trigger-object bit |
| `<lep>_trigObj_bit_mu_EleMu` | 13 | 5 | `hltMu*TrkIsoVVL*Ele*CaloIdLTrackIdLIsoVL*Filter*` | muon leg of electron-muon paths |

## Saved Branch Definitions

In the patterns below, `<lep>` is one of `lZ1`, `lZ2`, `lX1`, or `lX2`.
`lZ1/lZ2` are the two leptons in the selected Z0 candidate, ordered by pT.
`lX1/lX2` are the two leptons in the X candidate, also ordered by pT.  These
labels index the merged mkShapesRDF `Lepton_*` collection, not the original
`Electron_*` or `Muon_*` collection.

### Event Trigger Branches

| Branch | Definition |
|---|---|
| `HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL` | NanoAOD TriggerResults boolean for the versionless HLT path. |
| `HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ` | NanoAOD TriggerResults boolean for the versionless HLT path. |
| `HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ` | NanoAOD TriggerResults boolean for the versionless HLT path. |
| `HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8` | NanoAOD TriggerResults boolean for the versionless HLT path. |
| `HLT_IsoMu24` | NanoAOD TriggerResults boolean for the versionless HLT path. |
| `HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL` | NanoAOD TriggerResults boolean for the versionless HLT path. |
| `HLT_Ele30_WPTight_Gsf` | NanoAOD TriggerResults boolean for the versionless HLT path. |
| `Trigger_ElMu` | mkShapesRDF aggregate OR of the three configured electron-muon HLT branches. |
| `Trigger_dblMu` | mkShapesRDF aggregate OR of configured double-muon HLT branches. |
| `Trigger_sngMu` | mkShapesRDF aggregate OR of configured single-muon HLT branches. |
| `Trigger_dblEl` | mkShapesRDF aggregate OR of configured double-electron HLT branches. |
| `Trigger_sngEl` | mkShapesRDF aggregate OR of configured single-electron HLT branches. |

### Per-Lepton Trigger-Object Matching Branches

| Branch pattern | Type/values | Definition |
|---|---|---|
| `<lep>_trigObj_idx` | `Int_t`; `-1` if unmatched | Index of the nearest same-flavor `TrigObj` with `dR < 0.1`.  Matching compares `abs(Lepton_pdgId)` to `abs(TrigObj_id)` and does not require any filter bit. |
| `<lep>_trigObj_dR` | `Float_t`; `-999` if unmatched/invalid | Delta-R between the selected lepton and the nearest matched trigger object. |
| `<lep>_trigObj_nMatches` | `Int_t` | Number of same-flavor trigger objects within `dR < 0.1`. |
| `<lep>_trigObj_matchState` | `Int_t` | `-1=invalid lepton flavor/index`, `0=no match`, `1=exactly one match`, `2=multiple same-flavor trigger objects in cone`. |
| `<lep>_trigObj_pt`, `_eta`, `_phi` | `Float_t`; `-999` if unmatched | Kinematics of the matched `TrigObj`. |
| `<lep>_trigObj_pdgId`, `_id` | `Int_t`; `-999` if unmatched | Copy of `TrigObj_id`.  For electron/muon trigger objects this is `11` or `13`; it is not signed by charge. |
| `<lep>_trigObj_filterBits` | `ULong64_t`; `0` if unmatched | Raw `TrigObj_filterBits` mask copied through an unsigned 64-bit accessor. |

### Decoded Trigger-Object Bit Branches

Each decoded bit branch is a boolean and includes the corresponding lepton
flavor guard.  For example, an electron bit branch is false for muons even if
the raw numeric bit happens to be set on a muon object.

| Branch pattern | Definition |
|---|---|
| `<lep>_trigObj_bit_ele_CaloIdLTrackIdLIsoVL` | `TrigObj_id == 11` and NanoAOD electron bit 0. |
| `<lep>_trigObj_bit_ele_1eWPTight` | `TrigObj_id == 11` and NanoAOD electron bit 1.  In v15 this is broad and can receive X-trigger contributions, per upstream documentation. |
| `<lep>_trigObj_bit_ele_1eWPLoose` | `TrigObj_id == 11` and NanoAOD electron bit 2. |
| `<lep>_trigObj_bit_ele_DoubleEle` | `TrigObj_id == 11` and NanoAODv15 electron bit 4 or bit 5. |
| `<lep>_trigObj_bit_ele_DoubleEleLeg1` | `TrigObj_id == 11` and NanoAODv15 electron bit 4. |
| `<lep>_trigObj_bit_ele_DoubleEleLeg2` | `TrigObj_id == 11` and NanoAODv15 electron bit 5. |
| `<lep>_trigObj_bit_ele_EleMu` | `TrigObj_id == 11` and NanoAODv15 electron bit 6. |
| `<lep>_trigObj_bit_ele_Ele30WPTight` | `TrigObj_id == 11` and NanoAODv15 electron bit 18. |
| `<lep>_trigObj_bit_mu_TrkIsoVVL` | `TrigObj_id == 13` and NanoAOD muon bit 0. |
| `<lep>_trigObj_bit_mu_Iso` | `TrigObj_id == 13` and NanoAOD muon bit 1. |
| `<lep>_trigObj_bit_mu_SingleMu` | `TrigObj_id == 13` and NanoAOD muon bit 3. |
| `<lep>_trigObj_bit_mu_DoubleMu` | `TrigObj_id == 13` and NanoAOD muon bit 4. |
| `<lep>_trigObj_bit_mu_EleMu` | `TrigObj_id == 13` and NanoAOD muon bit 5. |

### Object Family and Fired Family Branches

`<lep>_trigObj_match_<family>` branches are object-level compatibility flags.
They use only the matched trigger object, the lepton flavor, and the decoded
filter-bit map.  They do not require the event-level HLT family to have fired.

`<lep>_trigObj_fired_<family>` branches add the corresponding aggregate
event trigger requirement:

| Branch pattern | Definition |
|---|---|
| `<lep>_trigObj_match_SingleMu` | `<lep>_trigObj_bit_mu_SingleMu`. |
| `<lep>_trigObj_fired_SingleMu` | `Trigger_sngMu && <lep>_trigObj_match_SingleMu`. |
| `<lep>_trigObj_match_DoubleMu` | `<lep>_trigObj_bit_mu_DoubleMu`. |
| `<lep>_trigObj_fired_DoubleMu` | `Trigger_dblMu && <lep>_trigObj_match_DoubleMu`. |
| `<lep>_trigObj_match_SingleEle` | `<lep>_trigObj_bit_ele_Ele30WPTight`. |
| `<lep>_trigObj_fired_SingleEle` | `Trigger_sngEl && <lep>_trigObj_match_SingleEle`. |
| `<lep>_trigObj_match_DoubleEle` | `<lep>_trigObj_bit_ele_DoubleEle`. |
| `<lep>_trigObj_fired_DoubleEle` | `Trigger_dblEl && <lep>_trigObj_match_DoubleEle`. |
| `<lep>_trigObj_match_EleMu` | `<lep>_trigObj_bit_ele_EleMu || <lep>_trigObj_bit_mu_EleMu`. |
| `<lep>_trigObj_fired_EleMu` | `Trigger_ElMu && <lep>_trigObj_match_EleMu`. |

The broad one-electron WPTight bit remains saved as
`<lep>_trigObj_bit_ele_1eWPTight`, but the active single-electron object
compatibility uses the explicit NanoAODv15 Ele30/WPTight bit 18.

### Path/Leg Compatibility Branches

Path/leg branches combine a concrete event-level `HLT_*` branch with the best
available object-level filter-bit compatibility.  They do not prove the
threshold leg of a multi-object path unless NanoAOD stores such a leg bit.

| Branch pattern | Definition |
|---|---|
| `<lep>_trigObj_leg_IsoMu24` | `HLT_IsoMu24 && <lep>_trigObj_match_SingleMu`. |
| `<lep>_trigObj_leg_Mu17_Mu8` | `HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8 && <lep>_trigObj_match_DoubleMu`. |
| `<lep>_trigObj_leg_Ele23_Ele12` | `HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL && <lep>_trigObj_match_DoubleEle`. |
| `<lep>_trigObj_leg_Ele23_Ele12_leg1` | `HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL && <lep>_trigObj_bit_ele_DoubleEleLeg1`. |
| `<lep>_trigObj_leg_Ele23_Ele12_leg2` | `HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL && <lep>_trigObj_bit_ele_DoubleEleLeg2`. |
| `<lep>_trigObj_leg_Ele30` | `HLT_Ele30_WPTight_Gsf && <lep>_trigObj_match_SingleEle`. |
| `<lep>_trigObj_leg_Mu23_Ele12` | `HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL && <lep>_trigObj_match_EleMu`. |
| `<lep>_trigObj_leg_Mu12_Ele23` | `HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ && <lep>_trigObj_match_EleMu`. |
| `<lep>_trigObj_leg_Mu8_Ele23` | `HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ && <lep>_trigObj_match_EleMu`. |

For electron-muon paths, the upstream object bit is generic `1e-1mu`; it does
not encode whether the event path was the Mu23-Ele12, Mu12-Ele23, or
Mu8-Ele23 variant.  The path/leg branches therefore mean "this path fired and
this object is compatible with the electron-muon object-bit family."

### Compact Trigger-Object Mask

`<lep>_trigObj_bits4l` is a `UInt_t` compact diagnostic mask derived from the
decoded booleans.  Prefer the named boolean branches for analysis selections;
the mask is for quick scans.

For electron leptons:

| Packed bit | Meaning |
|---:|---|
| 0 | electron-muon object bit |
| 1 | double-electron object compatibility |
| 2 | double-electron leg 1 |
| 3 | double-electron leg 2 |
| 4 | single-electron family compatibility |
| 5 | exact Ele30/WPTight |
| 6 | broad one-electron WPTight bit |

For muon leptons:

| Packed bit | Meaning |
|---:|---|
| 0 | electron-muon object bit |
| 1 | double-muon object bit |
| 2 | single-muon object bit |
| 3 | isolated-muon bit |
| 4 | TrkIsoVVL bit |

### Event Priority and Baseline Branches

| Branch | Values/definition |
|---|---|
| `ZZCR_dataStreamPriority` | `0=none`, `1=MuonEG`, `2=Muon/SingleMuon`, `3=EGamma`.  The priority mirrors the data stream de-duplication logic in `samples.py`: electron-muon first, then muon, then electron. |
| `ZZCR_streamPriority_MuonEG` | Boolean alias for `ZZCR_dataStreamPriority == 1`. |
| `ZZCR_streamPriority_Muon` | Boolean alias for `ZZCR_dataStreamPriority == 2`. |
| `ZZCR_streamPriority_EGamma` | Boolean alias for `ZZCR_dataStreamPriority == 3`. |
| `ZZCR_triggerFamilyPriority` | `0=none`, `1=ElMu`, `2=SingleMu`, `3=DoubleMu`, `4=SingleEle`, `5=DoubleEle`.  This is an analysis diagnostic priority, not a NanoAOD branch. |
| `ZZCR_nFiredTriggerFamilies` | Count of true aggregate `Trigger_*` family branches among the five configured families. |
| `ZZCR_hltPathPriority` | `0=none`, `1=Mu23_Ele12`, `2=Mu12_Ele23`, `3=Mu8_Ele23`, `4=Mu17_Mu8`, `5=IsoMu24`, `6=Ele23_Ele12`, `7=Ele30`. |
| `ZZCR_nFiredHLTPaths` | Count of true configured concrete `HLT_*` branches among the seven saved paths. |
| `ZZCR_hasValidZ0` | Both entries of `Z0_idx` are non-negative. |
| `ZZCR_hasValidX` | Both entries of `X_idx` are non-negative. |
| `ZZCR_dyLike2lBaseline` | Any configured aggregate trigger fired, `nLepton >= 2`, valid Z0, `Z0_mass > 30`, and both Z0 leptons have pT above 10 GeV. |
| `ZZCR_zzLike4lIncremental` | `ZZCR_dyLike2lBaseline`, valid X, ordered four-lepton pT thresholds 25/15/10/10 GeV, positive `m4l`, and net four-lepton charge zero.  This branch does not include `bVeto`; the commented cut template adds `bVeto` separately. |
| `ZZCR_Z0_trigMatchState` | Pair state for `lZ1/lZ2`: `-1=invalid pair`, `0=no lepton uniquely matched`, `1=partial unique matching`, `2=both leptons uniquely matched`, `3=at least one ambiguous lepton`. |
| `ZZCR_X_trigMatchState` | Same state code for `lX1/lX2`. |
| `ZZCR_4l_trigMatchState` | Same state code for all four leptons; `2` means all four leptons are uniquely matched, `3` means at least one is ambiguous. |

### Other Context Branches Saved With the Audit Tree

These branches are not trigger bits but are saved in the same tree so trigger
turn-on and selection audits can be done without reopening the input NanoAOD.

| Branch family | Definition |
|---|---|
| `Z0_mass`, `Z0_pt`, `Z0_eta`, `Z0_phi`, `X_mass`, `X_pt`, `X_eta`, `X_phi` | Kinematics of the selected Z0 and X lepton pairs computed from `Lepton_*` and the selected pair indices. |
| `m4l`, `pT4l`, `phi4l`, `sumLeptonCharge` | Four-lepton system observables from Z0+X. |
| `lZ1_*`, `lZ2_*`, `lX1_*`, `lX2_*` basic kinematics/gen fields | Per-selected-lepton values copied from `Lepton_*`; invalid indices use `-999`. |
| `l*_convVeto`, `l*_dxy`, `l*_dz`, `l*_hoe`, `l*_lostHits`, `l*_pfIsoId`, `l*_promptMVA`, and related quality branches | Per-selected-lepton quality observables.  Electron values are dereferenced through `Lepton_electronIdx`, muon values through `Lepton_muonIdx`; unavailable flavor/source branches use documented defaults. |
| `l*_isTightElectron_<wp>`, `l*_isTightMuon_<wp>` | Selected lepton's mkShapesRDF tight-object WP flags for the configured l2tight era. |
| `l*_selWP_TotSF` | Selected lepton's total scale factor for the electron or muon WP used by the Z0/X pair builder; data or unavailable inputs default to `1.0`. |
| `Z0_isEE`, `Z0_isMM`, `X_isEE`, `X_isMM`, `X_isSF`, `X_isDF` | Pair-flavor diagnostics. |
| `PuppiMET_pt`, `PuppiMET_phi`, `PuppiMET_significance`, `PuppiMET_sumEt` | MET observables; missing optional branches are filled with `-999`. |
| `dPhi_MET_*`, `dPhi_*_*`, `dEta_*_*`, `dR_*_*` | Angular diagnostics among MET, Z0, X, the four selected leptons, and the four-lepton system. |
| `recoil_ux`, `recoil_uy`, `recoil_ut`, `recoil_upar`, `recoil_uperp` | Hadronic recoil components computed from the four-lepton system and PuppiMET. |
| `HT`, `nCleanJet`, `nJetInHorn`, `CleanJet_*_0`, `CleanJet_*_1`, `bVeto` | Jet/recoil control diagnostics and the configured DeepFlavB veto. |
| `GenMET_*`, `Lepton_gen*`, `CleanJet_gen*` | Generator-level diagnostics when available; data fallbacks are empty vectors or zero/default values. |

## Known Limitations

NanoAOD trigger-object filter bits are object-filter family bits, not complete
HLT-path provenance.  They do not always encode threshold, DZ, or subpath
information.

The practical consequences for this audit are:

- The local code assumes NanoAODv15 trigger-object bits for every supported
  `ZZCR_YEAR`.  It does not fall back to NanoAODv12 behavior based on
  `l2tight_era` or historical input campaign names.
- If a file actually carries the older NanoAODv12 electron trigger-object bit
  table, the decoded electron split-leg, electron-muon, and Ele30-specific
  diagnostics follow the v15 positions anyway.  Such a file should be treated
  as schema-mismatched for this audit.
- The local single-electron object match uses the explicit Ele30 bit 18 and
  keeps the broad WPTight bit as a separate diagnostic.
- Electron-muon object bits are generic for the electron-muon trigger family.
  The path-specific branches distinguish the fired event HLT path, but the
  trigger object itself does not prove whether it was the Mu23, Mu12, Mu8,
  Ele23, or Ele12 threshold leg.
- `TrigObj_id` is an unsigned NanoAOD object category code, so matching uses
  absolute lepton flavor and does not encode charge.

## Validation

### Original Trigger-Audit Run

Representative input files were inspected for all supported years.  The checks
found all seven configured concrete HLT paths, all five aggregate `Trigger_*`
branches, `nTrigObj`, `TrigObj_pt/eta/phi/id/filterBits`,
`Lepton_pt/eta/phi/pdgId/electronIdx/muonIdx`, and the corresponding
`Electron_*` and `Muon_*` branches in representative 2022, 2022EE, 2023,
2023BPix, and 2024 data and MC files.

Those input inspections document what existed in the HWWNano campaigns at the
time.  The current local trigger-object decoding contract is stricter: the
saved ZZ_CR trigger-object diagnostics assume NanoAODv15 bit meanings for every
supported `ZZCR_YEAR`.

Observed input branch types:

| Branch | 130X/NanoAODv12 | 150X/NanoAODv15 |
|---|---|---|
| `TrigObj_id` | `UShort_t` | `UShort_t` |
| `TrigObj_filterBits` | `Int_t` | `ULong64_t` |

Representative files checked:

| Year | MC file | Data streams checked |
|---|---|---|
| 2022 | `/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer22_130x_nAODv12_Full2022v12/MCl2loose2022v12__MCCorr2022v12JetScaling__l2tight/nanoLatino_DYto2L-2Jets_MLL-50__part0.root` | `Run2022_ReReco_nAODv12_Full2022v12/DATAl2loose2022v12__l2loose`, EGamma, Muon, MuonEG |
| 2022EE | `/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer22EE_130x_nAODv12_Full2022v12/MCl2loose2022EEv12__MCCorr2022EEv12JetScaling__l2tight/nanoLatino_DYto2L-2Jets_MLL-50__part0.root` | `Run2022EE_Prompt_nAODv12_Full2022v12/DATAl2loose2022EEv12__l2loose`, EGamma, Muon, MuonEG |
| 2023 | `/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer23_130x_nAODv12_Full2023v12/MCl2loose2023v12__MCCorr2023v12JetScaling__l2tight/nanoLatino_DYto2L-2Jets_MLL-50__part0.root` | `Run2023_Prompt_nAODv12_Full2023v12/DATAl2loose2023v12__l2loose`, EGamma0, Muon0, MuonEG |
| 2023BPix | `/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer23BPix_130x_nAODv12_Full2023BPixv12/MCl2loose2023BPixv12__MCCorr2023BPixv12JetScaling__l2tight/nanoLatino_DYto2L-2Jets_MLL-50__part0.root` | `Run2023BPix_Prompt_nAODv12_Full2023BPixv12/DATAl2loose2023BPixv12__l2loose`, EGamma0, Muon0, MuonEG |
| 2024 | `/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/nanoLatino_DYto2E-2Jets_MLL-50__part0.root`, plus DYto2Mu analog | `Run2024_Prompt_nAODv15_Full2024v15/DATAl2loose2024v15__l2loose`, EGamma0, Muon0, MuonEG |

Commands recorded from the original validation:

```bash
python -m py_compile \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/zzcr_selection_config.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/aliases.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/variables.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/cuts.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/samples.py
```

```bash
python - <<'PY'
import ROOT
ROOT.gInterpreter.Declare('#include "PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/zh4lmet_zzcr_helpers.cc"')
print("declared")
print(ROOT.ZH4lMETZZCR.pack4lTrigObjBits(11, 1 << 1, 12))
print(ROOT.ZH4lMETZZCR.pack4lTrigObjBits(11, 1 << 18, 15))
PY
```

The Python compile and C++ declaration checks passed.

Config import/compile checks were run for `ZZCR_YEAR=2022`, `2022EE`, `2023`,
`2023BPix`, and `2024` with representative pinned DY files:

```bash
ZZCR_YEAR=<year> ZZCR_PINNED_SAMPLE=<sample> ZZCR_PINNED_FILES=<file> \
  mkShapesRDF -c 1 -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -configs /tmp/zzcr_compile_<year> -l 1
```

All five years returned `COMPILE_OK`.

Focused 2024 snapshot command:

```bash
ZZCR_YEAR=2024 \
ZZCR_PINNED_SAMPLE=DYto2E-2Jets_MLL-50 \
ZZCR_PINNED_FILES=/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/nanoLatino_DYto2E-2Jets_MLL-50__part0.root \
mkShapesRDF -c 1 -o 0 -b 0 -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -configs /tmp/zzcr_run_2024_configs -l 1000 \
  --output-folder /tmp/zzcr_2024_dy_snapshot
```

Output file:

`/tmp/zzcr_2024_dy_snapshot/mkShapes__ZH_4lMET_ZZCR_2024_20260721_171308.root`

The output `trees/zz_cr_ALL/DYto2E-2Jets_MLL-50/Events` tree had 427 entries
and contained the new event and per-lepton trigger-object diagnostic branches.
Checked branch types included `lZ1_trigObj_idx` as `Int_t`,
`lZ1_trigObj_dR` as `Float_t`, `lZ1_trigObj_filterBits` as `ULong64_t`,
`lZ1_trigObj_bits4l` as `UInt_t`, and the event categories as `Int_t`.

Small yield splits from that 2024 DY snapshot:

| Split | Raw entries | Sum weight |
|---|---:|---:|
| stream `MuonEG` | 1 | -0.708101 |
| stream `EGamma` | 426 | 215.263 |
| family `ElMu` | 1 | -0.708101 |
| family `SingleEle` | 403 | 200.393 |
| family `DoubleEle` | 23 | 14.8701 |
| HLT `Mu8_Ele23` | 1 | -0.708101 |
| HLT `Ele23_Ele12` | 392 | 196.852 |
| HLT `Ele30` | 34 | 18.4106 |
| `lZ1` unmatched / unique / ambiguous | 1 / 425 / 1 | -0.708101 / 214.555 / 0.708101 |
| `lZ2` unmatched / unique / ambiguous | 4 / 421 / 2 | 2.8324 / 213.138 / -1.4162 |

### NanoAODv15 Assumption Update

After changing the local trigger-object schema selection to assume NanoAODv15,
the following local checks were run on 2026-07-21 from the repository root after
`source start.sh`.

```bash
python -m py_compile \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/zzcr_selection_config.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/aliases.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/variables.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/cuts.py \
  PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/samples.py
```

Result: passed.

```bash
python -m pytest tests/test_zzcr_configuration_profiles.py -q
```

Result: `25 passed`.  The added coverage checks that every supported
`ZZCR_YEAR` resolves `trigobj_nanoaod_version()` to 15, rejects a legacy v12
override, and builds representative aliases with v15 electron bits 4, 5, 6,
and 18.

```bash
python - <<'PY'
import ROOT
ROOT.gInterpreter.Declare('#include "PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR/macros/zh4lmet_zzcr_helpers.cc"')
checks = {
    "electron_ele30_default": ROOT.ZH4lMETZZCR.pack4lTrigObjBits(11, 1 << 18),
    "electron_diele_leg1_v15": ROOT.ZH4lMETZZCR.pack4lTrigObjBits(11, 1 << 4, 15),
    "electron_elemu_v15": ROOT.ZH4lMETZZCR.pack4lTrigObjBits(11, 1 << 6, 15),
    "muon_singlemu_v15": ROOT.ZH4lMETZZCR.pack4lTrigObjBits(13, 1 << 3, 15),
}
expected = {
    "electron_ele30_default": (1 << 4) | (1 << 5),
    "electron_diele_leg1_v15": (1 << 1) | (1 << 2),
    "electron_elemu_v15": 1 << 0,
    "muon_singlemu_v15": 1 << 2,
}
assert checks == expected, (checks, expected)
print(checks)
PY
```

Result: passed with
`{'electron_ele30_default': 48, 'electron_diele_leg1_v15': 6, 'electron_elemu_v15': 1, 'muon_singlemu_v15': 4}`.

A bounded local postprocessing snapshot was also run with a 10-event limit on
the 2024 DYto2E pinned file:

```bash
ZZCR_YEAR=2024 \
ZZCR_PINNED_SAMPLE=DYto2E-2Jets_MLL-50 \
ZZCR_PINNED_FILES=/eos/cms/store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/nanoLatino_DYto2E-2Jets_MLL-50__part0.root \
mkShapesRDF -c 1 -o 0 -b 0 -f PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR \
  -configs /tmp/zzcr_v15_configs.<tmp> -l 10 \
  --output-folder /tmp/zzcr_v15_snapshot.<tmp>
```

The run reported 6 events passing preselections and wrote
`/tmp/zzcr_v15_snapshot.NZagh7/mkShapes__ZH_4lMET_ZZCR_2024_20260721_180819.root`.
The final `trees/zz_cr_ALL/DYto2E-2Jets_MLL-50/Events` tree had 3 entries and
contained the v15 trigger-object diagnostic branches:

```text
ZZCR_triggerFamilyPriority
lZ1_trigObj_bit_ele_DoubleEleLeg1
lZ1_trigObj_bit_ele_DoubleEleLeg2
lZ1_trigObj_bit_ele_Ele30WPTight
lZ1_trigObj_bit_ele_EleMu
lZ1_trigObj_bits4l
lZ1_trigObj_match_SingleEle
```
