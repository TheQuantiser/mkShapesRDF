# HWWNano lepton-association defects: evidence, consequences and repair

## Conclusions and production status

**The affected historical HWWNano ntuples are invalid inputs for analyses
that depend on their retained lepton IDs and object associations.** Direct
reads show offline tight decisions attached to the wrong retained leptons,
and a separate electron coordinate/index inconsistency. A controlled
producer comparison also demonstrates erroneous MC losses and acceptances
before the ntuple is written. These failures change the objects selected
and the events available to an analysis.

This is a **shared mkShapesRDF producer problem**. RunStability exposed it,
but any HWW analysis consuming the affected products and relying on these
lepton decisions or associations inherits the problem. The demonstrated
historical scope is the audited **2024 Full2024v15 inputs**; the extent in
other files, campaigns and years still requires a production audit. Product
invalidity for these analyses does not require every event or every branch
to be wrong. The parent central NanoAOD records remain the regeneration
inputs.

**A repair has been demonstrated on a separate branch, but it has not been
integrated into `ZH_devel`.** Six fresh nominal Events snapshots were written
on LPC on 2026-09-30 and independently reopened. The checked associations
passed, including real changes in lepton pT ordering. In the two complete DY
files, repaired final event keys equal the independent aligned-gate
reference exactly. This establishes the repair for those nominal outputs;
production adoption and campaign-wide regeneration remain to be done.

