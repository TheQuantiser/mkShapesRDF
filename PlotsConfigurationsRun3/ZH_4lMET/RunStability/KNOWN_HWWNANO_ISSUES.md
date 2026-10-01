# HWWNano association issues: findings, repairs and diagnostic guide

**Updated 2026-10-01. The affected historical HWWNano products are invalid
inputs for analyses that depend on their retained lepton IDs and object
associations.** Direct reads establish decisions attached to the wrong
leptons and a separate electron coordinate/index inconsistency. Controlled
producer comparisons establish both erroneous MC rejection and erroneous
acceptance before the output is written. Plausible histograms, readable
files, or a majority of correct events do not establish analysis validity
when this collection contract is broken.

These are findings in the **shared mkShapesRDF HWWNano producer**. This
personal RunStability study exposed them; they are not confined to its
aliases or plots. The demonstrated historical scope is the pinned **2024
Full2024v15** files. Which other productions, years and HWW channels used
the affected implementations remains a campaign/consumer audit question.
The original central NanoAOD is the source for regeneration.

**A bounded repair has been demonstrated, but its producer changes are not
integrated into `ZH_devel`.** The inspected pre-update head,
[`d036a257`][zh-inspected], has the same blobs as the original reference
[`69ff2dad`][original-commit] for `LeptonSel.py`, `L2TightSelection.py`,
`LeptonScaleSmearing.py` and `Steps_cfg.py`. This page consolidates evidence
and reproduction routes; updating documentation does not adopt the repair.

Use this page to choose the investigation and source revision. The
[repair report](diagnostics/hww_object_associations/REPAIR_REPORT.md)
contains the detailed measured tables, implementation excerpts and limits.
The [repair README][repair-readme] owns the exact producer/audit/replay
commands. The [chain audit](chain-audit.md) explains the broader
Coffea–mkShapes selection, source and weighting differences.

For a simple stored-file demonstration, use the
[direct ROOT event inspection](diagnostics/hww_object_associations/ROOT_INSPECTION.md).
One standalone PyROOT command displays four DATA witnesses, two historical
MC singletons and a retained MC wrong-bit example from the actual paired
central/HWW files. It needs no producer replay, Coffea, calibration payloads
or compiled analysis configuration; its actual terminal transcript is included.

## Contents

