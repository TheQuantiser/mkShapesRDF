# Bounded HWWNano producer repair demonstration

## Scope fixed before implementation

Base: `demo/2024-hwwnano-object-associations` at
`69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0`. Work is isolated on
`fix-demo/2024-hwwnano-object-associations`; historical files and the other
branches are preserved.

| Finding | Evidence | Authorized repair and held-fixed contract |
| --- | --- | --- |
| Tight vectors retain prefilter positions | Historical witnesses and complete two-file gate audit; current `LeptonSel` filters core arrays alone | Apply one stable retained-object mapping to all stage-created per-lepton decisions, preserving every WP expression |
| `l2tight` reads two stale positions | Actual versus aligned gates differ in both complete DY files | Guard retained multiplicity, preserve the OR over all configured WPs, including `Electron_testrecipes` |
| Corrected-pT permutation mutates itself; ratio may be permuted twice | Current code and recorded nonidentity-permutation witness | Use one immutable permutation once per genuinely aligned vector; preserve correction formulas and variation semantics |
| `isLoose` loses positional association | Defined before filtering, omitted from later `Lepton_*` permutation | Preserve its boolean meaning while following retention and nominal ordering |
| Historical electron eta/index disagreement | Direct retained-file observation; historical dirty source unavailable | Verify newly written eta/phi versus raw indices; do not claim the historical operation identified |
| DATA JEC source-map failure | Earlier full DATA run stopped at `Regrouped_*` lookup | Inspect actual payload support; repair only a proven configuration mismatch, without bypassing JEC |
| Nominal jet-cleaning concern | Sorted-prefix invariant holds in active sequence | No jet-cleaning selection change |

Completion requires real full-chain snapshots, independent reopening, complete
MC key accounting and bounded DATA witnesses. A counterfactual alone is not a
producer validation. Input normalization receipts are reused solely for the
existing producer `baseW`; no new Runs scan or partial-file normalization is
introduced. Sequential MC random draws preclude association-only attribution
of final kinematic differences unless common-event draws are explicitly held
fixed; otherwise the causal claim is restricted to pre-smearing gates and
object association.

## Executed result

**Six fresh nominal HWWNano Events snapshots were written and independently
reopened on LPC on 2026-09-30.** All checked object-association invariants
passed. The repaired complete-file MC accepted **keys** equal the independent
aligned-gate reference exactly, with no later event losses. This is a repair
demonstration on this branch, not a change to `ZH_devel` or a full-year result.

