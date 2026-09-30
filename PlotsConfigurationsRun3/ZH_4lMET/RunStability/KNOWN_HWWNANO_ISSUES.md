# Known HWWNano object-association issues in 2024 RunStability

**Status (2026-09-30):** This page records findings from a bounded, paired
central-NanoAOD/HWWNano audit of 2024 Muon C/I, EGamma C/I, and DY file
prefixes. It describes the retained historical HWWNano product and the source
now on `ZH_devel`. It is **not** a corrected full-year yield or a validation of
all HWWNano campaigns. The published RunStability campaign used a compiled
configuration and an earlier **dirty producer worktree whose exact source is
unavailable**. Its retained files and compiled selection govern the historical
observations; present source identifies possible mechanisms, not the exact
historical executing lines.

| Finding | Direct evidence | What is established |
| --- | --- | --- |
| Tight electron and muon decisions can belong to prefilter positions | Raw HWW objects, retained original indices, stored tight vectors, and paired final-category replays | A historical product association error in the audited events; a corresponding ordering defect is visible in current `LeptonSel.py`. |
| Retained electron `eta` can belong to a different raw electron | Raw HWW coordinates and retained indices in period I | A separate historical product error. Its producer operation is unlocated; the checked current sorting loop did not reproduce it. |
| Jet-cleaning combinations use inconsistent lepton index spaces | Current `JetSelMask.py` expressions | A conditional current source-code defect. Its historical yield effect has not been measured. |

