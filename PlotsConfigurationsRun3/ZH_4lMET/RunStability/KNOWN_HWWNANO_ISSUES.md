# HWWNano object-association findings relevant to 2024 RunStability

**Scope, updated 2026-10-01.** HWWNano is produced by the **shared mkShapesRDF
framework** used by the Latino group. This page lives in a personal
`RunStability` analysis leaf because that analysis exposed the failures; the
producer findings are not RunStability-only code. The retained 2024 HWWNano
files and compiled historical RunStability selection are evidence. The old
producer ran from an unavailable *dirty worktree*, so current source at
[`4e6793f`](https://github.com/TheQuantiser/mkShapesRDF/tree/4e6793fd315807b7db7823d2612dc1ad705f55bd)
shows present mechanisms, not the exact historical executable.

**Completed repair demonstration:** read the
[repair report](diagnostics/hww_object_associations/REPAIR_REPORT.md) for the
controlled two-file MC gate comparison, six freshly written and reopened
snapshots, and historical-policy Z replay. The producer repairs were executed
at [`9a0e9be`](https://github.com/TheQuantiser/mkShapesRDF/commit/9a0e9be35c27e2907e6201460d0a5de58a091651)
on `fix-demo/2024-hwwnano-object-associations`, with reviewed evidence at
[`8d940ab`](https://github.com/TheQuantiser/mkShapesRDF/commit/8d940abcf429f753074121a250db3717434eb2f6).
**The repairs are NOT present in `ZH_devel`.** This integration adds
documentation only; the four relevant producer files still match the
original complete-file diagnostic at
[`69ff2dad`](https://github.com/TheQuantiser/mkShapesRDF/commit/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0).
The report's reproduction commands point to the separate repair branch,
where the scripts and numerical evidence remain.

| Finding | Confidence | Relevant scope |
| --- | --- | --- |
| Tight electron/muon bits can describe prefilter positions | **Confirmed in audited historical HWW events**; matching omission visible in current source | Shared producer output; MC skim and downstream selections can consume these bits. |
| Electron eta can disagree with retained raw-electron index while phi agrees | **Confirmed in audited historical period-I HWW events**; producer operation unresolved | Retained product and its RunStability coordinate matching. |
| Corrected-pT reorder can reuse a mutable permutation | **Current-source conditional defect**, reproduced in an isolated live lepton-module witness; repaired snapshots pass real nonidentity-permutation checks | Historical eta-only cause and campaign prevalence remain unresolved; this stage follows MC `l2tight`. |
| `isLoose` is defined before filtering and is not carried through later reorder | **Current-source association/length concern**; repaired snapshot audits pass; no direct measured RunStability effect | Not consumed directly by this RunStability leaf. |
| DATA JEC requests unsupported uncertainty sources | **Recorded configuration failure**, resolved on the repair branch by requesting no DATA JES sources | Nominal corrections and cleaning were retained; this failure is separate from object association. |
| Jet-cleaning masked-slot expression | **Ruled out as an index error for the active 2024 module order** | Fragile only if reused with an unsorted lepton collection. |
| JES variation jet-index composition | **Conditional source risk requiring an input-order audit** | Variation branches only; no established nominal RunStability effect. |

## Production order: what can be lost before analysis?

The configured 2024 chains run in this order, as shown by
[`Steps_cfg.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/framework/Steps_cfg.py#L395-L445):

```text
Central NanoAOD → LeptonMaker (descending pT) → LeptonSel (HLT-safe filter)
  → corrected jets → JetSelMask
  DATA: → leptonScale_data → downstream kinematics → HWWNano snapshot
  MC:   → formulasMC → l2tight → leptonScale_mc
        → downstream kinematics → HWWNano snapshot
HWWNano → this leaf's compiled RunStability cuts, Z builder and histograms
```

The decisive MC fragment is literally:

```python
"formulasMC",
"l2tight",
"leptonScale_mc",
"l2Kin",
```

DATA has no matching `l2tight` production step in this chain. This order
separates an **upstream MC event loss** from a wrong **retained branch** or a
later RunStability rejection. An analysis alias cannot recover an event that
the producer omitted from its HWWNano snapshot.

## 1. Findings in the shared producer and retained HWWNano

### Tight working-point bits can describe the wrong retained lepton

**Invariant.** At retained position `i`, the offline
`Lepton_isTightMuon_*[i]` or `Lepton_isTightElectron_*[i]` decision must
describe the raw object named by `Lepton_muonIdx[i]` or
`Lepton_electronIdx[i]`. Every lepton-indexed vector must undergo the same
filter and each later permutation. These are **offline working-point bits,
not HLT bits**. The audited branches are
`Lepton_isTightMuon_cut_TightID_pfIsoTight_HWW_tthmva_67` and
`Lepton_isTightElectron_mvaWinter22V2Iso_WP90_tthMVA_Run3`.

**Current source operation.** [`LeptonSel.py` lines 149–178](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/LeptonSel.py#L149-L178)
define the tight vectors using the then-current indices:

```python
df = df.Define("Lepton_isTightElectron_"+ids, "propagateMask(Lepton_electronIdx, comb, false)")
df = df.Define("Lepton_isTightMuon_"+ids, "propagateMask(Lepton_muonIdx, comb, false)")
```

Later, [lines 204–217](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/LeptonSel.py#L204-L217)
filter only six core arrays:

```python
branches = ["pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx"]
for prop in branches:
    df = df.Redefine(
        f"Lepton_{prop}",
        f"Lepton_{prop}[LeptonMaskHyg_Ele && LeptonMaskHyg_Mu]",
    )
```

The tight vectors are absent from that loop. Defining a decision before
filtering its objects, without applying the same mask to the decision, does
not maintain positional association. The exact historical serialization or
producer operation that gave the retained vectors their observed *retained
length but prefilter prefix* remains unknown.

**Retained-file example.** In Muon C central source entry 234,
`(run, luminosityBlock, event) = (379416, 147, 131724611)`, HWW `part0`
entry 65 contains:

| Representation | Raw muon indices | Tight decisions |
| --- | --- | --- |
| Before HLT-safe filtering | `[0, 1, 2]` | `[false, true, true]` |
| Correctly aligned after filtering | `[1, 2]` | `[true, true]` |
| Actually stored at retained positions | `[1, 2]` | `[false, true]` |

Raw HWW muons 1 and 2 pass the named working-point inputs. The first stored
bit follows removed muon 0. This is a within-file object-association failure,
not an inference from a Coffea/mkShapesRDF yield difference. The
[muon mask audit](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/hww-tight-mask-audit.json)
records the raw inputs, original indices and stored vector. The analogous
[electron audit](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-hww-mask-audit.json)
shows EGamma C source entry 20774, `(379729, 907, 1396820419)`: retained
electron indices `[0, 1]` both pass the raw HWW working point, but stored
`[false, true]` replaces expected `[true, true]` after an earlier lepton was
removed.

**Measured scope and limit.** In the paired Muon C/I prefixes, Coffea selects
4,478 IsoMu24 DATA events and the compiled historical replay 3,935. Of 543
Coffea-only events, 508 have the historical leading-two decision false; 503
have both selected raw HWW muons passing the tight inputs but a wrong stored
bit at a retained position. For 502 of those 503, the stored vector is also
the prefilter decision prefix. These are fixed-prefix observations, not a
corrected full-year yield or proof that each event has only one cause. The
[paired muon report](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/2024-paired-lowpt-event-diagnostic-20260929.md)
and [historical replay notes](https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/HISTORICAL_HWW_DIAGNOSTIC.md)
give their provenance. The historical dirty producer source is unavailable:
the retained file proves the wrong bit association, while current source
supplies a consistent mechanism rather than proof of its exact old line.

**MC producer skim.** The current
[`L2TightSelection.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/L2TightSelection.py#L18-L35)
builds a predicate at positions 0 and 1 and filters the event:

```python
lepton1_selection = lepton1_selection + f"Lepton_isTightElectron_{wp}[0]>0.5"
lepton2_selection = lepton2_selection + f"Lepton_isTightElectron_{wp}[1]>0.5"
l2tight_selection = f"({lepton1_selection}) && ({lepton2_selection})"
df = df.Filter(f"{l2tight_selection}")
```

The first two lines are from the first electron-WP branch and the final two
lines are the completed predicate and filter; muon choices are also added in
between. A falsely attached bit can therefore omit an MC event **before**
`leptonScale_mc` and the HWWNano snapshot. The complete two-file investigation
now measures erroneous losses and acceptances causally on the current
pre-smearing producer graph; its accepted-key sets also match the actual
paired historical part0 membership. That does not recover the exact dirty
historical executable. DATA has no corresponding MC `l2tight` production
skim in its active chain; wrong retained bits can still change later DATA
selections. An HWWNano-only alias change cannot recover MC events absent
from that file. See [the complete-file gate result](diagnostics/hww_object_associations/REPAIR_REPORT.md#complete-file-mc-acceptance-causal-gate-result).

### Historical electron eta/index association is a separate error

**Invariant and retained evidence.** Retained `Lepton_eta[i]`,
`Lepton_phi[i]` and `Lepton_electronIdx[i]` must describe one raw electron.
EGamma I central source entry 27025, `(386509, 159, 333332716)`, has
`Lepton_electronIdx = [0, 1]`, raw electron eta approximately
`[-0.9336, -2.0571]`, and retained eta `[-2.0571, -0.9336]`. Retained phi
still follows `[0, 1]`; stored and correctly mapped tight bits are both
`[true, true]`. The [period-I retained-file audit](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-hww-mask-audit.json)
contains those arrays.

**Impact and uncertainty.** The RunStability
[`ProductionLeptonPt` matcher](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/PlotsConfigurationsRun3/ZH_4lMET/RunStability/aliases.py#L111-L123)
requires eta/phi agreement with the prefilter `VetoLepton` collection. For
this event its [helper](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/PlotsConfigurationsRun3/ZH_4lMET/RunStability/macros/run_stability_helpers.cc#L15-L54)
cannot match the two retained electrons, and the two
[`productionGateIndex` calls](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/PlotsConfigurationsRun3/ZH_4lMET/RunStability/macros/run_stability_helpers.cc#L109-L116)
each return `-1`. The leading-two gate rejects it despite two genuinely
tight raw electrons; removing only that gate recovers this event in the
compiled historical replay. Wrong coordinates can also affect Z kinematics.
The exact operation that made the historical eta-only mismatch is **not
identified**. A bounded check of the current
[`LeptonMaker.py` sorting loop](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/LeptonMaker.py#L13-L50)
did not reproduce it. The current correction reordering risk below has **not**
been shown to cause this particular historical event.

### Corrected-pT reordering can split aligned lepton arrays

**Invariant.** A corrected-pT permutation must remain immutable and be
applied **once** to each originally aligned per-lepton vector. The permutation
itself and a product already reordered with it must not be reordered again.

**Current source operation.** After lepton scale/smearing, current
[`LeptonScaleSmearing.py` lines 287–295](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/LeptonScaleSmearing.py#L287-L295)
contains:

```python
df = df.Define("Lepton_sorting",     "sortedIndices(Lepton_newPt)")
df = df.Define("Lepton_rochesterSF", "Take(Lepton_newPt/Lepton_pt, Lepton_sorting)")
df = df.Redefine("Lepton_pt",        "Take(Lepton_newPt, Lepton_sorting)")

for branch in df.GetColumnNames():
    if branch.startswith("Lepton_") and branch!="Lepton_pt":
        df = df.Redefine(branch, f"Take({branch}, Lepton_sorting)")
```

The generic loop includes `Lepton_sorting` itself. If the corrected-pT
permutation is `p`, redefining that column as `Take(p,p)` changes what later
loop iterations use. For a two-lepton swap, `p = [1,0]` but
`Take(p,p) = [0,1]`: columns visited before the self-redefinition receive a
swap, while later ones may receive the identity. `Lepton_rochesterSF` is
already permuted at definition and can be taken a second time by the same
loop. [`mRDF.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/framework/mRDF.py#L137-L143)
assembles columns with `c.cols = list(set(c.cols + [a]))`, and
[`GetColumnNames()`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/framework/mRDF.py#L284-L286)
returns that list; iteration order is not an object-association contract.

This is a **conditional source-level defect when momentum corrections change
ordering**. Misordered stored coordinates, original indices, ID/selection or
weight vectors, and derived kinematics are possible. An
[isolated live trace](https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/observed-summary.json)
for EGamma I entry 27025 reproduces a phi/index mismatch under a real swap
and its recorded column order. That run omitted preceding JME and was not
a full DATA snapshot; it did **not** reproduce the historical eta-only
pattern. Campaign prevalence and the share of the published full-year
discrepancy remain unmeasured. In MC,
`l2tight` precedes this loop, so this reordering cannot be the cause of an
earlier `l2tight` event loss. A conceptual correction would retain one
immutable permutation, apply it once to each aligned input vector, and
exclude the permutation and already reordered outputs from the generic loop.
The separate repair branch implements this mapping and validates fresh
snapshots, including real reorderings. No producer fix is integrated here.

### `isLoose` is a narrower association concern

The active `Loose` mapping selects `FakeObjWP` in
[`LeptonSel_cfg.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/data/LeptonSel_cfg.py#L1-L8).
[`LeptonSel.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/LeptonSel.py#L113-L118)
then defines:

```python
df = df.Define("isLoose", "LeptonMaskHyg_Mu || LeptonMaskHyg_Ele")
```

That definition precedes the six-core-array filter quoted above. `isLoose`
is not masked there, and its name does not match the later `Lepton_*` reorder
loop. The positional invariant would require it to follow both operations if
it is to describe retained/reordered leptons. In this exact `Loose` route,
the opposite-flavor `propagateMask` call uses a `true` default for each
electron or muon, so the OR is already true for each original lepton. That
limits what a stale position can change here; do not infer a measured false
decision from the code alone. A source search finds **no direct `isLoose`
consumer in this RunStability leaf**. Its presence or effect in a particular
retained file, or another Latino analysis, needs its own audit.

The repaired producer includes `isLoose` in both the immutable retention
mapping and the once-only correction permutation. Fresh snapshot checks
confirm its retained length and association; this does not establish that
`isLoose` caused a historical RunStability yield change.

## 2. Consequences in this RunStability analysis

The leaf's [`aliases.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/PlotsConfigurationsRun3/ZH_4lMET/RunStability/aliases.py#L94-L155)
indexes the stored tight vectors at the two `ProductionLeptonPt` positions
for `L2TightLeading2`, and passes them to `bestZ0IdxWithID` for the global
closest-Z pair. Its [`category_config.py` preselection](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/PlotsConfigurationsRun3/ZH_4lMET/RunStability/category_config.py#L18-L34)
contains:

```python
PRESELECTION = f"{TRIGGER_OR} && nLepton >= 2 && L2TightLeading2 && nJetInHorn == 0"
```

The pair builder and mass aliases then feed category cuts and the `Z0_mass`
histogram. Thus a wrong retained bit can reject DATA at the leading-two gate
or invalidate/change its Z candidate. Removing only that gate cannot repair
a bit still used by `bestZ0IdxWithID`. Conversely, omitting the historical
gate in the intended Coffea selection is a deliberate policy difference,
not an HWWNano bug.

The [electron counterfactual replay](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-counterfactual-summary.json)
changed the stored named electron tight vector, removed the compiled
leading-two clause, or did both **in memory**, while keeping the retained
HWW input, other cuts and stream weights fixed. Its *disjoint final-category*
outcomes among Coffea-only EGamma C/I events are:

| Category | Tight alignment alone | Gate removal alone | Both required | Neither: historical stream ownership | Coffea-only total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ele30 | 39 | 18 | 1 | 2 | 60 |
| Ele23–Ele12 | 37 | 16 | 1 | 2 | 56 |

The two stream-zero events per category are intentional MuonEG → Muon →
EGamma priority, not misassociated objects. The
[electron report](https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/2024-paired-lowpt-electron-diagnostic-20260929.md)
also records the independent flags, overlapping mechanisms and historical-only
events. Those flags must not be summed as disjoint causes. None of these
prefix counts assigns a full-year correction.

### Completed repair: producer acceptance and selected Z yield differ

With all WP definitions held fixed, including the production OR's permissive
`Electron_testrecipes` (`pT > 10`), the complete-file repair has the following
gate results. Passing that OR does not establish passing this leaf's specific
tight WP or its Z selection.

| Complete MC file | Rescued gate events | Removed false acceptances | Historical part0 → repaired snapshot |
| --- | ---: | ---: | ---: |
| DY→ee | 606 | 25,689 | 68,421 → 43,338 |
| DY→μμ | 5,914 | 5,324 | 88,692 → 89,282 |

Repaired accepted keys equal the independent aligned-gate reference exactly;
reopened snapshots have no n<2 MC survivors and pass the recorded object
audits. Removed ee events comprise 25,638 singletons and 51 n≥2 events;
removed μμ events comprise 5,269 singletons and 55 n≥2 events. Legitimate
singleton rejections remain rejected. **None of the removed gate events
contributed to the historical four Z categories**, as established by the
selected-event ledgers. Thus removing many wrongly retained ee entries can
coexist with more selected Z events. DATA singletons are legitimate producer
outputs under its loose chain, which does not apply the MC tight skim.

The [bounded replay tables and assessment](diagnostics/hww_object_associations/REPAIR_REPORT.md#bounded-runstability-replay-descriptive-downstream-result)
retain the historical leading-two analysis gate, global Z choice, stream
priorities, weights and full-source normalization receipts. They do not
substitute Coffea's selection or normalize by the partial input-file sum.
Selected MC counts increase by about 1.5% for electrons and 7.6–7.7% for
muons; signed yields at 1 fb⁻¹ increase by about 1.8% and 8.7%. The four
fixed DATA prefixes show electron increases of 2.0–3.6% and muon increases
of 14.5–15.0%.

Those final changes are **descriptive**, while the pre-smearing gate result
is a controlled causal measurement. Changed acceptance shifts sequential
MC smearing and trigger-period random draws; correctly attached arrays and
the unavailable historical producer/payload can also change common-gate
events. For example, +2,484 IsoMu24 selections consist of 1,694 rescued-class
events plus a net +790 within the pass-both class; the latter is not attributed
entirely to RNG. The final baseline is actual historical part0, not a newly
run original final-kinematic snapshot.

The measured association effects are substantial in these paired inputs;
their flavor-dependent pattern supports a producer contribution to the
earlier published comparison. Two MC files and four
DATA prefixes do **not** measure their exact contribution to the published
full-year 12.4% muon DATA, 2.8% electron DATA or 6.66% muon MC differences.

## 3. Investigated concerns outside the established historical errors

### Nominal jet cleaning: masked indices address the active prefix

Current [`JetSelMask.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/JetSelMask.py#L110-L122)
does use a masked count for combinations and unmasked eta/phi for their
indices:

```python
df = df.Define("LeptonMask_JC", "(Lepton_pt >= 10)")
df = df.Define("Jet_Lepton_comb", "ROOT::VecOps::Combinations(CorrectedJet_pt.size(), Lepton_pt[LeptonMask_JC].size())")
```

The following `dR2` expression uses the combination's lepton slot on the
unmasked coordinates:

```cpp
Take(Lepton_eta, Jet_Lepton_comb[1]),
Take(Lepton_phi, Jet_Lepton_comb[1])
```

That pattern would be wrong for an arbitrarily ordered input such as
`[8,20]` GeV. It does **not** establish wrong nominal jet cleaning in the
active 2024 chain. [`LeptonMaker.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/LeptonMaker.py#L13-L48)
sorts descending pT; `LeptonSel.py` filters core arrays without changing
their relative order; `JetSelMask` runs **before** `LeptonScaleSmearing`, as
the production map shows. For `[20,8]` GeV, the `>=10` mask is
`[true,false]`: masked slot 0 and unmasked eta/phi slot 0 are the same lepton.
The surviving mask is a prefix for this sequence. The expression is fragile
if reused with an unsorted collection, but it is **not evidence of a nominal
2024 jet-cleaning defect or a cause of the published RunStability difference**.
The earlier version of this page incorrectly called it an active-chain bug.

### JES variation jet-index composition: requires an ordering audit

In [`JMECalculator.py`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/JMECalculator.py#L165-L171),
`CorrectedJet_jetIdx` initially stores the permutation that sorts input
`Jet_pt`:

```python
df = df.Define("CorrectedJet_jetIdx", "CorrectedJet_sorting")
```

After nominal correction, [lines 230–241](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/JMECalculator.py#L230-L241)
save that old index vector as `tmp_CorrectedJet_jetIdx` while setting the
nominal index to the corrected-pT sort. JES variation code separately sorts
variation pT and then uses
[`Take(tmp_CorrectedJet_jetIdx, variation_sorting)`](https://github.com/TheQuantiser/mkShapesRDF/blob/4e6793fd315807b7db7823d2612dc1ad705f55bd/mkShapesRDF/processor/modules/JMECalculator.py#L264-L299)
for the varied index:

```python
variations_jetIdx.append(
    f"Take(tmp_{JetColl}_jetIdx, tmp_{JetColl}_pt__JES_{source}_{tag}_sorting)",
)
```

Varied eta/phi use the variation sort directly
on `Jet_eta`/`Jet_phi`. If the original `Jet_pt` order is not descending,
the old permutation need not be identity, and that composition may attach a
varied jet index to different coordinates. For example, with initial sort
`p=[1,0]` and variation sort `r=[0,1]`, varied coordinates follow `r`, while
the saved-index expression yields `Take(p,r)=[1,0]`; each varied index would
name the other raw jet. The index should name the same raw jet as its varied
coordinates. This is a **conditional variation
index risk**, not a demonstrated affected 2024 file or nominal RunStability
effect. Audit the actual input ordering and varied branch associations before
using it for a claim; do not fold it into the historical DATA/MC discrepancy.

## Practical impact and required evidence

| Population or product | Established or conditional impact | What is needed |
| --- | --- | --- |
| Historical DATA HWWNano | Wrong tight-bit and period-I coordinate associations are demonstrated in audited entries. No MC `l2tight` production skim applies to this DATA chain. | Retained raw HWW branches can diagnose, and sometimes recompute, decisions for events present. A complete corrected result needs a coverage audit and fresh downstream outputs; rebuilding corrected HWW from original NanoAOD is the producer-level remedy. |
| Historical MC HWWNano | The two-file historical join and controlled current-source gate comparison establish corresponding erroneous losses/acceptances. Exact historical failing lines and full-year prevalence remain unproven. | HWW-only edits, replotting or renormalizing a skim cannot restore absent events. Regenerate affected inputs from parent NanoAOD, then dependent outputs. |
| Newly produced files from unrepaired `ZH_devel` | Tight-vector filtering and corrected-pT permutation paths remain susceptible under their stated conditions; historical eta-only behavior is unproven for them. | Pin producer revision and audit raw-index/coordinate/bit alignment on the actual campaign before use; documentation alone does not repair it. |
| Fresh snapshots on the separate repair branch | All recorded nominal association checks pass in two complete MC files and four DATA prefixes, including rescued events and nonidentity permutations. | Bounded evidence only; not a full systematic, auxiliary ROOT metadata or remote stage-out qualification. |
| Nominal versus systematic jet branches | The active nominal 2024 jet-cleaning prefix has no shown mask-index defect. JES variation index composition has a conditional input-order risk only. | Audit variation ordering and association before interpreting JES branches; no nominal yield correction follows from this note. |
| Native unsigned event-ID serialization | The ≥2⁶³ Snapshot/list conversion limitation remains unresolved; no such event occurred in these six executed ranges. | Audit the identity boundary for any campaign that reaches it; the signed-bridge check does not fix native production serialization. |
| Original central NanoAOD | These HWW producer observations do not establish a defect in the original input. | Preserve it as the source for any required regeneration. |
| This RunStability output | It consumes retained tight bits and coordinates; affected entries can change selection and mass. | Reprocess from trustworthy HWW after campaign-specific producer/coverage audit for corrected yields. Do not replot old histograms as a fix. |

Affected records or derived results can be unreliable without making **all**
HWWNano files or observables invalid. The paired prefixes do not establish
how much of the published full-year **12.4% muon DATA** or **2.8% electron
DATA** difference is due to each mechanism. Historical MuonEG stream priority,
Coffea's deliberate leading-two policy, selected-pair TrigObj matching, MC
35 GeV threshold migrations, and the separate DATA JEC `Regrouped_*`
production failure are distinct from the association findings above.