- [Branch and document map](#branch-and-document-map)
- [Findings and repair status](#findings-and-repair-status)
- [Production order and failure mechanisms](#production-order-and-failure-mechanisms)
- [Investigations and recorded checks](#investigations-and-recorded-checks)
- [Consequences for RunStability](#consequences-for-runstability)
- [Reproduce the diagnostics](#reproduce-the-diagnostics)
- [Remaining work and proposed changes](#remaining-work-and-proposed-changes)

## Branch and document map

### mkShapesRDF

The three investigation branches are successive evidence routes, not three
alternative fixes. Use the pinned revisions below rather than assuming a
branch's future HEAD reproduces the measured source.

| Branch / pinned revision | Purpose and contents | Start here |
| --- | --- | --- |
| `ZH_devel`; producer inspected at [`d036a257`][zh-inspected] | Consolidated issue/repair documentation and the current RunStability leaf. The four relevant producer files remain unrepaired. The standalone read-only ROOT display is available here; the full historical replay and producer-demo harnesses remain on the investigation branches. | This page; [direct ROOT inspection](diagnostics/hww_object_associations/ROOT_INSPECTION.md); [repair report](diagnostics/hww_object_associations/REPAIR_REPORT.md); [chain audit](chain-audit.md); [USAGE.MD](USAGE.MD). |
| `codex/2024-electron-diagnostic`; [`7843a7f`][electron-commit] | Historical compiled-HWW replay, local producer stage ledger, electron alignment/gate-removal counterfactuals and diagnostic tests. **No producer repair.** | [HISTORICAL_HWW_DIAGNOSTIC.md][historical-guide]. |
| `demo/2024-hwwnano-object-associations`; [`69ff2dad`][original-commit] | Original producer unchanged; six historical/live witnesses, one-entry MC stage traces, complete two-file membership join and original-versus-aligned MC gate comparison. | [Original README][original-readme], [observed summary][observations], [complete gate results][complete-results], [join receipt][join-receipt]. |
| `fix-demo/2024-hwwnano-object-associations`; [`8d940ab`][repair-evidence-commit] | Actual producer repairs, regression tests, six newly written/reopened nominal Events outputs, exact MC gate closure and historical-policy Z replay. Measured producer revision is [`9a0e9be`][repair-producer-commit]. | [Repair README][repair-readme], [executed report][executed-report], [environment][environment], [results][repair-results], [witnesses][repair-witnesses]. |

Relevant commit history:

- Historical replay/ledger additions at [`fa1a1e0`][historical-additions]
  and tight-mask documentation at [`2fd798f`][historical-mask-doc] are
  ancestors of `7843a7f`. They were initially placed on `ZH_devel`, then
  retained on the separate electron diagnostic branch. Their scripts are
  not expected to exist on today's `ZH_devel`.
- [`bf75c7f`][witness-commit] added the original six-witness demo;
  `69ff2dad` extended it with the complete DY join/gate investigation.
- [`68a082c`][jec-commit] separately corrected the DATA JEC source request;
  `9a0e9be` repaired lepton retention/gate/reordering; `8d940ab` committed
  the completed output evidence and reproduction material.
- [`4e6793f`][initial-issues-commit] introduced this issue note;
  [`c064927`][corrected-issues-commit] corrected the nominal jet-cleaning
  allegation and producer-order interpretation;
  [`a3b160a`][repair-doc-integration] added repair documentation to
  `ZH_devel`; `d036a257` reorganized the repair report. These documentation
  commits are not producer adoption.

### Companion ZH4l_coffea evidence

The initial paired low-pT study is retained at [`062cfea`][coffea-paired-commit],
with the [muon/MC paired-event report][paired-report]. The companion
`codex/2024-electron-diagnostic` branch added the electron investigation at
[`a5bba58`][coffea-electron-commit]; later documentation at
[`44e7ae7`][coffea-evidence-commit] retains the
[electron report][electron-report] and
[paired diagnostic evidence directory][coffea-evidence]. Its
[reducer README][coffea-reducer-guide] documents how to rebuild the compact
comparison evidence from retained traces, and the
[local-run note][coffea-run-note] records the original Coffea execution.
These are pinned
evidence revisions, not assertions about today's Coffea `main`.

The copied [input manifest][manifest] and [parent-pair evidence][pair-evidence]
on the mkShapes demo branch suffice for its witness and complete-file
diagnostics. Reproducing the original Coffea/HWW eventwise comparison also
requires the companion repository and its report's recorded campaign
artifacts. Companion links may require repository access. The numerical
producer/repair findings below also have committed mkShapes evidence.

## Findings and repair status

| Finding | What is established | Repair / next action |
| --- | --- | --- |
| Tight electron/muon decisions remain in prefilter positions | Wrong associations directly observed inside historical HWW events; omission reproduced in live original `LeptonSel`. | Implemented on repair branch: one immutable retention mapping for six core arrays, all 13 configured tight-WP vectors and `isLoose`. Not adopted on `ZH_devel`. |
| MC `l2tight` reads stale first-two slots without a retained-size guard | Controlled complete-file comparison proves erroneous losses and acceptances; original accepted keys equal paired historical membership. | Implemented: corrected vectors plus `Lepton_pt.size() >= 2` before slot access. Existing all-WP OR policy preserved. |
| Correction reorder mutates its own permutation / reorders an already ordered ratio | Current-source defect reproduced under a real electron swap; separate synthetic order tests and repaired snapshots exercise nonidentity permutations. | Implemented: immutable permutation, once-only mapping of genuine per-lepton arrays, including `isLoose` and applicable SF/variation fields. |
| Historical electron eta disagrees with raw index while phi agrees | Direct historical period-I observation, even where tight bits are correct. Exact historical operation is unresolved. | Fresh repaired snapshots pass eta/phi/index checks. This establishes the new invariant, not the exact old cause. |
| `isLoose` is not filtered or carried through the later sort | Source association/length defect. No direct consumer or measured contribution in this RunStability leaf. | Included in both repaired mappings. Existing boolean policy preserved; review semantics separately if required. |
| DATA JEC requests unavailable `Regrouped_*` uncertainties | Actual configuration lookup failure prevented an earlier complete DATA run. | Separate repair at `68a082c`: DATA `jes_unc=[]`; nominal JEC and cleaning retained. |
| Nominal jet-cleaning masked-slot expression | Earlier active-chain bug allegation **withdrawn**: the 2024 pre-correction lepton order makes the mask a prefix. | No nominal cleaning change justified by this investigation. Retain the ordering requirement if the module is reused. |
| JES variation jet-index composition | Conditional source risk if original jet pT ordering is nonidentity; no affected produced-file witness or nominal yield effect established. | Audit input order and varied index/coordinate identity before proposing a verified correction. Outside repair demonstration. |
| Native unsigned event-ID serialization at ≥2^63 | Synthetic real-Snapshot test records an expected failure in conversion through untyped Python lists. | Unresolved production boundary. Signed bridge is a diagnostic check, not an adopted native-serialization fix. |

## Production order and failure mechanisms

The [original 2024 step configuration][original-steps] gives:

```text
Central NanoAOD
  → LeptonMaker: combine, sort by descending pT, preserve VetoLepton copy
  → LeptonSel: compute WPs, retain hygiene-passing core leptons
  → nominal jet corrections and JetSelMask
  DATA → leptonScale_data → kinematics/triggers → snapshot
  MC   → formulasMC → l2tight → leptonScale_mc
       → kinematics/triggers → snapshot
HWWNano → compiled RunStability selection, Z builder, weights, histograms
```

The MC chain is
`MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight`.
The DATA chain is `DATAl2loose2024v15__l2loose` and has **no MC-like
production `l2tight` skim**. Later correction reordering cannot cause a
rejection at an earlier gate. An HWW-only analysis edit cannot restore an
event already omitted by that gate.

### LeptonSel: a correct mask is not a complete association operation

At retained position `i`, momentum, coordinates, raw index, WP decisions and
applicable SFs must describe the same physical object. `propagateMask`
correctly maps a raw electron/muon decision to combined lepton positions
**at the stage where it is defined**. The hygiene masks use `true` for the
other flavor, making the electron mask neutral for muons and vice versa.
Tight vectors use `false` for the other flavor.

The [original module][original-selection] computes tight decisions before
retention:

```python
df = df.Define("Lepton_isTightElectron_"+ids, "propagateMask(Lepton_electronIdx, comb, false)")
df = df.Define("Lepton_isTightMuon_"+ids, "propagateMask(Lepton_muonIdx, comb, false)")
```

It later filters only six fields:

```python
branches = ["pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx"]
for prop in branches:
    df = df.Redefine(
        f"Lepton_{prop}",
        f"Lepton_{prop}[LeptonMaskHyg_Ele && LeptonMaskHyg_Mu]",
    )
```

The same mask is not applied to the already defined ID vectors or `isLoose`.
ROOT's lazy definitions do not automatically rebind those earlier decisions
to the subsequently shortened indices.

```text
Original raw muons       [0,     1,    2]
Original tight bits      [false, true, true]
Hygiene retention        [false, true, true]
Retained raw muons       [1,    2]
Correct retained bits    [true, true]
Wrong first-two bits     [false, true]  ← still describe old positions 0,1
```

Historical Muon C source entry 234, key `(379416,147,131724611)`, HWW
entry 65, has this wrong `[false,true]` association for retained muons
`[1,2]`. The named WP was recomputed from raw muon inputs **inside that
same HWW record**. EGamma C source entry 20774, key
`(379729,907,1396820419)`, HWW entry 991, analogously has retained electrons
`[0,1]` with stored `[false,true]` instead of `[true,true]`.
See [observed witnesses][observations] and the companion
[muon][muon-audit] / [electron][electron-audit] raw-WP audits.

The clean original live vectors remain longer than the retained core
collection; some historical stored vectors have retained length but the
wrong prefix. The historical producer ran from an unavailable dirty
worktree. **The wrong historical association is proven; the precise old
shortening/serialization operation is not identified.**

The [implemented repair][repaired-selection] freezes the retention mapping
before any core redefinition:

```python
df = df.Define(
    "LeptonSel_keepIdx",
    "ROOT::VecOps::Nonzero(LeptonMaskHyg_Ele && LeptonMaskHyg_Mu)",
)
```

It builds `lepton_columns` from the core fields, `isLoose`, and every
configured electron/muon tight WP, then uses:

```python
for column in lepton_columns:
    df = df.Redefine(
        column,
        f"ROOT::VecOps::Take({column}, LeptonSel_keepIdx)",
    )
```

Raw Electron/Muon and prefilter VetoLepton arrays are preserved. This repairs
association without changing WP definitions, thresholds or isolation/MVA
choices. The module's `pT > 8` requirement is an **event requirement for
at least one hygiene-passing object**, not the final retention mask. The
regression retains this existing distinction and checks low-pT survivors.

For the active Loose route, the original expression
`isLoose = LeptonMaskHyg_Mu || LeptonMaskHyg_Ele` is already true for each
ordinary electron/muon because the other-flavor mask defaults to true.
That limits the effect of stale boolean values in this route, but does not
justify a wrong vector length. Other cleaning routes calculate loose
decisions with false defaults. The repair fixes association while preserving
the existing boolean policy; it does not establish a historical
RunStability loss caused by `isLoose`.

### L2TightSelection: incorrect objects can decide event existence

The [original gate][original-gate] ORs **all configured electron and muon
tight WPs** separately at positions 0 and 1, then ANDs those positions:

```python
l2tight_selection = f"({lepton1_selection}) && ({lepton2_selection})"
df = df.Filter(f"{l2tight_selection}")
```

With stale decisions, a removed object's bit can reject a valid retained
pair or supply a second passing slot to a one-lepton survivor. The
[repair][repaired-gate] first applies:

```python
df = df.Filter("Lepton_pt.size() >= 2")
```

It then evaluates the unchanged all-WP predicate on correctly attached
vectors. `Electron_testrecipes`, whose original cut is strict raw
`Electron_pt > 10`, remains in that OR. Passing this producer gate is
therefore **not equivalent** to passing RunStability's specific named WPs.
Changing the allowed WP policy is a separate proposal, not part of the
association comparison.

### LeptonScaleSmearing: preserve one permutation and apply it once

The [original correction module][original-scale] contains:

```python
df = df.Define("Lepton_sorting",     "sortedIndices(Lepton_newPt)")
df = df.Define("Lepton_rochesterSF", "Take(Lepton_newPt/Lepton_pt, Lepton_sorting)")
df = df.Redefine("Lepton_pt",        "Take(Lepton_newPt, Lepton_sorting)")
for branch in df.GetColumnNames():
    if branch.startswith("Lepton_") and branch!="Lepton_pt":
        df = df.Redefine(branch, f"Take({branch}, Lepton_sorting)")
```

The loop includes `Lepton_sorting` itself. For a swap `p=[1,0]`,
`Take(p,p)=[0,1]`; fields visited afterward can receive a different
permutation. `Lepton_rochesterSF` was already ordered and can be ordered
twice. The [dataframe wrapper][mrdf-source] tracks columns through a set;
iteration order is not a physical association contract. Sorting the column
names would make the failure deterministic, not correct.

An isolated live run of EGamma I entry 27025 exercised a real pT swap and
produced a **phi/index mismatch** under the recorded loop order. It omitted
preceding JME and was not a full DATA production run. The historical record
for key `(386509,159,333332716)` instead has an **eta-only mismatch**:
raw/expected eta `[-0.9336,-2.0571]`, stored eta `[-2.0571,-0.9336]`, while
phi follows `electronIdx=[0,1]` and tight bits are correct. These observations
prove two association failures, but do not prove the live operation produced
the exact historical pattern. Entry 46209, key `(386509,735,1539152813)`,
has both historical tight-bit and eta/index failures; their counts cannot
be added as independent losses.

The [implemented correction repair][repaired-scale] captures genuine flat
per-lepton input columns before creating the permutation. It excludes
temporaries, generated variation columns, the permutation, sorted pT and
the already sorted ratio; includes `isLoose`; and applies the frozen
permutation once. Registered SF variations follow their nominal mapping;
existing pT variation arrays are mapped explicitly. Nominal real-file
audits and synthetic variation/MET checks support this implementation.
They do not validate every existing systematic formula or a full
systematic production.

### Separate JEC, jet-index and serialization findings

- **DATA JEC blocker:** requested `Regrouped_*` uncertainty corrections were
  absent from the pinned DATA payload and raised `map::at`, despite disabled
  DATA variation storage. The separate [configuration repair][jec-commit]
  sets DATA `jes_unc=[]`; nominal JEC, jet sorting, veto/cleaning and
  `do_JER=False`, `store_nominal=True`, `store_variations=False`,
  `isMC=False` remain. MC configuration is unchanged.
- **Nominal jet cleaning:** [JetSelMask][jet-cleaning-source] builds a masked
  lepton count but uses its slots on unmasked coordinates. That would fail
  for an unsorted collection such as `[8,20]` GeV. In the active 2024 order,
  LeptonMaker sorts descending, LeptonSel preserves survivor order, and
  cleaning precedes momentum correction. The `pT >= 10` mask is a prefix,
  so the slots agree. The earlier nominal-bug claim was withdrawn; the nine
  `jetSelMask` losses in the paired MC ledger do not prove an index defect.
- **JES variation indexing:** [JMECalculator][jme-source] saves the initial
  jet-sort index vector, then uses
  `Take(tmp_CorrectedJet_jetIdx, variation_sorting)` for varied indices while
  varied coordinates follow the variation sort directly on raw jet arrays.
  For initial `p=[1,0]` and variation `r=[0,1]`, indices can follow `[1,0]`
  while coordinates follow `[0,1]`. This requires nonidentity input ordering;
  no real-file prerequisite/effect or nominal RunStability impact was
  established. It is outside the demonstrated repair.
- **Event-ID boundary:** historical signed int64 event values are interpreted
  by their unsigned 64-bit bit pattern for joins. A signed diagnostic bridge
  round-trips high-bit identities through the actual Snapshot callback;
  native unsigned-to-list conversion at ≥2^63 remains an expected failure.
  No high-bit event occurs in the six executed repair ranges. Do not infer
  full-range production correctness from the low-range real outputs.

## Investigations and recorded checks

### What each investigation established

| Investigation | Executed domain / result | Evidence and boundary |
| --- | --- | --- |
| Initial paired Coffea/HWW study | Two 80,000-entry DY prefixes and four 200,000-entry DATA prefixes, joined by full keys to verified historical part0. Muon C/I IsoMu24: 4,478 Coffea vs 3,935 historical selections; 543 Coffea-only. | [Paired report][paired-report], [historical replay guide][historical-guide], frozen [manifest][manifest]. Fixed local domain, not complete datasets. |
| Raw muon WP audit inside HWW | Among 508 Coffea-only IsoMu24 events with historical leading-two decision false, both selected raw muons pass; 503 have wrong stored retained bits; 502 also match the prefilter prefix. | [Muon audit][muon-audit]. Conditioned discrepancy-class count, not a file-wide defect fraction. |
| Electron historical counterfactuals | Alignment only, gate removal only and both were evaluated on retained EGamma C/I with the compiled selection. Distinct bit and eta/index failures found. | [Electron report][electron-report], [counterfactual summary][electron-counterfactual], [replay guide][historical-guide]. In-memory changes, no rewritten input or producer repair. |
| Initial paired DY→μμ stage/weight comparison | Of 1,098 Coffea-only IsoMu24 events, 632 absent from HWW; current producer ledger first rejects 623 at `l2tight`, nine at `jetSelMask`. Common-event weights agree at roughly 10^-8 relative. | [Paired report][paired-report], [chain audit](chain-audit.md). Current first-loss attribution is not recovery of the unavailable historical executable. |
| Original six-witness demo | Four DATA records plus ee loss witness 174 and μμ legitimate rejection control 127; separate one-entry full MC traces; isolated correction-loop trace. | [Original README][original-readme], [observations][observations]. Original shared modules unchanged; initial DATA trace did not execute a complete chain. |
| Complete reverse membership join | Entire central ee/μμ files vs paired historical part0: 158,487→68,421 and 222,331→88,692. Zero HWW-only or ambiguous keys. | [Join receipt][join-receipt]. UUIDs, lineage, uniqueness and full-width identity checked. Absence is from these verified part0 files, not every part. |
| Complete original/aligned producer gate | Same pre-gate events and raw WPs, independent raw-index remap of all 13 WPs, retained-size guard, unchanged all-WP policy. Original accepted keys equal historical part0 membership exactly. | [Complete results][complete-results]. Stops before smearing; causal association/slot comparison. |
| Actual repaired production and independent reopen | Four DATA 0:50,000 prefixes plus both complete DY files; all configured event-producing modules and actual Snapshot callback; zero checked association anomalies. | [Executed report][executed-report], [results][repair-results], [environment][environment], [witnesses][repair-witnesses]. Nominal Events output demonstration. |
| Historical-policy final Z replay | Repaired and actual historical outputs replayed with the same compiled selection/weights; selected ledgers and reopened histograms reconcile. | [Current repair report](diagnostics/hww_object_associations/REPAIR_REPORT.md#bounded-runstability-replay-descriptive-downstream-result). Descriptive final MC comparison; common-event random draws were not held equal. |

### Complete-file gate accounting

| Gate outcome | DY→ee | DY→μμ |
| --- | ---: | ---: |
| Pre-gate events | 74,938 | 116,303 |
| Pass original and aligned | 42,732 | 83,368 |
| Original rejects; aligned accepts (rescued) | **606** | **5,914** |
| Original accepts; aligned rejects (removed) | **25,689** | **5,324** |
| Reject both | 5,911 | 21,697 |
| Original accepted / historical paired total | 68,421 | 88,692 |
| Aligned accepted / repaired final total | **43,338** | **89,282** |

The four classes partition all pre-gate events. The repaired final accepted
keys equal the aligned reference exactly, with zero later losses. Removed
events comprise **25,638 ee singletons + 51 with n≥2**, and **5,269 μμ
singletons + 55 with n≥2**. The repaired audit closes the earlier missing
eventwise current/historical multiplicity cross-tab; the original demo
alone had not established that reconciliation. None of the removed events
contributed to the historical four Z categories. Gross producer migrations
are not selected-Z yield migrations.

The reference compares pre-gate key sets, outcomes and `genWeight`, but
records `pregate_collection_comparison="not assessed"`. Do not restate
accepted-key closure as an exhaustive original/repaired pre-gate array
comparison. Repaired serialized arrays have separate invariant checks.

### Reopened repaired output checks

| Role | Executed source range | Final Events | Real correction reorderings |
| --- | --- | ---: | ---: |
| EGamma C | `[0,50000)` | 3,189 | 8 |
| EGamma I | `[0,50000)` | 3,590 | 15 |
| Muon C | `[0,50000)` | 11,927 | 2 |
| Muon I | `[0,50000)` | 11,447 | 7 |
| DY→ee | `[0,158487)` — complete file | 43,338 | 1,419 |
| DY→μμ | `[0,222331)` — complete file | 89,282 | 978 |

Each DATA output was audited for 21 flat per-lepton arrays; each MC output
for 186, including 159 SF arrays compared with frozen pre-correction values.
Checks cover full event identity, raw-index/flavor and eta/phi correspondence,
all 13 tight WPs, `isLoose`, vector lengths, descending corrected-pT order,
correction-ratio identity and SF permutation. All six have zero checked
anomalous events; largest MC ratio residual is below `5.961e-8`.
Rescued ee entry 174 and μμ entry 5 are present; wrong singleton acceptances
ee entry 8 and μμ entry 102 are absent. The μμ entry-127 control remains
rejected. DATA singletons are permitted by its loose chain.

The snapshot demonstration used an immutable native ROOT checkpoint before
the configured callback's chunked reads, and its wildcard nominal columns
with existing serialization exclusions. It did not qualify auxiliary ROOT
metadata copying, remote publication or full systematic output. Six
successful producer runs total 44.40 minutes; this excludes failed attempts
and later audits/replays.

### Test inventory and execution qualifications

| Check / location | Recorded result and what it tests |
| --- | --- |
| [Historical replay contracts][historical-tests] on `7843a7f` | Recorded electron-study run: **one identity test passed; two tests failed** because the fixture resolved the workspace one parent too high, to `/uscms_data/d3/mwadud/private/mkShapesRDF/` rather than `mkShapesRDF_devel/`. Equivalent pinned-pickle, six-file identity, category and helper assertions passed at the actual workspace path. No test or producer change suppressed the failures. These checks require retained artifacts and are not fresh producer regression evidence. |
| [Local producer diagnostic checks][local-ledger-tests] on `7843a7f` | Pinned manifest/hash/catalog/PFN/range, clean compatible source tree, fresh output, normalization receipt algebra, entry/key ledger, and synthetic native ROOT unsigned-identity preservation. That native ROOT Snapshot check is distinct from the later framework callback's list conversion. |
| [Original Coffea local runs][coffea-run-note] | Six one-CPU runs, 48 partitions of 20,000 entries, **960,000 entries total**; all six exited zero. Each MC run reported one Awkward invalid-divide warning; DATA reported no warnings/errors. Partition membership, six receipt/hash sets, accumulator contents, MC moments and row checksums were verified. This is the original bounded diagnostic, not a later full production pass. |
| [Published paired-result reducers][coffea-reducer-guide] | After replacing task-owned path constants with explicit arguments, all four published payloads reproduced **byte for byte by SHA-256**: stage comparison, weight comparison, tight-muon audit and decompressed mismatch JSONL. This reran retained-trace reductions only. |
| [Electron evidence validation][electron-report] | Reopened counterfactual ROOT integrals matched selected-row sums; disjoint recovery and signed MC yield closure passed. Evidence/replay receipt hashes were checked against `electron-evidence-manifest.json`; four diagnostic Python files passed Black checks. This accompanies the historical pytest failures above, not a claim that the whole historical suite passed. |
| [Selection and gate regressions][selection-tests] on repair branch | **Five real-ROOT tests passed:** all tight vectors/`isLoose` follow retention; raw/core/VetoLepton fields survive snapshot; short collections rejected before evaluating flags; every configured WP remains in both slots; strict `testrecipes` boundary and retained-gate behavior. |
| [Correction association regressions][scale-tests] on repair branch | **Four real-ROOT synthetic cases passed:** DATA/MC × normal/reversed column iteration, forced three-cycle pT permutation, ID/index/coordinate/loose/SF/ratio mapping, pT/SF variations and MET response. Calibration payloads/formulas and random draws are outside this synthetic check. |
| [Snapshot identity boundary][identity-tests] on repair branch | Signed two's-complement bridge passed; native unsigned ≥2^63 conversion is a **strict expected failure**, not a fixed boundary. |
| Original-versus-repaired regression control | Both repair regression suites fail on unrepaired modules; they distinguish the defect from a passing identity-only example. |
| Real output audits and replay reopening | Six independent serialized-array audits and exact accepted-key closure; replay histograms/variances including flows agree with selected ledgers. These are separate from synthetic tests. |

Earlier failed repair attempts are documented in the [executed report][executed-report]:
incorrect absolute LumiMask substitution, many-column Cache compilation/memory
exhaustion, and a narrow snapshot lacking TrigObj fields required for replay.
Final runs used the framework-relative mask, native checkpoint and configured
wildcard persistence; no physics module was bypassed. ROOT/XRootD teardown
could stall after files closed, so the task-local CLI exits after writing
and a basic reopen/count. **Independent invariant reopening establishes
acceptance, not the CLI exit alone.**

The first original complete-gate pass used a float squared-weight reducer;
the later script casts to double. Outcome sums were already accumulated in
Python double precision, and independent float64 uncut-weight reads verify
the input accounting. Source-tree/join/raw-index validation was strengthened
after that original pass without repeating it solely for those checks.
The README distinguishes measured first-pass results from stricter future
reproduction. This documentation update reruns no ROOT production or physics
test and introduces no new campaign measurement.

## Consequences for RunStability

This leaf consumes the stored named tight bits both in `L2TightLeading2`
and the global closest-Z builder `bestZ0IdxWithID`. Its historical
preselection requires triggers, `nLepton >= 2`, that leading-two gate and
zero horn jets. Wrong bits can reject an event or change/invalidate its Z
candidate. Removing only the gate does not repair the ID input to the pair
builder. The historical `ProductionLeptonPt` matcher also requires coherent
eta/phi correspondence with VetoLepton; the eta-only witness gives two
failed matches and gate indices `-1`. See [aliases][analysis-aliases] and
[helper][analysis-helper].

The historical electron counterfactual partitions **final Coffea-only
category events** as follows:

| Category | Tight alignment alone | Gate removal alone | Both required | Neither: historical stream ownership | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ele30 | 39 | 18 | 1 | 2 | 60 |
| Ele23–Ele12 | 37 | 16 | 1 | 2 | 56 |

These classes are disjoint; separate bit/coordinate/gate flags can overlap
and must not be summed as independent causes. The two stream-zero events
per category reflect MuonEG → Muon → EGamma priority.

The repaired replay **retains historical policy**: compiled leading-two
analysis gate, global Z arbitration, strict 35/35 GeV and 60–120 GeV cuts,
stream priority, sample/component weights and retained full-source
normalization. It does not substitute Coffea's intended selection or
normalize an individual file by its partial `genWeight` sum.

- Electron MC selected counts increase about 1.5%; signed weighted
  contributions at 1 fb^-1 increase about 1.8%.
- Muon MC counts increase about 7.6–7.7%; weighted contributions about 8.7%.
- Four fixed DATA prefixes show electron increases of 2.0–3.6% and muon
  increases of 14.5–15.0%.

Detailed categories, signed sums and decomposition are in the
[repair report](diagnostics/hww_object_associations/REPAIR_REPORT.md#bounded-runstability-replay-descriptive-downstream-result).
The IsoMu24 gain of 2,484 comprises 1,694 rescued-class selections plus a
net 790 within the pass-both class. That net change is not 790 proven one-way
recoveries or an effect attributed entirely to random draws.

The **pre-smearing gate comparison is causal**. Final historical-versus-
repaired MC yields are **descriptive**: changed acceptance shifts sequential
electron smearing, muon/shared gRandom and trigger-period draws. Common-event
random variates were not held equal. The final original baseline is actual
historical part0, not a fresh original final-kinematic snapshot; historical
dirty source and payload-byte equivalence remain unavailable. DATA corrections
are deterministic, but that historical provenance limit also applies there.

These defects are substantial contributors in the paired domain, but the
two MC files/four prefixes do not partition the published full-year
approximately 12.4% muon DATA, 2.8% electron DATA or 6.66% muon MC differences.
Coffea's central source tier, different stream coverage/ownership, deliberate
omission of the leading-two gate, category-specific eligible-pair ranking
and selected-pair TrigObj requirements remain separate choices. The
[chain audit](chain-audit.md) traces these differences. Matching old
histogram totals is not sufficient evidence of correctness.

## Reproduce the diagnostics

### Direct historical-file display, without producer execution

Start with [ROOT_INSPECTION.md](diagnostics/hww_object_associations/ROOT_INSPECTION.md)
for the simplest route. Activate the existing ROOT runtime and run its one
PyROOT command from `ZH_devel`. The script reads the actual historical
part0s, validates fixed event keys and prints indexed raw versus retained
coordinates and full named tight decisions. The copied manifest and
successful seven-event transcript are included here. This route needs remote
file access; corrections, Golden JSON, companion checkouts and compiled
analysis configuration are unnecessary for this display. It reproduces
stored-file observations; it does not repair files
or establish the exact operation in the unavailable historical dirty producer.

### Prerequisites and revision selection

Run on the supported CMS/LPC runtime with the recorded ROOT 6.38 environment,
remote-file/proxy access, CVMFS correction payloads and Golden JSON. The
[environment manifest][environment] records exact source trees, tags,
payloads and hashes. Input paths are fixed physical files; scripts check
their identities and reject substitutions. Detailed ROOT/NPZ outputs,
entry maps and the compiled pickle are **local LPC artifacts**, not files
bundled by Git. Their paths/hashes are in the receipts/results.

Use a separate clean checkout per producer revision and separate ROOT
processes. For example, from an existing repository:

```bash
git fetch origin
git worktree add --detach ../hww-original 69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0
git worktree add --detach ../hww-repair 8d940abcf429f753074121a250db3717434eb2f6
git worktree add --detach ../hww-historical 7843a7ff8680f6c9ff48b9372cc0a7784468cb6f
```

Activate the existing supported framework installation, then put the chosen
checkout first on the import path:

```bash
source /absolute/path/to/installed/mkShapesRDF/start.sh
export PYTHONPATH="$PWD:${PYTHONPATH:-}"
export PYTHONHASHSEED=0
export XRD_REQUESTTIMEOUT=30
leaf=PlotsConfigurationsRun3/ZH_4lMET/RunStability
diag="$leaf/diagnostics/hww_object_associations"
```

If no installed runtime exists, follow that revision's README and supported
`install.sh`/`install.sh --check`. A generic desktop Python environment is
not an equivalent ROOT/CMS reproduction environment.

All output directories passed to diagnostics must be **new**. Commands
below use illustrative output paths; create only their parent directory.
Do not reuse an old output or disable source/hash checks to get a run to pass.

### A. Historical selection and electron counterfactuals

In `hww-historical` at `7843a7f`, set `COFFEA` to the companion checkout
containing the pinned inputs and follow [the historical guide][historical-guide]:

```bash
python "$leaf/historical_hww_diagnostic.py" \
  --manifest "$COFFEA/docs/diagnostics/paired-2024-lowpt/inputs.json" \
  --pair-evidence "$COFFEA/docs/diagnostics/paired-2024-lowpt/parent-pair-evidence.json" \
  --role egamma_c --output-dir /absolute/new/history-egamma-c
```

Repeat for the required roles. For EGamma C/I, run each of
`--counterfactual aligned_electron_tight`, `no_leading_two_gate`, and
`aligned_electron_tight_no_gate` into separate fresh outputs. The replay
requires the retained `config_26-08-18_21_38_40.pkl`, SHA-256
`6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef`,
and its byte-checked retained helpers. Recompiling today's leaf is not a
historical replay. Outputs are `historical_histograms.root`,
`historical_rows.jsonl`, and `receipt.json`.

The local producer ledger and its tests are also on this branch; use their
recorded manifest and full-source normalization receipts. The companion
[paired report][paired-report] is the entry point for the original Coffea
comparison, not the repair runner.

### B. Original historical/live event witnesses

In `hww-original` at `69ff2dad`:

```bash
python "$diag/run.py" \
  --manifest "$diag/inputs/inputs.json" \
  --pair-evidence "$diag/inputs/parent-pair-evidence.json" \
  --output-dir /absolute/new/witnesses

python "$diag/full_mc.py" --manifest "$diag/inputs/inputs.json" \
  --role dy_ee --entry 174 --key 1 384532 2060318616
python "$diag/full_mc.py" --manifest "$diag/inputs/inputs.json" \
  --role dy_mumu --entry 127 --key 1 260002 1443526502
```

`run.py` writes `events.json`; the two `full_mc.py` commands emit stage
ledgers whose final stdout line is JSON. The original [README][original-readme]
explains the isolated correction witness and legitimate μμ rejection control.
These commands do not write a fresh full-chain HWW snapshot.

### C. Complete paired MC membership and original/aligned gate

Still in the original checkout:

```bash
python "$diag/complete_join.py" --output-dir /absolute/new/complete-join
for role in dy_ee dy_mumu; do
  python "$diag/complete_gate.py" --manifest "$diag/inputs/inputs.json" \
    --join-dir /absolute/new/complete-join \
    --role "$role" --output-dir "/absolute/new/complete-gate-$role"
done
```

This processes **complete** 158,487/222,331-entry MC files even though the
copied manifest records 80,000-entry windows for the earlier study. Check
full accepted key sets and the four gate classes, not only totals.
If reusing recorded compressed join maps, verify the [join receipt][join-receipt]
hashes; do not repeat the remote identity scan just to change prose.
`Runs` headers establish parent lineage here, not a new partial-file
normalization prescription. The chain uses retained full-source baseW
receipts; raw outcome `genWeight` sums are accounting, not Z yields.

### D. Actual repair production, original gate reference and reopen audit

In `hww-repair` at `8d940ab`, after resetting `PYTHONPATH` to this checkout:

```bash
revision=$(git rev-parse HEAD)
out=/absolute/new/repair-reproduction
mkdir "$out"
for role in egamma_c egamma_i muon_c muon_i dy_ee dy_mumu; do
  timeout 1800 python -u "$diag/repair_demo.py" \
    --role "$role" --kind repaired --stop 50000 \
    --producer-root "$PWD" --producer-revision "$revision" \
    --output-dir "$out/final-repaired-$role" \
    > "$out/production-$role.log" 2>&1 || exit $?
done
```

`--stop 50000` applies to DATA only; MC uses the complete files. The
measured producer was `9a0e9be`; evidence HEAD `8d940ab` has the same
repaired processor/include trees. The [repair README][repair-readme] owns
the complete commands for a separate original gate reference, all six
independent audits, witness extraction and both replay views. For example:

```bash
original=/absolute/path/to/hww-original
join=/absolute/path/to/verified/complete-join
PYTHONPATH="$original:$PYTHONPATH" python "$diag/repair_original_gate.py" \
  --role dy_ee --producer-root "$original" --join-dir "$join" \
  --output-dir "$out/reference-gate-dy_ee"

python "$diag/repair_audit.py" \
  --repaired-dir "$out/final-repaired-dy_ee" \
  --reference-gate-dir "$out/reference-gate-dy_ee" --join-dir "$join" \
  --output-dir "$out/audit-final-dy_ee"
```

Repeat the reference for μμ and the audit for every role; DATA audits omit
the MC reference/join arguments. Require zero checked anomalies and exact
aligned accepted keys. Output directories contain `production.json`, input
identity NPZ, native checkpoint, final role ROOT file, and MC gate ledger;
audits create their own receipts. The environment/result JSON records
paths and hashes of the actual LPC outputs under
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/hww-repair-demo-20260930/`.

For each role's repaired/historical Z views:

```bash
python "$diag/repair_replay.py" --role dy_ee \
  --production-dir "$out/final-repaired-dy_ee" \
  --output-dir "$out/replay-repaired-dy_ee"
python "$diag/repair_replay.py" --role dy_ee --historical \
  --production-dir "$out/final-repaired-dy_ee" \
  --output-dir "$out/replay-historical-dy_ee"
```

This requires the same retained compiled pickle and historical input access.
Nested historical replay receipts inherit the repaired-context
`producer_revision`; that field does **not** identify the unavailable
historical HWW producer. Input URI, parent evidence and compiled pickle
identify the historical comparison.

### E. Focused software tests

In the supported runtime, from the repair checkout run:

```bash
python -m pytest -q tests/test_processor_lepton_selection_associations.py
python -m pytest -q "$diag/tests/test_lepton_scale_association.py"
python -m pytest -q "$diag/tests/test_snapshot_identity.py"
```

Interpret the expected unsigned-ID failure explicitly. A skipped ROOT test
is not a pass of the association behavior. Synthetic checks complement,
not replace, independent fresh-output reopening.

The historical branch also contains:

```bash
python -m pytest -q "$leaf/tests/test_historical_hww_diagnostic.py" \
  "$leaf/tests/test_local_producer_diagnostic.py"
```

Its tests include workspace-specific retained paths and require those
artifacts in the documented layout; inspect the pinned tests before
relocating a checkout. The recorded historical module had one pass and two
fixture-path failures; resolve the retained workspace path and rerun rather
than treating those failures as association regressions or claiming an
all-green historical suite. They do not all run in a bare Git clone. General
RunStability leaf tests in [USAGE.MD](USAGE.MD) test the analysis contract,
not historical HWW validity or the unadopted producer repair.

### F. Rebuild the paired Coffea/HWW evidence from retained traces

In the companion checkout at `44e7ae7`, follow the
[reducer README][coffea-reducer-guide]. The original
[local-run note][coffea-run-note] records six `coffea-rs run` invocations,
the ownership index, frozen configuration/plan and partition boundaries.
The initial windows were 80,000 entries per DY file and 200,000 per DATA
file; this is distinct from the complete-file MC gate study and 50,000-entry
DATA repair demonstration above.

Retain `coffea-category-counts.json`, `rows-gzip/`, the historical replay
root's six canonical directories (`dy_ee_v4`, `dy_mumu_v1`, `muon_c_v1`,
`muon_i_v1`, `egamma_c_v1`, `egamma_i_v1`), and the producer root's two DY
`entry_ledger.json.gz` files. Redundant `dy_mumu_v2` and interrupted
`muon_c_v2` runs were not used in the published evidence. For example:

```bash
python scripts/paired_lowpt_2024/compare_outputs.py \
  --inputs docs/diagnostics/paired-2024-lowpt/inputs.json \
  --coffea-task /absolute/path/to/completed/coffea-task \
  --hww-replay-root /absolute/path/to/completed/hww-replays \
  --producer-root /absolute/path/to/completed/producer-ledgers \
  --normalization-summary docs/diagnostics/paired-2024-lowpt/full-source-normalization.json \
  --output /absolute/new/local/comparison

python scripts/paired_lowpt_2024/audit_hww_muon_mask.py \
  --inputs docs/diagnostics/paired-2024-lowpt/inputs.json \
  --mismatches /absolute/path/to/comparison/mismatched-events.jsonl \
  --hww-replay-root /absolute/path/to/completed/hww-replays \
  --output /absolute/new/local/hww-tight-mask-audit.json
```

The second command uses the supported mkShapesRDF `start.sh` runtime and
retained historical Muon C/I files. The comparison checks original
source-entry coverage and typed event keys before writing results.
The same directory contains `audit_hww_electron_mask.py`,
`summarize_electron_counterfactuals.py` and
`analyze_electron_mc_migrations.py`; use their `--help` and the reducer
README for the exact input/output arguments. They reconstruct historical
electron decisions, reduce the opt-in historical replays and join DY→ee
migrations to the retained producer ledger. The
[electron evidence manifest][electron-evidence-manifest] hashes these
additional reducers, compact results and local replay receipts without
replacing the first study's manifest. These reducers neither reread central
NanoAOD nor repair a producer.

## Remaining work and proposed changes

| Action / proposal | Present status and acceptance requirement |
| --- | --- |
| Adopt shared retention/gate/reordering repairs | Concrete implementation and bounded evidence exist on the repair branch. Review/integrate into the production branch; include all genuine per-lepton families and their required variations. Documentation integration alone is insufficient. |
| Adopt the separate DATA JEC configuration correction | Demonstrated nominal DATA blocker resolved on repair branch. Verify the chosen campaign's payload-supported sources; preserve nominal corrections and cleaning. |
| Determine affected production/consumer inventory | Trace actual executable revisions, dirty-state provenance and recipes for relevant 2022–2024 samples/channels. Audit retained raw-index/coordinate/ID invariants and producer skim behavior. No universal defect fraction or channel correction follows from DY. |
| Recover exact historical causes where possible | Historical eta-only mismatch and shortened wrong tight vectors are directly observed; precise dirty producer operations/payload equality remain unresolved. Do not claim that a current-source mechanism identifies those exact old lines. |
| Qualify ordinary corrected production | Validate required systematic outputs, auxiliary metadata, normal Snapshot path and publication in addition to nominal Events associations. Exercise filtering and real nonidentity permutations; preserve full-width unique event identity. |
| Regenerate affected HWWNano and dependent analyses | Start from parent NanoAOD for complete corrected MC acceptance. Recompute downstream histograms/observables with intended analysis policies. HWW-only alias changes, skim renormalization or replotting cannot restore missing events. |
| Audit conditional JES variation index composition | Establish input-order prerequisite and index/coordinate mismatch on real varied branches before prescribing the corrected mapping. No nominal cleaning or yield patch is justified by this conditional concern. |
| Repair native unsigned Snapshot boundary | Preserve explicit uint64 typing or a reviewed lossless representation through serialization; require actual high-bit round-trip tests of the ordinary callback. Diagnostic signed bridge is not production adoption. |
| Review `isLoose` semantics / allowed gate WPs if desired | Policy questions separate from association repair. The demonstrated repair intentionally preserves the active OR semantics and permissive `testrecipes` participation. Changing either requires its own selection decision and validation. |
| Attribute full-year framework differences | Requires campaign-wide matched coverage/ownership and intended-policy comparisons; control common-event random variates for causal final-MC attribution. Local repair percentages are not full-year correction factors. |

Affected products fail the requirements of lepton-ID-dependent analyses even
without every event or branch being wrong. The established scope must be
kept explicit, but uncertainty about other campaigns does not postpone the
validity conclusion for the products with demonstrated broken associations
or acceptance. Preserve the original NanoAOD and the pinned diagnostic
evidence while adopting and qualifying the shared producer repair.

[zh-inspected]: https://github.com/TheQuantiser/mkShapesRDF/commit/d036a25754ff1a922a908008ae1d6c0e763cb7c3
[electron-commit]: https://github.com/TheQuantiser/mkShapesRDF/commit/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f
[original-commit]: https://github.com/TheQuantiser/mkShapesRDF/commit/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0
[repair-evidence-commit]: https://github.com/TheQuantiser/mkShapesRDF/commit/8d940abcf429f753074121a250db3717434eb2f6
[repair-producer-commit]: https://github.com/TheQuantiser/mkShapesRDF/commit/9a0e9be35c27e2907e6201460d0a5de58a091651
[historical-additions]: https://github.com/TheQuantiser/mkShapesRDF/commit/fa1a1e0d2e6cbbbe7b1ce6c50081dc61f3b372ef
[historical-mask-doc]: https://github.com/TheQuantiser/mkShapesRDF/commit/2fd798f6358f7093bdc166de33a40b6c8d1354a9
[witness-commit]: https://github.com/TheQuantiser/mkShapesRDF/commit/bf75c7f50245891ddad20aa3bced35057148fca2
[jec-commit]: https://github.com/TheQuantiser/mkShapesRDF/commit/68a082c29b08d85978e9af33e9d194610b19f8a6
[initial-issues-commit]: https://github.com/TheQuantiser/mkShapesRDF/commit/4e6793fd315807b7db7823d2612dc1ad705f55bd
[corrected-issues-commit]: https://github.com/TheQuantiser/mkShapesRDF/commit/c0649272854fdd03812af19b6677fc82d6855091
[repair-doc-integration]: https://github.com/TheQuantiser/mkShapesRDF/commit/a3b160a5952e4198e61060b17be64da5b4c445e3
[coffea-paired-commit]: https://github.com/TheQuantiser/ZH4l_coffea/commit/062cfea35ba6a6395b926854228efc94753d02cb
[coffea-electron-commit]: https://github.com/TheQuantiser/ZH4l_coffea/commit/a5bba58ed10e53df463fec9bf23ca8c002df909e
[coffea-evidence-commit]: https://github.com/TheQuantiser/ZH4l_coffea/commit/44e7ae7b98a894f79c647ae637791feded3ea381
[paired-report]: https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/2024-paired-lowpt-event-diagnostic-20260929.md
[electron-report]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/2024-paired-lowpt-electron-diagnostic-20260929.md
[coffea-evidence]: https://github.com/TheQuantiser/ZH4l_coffea/tree/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt
[coffea-reducer-guide]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/scripts/paired_lowpt_2024/README.md
[coffea-run-note]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/coffea-diagnostic-note.md
[electron-evidence-manifest]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-evidence-manifest.json
[muon-audit]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/hww-tight-mask-audit.json
[electron-audit]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-hww-mask-audit.json
[electron-counterfactual]: https://github.com/TheQuantiser/ZH4l_coffea/blob/44e7ae7b98a894f79c647ae637791feded3ea381/docs/diagnostics/paired-2024-lowpt/electron-counterfactual-summary.json
[historical-guide]: https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/HISTORICAL_HWW_DIAGNOSTIC.md
[historical-tests]: https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/tests/test_historical_hww_diagnostic.py
[local-ledger-tests]: https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/tests/test_local_producer_diagnostic.py
[original-readme]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/README.md
[repair-readme]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/README.md#repair-demonstration-on-this-branch
[executed-report]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/REPAIR_REPORT.md
[observations]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/observed-summary.json
[complete-results]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/complete-two-file-summary.json
[join-receipt]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/complete-join-receipt.json
[manifest]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/inputs.json
[pair-evidence]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/parent-pair-evidence.json
[environment]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-environment.json
[repair-results]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-results.json
[repair-witnesses]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-witnesses.json
[original-selection]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/LeptonSel.py
[repaired-selection]: https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/modules/LeptonSel.py
[original-gate]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/L2TightSelection.py
[repaired-gate]: https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/modules/L2TightSelection.py
[original-scale]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/LeptonScaleSmearing.py
[repaired-scale]: https://github.com/TheQuantiser/mkShapesRDF/blob/9a0e9be35c27e2907e6201460d0a5de58a091651/mkShapesRDF/processor/modules/LeptonScaleSmearing.py
[original-steps]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/framework/Steps_cfg.py
[mrdf-source]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/framework/mRDF.py
[jet-cleaning-source]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/JetSelMask.py
[jme-source]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/JMECalculator.py
[analysis-aliases]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/aliases.py
[analysis-helper]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/macros/run_stability_helpers.cc
[selection-tests]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/tests/test_processor_lepton_selection_associations.py
[scale-tests]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/tests/test_lepton_scale_association.py
[identity-tests]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/tests/test_snapshot_identity.py