The source and consumer paths are
[`LeptonSel.py`](../../../mkShapesRDF/processor/modules/LeptonSel.py#L149-L217),
[`LeptonMaker.py`](../../../mkShapesRDF/processor/modules/LeptonMaker.py#L13-L53),
[`JetSelMask.py`](../../../mkShapesRDF/processor/modules/JetSelMask.py#L111-L137),
[`aliases.py`](aliases.py#L94-L145),
[`category_config.py`](category_config.py#L18-L34), and
[`run_stability_helpers.cc`](macros/run_stability_helpers.cc#L15-L117).
The [paired muon report](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/2024-paired-lowpt-event-diagnostic-20260929.md),
[electron report](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/2024-paired-lowpt-electron-diagnostic-20260929.md),
and [historical replay notes](https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/HISTORICAL_HWW_DIAGNOSTIC.md)
retain the full method and provenance. Those diagnostic files live on separate
branches; they are not part of this `ZH_devel` tree.

## 1. Tight-lepton vector association

**Invariant.** At retained lepton position `i`, a
`Lepton_isTightMuon_*[i]` or `Lepton_isTightElectron_*[i]` bit must describe the
raw object named by `Lepton_muonIdx[i]` or `Lepton_electronIdx[i]`, under the
named working point. These are **offline identification/selection decisions,
not HLT trigger bits**. A vector can have the expected length yet still attach
a decision to the wrong object. The audited branches are
`Lepton_isTightMuon_cut_TightID_pfIsoTight_HWW_tthmva_67` and
`Lepton_isTightElectron_mvaWinter22V2Iso_WP90_tthMVA_Run3`.

**Historical product evidence.** Muon C central source entry 234,
`(run, luminosityBlock, event) = (379416, 147, 131724611)`, is HWW `part0`
entry 65. The raw HWW muons have original indices `[0, 1, 2]` and recomputed
2024 tight decisions `[false, true, true]`. HLT-safe `Lepton_muonIdx` retains
`[1, 2]`, requiring `[true, true]`; the stored tight vector is
`[false, true]`. Its first bit describes the removed muon 0, not retained
muon 1. The raw-input and stored-vector comparison is in the
[muon mask audit](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/hww-tight-mask-audit.json).

In the paired Muon C/I prefixes, Coffea selects 4,478 IsoMu24 DATA events and
the compiled historical replay selects 3,935. Of the **543 Coffea-only**
events, 508 have the historical leading-two decision false; **503** of those
have both selected raw HWW muons passing the named tight inputs but a stored
bit disagreeing at a retained selected-lepton position. In 502 of those 503,
the stored vector also equals the prefilter decision prefix. This measures
the prevalence of the association error among these local differences. It is
not a corrected 2024 yield, nor proof that each of the 543 has only this cause.

EGamma C source entry 20774, `(379729, 907, 1396820419)`, gives an electron
example. Prefilter `VetoLepton_electronIdx` is `[-1, 0, 1, -1, 2]`; retained
`Lepton_electronIdx` is `[0, 1]`. Both retained raw HWW electrons pass every
named 2024 tight-electron input. The stored vector is `[false, true]`, the
correctly mapped vector `[true, true]`. The
[electron mask audit](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-hww-mask-audit.json)
records the ID, isolation, impact-parameter, conversion, and prompt-MVA
decisions from the *same HWW event*.

**Visible source mechanism and consumer.** Current
[`LeptonSel.py`](../../../mkShapesRDF/processor/modules/LeptonSel.py#L149-L217)
defines propagated `Lepton_isTightElectron_*` and `Lepton_isTightMuon_*`
vectors before applying the HLT-safe mask to six core `Lepton_*` arrays:
`pt`, `eta`, `phi`, `pdgId`, `electronIdx`, and `muonIdx`. It does not apply that
mask to the already defined tight vectors in the same step. When an earlier
lepton is removed, this ordering does not preserve the position-to-object
invariant. The retained historical vectors often have the *retained length*
but the *prefilter prefix*; the exact historical serialization/producer
operation that yielded that representation cannot be inferred from the
current source alone.

RunStability's [`L2TightLeading2`](aliases.py#L94-L125) indexes those stored
bits at positions found through `ProductionLeptonPt`; its
[`bestZ0IdxWithID`](aliases.py#L128-L145) uses them to construct the global Z
pair. The [preselection](category_config.py#L18-L34) requires the leading-two
gate, and final categories and `Z0_mass` histograms consume the selected pair.
For the Muon C example, the false bit rejects a genuinely tight retained
muon and prevents a valid historical Z candidate. Merely removing the
leading-two gate cannot repair a wrong bit still used by the pair builder.

**Measured electron counterfactual.** In the paired EGamma C/I prefixes, the
[compiled-selection replay](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-counterfactual-summary.json)
changed either the stored named electron tight vector, the historical
leading-two clause, or both *in memory*, leaving the HWW inputs, other cuts,
stream weights, and category definitions fixed. Its disjoint classification
of **Coffea-only** events that pass the final historical category is:

| Path, C+I | Tight-vector alignment alone | Gate removal alone | Both required | Neither: historical stream weight zero | Coffea-only total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ele30 | 39 | 18 | 1 | 2 | 60 |
| Ele23–Ele12 | 37 | 16 | 1 | 2 | 56 |

The counts are for fixed file prefixes, not a full-year correction. They
separate a stored-bit error from the intentionally different leading-two
requirement and DATA stream priority. Some independent failure flags overlap;
the disjoint final-category outcomes above must not be added to those flags.

**Disposition.** Audit each campaign's producer revision and raw-index to
retained-bit alignment before using these fields. A future producer fix must
filter every lepton-indexed derived vector consistently, then regenerate and
validate affected ntuples and downstream products. This page changes no
producer code or historical evidence.

## 2. Historical electron coordinate association

**Invariant and evidence.** `Lepton_eta[i]`, `Lepton_phi[i]`, and
`Lepton_electronIdx[i]` must refer to the same raw electron. In the retained
EGamma I event at central source entry 27025, `(386509, 159, 333332716)`,
`Lepton_electronIdx = [0, 1]`. Raw HWW electron eta is approximately
`[-0.9336, -2.0571]`, while retained `Lepton_eta` is
`[-2.0571, -0.9336]`; retained `phi` follows indices `[0, 1]`. Both stored
tight bits and correctly mapped bits are `[true, true]`. These values are in
the [electron retained-file audit](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-hww-mask-audit.json).

**Consequence.** [`ProductionLeptonPt`](aliases.py#L111-L123) uses a tight
eta/phi match to prefilter `VetoLepton` coordinates; the
[`productionAlignedPt` helper](macros/run_stability_helpers.cc#L15-L54)
cannot match either leading retained electron in this event, and
[`productionGateIndex`](macros/run_stability_helpers.cc#L109-L116) returns
`[-1, -1]` for ranks zero and one. The leading-two gate is therefore false
despite both electrons passing their raw working point. In the local replay,
removing only that gate recovers this event. In general, an incoherent eta
can also alter pair mass, ranking, and later histogram membership because the
Z builder uses retained coordinates.

Among Coffea-only EGamma I events, the audit finds this coordinate mismatch
in 19/35 Ele30 and 17/32 Ele23–Ele12 events; those are **independent flags**.
The disjoint final-category replays recover 18 and 16, respectively, by gate
removal alone, with one event per path requiring both gate removal and tight
alignment. The numerical effect is measured only on these prefixes.

**Code path, uncertainty, disposition.** The exact operation in the dirty
historical producer that changed eta association has **not** been identified.
The [current `LeptonMaker.py` sorting loop](../../../mkShapesRDF/processor/modules/LeptonMaker.py#L13-L50)
was checked and did **not** reproduce this eta-only error; assigning it to
that loop or to `LeptonSel.py` would exceed the evidence. Audit coordinate
coherence by original index in any campaign of interest. Do not presume that
newly produced HWWNano has this historical eta defect without such an audit.

## 3. Jet-cleaning masked-index mismatch in current source

**Invariant and source defect.** A combination index produced for masked
lepton slot `j` must retrieve eta and phi from that same masked lepton. Current
[`JetSelMask.py`](../../../mkShapesRDF/processor/modules/JetSelMask.py#L111-L137)
builds `Jet_Lepton_comb` with `Lepton_pt[LeptonMask_JC].size()` but computes
`dR2` with `Take(Lepton_eta, Jet_Lepton_comb[1])` and the corresponding
unmasked `Lepton_phi`. If `Lepton_pt = [8, 20]` GeV, then
`LeptonMask_JC = [false, true]` and masked slot 0 denotes original lepton 1;
`Take(Lepton_eta, [0])` instead uses original lepton 0. This can clean or
retain the wrong corrected jet. RunStability then applies the horn count
[`nJetInHorn`](aliases.py#L184-L188) and its zero-jet preselection, so the
selection can change if this code path is used and the geometry matters.

This is a **separate current source-code indexing defect**, conditional on
lepton ordering and the mask. The 2024 configured producer chains include
`jetSelMask` after `lepSel` in
[`Steps_cfg.py`](../../../mkShapesRDF/processor/framework/Steps_cfg.py#L395-L446),
but the defect's numerical contribution to the published 2024 RunStability
difference has **not** been established. It is unrelated to the separate DATA
JEC `Regrouped_*` failure, which prevented a fresh local DATA producer replay.
No jet-cleaning producer change is made here.

## What is and is not invalid?

Affected historical entries are unreliable **for analyses consuming the
misassociated tight bits, incoherent coordinates, or selections derived from
them**, including affected RunStability Z decisions. The separate jet-index
defect makes horn decisions suspect where its mask shifts indices, but its
historical effect has not been measured. These findings do not invalidate
every HWWNano entry, every branch, or the parent
central NanoAOD. The current tight-vector source ordering makes newly
produced ntuples susceptible when filtering changes positions. The historical
eta-only error has not been shown to persist in current production. A source
correction cannot retroactively repair already written files. For a
trustworthy RunStability yield, establish the producer revision, audit
alignment and campaign coverage, then regenerate affected ntuples and
downstream outputs under a fresh identity where required.

**Other differences are not these bugs.** Historical MuonEG → Muon → EGamma
stream priority, Coffea's intentional omission of the leading-two gate,
Coffea selected-pair TrigObj matching, MC migrations across the 35 GeV
threshold, and the separate DATA JEC failure have different semantics. A
framework disagreement alone does not prove an HWWNano bug. The paired-prefix
diagnostics identify concrete historical errors, but they do not completely
attribute the published full-year **12.4% muon DATA** or **2.8% electron
DATA** differences.