| Question | Conclusion | Decisive evidence |
| --- | --- | --- |
| Are the old inputs trustworthy for lepton-ID-dependent analyses? | **No, for the affected products.** Stored decisions can describe another object; coordinate and index fields can disagree. | [Within-record historical checks](#direct-evidence-in-historical-ntuples), including raw-WP reconstruction inside the same HWW events. |
| Can an analysis-only edit restore the correct MC sample? | **No.** Correcting retained branches cannot recover events already rejected by the producer. Regeneration must start from parent NanoAOD. | [Complete-file gate comparison](#complete-file-mc-acceptance-causal-gate-result): 606 ee and 5,914 μμ events satisfy the aligned gate but are absent from the paired historical outputs. |
| Does the proposed producer repair work? | **Yes for the six executed nominal snapshots and the checked invariants.** | [Independent reopening](#fresh-snapshots-and-repair-validation): exact accepted-key closure and zero checked association anomalies. |
| How much did this change the RunStability result? | The fixed-policy local Z replay gains about 2.0–3.6% electron DATA and 14.5–15.0% muon DATA; MC signed weighted contributions gain about 1.8% and 8.7%. | [Downstream replay](#bounded-runstability-replay-descriptive-downstream-result). These are measured local changes, not campaign correction factors. |
| Does that explain the entire published Coffea discrepancy? | The defects are a substantial demonstrated contributor in the paired inputs. Their exact full-year contribution has not been measured. | Historical association failures, causal gate losses and the flavor-dependent local replay, with [remaining attribution limits](#what-remains-unresolved). |

### Which source contains the repair?

| Revision / branch | What it establishes |
| --- | --- |
| [`69ff2dad`][original-revision] on `demo/2024-hwwnano-object-associations` | Clean original producer and complete-file diagnostic reference. |
| [`9a0e9be`][repaired-revision] on `fix-demo/2024-hwwnano-object-associations` | Producer actually used to write the repaired snapshots. |
| [`8d940ab`][evidence-revision] on the repair branch | Reviewed report, scripts and committed numerical evidence for the completed demonstration. |
| [`a3b160a`][inspected-zh-revision] on `ZH_devel`, inspected for this revision | `LeptonSel.py`, `L2TightSelection.py`, `LeptonScaleSmearing.py` and `Steps_cfg.py` all have the same Git blobs as the original reference. **The producer remains unrepaired here.** |

This `ZH_devel` update changes this report only. The implementation, tests,
scripts and JSON evidence remain on the repair branch. Reproduction commands
are in its [README][repair-readme]; the scripts do not exist in this
`ZH_devel` diagnostic directory. Existing historical ROOT files, scientific
selections and Coffea code were not changed by this documentation revision.

## Evidence scope

A framework yield disagreement motivated the investigation. The historical
object-invariant checks and controlled gate comparison establish the
defects; fresh serialized outputs establish the repair. The downstream
replay then measures the local analysis impact.

The four repaired DATA runs each cover source entries `0:50000` of one
EGamma or Muon file in periods C or I. The two MC runs cover **all 158,487
DY→ee and 222,331 DY→μμ entries** of the pinned individual files. These are
six fixed inputs, not six complete datasets. Earlier historical DATA audits
used longer prefixes; their counts must not be combined with the repair-run
counts. [Environment and input identities][environment] record the exact
PFNs, UUIDs, payloads and hashes; each run's executed interval is retained
in [the results][results].

## Direct evidence in historical ntuples

### Tight decisions are attached to the wrong retained objects

At retained position `i`, `Lepton_isTightMuon_*[i]` must describe the raw
muon named by `Lepton_muonIdx[i]`; the corresponding electron decision must
describe `Lepton_electronIdx[i]`. Every object-indexed vector must follow
the same retention mapping and later permutations. Equal vector lengths
alone do not establish this correspondence. These are **offline working-point
bits**, not HLT decisions.

The following records were read from the actual historical paired `part0`
files. The named WPs were recomputed from raw inputs **within those same HWW
events**:

| Historical witness | Retained raw objects | Correct named tight bits | Stored named tight bits |
| --- | --- | --- | --- |
| Muon C source entry 234; key `(379416,147,131724611)`; HWW entry 65 | Muons `[1,2]` | `[true,true]` | **`[false,true]`** |
| EGamma C source entry 20774; key `(379729,907,1396820419)`; HWW entry 991 | Electrons `[0,1]` | `[true,true]` | **`[false,true]`** |

The muon WP is
`Lepton_isTightMuon_cut_TightID_pfIsoTight_HWW_tthmva_67`; the electron WP is
`Lepton_isTightElectron_mvaWinter22V2Iso_WP90_tthMVA_Run3`. In the muon
record, prefilter raw indices `[0,1,2]` have decisions
`[false,true,true]`. Retention removes muon 0, but the stored first bit still
describes it. The [historical muon audit][muon-audit],
[electron audit][electron-audit] and [observed witnesses][observations]
record the raw inputs and arrays.

The historical muon audit extends beyond one example. Among the **508
Coffea-only IsoMu24 events with the historical leading-two decision false**
in the paired C/I prefixes, both selected raw HWW muons pass the named WP.
**503** have a wrong stored decision for the retained pair; **502** of those
also have the prefilter decision prefix stored at retained positions. The
audit is conditioned on this discrepancy class, so these counts establish
repeated historical failures rather than a file-wide defect fraction.

The clean [original `LeptonSel`][original-selection] defines tight vectors
before filtering. Later it filters only the six core arrays, leaving the
decisions in prefilter positions. This is a consistent live mechanism for
the retained failures. The unavailable dirty historical source is needed to
identify the exact old operation, including how its stored tight vectors
acquired retained length while keeping the wrong prefix.

**Analysis consequence:** a selection can reject two genuinely tight
retained leptons or accept a decision belonging to a removed object.
Changing a downstream Z builder or fitting a normalization factor does not
restore the ID-to-object contract.

### Electron coordinates can disagree with their raw indices

For EGamma I source entry 27025, key `(386509,159,333332716)`, historical
HWW entry 1936 contains:

| Field | Correct values for retained `electronIdx=[0,1]` | Historical values |
| --- | --- | --- |
| `Lepton_eta` | `[-0.9336,-2.0571]` | **`[-2.0571,-0.9336]`** |
| `Lepton_phi` | `[-1.2280,1.9678]` | `[-1.2280,1.9678]` |
| Named electron tight bits | `[true,true]` | `[true,true]` |

The eta swap is therefore a separate association failure even when both
tight bits are correct. The historical RunStability coordinate matcher
cannot connect either retained electron to its prefilter `VetoLepton`
identity; both production-gate indices become `-1` and the leading-two gate
rejects the event. Coordinate errors can also affect reconstructed
kinematics. EGamma I entry 46209, key `(386509,735,1539152813)`, contains
both a tight-bit failure and an eta/index failure. Their event counts cannot
be added as independent losses. The [electron audit][electron-audit] and
[historical replay note][historical-replay-note] retain these checks.

The current [scale/smearing module][original-scale] has a reproduced
ordering hazard: its generic permutation loop can reorder the permutation
itself and an already ordered correction ratio. An isolated live run of
entry 27025 produced a real swap and a **phi/index mismatch**, with the
actual loop order recorded in [the witness artifact][observations]. That
establishes the present source defect. The exact operation responsible for
the historical **eta-only** mismatch remains unresolved. Fresh repaired
snapshots verify the coordinate/index invariant directly.

## Complete-file MC acceptance: causal gate result

### The failure happens before the analysis can see the event

The configured 2024 MC path is
`MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight`. Its decisive
[production order][original-steps] is:

```python
"formulasMC",
"l2tight",
"leptonScale_mc",
"l2Kin",
```

`l2tight` runs before lepton scale/smearing and the HWW snapshot. It reads
positions 0 and 1 of the WP vectors, OR-ing **every configured electron and
muon tight WP for each position**, then AND-ing the two positions. The
original module has no guard on the retained collection's size. Thus a
removed object's stale bit can affect acceptance, including when only one
lepton remains.

The all-WP OR includes `Electron_testrecipes`, whose original recipe is
strict raw `pT > 10`. It was preserved in the reference and repair. Passing
this producer gate is consequently a different requirement from passing
RunStability's specific named tight WPs. The corresponding DATA chain,
`DATAl2loose2024v15__l2loose`, has **no production `l2tight` skim**; retained
DATA bits still affect subsequent analysis cuts. Single retained leptons
are legitimate in that loose DATA output.

### Controlled comparison on the two complete parent files

The original diagnostic runs the configured modules through `l2tight`,
stopping before smearing. Its independent reference remaps all **seven
electron and six muon WP vectors** to retained raw identities and rejects
collections with fewer than two retained leptons, then evaluates the
unchanged all-WP predicate. It uses raw indices and flavor, rather than
coordinate or pT matching. Both branches consume the same pre-gate events
and raw decisions. [Complete-file results][complete-results] document the
reference; [repair results][results] record its exact key comparison to the
repaired producer.

| Gate accounting | DY→ee | DY→μμ |
| --- | ---: | ---: |
| Pre-gate events | 74,938 | 116,303 |
| Pass both | 42,732 | 83,368 |
| Original rejects; aligned passes (**rescued**) | **606** | **5,914** |
| Original passes; aligned rejects (**removed**) | **25,689** | **5,324** |
| Reject both | 5,911 | 21,697 |
| Original accepted / historical paired total | **68,421** | **88,692** |
| Aligned accepted / repaired final total | **43,338** | **89,282** |

The four outcome classes partition every pre-gate event. Their differences
are **causal association/slot-handling effects** in this controlled graph:
the WP definitions, gate policy and input events are unchanged.

The complete central-to-historical join checks full `(run,lumi,event)`
keys, UUIDs, parent pairing and uniqueness. The original accepted-key set
equals historical paired `part0` membership exactly in both files; there
are no HWW-only or ambiguous keys. Every rescued key is absent from that
paired `part0`, and every removed key is present. This corroborates the
retention mechanism in the actual files; exact historical source-line
attribution remains limited by the unavailable producer worktree. Absence
has been proved for these verified paired files, not every HWW part.

Independent repaired-output checks establish that:

- The pre-gate source-entry/key sets, original/aligned gate outcomes and
  `genWeight` values match the saved original reference.
- Final repaired source-entry/key sets equal the aligned accepted sets
  **exactly**, with zero event losses between the gate and final snapshot.
- Final repaired output has **zero events with fewer than two leptons**.

The reference does not retain all pre-gate collection arrays; the result
explicitly records `pregate_collection_comparison="not assessed"`. Exact
key and gate closure must not be restated as a complete original-versus-
repaired pre-gate array comparison. Repaired serialized array associations
are checked separately in the next section.

### Losses and false acceptances must both be counted

Of the removed events, **25,638 ee and 5,269 μμ** are historical
one-lepton survivors. The remaining **51 ee and 55 μμ** have at least two
retained leptons, so false acceptance is not confined to singletons. The
full multiplicity cross-tab is in [the accounting appendix](#mc-accounting-details).

The net producer output changes are **−25,083 ee** and **+590 μμ**. Those
net values hide substantial opposing movements and are not changes to a
selected Z yield. A single-retained-lepton rejection is expected: DY→μμ
source entry 127, key `(1,260002,1443526502)`, is rejected by both gates and
absent from both outputs. It is a control, not evidence of an erroneous loss.

**Required recovery:** for a complete corrected MC selection, regenerate
affected HWWNano from its parent NanoAOD. An HWW-only alias can operate on
retained events; it cannot recreate the missing accepted keys.

## Fresh snapshots and repair validation

### Executed chains and stage counts

The repaired producer at [`9a0e9be`][repaired-revision] ran all configured
event-producing DATA or MC modules and the actual Snapshot callback. The
callback uses its configured wildcard nominal columns, subject to the
unchanged serialization exclusions (`BeamSpot_type`,
`Electron_seediEtaOriX`, `Photon_seediEtaOriX` in these inputs). An immutable
native ROOT checkpoint computes the columns once before the callback reads
10,000-event chunks. No producer physics module, nominal JEC or event
cleaning was bypassed. Auxiliary ROOT-key copying and EOS publication are
outside this local **Events-output** demonstration.

| Stage | EGamma C | EGamma I | Muon C | Muon I | DY→ee | DY→μμ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Input Events | 50,000 | 50,000 | 50,000 | 50,000 | 158,487 | 222,331 |
| Chain raw multiplicity | 15,896 | 16,431 | 30,305 | 30,580 | 94,106 | 129,548 |
| Golden mask | 13,341 | 16,431 | 30,305 | 30,580 | — | — |
| LeptonMaker | 12,493 | 14,814 | 25,497 | 26,220 | 93,059 | 127,633 |
| LeptonSel | 3,353 | 3,782 | 12,619 | 12,176 | 78,696 | 121,809 |
| JetSelMask / MC pre-gate | 3,189 | 3,590 | 11,927 | 11,447 | 74,938 | 116,303 |
| Repaired l2tight | — | — | — | — | 43,338 | 89,282 |
| Independently reopened final Events | **3,189** | **3,590** | **11,927** | **11,447** | **43,338** | **89,282** |
| Actual correction reorderings | 8 | 15 | 2 | 7 | **1,419** | **978** |
| Successful producer seconds | 114.95 | 118.46 | 178.12 | 181.30 | 748.66 | 1,322.71 |

The six successful producer runs sum to **44.40 minutes** of processing,
excluding failed attempts and subsequent audits/replays. The original gate
reference runs took 83.59 s and 110.03 s. These are run timings rather than
campaign wall time. Input ledgers cover every assigned source entry before
cuts, with unique identities throughout the six ranges.

### What independent reopening checked

The [audit implementation][repair-audit] reopened the actual written ROOT
files and compared retained objects with raw indices, prefilter decisions
and frozen pre-correction vectors. It checked **21 flat per-lepton arrays
per DATA output and 186 per MC output**, including **159 SF arrays** in MC.
All six outputs had **zero checked anomalous events** for:

- Full event identity and unique source-entry correspondence.
- Lepton raw identity/flavor, eta/phi mapping, vector lengths and descending
  corrected-pT order.
- All 13 tight-WP vectors and `isLoose` following retained object identity.
- Correction-ratio association and each frozen MC SF array following the
  same nominal permutation.

The largest MC correction-ratio residual was below `5.961e-8`. The real
reorderings in the table exercise nonidentity permutations. The audit
therefore verifies serialization and changing order, as well as cases where
order remains unchanged. These checks establish association correctness;
they do not independently validate the physics definitions of every WP,
correction or systematic formula.

### Reopened witnesses

The [repair witness artifact][repair-witnesses] retains raw, maker,
filtered, pre-scale and serialized fields, checked by full event key:

| Role / source entry | Key `(run,lumi,event)` | Repaired snapshot observation |
| --- | --- | --- |
| Muon C / 234 | `(379416,147,131724611)` | Two retained muons; tight bits and coordinates follow their raw indices. |
| EGamma C / 20774 | `(379729,907,1396820419)` | Two retained electrons with the corrected tight association. |
| EGamma I / 27025 | `(386509,159,333332716)` | Both eta and phi follow `electronIdx`. |
| EGamma I / 46209 | `(386509,735,1539152813)` | Both decision and coordinate invariants pass. |
| DY→ee / 174 | `(1,384532,2060318616)` | Rescued event written with two retained leptons; absent from historical paired `part0`. |
| DY→μμ / 5 | `(1,260002,1443525631)` | Rescued event written with two retained leptons; absent from historical paired `part0`. |
| DY→ee / 8 | `(1,384532,2060317109)` | Old one-lepton acceptance removed; absent from repaired output. |
| DY→μμ / 102 | `(1,260002,1443526295)` | Old one-lepton acceptance removed; absent from repaired output. |

Correct newly written electron eta establishes the repaired output invariant.
Identifying the historical eta-only failing operation remains a separate
provenance question.

## Bounded RunStability replay: descriptive downstream result

### Fixed analysis policy and normalization

The replay uses the retained compiled pickle SHA-256
`6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef`
and the [commit-pinned historical runner][historical-runner]. It preserves
the global Z builder, historical leading-two analysis gate, 35/35 GeV and
60–120 GeV cuts, DATA stream priorities and component weights. The repaired
view replaces only the HWW input URI. The selection remains the historical
RunStability policy throughout this comparison.

MC uses `XSWeight × METFilter_Common × puWeight × SelectedLeptonSF_Z ×
TriggerSF_Z`, with `XSWeight=baseW×genWeight`. Existing **full-source**
`baseW` receipts are reused. No new Runs scan or partial-file normalization
is introduced. The runner's compiled source luminosity is **109.08 fb⁻¹**;
reported MC sums divide by that same reference to express **one file's
contribution at 1 fb⁻¹**. They are not complete-source predictions or
absolute DATA/MC calibrations.

### Measured local changes

| DATA prefix / category | Historical selected | Repaired selected | ΔN | ΔN / historical |
| --- | ---: | ---: | ---: | ---: |
| EGamma C / Ele30 | 204 | 208 | +4 | +1.96% |
| EGamma C / Ele23–Ele12 | 191 | 195 | +4 | +2.09% |
| EGamma I / Ele30 | 208 | 215 | +7 | +3.37% |
| EGamma I / Ele23–Ele12 | 196 | 203 | +7 | +3.57% |
| Muon C / IsoMu24 | 525 | 604 | +79 | +15.05% |
| Muon C / Mu17–Mu8 | 480 | 552 | +72 | +15.00% |
| Muon I / IsoMu24 | 434 | 497 | +63 | +14.52% |
| Muon I / Mu17–Mu8 | 399 | 458 | +59 | +14.79% |

DATA `sumw` and `sumw²` equal these counts. These are the repair runs'
fixed 50,000-entry prefixes, not the longer historical diagnostic ranges.

| MC / category | Historical N | Repaired N | ΔN / historical | Historical Σw at 1 fb⁻¹ | Repaired Σw at 1 fb⁻¹ | ΔΣw / historical |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ee / Ele30 | 15,033 | 15,261 | +1.52% | 59.565510 | 60.618720 | +1.77% |
| ee / Ele23–Ele12 | 13,774 | 13,982 | +1.51% | 54.403805 | 55.396279 | +1.82% |
| μμ / IsoMu24 | 32,559 | 35,043 | +7.63% | 137.409340 | 149.380820 | +8.71% |
| μμ / Mu17–Mu8 | 31,373 | 33,782 | +7.68% | 132.131206 | 143.675053 | +8.74% |

Exact signed sums, variances and outcome contributions are in
[repair-results.json][results]. Repaired MC `Σw²` at the same 1 fb⁻¹
projection are `0.618482`, `0.562286`, `1.674378` and `1.613938` in table
order. The trigger categories overlap and must not be summed as unique
events.

### Why fewer producer entries can give more selected Z events

**None of the removed gate events enters any of these historical Z
categories**, as verified by the outcome-tagged selected ledgers. This
statement includes the removed events with at least two retained leptons;
it is established by the replay rather than inferred from singleton counts.
Only 158/139 of the 606 rescued ee events and 1,694/1,640 of the 5,914
rescued μμ events enter the respective single/double-lepton-trigger
categories. Passing the producer gate is necessary but insufficient for
the Z selection.

| Repaired MC category | Selected from pass-both class | Selected from rescued class | Net Δ selected within pass-both | Total Δ selected |
| --- | ---: | ---: | ---: | ---: |
| ee / Ele30 | 15,103 | 158 | +70 | **+228** |
| ee / Ele23–Ele12 | 13,843 | 139 | +69 | **+208** |
| μμ / IsoMu24 | 33,349 | 1,694 | +790 | **+2,484** |
| μμ / Mu17–Mu8 | 32,142 | 1,640 | +769 | **+2,409** |

The ee producer loses a net 25,083 entries while these selected Z counts
rise by 228/208: it removes false production acceptances that never entered
the historical Z categories and recovers relevant events. Gross ntuple
entry counts are not selected-sample yields or purity measures.

For IsoMu24, the exact count accounting is
**+2,484 = 1,694 rescued-class events + 790 net additional pass-both
events**. The weighted increase is **11.971479**, comprising **8.557196
from rescued events** and a **3.414284 net increase in the pass-both
class**; components are calculated from unrounded JSON values and rounded
independently for display. The 790 is a net class-count change,
not a claim of 790 one-way individual recoveries. Events accepted by both
producer gates can still change their selected pair, correctly attached WP
outcome, kinematics or weights.

### What these yield changes establish

The larger muon changes reproduce the **qualitative flavor pattern** of the
earlier Coffea comparison. Together with the directly observed historical
failures and controlled producer losses, this makes association defects a
substantial explanation in the paired inputs and a demonstrated contributor
to that discrepancy. The local percentages are insufficient to assign an
exact share of a full-year difference or to supply a universal correction.

Final MC yield comparisons also contain stochastic and historical-provenance
effects. Electron smearing uses a sequential static TRandom3; muon smearing
and unseeded TrigMaker use shared gRandom. Changing the surviving events
shifts subsequent draws, including trigger-period and weight assignments.
Common-event draws were **not held equal**. Corrected associations,
historical producer differences and shifted draws can all contribute to
the pass-both changes; their causal shares have not been partitioned.

Consequently, the **pre-smearing gate comparison** measures the causal
association/slot effect. The **historical-versus-repaired final replay**
measures descriptive downstream changes. The original reference stops at
the gate; its baseline final output is the actual historical `part0`.
DATA scale corrections are deterministic, but exact historical source and
payload-byte equality remain unavailable for the DATA comparison too.
Different source coverage, intentional stream/gate/pair policies, trigger
association and normalization choices remain separate parts of the broader
framework comparison.

Each replay books one RDF graph. Independent histogram reopening verifies
contents and variances, including flows, against the selected ledgers, with
109.08 and 109.08² restored for MC. Selected keys match source entries,
with no within-category duplicates or missing gate labels. These checks
validate the reported replay accounting.

## Shared producer changes

The repair changes **how existing per-object values follow their objects**.
It preserves WP expressions, isolation/MVA choices, thresholds, the all-WP
gate policy and nominal correction formulas. The following source excerpts
are selected operations; intervening setup is described or linked.

### One retained-object mapping for every stage-created decision

The [original selection module][original-selection] defines the electron
and muon tight vectors in their respective WP loops:

```python
df = df.Define("Lepton_isTightElectron_"+ids, "propagateMask(Lepton_electronIdx, comb, false)")
df = df.Define("Lepton_isTightMuon_"+ids, "propagateMask(Lepton_muonIdx, comb, false)")
```

Its later filtering loop includes only core fields:

```python
branches = ["pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx"]
for prop in branches:
    df = df.Redefine(
        f"Lepton_{prop}",
        f"Lepton_{prop}[LeptonMaskHyg_Ele && LeptonMaskHyg_Mu]",
    )
```

The [repaired selection][repaired-selection] binds one immutable mapping
before any core redefinition:

```python
df = df.Define(
    "LeptonSel_keepIdx",
    "ROOT::VecOps::Nonzero(LeptonMaskHyg_Ele && LeptonMaskHyg_Mu)",
)
```

It builds `lepton_columns` from the six core fields, `isLoose`, and every
configured electron and muon tight-WP column, then applies the same mapping:

```python
for column in lepton_columns:
    df = df.Redefine(
        column,
        f"ROOT::VecOps::Take({column}, LeptonSel_keepIdx)",
    )
```

Binding the indices once avoids reevaluating a mask against already shortened
collections. Raw Electron/Muon and prefilter VetoLepton collections are
preserved. The muon example `[false,true,true]` at raw indices `[0,1,2]`
becomes `[true,true]` when retained indices are `[1,2]`.

### Guard the two-slot gate

The [repaired `L2TightSelection`][repaired-gate] starts with:

```python
def runModule(self, df, values):

    # Reject short retained collections before evaluating either tight slot.
    df = df.Filter("Lepton_pt.size() >= 2")

    first = True
```

The original begins with `first = True` without that filter. Both modules
construct the same per-slot OR over all configured WPs, including
`Electron_testrecipes`, and retain the same final predicate:

```python
l2tight_selection = f"({lepton1_selection}) && ({lepton2_selection})"

df = df.Filter(f"{l2tight_selection}")
```

The retention repair fixes whose bit is read; the guard fixes the existence
of the two retained slots. Neither changes the intended WP policy.

### Apply the correction permutation once and keep it immutable

The [original scale module][original-scale] contains:

```python
df = df.Define("Lepton_sorting",     "sortedIndices(Lepton_newPt)")
df = df.Define("Lepton_rochesterSF", "Take(Lepton_newPt/Lepton_pt, Lepton_sorting)")
df = df.Redefine("Lepton_pt",        "Take(Lepton_newPt, Lepton_sorting)")
for branch in df.GetColumnNames():
    if branch.startswith("Lepton_") and branch!="Lepton_pt":
        df = df.Redefine(branch, f"Take({branch}, Lepton_sorting)")
```

For `p=[1,0]`, `Take(p,p)` is `[0,1]`. Once the loop processes
`Lepton_sorting` itself, later fields may receive a different permutation.
`Lepton_rochesterSF` is already ordered at definition and may be ordered
twice. The [recorded isolated witness][observations] demonstrates the
resulting phi/index mismatch under an actual swap.

The [repaired module][repaired-scale] captures genuine flat per-lepton
arrays **before** defining the permutation. It includes `isLoose` and
excludes correction temporaries, generated variation columns, nonflat
fields, `Lepton_pt`, the permutation and the already ordered ratio:

```python
varied_columns = set(df.GetVariedColumns(df.GetColumnNames()))
excluded_columns = set(self.columnsToDrop) | varied_columns | {
    "Lepton_pt",
    "Lepton_sorting",
    "Lepton_rochesterSF",
}
```

After constructing the filtered `lepton_columns` list, it defines the
permutation, ratio and ordered pT as above. The existing pT variations and
captured nominal arrays then follow that unchanged permutation once:

```python
for branch in df.GetVariedColumns(["Lepton_pt"]):
    df = df.Define(
        branch, f"Take({branch}, Lepton_sorting)", excludeVariations=["*"]
    )
for branch in lepton_columns:
    df = df.Redefine(branch, f"Take({branch}, Lepton_sorting)")
```

mRDF propagates registered SF variations through nominal redefinition. Real
snapshots here persist nominal fields; synthetic ROOT checks separately
exercise variation associations and MET propagation. Full systematic
production remains outside the executed validation.

`isLoose` also follows both retention and ordering in the repair. Its old
length/association handling is a narrower source concern: this RunStability
leaf does not consume it directly, and its exact active Loose recipe limits
what a stale boolean can change. No historical RunStability yield loss is
assigned to `isLoose`.

### Separate DATA JEC configuration correction

The DATA JEC change was separately committed at [`68a082c`][jec-revision].
The pinned DATA payload supplies nominal JEC levels but lacks the requested
`Regrouped_*` uncertainty corrections. Their lookup raised `map::at`
although DATA JES variations were already disabled. The repair changes the
DATA-only `jes_unc` list to `[]` in [Steps_cfg.py][repaired-steps]. It retains
nominal JEC, corrected-jet sorting, veto/cleaning and the settings
`do_JER=False`, `store_nominal=True`, `store_variations=False`, `isMC=False`.
MC source configuration is unchanged. This fixes an execution blocker and
is separate from the lepton-association findings.

## What remains unresolved

| Remaining question | Present evidence boundary |
| --- | --- |
| Which exact old operation made the historical eta-only error and shortened wrong tight vectors? | The historical dirty producer worktree is unavailable. Retained-file defects are directly established; exact historical operation/payload equivalence is unresolved. |
| Which additional productions and analyses are affected? | Demonstrated inputs are the pinned 2024 files. The defective operations are in shared source; campaign/year inventory and consumer audits are still needed. |
| What fraction of each full-year Coffea difference comes from these defects? | Different coverage and policies remain, and MC common-event draws were not fixed. No full-year 12.4%, 2.8% or 6.66% attribution is established. |
| Are all systematic products and ordinary production outputs ready? | Nominal Events outputs and focused synthetic variation checks were exercised. Full systematic production, auxiliary metadata copying and remote publication were not. |
| Is nominal jet cleaning also broken? | The active sorted-prefix invariant holds; its selection was left unchanged. A conditional JES variation index-composition concern requires a separate ordering audit. |
| Does Snapshot handle the full unsigned event-ID range? | The native unsigned ≥2⁶³ conversion remains a known limitation. No high-bit event occurs in these six ranges; the signed two's-complement bridge was checked separately. |

These limits define the reach of the measurements. They do not defer the
analysis-input conclusion for the products with demonstrated wrong IDs or
incomplete acceptance.

## Required follow-up for analysis use

1. **Adopt and review the shared producer repair.** `ZH_devel` currently
   retains the defective source. The demonstrated repair is a concrete
   starting point, with tests and output evidence on its own branch.
2. **Determine the affected production inventory.** Trace actual producer
   revisions/configurations and audit retained object invariants and skim
   behavior for the relevant campaigns, rather than assigning this study's
   percentages to unmeasured files.
3. **Regenerate affected HWWNano from parent NanoAOD and validate the ordinary
   production output.** Include accepted-key/identity checks, serialized
   lepton decisions and coordinates, exercised ordering changes, required
   systematic products and metadata. Missing MC events require the parent
   inputs.
4. **Regenerate dependent histograms and assess analysis results.** Repeat
   RunStability and other consumers on validated inputs with their intended
   selections. The repaired local replay demonstrates material impact; it
   is not a substitute for that production and analysis validation.

## Evidence and reproduction details

### MC accounting details

The following are **raw signed `genWeight` accounting sums**, not normalized
Z yields. They belong to the controlled pre-gate partition above.

| File / outcome | Events | Σ genWeight | Σ genWeight² |
| --- | ---: | ---: | ---: |
| ee pass both | 42,732 | 778,066,460.476563 | 30,646,066,889,812.742 |
| ee rescued | 606 | 10,176,404.453125 | 434,604,430,759.771 |
| ee removed | 25,689 | 449,716,736.792969 | 18,423,355,151,464.934 |
| ee reject both | 5,911 | 101,576,584.449219 | 4,239,186,122,476.905 |
| μμ pass both | 83,368 | 1,525,389,467.500000 | 59,788,947,497,657.695 |
| μμ rescued | 5,914 | 105,245,446.054688 | 4,241,337,629,559.875 |
| μμ removed | 5,324 | 77,715,594.007813 | 3,818,207,903,242.606 |
| μμ reject both | 21,697 | 379,713,786.160156 | 15,560,416,393,060.637 |

Uncut input `(Σw,Σw²)` are ee `(2,825,907,176.597656,
113,661,967,686,177.86)` and μμ `(3,974,341,199.144531,
159,448,907,087,872.25)`. These totals include events leaving before
the pre-gate partition. No normalization denominator was recomputed from
these individual files.

The repaired audit closes the earlier current-versus-historical
multiplicity ambiguity by joining all keys and reopening historical counts:

| File / gate outcome | n=1 | n=2 | n=3 | n=4 | Historical paired part0 |
| --- | ---: | ---: | ---: | ---: | --- |
| ee both | 0 | 42,541 | 185 | 6 | All present, same multiplicity |
| ee rescued | 0 | 601 | 5 | 0 | All absent |
| ee removed | 25,638 | 51 | 0 | 0 | All present, same multiplicity |
| ee neither | 5,850 | 61 | 0 | 0 | All absent |
| μμ both | 0 | 82,987 | 373 | 8 | All present, same multiplicity |
| μμ rescued | 0 | 5,884 | 29 | 1 | All absent |
| μμ removed | 5,269 | 54 | 1 | 0 | All present, same multiplicity |
| μμ neither | 20,839 | 855 | 3 | 0 | All absent |

`n` is retained multiplicity before correction in the repaired gate ledger;
the historical comparison checks the corresponding keys. Final repaired
multiplicities are ee `43,142 / 190 / 6` and μμ `88,871 / 402 / 9` at
n=2/3/4, with zero n<2 survivors.

### Provenance and artifact interpretation

- [repair-environment.json][environment]: source identities, installed
  runtime, fixed inputs, payloads and hashes.
- [repair-results.json][results]: stage counts, gate outcomes, signed sums,
  multiplicity cross-tabs, reopened invariants, replay ledgers and local
  artifact paths/hashes.
- [repair-witnesses.json][repair-witnesses]: retained full-key examples from
  already written repaired outputs.
- [observed-summary.json][observations] and
  [complete-two-file-summary.json][complete-results]: original historical
  and live-source witnesses, and the controlled complete-file reference.
- [repair-branch README][repair-readme]: exact environment, producer, gate
  reference, independent audit and replay commands.

The measured repaired processor tree is
`592fdadf25d978a469546c6d22656b94fd1540d2`; its include tree is
`311e5fd6311c74b58ba233258acb2018aabcdd7d`. Each output directory archives
the executed `repair_demo-used.py`, SHA-256
`b035e8cf2554c0195bbc0391e8b3ced5db50d0525c0dc2c04c9d441c5334a8ba`.
Detailed ROOT/NPZ artifacts remain in the recorded LPC workspace; the
committed JSON links pin the numerical evidence.

**Metadata interpretation:** nested historical replay summaries inherit
`producer_revision=9a0e9be...` from the repaired-run receipt. It describes
the replay context, **not the historical HWW producer identity**. The
historical input URI, parent pairing and compiled pickle identify that
comparison; its dirty producer source remains unavailable. Likewise, the
environment manifest's earlier DATA/MC windows are input-study provenance;
the repair executions use the intervals recorded in the results.

### Execution qualifications and recorded tests

The pinned [repair-branch report][executed-report] retains the failed
attempts and runtime workarounds. Final runs used the complete configured
event-producing chain. ROOT/XRootD teardown could stall after files closed;
the task-local CLI explicitly exits after writing and a basic reopen/count.
**The separate invariant audit establishes output acceptance**, rather than
the CLI exit alone.

Recorded ROOT checks passed: five selection/guard tests and four synthetic
correction/permutation/variation tests. Both repair regression suites fail
on unrepaired modules. The signed serialization bridge passed; native
unsigned high-bit conversion remains an expected failure. Reproduction
commands and test locations are retained in [the executed report][executed-report].

This documentation revision reorganizes and checks the existing source and
artifact evidence. It does not represent a new producer run or a rerun of
these ROOT tests. The [companion issues note](../../KNOWN_HWWNANO_ISSUES.md)
provides the wider source and consumer context.

[original-revision]: https://github.com/TheQuantiser/mkShapesRDF/commit/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0
[repaired-revision]: https://github.com/TheQuantiser/mkShapesRDF/commit/9a0e9be35c27e2907e6201460d0a5de58a091651
[evidence-revision]: https://github.com/TheQuantiser/mkShapesRDF/commit/8d940abcf429f753074121a250db3717434eb2f6
[inspected-zh-revision]: https://github.com/TheQuantiser/mkShapesRDF/commit/a3b160a5952e4198e61060b17be64da5b4c445e3
[jec-revision]: https://github.com/TheQuantiser/mkShapesRDF/commit/68a082c29b08d85978e9af33e9d194610b19f8a6
[repair-readme]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/README.md#repair-demonstration-on-this-branch
[executed-report]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/REPAIR_REPORT.md
[environment]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-environment.json
[results]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-results.json
[repair-witnesses]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-witnesses.json
[observations]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/observed-summary.json
[complete-results]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/complete-two-file-summary.json
[repair-audit]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair_audit.py
[muon-audit]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/hww-tight-mask-audit.json
[electron-audit]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-hww-mask-audit.json
[historical-replay-note]: https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/HISTORICAL_HWW_DIAGNOSTIC.md
[historical-runner]: https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/historical_hww_diagnostic.py
[original-selection]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/LeptonSel.py
[repaired-selection]: https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/modules/LeptonSel.py
[repaired-gate]: https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/modules/L2TightSelection.py
[original-scale]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/LeptonScaleSmearing.py
[repaired-scale]: https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/modules/LeptonScaleSmearing.py
[original-steps]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/framework/Steps_cfg.py
[repaired-steps]: https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/framework/Steps_cfg.py