The measured producer was
[`9a0e9be`](https://github.com/TheQuantiser/mkShapesRDF/commit/9a0e9be35c27e2907e6201460d0a5de58a091651).
Its processor tree is `592fdadf25d978a469546c6d22656b94fd1540d2`; its include
tree is `311e5fd6311c74b58ba233258acb2018aabcdd7d`. The executed harness was
archived in each output directory as `repair_demo-used.py`, SHA-256
`b035e8cf2554c0195bbc0391e8b3ced5db50d0525c0dc2c04c9d441c5334a8ba`.
[Environment and inputs](repair-environment.json),
[compact results](repair-results.json), and [event witnesses](repair-witnesses.json)
retain the numerical provenance. Exact commands are in the [README](README.md#repair-demonstration-on-this-branch).

## Shared producer changes

### One retained-object mapping for all decisions

At the [original `LeptonSel` stage](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/LeptonSel.py),
WP bits were defined using the original indices, but only the six core arrays
were subsequently filtered:

```python
df = df.Define("Lepton_isTightElectron_"+ids, "propagateMask(Lepton_electronIdx, comb, false)")
df = df.Define("Lepton_isTightMuon_"+ids, "propagateMask(Lepton_muonIdx, comb, false)")
branches = ["pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx"]
df = df.Redefine(
    f"Lepton_{prop}",
    f"Lepton_{prop}[LeptonMaskHyg_Ele && LeptonMaskHyg_Mu]",
)
```

The definition and loop excerpts are separate operations. The repair binds
the mask **before** any core redefinition, then takes the same retained
indices from every core array, all seven electron and six muon tight-WP
vectors, and `isLoose`:

```python
df = df.Define(
    "LeptonSel_keepIdx",
    "ROOT::VecOps::Nonzero(LeptonMaskHyg_Ele && LeptonMaskHyg_Mu)",
)
for column in lepton_columns:
    df = df.Redefine(
        column,
        f"ROOT::VecOps::Take({column}, LeptonSel_keepIdx)",
    )
```

See [the exact repaired module](https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/modules/LeptonSel.py).
ROOT's lazy expressions remain bound to the original nodes; the immutable
mapping avoids recomputing a mask against already shortened indices. Raw
Electron/Muon and the prefilter VetoLepton collection are preserved.
For raw muons `[0,1,2]` with decisions `[false,true,true]`, retaining `[1,2]`
now gives `[true,true]`. These are offline WP bits, not HLT bits.

`L2TightSelection` adds `df.Filter("Lepton_pt.size() >= 2")` before its
unchanged two-slot all-WP OR. **Electron_testrecipes remains its original
strict raw `pT > 10` recipe**, including its participation in that OR.
No ID, isolation, MVA or threshold policy was changed.

### One immutable correction permutation

The [original scale module](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/LeptonScaleSmearing.py)
defined an already ordered correction ratio, then included the permutation
and that ratio in a generic loop:

```python
df = df.Define("Lepton_sorting",     "sortedIndices(Lepton_newPt)")
df = df.Define("Lepton_rochesterSF", "Take(Lepton_newPt/Lepton_pt, Lepton_sorting)")
df = df.Redefine("Lepton_pt",        "Take(Lepton_newPt, Lepton_sorting)")
for branch in df.GetColumnNames():
    if branch.startswith("Lepton_") and branch!="Lepton_pt":
        df = df.Redefine(branch, f"Take({branch}, Lepton_sorting)")
```

For a swap `p=[1,0]`, redefining `p` as `Take(p,p)` produces `[0,1]`.
Later fields could therefore follow a different order; the ratio could be
permuted twice. The [repair](https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/modules/LeptonScaleSmearing.py)
captures genuine flat per-lepton arrays **before** defining the permutation,
excludes temporary, nested/scalar, generated-variation and already sorted
products, includes `isLoose`, and takes each original aligned array once:

```python
varied_columns = set(df.GetVariedColumns(df.GetColumnNames()))
excluded_columns = set(self.columnsToDrop) | varied_columns | {
    "Lepton_pt",
    "Lepton_sorting",
    "Lepton_rochesterSF",
}
for branch in df.GetVariedColumns(["Lepton_pt"]):
    df = df.Define(
        branch, f"Take({branch}, Lepton_sorting)", excludeVariations=["*"]
    )
for branch in lepton_columns:
    df = df.Redefine(branch, f"Take({branch}, Lepton_sorting)")
```

The existing four pT variation arrays follow the nominal identity order once;
mRDF propagates registered SF variations through their nominal redefinition.
This does not establish physics validity of every pre-existing variation
formula. Real snapshots here persist nominal fields; focused synthetic ROOT
checks exercise variation associations and MET propagation separately.

### DATA JEC configuration, separately committed

[`68a082c`](https://github.com/TheQuantiser/mkShapesRDF/commit/68a082c)
changes the DATA-only JES uncertainty source list to `[]`. The actual pinned
DATA payload contains nominal JEC levels, but no corresponding
`Regrouped_*` DATA uncertainty corrections. Their lookup raised `map::at`
even though DATA JES variations were already disabled. The full DATA chains
now execute nominal JEC, corrected-jet sorting, veto/cleaning, and the other
configured modules. No JEC or event-cleaning bypass was used. MC source
configuration and nominal correction formulas are unchanged.

## Executed chains and stage counts

`repair_demo.py` loads the actual DATA or MC `Steps_cfg` subTargets, runs all
event-producing modules in order, and invokes the actual configured Snapshot
module with its configured **wildcard nominal column selection**, subject
to the unchanged Snapshot serialization exclusions. In these inputs that
excludes `BeamSpot_type`, `Electron_seediEtaOriX` and `Photon_seediEtaOriX`.
Those exclusions do not remove the audited identity or lepton fields. An
immutable native ROOT checkpoint freezes the computed columns once before
the HWW callback reads them in 10,000-event chunks. Corrections are not
recomputed separately for each output chunk. Auxiliary ROOT-key copying and
EOS stage-out are outside this local Events demonstration.

The DATA chain is `DATAl2loose2024v15__l2loose`. The MC chain is
`MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight`. MC `l2tight` still
runs **before** scale/smearing and snapshot. DATA has no corresponding tight
production skim. Diagnostic observations freeze maker, selected, pre-scale,
and SF vectors; they do not replace the baseline producer expressions.

| Stage | EGamma C | EGamma I | Muon C | Muon I | DY→ee | DY→μμ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Input Events | 50,000 | 50,000 | 50,000 | 50,000 | 158,487 | 222,331 |
| Chain raw multiplicity | 15,896 | 16,431 | 30,305 | 30,580 | 94,106 | 129,548 |
| Golden mask | 13,341 | 16,431 | 30,305 | 30,580 | — | — |
| LeptonMaker | 12,493 | 14,814 | 25,497 | 26,220 | 93,059 | 127,633 |
| LeptonSel | 3,353 | 3,782 | 12,619 | 12,176 | 78,696 | 121,809 |
| JetSelMask / MC pre-gate | 3,189 | 3,590 | 11,927 | 11,447 | 74,938 | 116,303 |
| Repaired l2tight | — | — | — | — | **43,338** | **89,282** |
| Reopened final Events | **3,189** | **3,590** | **11,927** | **11,447** | **43,338** | **89,282** |
| Actual correction reorderings | 8 | 15 | 2 | 7 | 1,419 | 978 |
| Successful producer seconds | 114.95 | 118.46 | 178.12 | 181.30 | 748.66 | 1,322.71 |

All input identities are unique and have no high-bit event numbers in the
six executed ranges: four DATA 0:50,000 prefixes and two complete MC files.
Input ledgers cover each assigned range before cuts. The six
successful producer payloads sum to **44.40 minutes**; this is not campaign
wall time and excludes earlier failed attempts and subsequent audits/replays.
The original gate reference runs took 83.59 s (ee) and 110.03 s (μμ).

The independent audit reopened 21 flat per-lepton arrays in each DATA output
and 186 in each MC output, including 159 SF arrays compared with their frozen
pre-correction copies, against raw
indices, prefilter WP decisions and saved pre-correction fields. It found
**zero anomalous events**: identity/flavor, eta/phi, all 13 WPs, `isLoose`,
lengths, correction-ratio association and descending corrected-pT order all
pass. Largest MC ratio residual is below `5.961e-8`. This also checks real
nonidentity permutations; it is not merely an identity-order test.

## Complete-file MC acceptance: causal gate result

The clean original producer at `69ff2dad` was run only through the gate to
persist its missing exact accepted-entry reference. Its independently
aligned predicate keeps the same all-WP policy and raw decisions. The
repaired pre-gate keys, decisions and genWeight match that reference, and
the final repaired key sets equal its aligned accepted sets exactly.

| File | Pass both | Original rejects; repaired passes | Original passes; repaired rejects | Reject both | Repaired final |
| --- | ---: | ---: | ---: | ---: | ---: |
| DY→ee | 42,732 | **606** | **25,689** | 5,911 | **43,338** |
| DY→μμ | 83,368 | **5,914** | **5,324** | 21,697 | **89,282** |

| File / outcome | Σ genWeight | Σ genWeight² |
| --- | ---: | ---: |
| ee pass both | 778,066,460.476563 | 30,646,066,889,812.742 |
| ee rescued | 10,176,404.453125 | 434,604,430,759.771 |
| ee removed | 449,716,736.792969 | 18,423,355,151,464.934 |
| ee reject both | 101,576,584.449219 | 4,239,186,122,476.905 |
| μμ pass both | 1,525,389,467.500000 | 59,788,947,497,657.695 |
| μμ rescued | 105,245,446.054688 | 4,241,337,629,559.875 |
| μμ removed | 77,715,594.007813 | 3,818,207,903,242.606 |
| μμ reject both | 379,713,786.160156 | 15,560,416,393,060.637 |

These are **raw signed accounting sums**, not normalized Z yields. Uncut
input `(Σw,Σw²)` are ee `(2,825,907,176.597656,
113,661,967,686,177.86)` and μμ `(3,974,341,199.144531,
159,448,907,087,872.25)`. No denominator was recomputed from these files.

The reopened repaired multiplicities close the earlier ambiguity:

| File / gate outcome | n=1 | n=2 | n=3 | n=4 | Historical paired part0 |
| --- | ---: | ---: | ---: | ---: | --- |
| ee both | 0 | 42,541 | 185 | 6 | All present, same multiplicity |
| ee rescued | 0 | 601 | 5 | 0 | All absent |
| ee removed | **25,638** | **51** | 0 | 0 | All present, same multiplicity |
| ee neither | 5,850 | 61 | 0 | 0 | All absent |
| μμ both | 0 | 82,987 | 373 | 8 | All present, same multiplicity |
| μμ rescued | 0 | 5,884 | 29 | 1 | All absent |
| μμ removed | **5,269** | **54** | **1** | 0 | All present, same multiplicity |
| μμ neither | 20,839 | 855 | 3 | 0 | All absent |

Thus not every false acceptance is a singleton. Conversely, a legitimate
one-retained-lepton rejection is not a bug: μμ source entry 127 remains
rejected by both gates and absent from both historical and repaired output.
Final repaired multiplicities are ee `43,142 / 190 / 6` and μμ
`88,871 / 402 / 9` at n=2/3/4, with **zero n<2 survivors**.

The complete historical join establishes absence only from the verified
paired **part0**. The original gate's accepted keys equal that membership;
this strongly corroborates the retention mechanism for these files, while
the exact historical dirty-worktree executable remains unavailable.

## Reopened witnesses

The [witness artifact](repair-witnesses.json) contains the original raw-index
and gate evidence plus maker, filtered, pre-scale and serialized fields for
retained repaired events. Full keys are checked, never inferred from entries.

| Role / input entry | (run, lumi, event) | Fresh snapshot result |
| --- | --- | --- |
| Muon C / 234 | (379416,147,131724611) | Two retained muons; tight bits and raw-index coordinates attached correctly |
| EGamma C / 20774 | (379729,907,1396820419) | Two retained electrons; corrected tight association |
| EGamma I / 27025 | (386509,159,333332716) | Two retained electrons; eta and phi follow electronIdx, unlike historical eta-only mismatch |
| EGamma I / 46209 | (386509,735,1539152813) | Two retained electrons; both decision and coordinate invariants pass |
| DY→ee / 174 | (1,384532,2060318616) | Rescued, written with two retained leptons; historical part0 absent |
| DY→μμ / 5 | (1,260002,1443525631) | Rescued, written with two retained leptons; historical part0 absent |
| DY→ee / 8 | (1,384532,2060317109) | Old one-lepton acceptance removed; repaired snapshot absent |
| DY→μμ / 102 | (1,260002,1443526295) | Old one-lepton acceptance removed; repaired snapshot absent |

Fresh correct electron eta establishes the invariant for the new output.
It does **not** identify the historical eta-only failing operation.

## Bounded RunStability replay: descriptive downstream result

The replay uses the exact retained compiled pickle SHA-256
`6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef`,
commit-pinned historical runner, unchanged global Z builder, historical
leading-two analysis gate, 35/35 GeV and 60–120 GeV cuts, historical DATA
stream priorities, and component weights. The repaired view replaces only
the HWW input URI. There is no Coffea selection rewrite or gate omission in
this comparison.

MC retains `XSWeight × METFilter_Common × puWeight × SelectedLeptonSF_Z ×
TriggerSF_Z`, with `XSWeight=baseW×genWeight`. The verified existing full-source
`baseW` receipts are reused; no new Runs scan occurs and no partial-file sum
normalizes these outputs. The histogram runner multiplies by its compiled
109.08 fb⁻¹; reported MC sums below divide by that same reference to express
the contribution of this **one file at 1 fb⁻¹**. This is not a complete-source
prediction or an absolute DATA/MC calibration.

| DATA prefix / category | Historical selected | Repaired selected |
| --- | ---: | ---: |
| EGamma C / Ele30 | 204 | 208 |
| EGamma C / Ele23–Ele12 | 191 | 195 |
| EGamma I / Ele30 | 208 | 215 |
| EGamma I / Ele23–Ele12 | 196 | 203 |
| Muon C / IsoMu24 | 525 | 604 |
| Muon C / Mu17–Mu8 | 480 | 552 |
| Muon I / IsoMu24 | 434 | 497 |
| Muon I / Mu17–Mu8 | 399 | 458 |

DATA sumw and sumw² equal those counts. These are new fixed 50,000-entry
prefixes, not the earlier diagnostic's longer ranges.

| MC / category | Historical N / Σw at 1 fb⁻¹ | Repaired N / Σw at 1 fb⁻¹ | Repaired Σw² (1 fb⁻¹ projection) | Repaired: both / rescued |
| --- | --- | --- | ---: | --- |
| ee / Ele30 | 15,033 / 59.565510 | 15,261 / 60.618720 | 0.618482 | 15,103 / 158 |
| ee / Ele23–Ele12 | 13,774 / 54.403805 | 13,982 / 55.396279 | 0.562286 | 13,843 / 139 |
| μμ / IsoMu24 | 32,559 / 137.409340 | 35,043 / 149.380820 | 1.674378 | 33,349 / 1,694 |
| μμ / Mu17–Mu8 | 31,373 / 132.131206 | 33,782 / 143.675053 | 1.613938 | 32,142 / 1,640 |

Exact historical variances and **signed weighted sums for each outcome** are
in [repair-results.json](repair-results.json). All historically selected rows
belong to `passes_both`; none of the removed gate events reaches these Z
categories. Gates are necessary but not sufficient: only 158/139 of the 606
rescued ee events and 1,694/1,640 of the 5,914 rescued μμ events enter the
respective final categories. The categories overlap and must not be summed
as unique events.

| Repaired MC category | Σw from pass-both class | Σw from rescued class | Σw from removed class |
| --- | ---: | ---: | ---: |
| ee / Ele30 | 59.967994 | 0.650726 | 0 |
| ee / Ele23–Ele12 | 54.805197 | 0.591082 | 0 |
| μμ / IsoMu24 | 140.823624 | 8.557196 | 0 |
| μμ / Mu17–Mu8 | 135.448927 | 8.226126 | 0 |

These sums use the same 1 fb⁻¹ projection as the previous table. Rescued
producer events that fail downstream cuts contribute zero to those categories;
removed events are absent from repaired snapshots and none selected in the
historical view. Full sumw² contributions are retained in the compact JSON.

Common-gate membership also changes downstream: +70/+69 selected ee events
and +790/+769 μμ events within `passes_both`, alongside the rescued rows.
Electron smearing uses a sequential static TRandom3; muon smearing and
unseeded TrigMaker use shared gRandom. Different surviving events shift
subsequent random variates, including trigger-period and weight assignments.
No attempt was made to alter nominal RNG policy. **These final migrations
and weighted differences are descriptive**, whereas the pre-smearing gate
result above is the association-only causal measurement. A new original
final-kinematic snapshot is not claimed: the independent original reference
stops before corrections; the final baseline is the actual historical part0.
DATA scale corrections are deterministic and do not have this MC smearing
confound. Their historical-versus-fresh replay still compares an unavailable
dirty historical producer with the pinned repaired source; exact historical
source and payload-byte equivalence are not established by this exercise.

Every replay ran one booked RDF graph. ROOT histograms were independently
reopened: contents and variances including flows equal the ledger's sums
(with 109.08 and 109.08² restored for MC). Each selected key matches its
input entry; there are no within-category duplicates or missing gate labels.

## Execution failures and bounded checks

Earlier task-owned attempts remain in local scratch as failed evidence:
an incorrect absolute LumiMask substitution; many-column Cache compilation
and memory exhaustion; and a narrow snapshot lacking TrigObj inputs needed
by the compiled replay. Final runs use the correct framework-relative mask,
native checkpoint and configured wildcard nominal persistence with the
existing Snapshot exclusions. No producer physics
module was removed to resolve those failures.

On this ROOT/XRootD runtime, teardown could stall in `File::Close` after the
real outputs had closed. The stack is retained locally. The diagnostic CLI
explicitly flushes and exits after its outputs are written and a basic
reopen/count succeeds; failures before that point retain nonzero exits. This
task-local policy does not alter framework modules. The **separate reopened
invariant audit**, rather than that exit code, establishes output acceptance.
A replay bottleneck from repeated compressed-NPZ member access was fixed
by loading identity and gate arrays once; no repeated producer traversal was
needed.

Focused checks: five real ROOT selection/guard tests passed; four real ROOT
synthetic correction/permutation/variation tests passed. A serialization
boundary check passed with an explicit signed two's-complement bridge; the
native unsigned ≥2⁶³ list conversion remains an expected failure. No such
high-bit event exists in the six executed input ranges. The shared Snapshot identity
boundary is a separate known limitation, not repaired or hidden here.
The focused commands were `python -m pytest -q
tests/test_processor_lepton_selection_associations.py`, `python -m pytest -q
PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/tests/test_lepton_scale_association.py`,
and `python -m pytest -q
PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/tests/test_snapshot_identity.py`.
The two repair regressions fail on the unrepaired modules. Previously completed
checks were reused rather than repeated as a broad test campaign.

## Impact and limits

- **Shared producer:** retention and correction permutations now preserve
  object identity on this branch; guarded all-WP l2tight fixes both losses
  and false acceptances in the two measured MC files.
- **Produced content:** fresh repaired snapshots contain rescued events and
  correctly attached vectors. An HWW-only alias edit cannot restore events
  absent from an old skim. Regenerate affected HWW from original NanoAOD,
  then regenerate dependent histograms where complete corrected results
  are required.
- **Personal RunStability:** the bounded historical-policy replay changes
  selected Z counts and weights. It is not a full-year yield correction.
- **Intentional differences:** stream priority, Coffea's omission of the
  historical analysis gate, trigger association and normalization policy
  remain separate analysis choices.
- **Unresolved/unexercised:** the exact historical eta-only cause and dirty
  producer remain unavailable; full systematic production, conditional JES
  index risk, standard auxiliary metadata and remote publication are outside
  the executed scope. The active nominal jet-cleaning sorted prefix remains
  unchanged and is not declared defective.

The results do not establish a full-year 12.4%, 2.8% or 6.66% attribution,
nor invalidate every historical HWWNano event or the original NanoAOD.
