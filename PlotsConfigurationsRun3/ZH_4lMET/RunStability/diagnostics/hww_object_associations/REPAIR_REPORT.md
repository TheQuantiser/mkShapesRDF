# HWWNano lepton-association repair: what was measured and how

**Updated 2026-10-01.** This report explains the historical defects, the
bounded producer repair, and the change in the RunStability Z selection.
The affected 2024 HWWNano products have incorrect retained lepton IDs or
coordinates and are invalid inputs for analyses that depend on those
associations.

There are three different measurements in this report:

| Measurement | Question answered | What is counted or checked |
| --- | --- | --- |
| Historical object inspection | Do stored properties describe the lepton named by its raw index? | Raw inputs, stored decisions and coordinates in specific historical events. |
| Controlled MC production-gate comparison | Which events does the original gate reject or accept incorrectly? | Event-key sets before smearing, with the same inputs and WP policy. |
| Historical-versus-repaired Z replay | How does the final analysis result change on these fixed inputs? | Selected events and their weights after the same frozen analysis selection. |

**DATA and MC differ at production.** The identified retention and reorder
bugs corrupt properties in both. In the investigated DATA recipe, these
bugs do not themselves discard events before writing. MC additionally has
a production `l2tight` gate that consumes the wrong decisions and can
discard valid events or accept invalid ones.

**The repair remains on a separate branch.** Six fresh nominal Events
outputs were produced and independently checked. The producer changes have
not been integrated into `ZH_devel`; this update revises documentation.

## Contents

- [Conclusions and production status](#conclusions-and-production-status)
- [Evidence scope](#evidence-scope)
- [Direct evidence in historical ntuples](#direct-evidence-in-historical-ntuples)
- [Complete-file MC acceptance: causal gate result](#complete-file-mc-acceptance-causal-gate-result)
- [Fresh snapshots and repair validation](#fresh-snapshots-and-repair-validation)
- [Bounded RunStability replay: descriptive downstream result](#bounded-runstability-replay-descriptive-downstream-result)
- [Shared producer changes](#shared-producer-changes)
- [What remains unresolved](#what-remains-unresolved)
- [Required follow-up for analysis use](#required-follow-up-for-analysis-use)
- [Evidence and reproduction details](#evidence-and-reproduction-details)

## Conclusions and production status

The wrong historical ID and coordinate associations are directly observed.
The controlled MC gate comparison establishes erroneous rejection and
acceptance in the available original implementation. Independent reopening
establishes correct checked associations in the six repaired nominal
outputs.

The final Z replay finds local increases of about **2.0–3.6% in electron
DATA**, **14.5–15.0% in muon DATA**, and **1.8% / 8.7% in the ee / μμ MC
weighted contributions**. These are changes in a bounded analysis result,
not defect fractions or correction factors for full campaigns.

### Which source contains the repair?

| Source | Purpose |
| --- | --- |
| `demo/2024-hwwnano-object-associations`, pinned at [`69ff2dad`][original-revision] | Original producer, historical witnesses and complete-file gate reference. |
| `fix-demo/2024-hwwnano-object-associations`, measured at [`9a0e9be`][repaired-revision] | Repaired producer used to write the six outputs. |
| Repair branch evidence at [`8d940ab`][evidence-revision] | Scripts, tests, reports and numerical evidence for the executed demonstration. |
| `ZH_devel`, checked at [`44bd978`][inspected-zh-revision] before this update | Documentation. The four relevant producer files still have the original blobs. |

The four checked files are `LeptonSel.py`, `L2TightSelection.py`,
`LeptonScaleSmearing.py` and `Steps_cfg.py`. The diagnostic scripts and
JSON evidence linked here remain on the repair branch; they are not
installed in this `ZH_devel` directory. Its [README][repair-readme] gives
the executable reproduction commands. The
[consolidated issues guide](../../KNOWN_HWWNANO_ISSUES.md) maps the earlier
branches, tests and investigations.

## Evidence scope

The repair used six fixed central NanoAOD files:

| Role | Central source range | Meaning |
| --- | --- | --- |
| EGamma C | `[0,50000)` | First 50,000 entries of one period-C EGamma0 file. |
| EGamma I | `[0,50000)` | First 50,000 entries of one period-I EGamma0 file. |
| Muon C | `[0,50000)` | First 50,000 entries of one period-C Muon0 file. |
| Muon I | `[0,50000)` | First 50,000 entries of one period-I Muon0 file. |
| DY→ee | `[0,158487)` | Complete individual central MC file. |
| DY→μμ | `[0,222331)` | Complete individual central MC file. |

Ranges are zero-based and half-open. They describe **central Events
entries**, not entries in a skimmed HWW output. C and I are DATA periods;
neither row represents all files from that period. A complete MC file is
still only part of its full dataset.

The [input manifest][inputs] and [environment record][environment] identify
the exact central/HWW file pairs, UUIDs, payloads and hashes. The
[results][results] record the executed ranges. Earlier studies used
200,000-entry DATA and 80,000-entry MC prefixes; their counts must not be
mixed with this repair demonstration.

The relevant production order is:

```text
DATA:
  central selection → luminosity mask → LeptonMaker
  → LeptonSel [retention defect]
  → jet ID/corrections/JetSelMask
  → leptonScale_data [reorder defect]
  → kinematics/triggers/DATA formulas → Snapshot → analysis

MC:
  central selection → LeptonMaker → LeptonSel [retention defect]
  → jet ID/corrections/JetSelMask
  → generator quantities/matching/normalization/triggers/SFs/weights/formulas
  → l2tight [consumes stale decisions]
  → leptonScale_mc [reorder defect]
  → kinematics → Snapshot → analysis
```

The configured DATA chain has no production `l2tight`. Its `LeptonSel`
event requirement is evaluated before inconsistent retention, and the
modules after the correction reorder calculate columns without applying
an event filter. A wrong stored DATA ID can reject an existing event in
the analysis; it does not itself remove that event from the ntuple.
Ordinary production cuts are separate from these defects.

## Direct evidence in historical ntuples

### Tight decisions are attached to the wrong retained objects

At retained position `i`, a muon tight bit must describe the raw muon
named by `Lepton_muonIdx[i]`; the electron rule uses
`Lepton_electronIdx[i]`. Matching vector lengths alone is insufficient.

The following events were read from actual historical paired `part0`
files. The complete named WPs were recomputed from raw inputs **inside the
same HWW records**, not inferred from a single primitive ID flag.

| DATA witness | Retained raw indices | Expected named tight bits | Stored named tight bits |
| --- | --- | --- | --- |
| Muon C: central entry 234, HWW entry 65; key `(379416,147,131724611)` | Muons `[1,2]` | `[true,true]` | **`[false,true]`** |
| EGamma C: central entry 20774, HWW entry 991; key `(379729,907,1396820419)` | Electrons `[0,1]` | `[true,true]` | **`[false,true]`** |

The named columns are:

- `Lepton_isTightMuon_cut_TightID_pfIsoTight_HWW_tthmva_67`
- `Lepton_isTightElectron_mvaWinter22V2Iso_WP90_tthMVA_Run3`

The muon event exposes the positional error:

```text
Before retention:
  raw muon indices   [0,     1,    2]
  named tight bits   [false, true, true]

After retaining raw muons 1 and 2:
  correct bits       [true, true]
  historical bits    [false,true]  ← first bit describes removed muon 0
```

The available original `LeptonSel` computes decisions before retention,
then filters only pT, eta, phi, pdgId and the two raw-index arrays. It omits
the tight vectors and `isLoose`. The core fields remain mutually aligned
at this step; the decisions no longer follow them. Raw Electron/Muon and
prefilter VetoLepton collections are preserved.

In clean original live runs, the omitted decision vectors remain longer
than the retained collection. Some historical vectors have retained length
but the wrong prefix. The historical producer's dirty worktree is
unavailable, so its exact shortening/serialization operation is unresolved.

The [observed witnesses][observations], [muon audit][muon-audit] and
[electron audit][electron-audit] record the inputs and comparisons. In the
earlier paired C/I discrepancy class, 508 Coffea-only IsoMu24 events had
a false historical leading-two decision although both selected raw HWW
muons passed. Of those, 503 had wrong stored retained bits and 502 also
matched the prefilter prefix. These are counts conditioned on that
discrepancy class, not a file-wide defect fraction.

### Electron coordinates can disagree with their raw indices

EGamma I central entry 27025, HWW entry 1936, key
`(386509,159,333332716)`, contains:

| Field | Expected for stored `electronIdx=[0,1]` | Historical value |
| --- | --- | --- |
| `Lepton_eta` | `[-0.93359375,-2.05712890625]` | **`[-2.05712890625,-0.93359375]`** |
| `Lepton_phi` | `[-1.22802734375,1.9677734375]` | Same as expected |
| Named tight bits | `[true,true]` | Same as expected |

Eta is exchanged between the two electrons while phi and tight bits agree
with the stored indices. The historical analysis's retained-to-VetoLepton
coordinate matcher consequently fails for both electrons: both gate
indices become `-1`, and its leading-two analysis requirement fails.
Coordinates can also affect reconstructed pair kinematics.

Entry 46209, key `(386509,735,1539152813)`, has both wrong tight bits and
an eta/index mismatch. These defects overlap; their event counts cannot
be added as independent losses.

A live original correction run of entry 27025 exercised a real pT swap
and produced a **phi/index** mismatch under the recorded column order.
It proves the available source's reorder defect, but does not reproduce
the historical eta-only pattern. Its exact historical cause remains
unresolved. The shared reorder loop can affect electrons or muons;
correct coordinates in a muon witness do not establish muon immunity.
The electron supercluster-eta calculation is a local correction input,
not an overwrite of `Lepton_eta`.

## Complete-file MC acceptance: causal gate result

### The failure happens before the analysis can see the event

The original production `l2tight` reads positions 0 and 1 of the decision
vectors, ORs **all configured electron and muon WPs at each position**, and
ANDs the two results. It has no explicit retained-size ≥ 2 guard.

A removed object's decision can therefore reject a valid retained pair or
supply a passing second slot to an event with only one retained lepton.
This happens before smearing and writing.

The gate includes `Electron_testrecipes`, whose original cut is strict
raw pT > 10 GeV. That permissive WP remains in the repair. The production
all-WP gate and the analysis's specific named-WP requirements are different
selections.

### Controlled comparison on the two complete parent files

The original diagnostic runs the configured modules up to the gate and
stops before smearing. An independent aligned reference maps all seven
electron and six muon WP vectors through retained raw indices, requires
two retained leptons, then applies the **same all-WP predicate**.

Both decisions use the same pre-gate events and raw WPs. Thus the controlled
difference isolates association and retained-slot handling, rather than
changed WP definitions or random smearing.

| Gate accounting | DY→ee | DY→μμ |
| --- | ---: | ---: |
| Events reaching the gate | 74,938 | 116,303 |
| Pass original and aligned | 42,732 | 83,368 |
| Original rejects; aligned passes (**rescued**) | **606** | **5,914** |
| Original passes; aligned rejects (**removed**) | **25,689** | **5,324** |
| Reject both | 5,911 | 21,697 |
| Original accepted / historical paired total | **68,421** | **88,692** |
| Aligned accepted / repaired final total | **43,338** | **89,282** |

The four outcome rows partition the gate input. Original acceptance is
pass-both plus removed; aligned acceptance is pass-both plus rescued.

The complete key join verifies full `(run,luminosityBlock,event)`
identities, UUIDs, parent pairing and uniqueness. Original accepted keys
equal actual historical paired `part0` membership exactly: every rescued
key is absent there, and every removed key is present. This verifies those
files' membership; it does not recover the unavailable historical source
or prove absence from every HWW part.

The repaired output has exactly the aligned accepted keys, with no later
event losses and no fewer-than-two-lepton survivors. The audit also matches
pre-gate key sets, gate outcomes and `genWeight` to the original reference.
It does **not** compare all original/repaired pre-gate collection arrays;
the saved result explicitly says `pregate_collection_comparison="not assessed"`.

### Losses and false acceptances must both be counted

Removed events include:

| Historical retained multiplicity | DY→ee removed | DY→μμ removed |
| --- | ---: | ---: |
| One lepton | 25,638 | 5,269 |
| At least two leptons | 51 | 55 |
| Total | 25,689 | 5,324 |

Net output changes are **−25,083 ee** and **+590 μμ**, but these hide
opposing acceptance changes. They are not changes in selected Z yields.

DY→μμ entry 127, key `(1,260002,1443526502)`, fails both gates and is
absent from both outputs. It is a legitimate rejection control. Recovering
erroneously rejected MC requires parent NanoAOD; changing aliases on the
retained HWW file cannot restore absent events.

[Complete original results][complete-results] and [repair results][results]
retain the exact accounting and key comparisons.

## Fresh snapshots and repair validation

### Executed chains and stage counts

The repaired producer ran all configured event-producing modules and the
actual Snapshot callback. An immutable native ROOT checkpoint computed
the columns once before the callback's 10,000-event chunk reads.

Nominal wildcard persistence kept the existing exclusions
(`BeamSpot_type`, `Electron_seediEtaOriX`, `Photon_seediEtaOriX`).
No physics module, nominal JEC or cleaning was bypassed. Auxiliary ROOT
metadata copying, remote stage-out and full systematic persistence were
outside this local nominal **Events** demonstration.

| Stage | EGamma C | EGamma I | Muon C | Muon I | DY→ee | DY→μμ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Input Events | 50,000 | 50,000 | 50,000 | 50,000 | 158,487 | 222,331 |
| Chain raw multiplicity | 15,896 | 16,431 | 30,305 | 30,580 | 94,106 | 129,548 |
| Golden mask | 13,341 | 16,431 | 30,305 | 30,580 | — | — |
| LeptonMaker | 12,493 | 14,814 | 25,497 | 26,220 | 93,059 | 127,633 |
| LeptonSel | 3,353 | 3,782 | 12,619 | 12,176 | 78,696 | 121,809 |
| JetSelMask / MC pre-gate | 3,189 | 3,590 | 11,927 | 11,447 | 74,938 | 116,303 |
| Repaired l2tight | — | — | — | — | 43,338 | 89,282 |
| Reopened final Events | **3,189** | **3,590** | **11,927** | **11,447** | **43,338** | **89,282** |
| Events with correction-induced reordering | 8 | 15 | 2 | 7 | **1,419** | **978** |
| Successful producer seconds | 114.95 | 118.46 | 178.12 | 181.30 | 748.66 | 1,322.71 |

Event counts are those remaining after each named stage. Dashes mean the
step is absent or inapplicable, not zero. The reordering row counts events
whose lepton order changed, not events rejected or failing an audit.

Successful producer time totals **44.40 minutes**, excluding failed
attempts and later audits/replays. The original gate reference took
83.59 s / 110.03 s. These are measured run times, not campaign wall time.

### What independent reopening checked

The [auditor][repair-audit] read the written ROOT files and compared their
objects against raw indices, prefilter decisions and frozen pre-correction
arrays. It checked 21 flat per-lepton arrays per DATA output and 186 per MC
output, including 159 MC SF arrays.

All six outputs had **zero checked anomalous events** for:

- Full event identity, uniqueness and source-entry mapping.
- Flavor/raw-index correspondence, eta/phi, array lengths and descending corrected pT.
- All 13 tight-WP vectors and `isLoose`.
- Correction ratios and the permutation of frozen MC SF arrays.

The maximum MC correction-ratio residual was below `5.961e-8`. Real
reorderings test the repair where the original defect becomes visible.
These checks establish associations, not an independent physics validation
of every calibration, WP or systematic formula.

### Reopened witnesses

| Role / central entry | Full event key | Repaired observation |
| --- | --- | --- |
| Muon C / 234 | `(379416,147,131724611)` | Tight bits and coordinates follow both retained muons. |
| EGamma C / 20774 | `(379729,907,1396820419)` | Tight bits follow both retained electrons. |
| EGamma I / 27025 | `(386509,159,333332716)` | Eta and phi follow electronIdx. |
| EGamma I / 46209 | `(386509,735,1539152813)` | ID and coordinate associations pass. |
| DY→ee / 174 | `(1,384532,2060318616)` | Rescued event is written with two leptons; absent from historical paired part0. |
| DY→μμ / 5 | `(1,260002,1443525631)` | Rescued event is written with two leptons; absent from historical paired part0. |
| DY→ee / 8 | `(1,384532,2060317109)` | Old singleton acceptance is removed. |
| DY→μμ / 102 | `(1,260002,1443526295)` | Old singleton acceptance is removed. |

The [witness artifact][repair-witnesses] records raw, maker, retained,
pre-correction and serialized arrays. Correct repaired eta proves the new
output invariant; it does not identify the exact old eta-only operation.

## Bounded RunStability replay: descriptive downstream result

**These tables count events after the final Z analysis selection, not all
events written to HWWNano.** The replay applies the same frozen historical
analysis to actual historical outputs and newly repaired outputs.

### Step 1: choose the input domain and the two views

The domain is the six central ranges in [Evidence scope](#evidence-scope).
The two views are:

| View | Analysis input |
| --- | --- |
| Historical | Actual previously produced paired HWW `part0.root`. |
| Repaired | Fresh repaired nominal HWW output from the chosen central range. |

The historical baseline is not a newly produced unrepaired final file.
The separate original producer reference stops at the MC gate.

[repair_replay.py][repair-replay] loads `production.json` and the saved
`input-identity.npz`, builds full central event keys, and restricts each
HWW view to that key set. For DATA this means the keys from **central
entries 0–49,999**, not the first 50,000 skimmed HWW entries. MC uses keys
from the complete individual central file.

The two views have the same parent domain; their surviving event sets can
differ. The script verifies input identity, manifest and producer trees.

### Step 2: apply the same frozen analysis selection

The replay loads the retained compiled pickle, SHA-256
`6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef`,
through the [pinned historical runner][historical-runner]. For the repaired
view it replaces the sample's input URI. Historical aliases, cuts, DATA
stream priorities and component weights remain unchanged.

Selection proceeds through:

1. Historical aggregate trigger OR, at least two leptons, the historical **analysis** leading-two tight requirement, zero horn jets and nonzero weight.
2. The global Z builder: construct opposite-sign, same-flavor pairs passing the configured IDs and choose the candidate closest to the Z across both flavors.
3. The DY selection: valid candidate, the retained construction checks, strict **60 < mℓℓ < 120 GeV**, and strict **pT > 35 GeV for each selected lepton**.
4. The category's selected-Z flavor and event HLT bit.

The construction includes the historical mass > 30 GeV and selected-lepton
pT > 10 GeV checks; the final mass/pT requirements are tighter.
The preselection also retains applicable event-quality and DATA
stream/component rules through the historical weights.

The production MC `l2tight` and the downstream analysis leading-two gate
are different operations. This replay preserves the latter; it does not
remove it to recover more events.

| Table label | Event HLT bit | Required selected Z flavor |
| --- | --- | --- |
| Ele30 | `HLT_Ele30_WPTight_Gsf` | ee |
| Ele23–Ele12 | `HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL` | ee |
| IsoMu24 | `HLT_IsoMu24` | μμ |
| Mu17–Mu8 | `HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8` | μμ |

Trigger names do not replace the offline 35/35 GeV cuts. These historical
categories use event HLT bits, without Coffea's selected-pair TrigObj
matching requirement. The replay is an HWW-versus-repaired-HWW comparison,
not a substitution of Coffea selection. See the
[chain audit](../../chain-audit.md) for the policy differences.

### Step 3: count selected DATA events

For each category, the script collects the selected event rows:

```python
N = len(selected_rows)
delta_N = N_repaired - N_historical
percent_change = 100 * delta_N / N_historical
```

| DATA column | Meaning |
| --- | --- |
| DATA prefix / category | Fixed input file/prefix and selected trigger/flavor category. |
| Historical selected | Events passing the full selection on historical HWW properties. |
| Repaired selected | Events passing the same selection on repaired HWW properties. |
| ΔN | Repaired minus historical count. |
| ΔN / historical | Percentage difference relative to the historical count. |

### Measured local changes

#### DATA: selected counts from four 50,000-entry central prefixes

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

Each EGamma row counts selected ee events; each Muon row counts selected
μμ events. C/I specifies the one period-specific input file.

For example, EGamma C / Ele30 gives `208 − 204 = 4`, then
`100 × 4 / 204 = 1.96%`. Muon C / IsoMu24 gives `604 − 525 = 79`,
then `100 × 79 / 525 = 15.05%`.

These are **net** changes. Subtracting totals does not count all one-way
entries and exits. The DATA gain is a change in analysis selection, not
evidence that these bugs previously deleted the gained events at
production. Selected DATA weights are one here, so `sumw = sumw2 = N`.

The event populations are much smaller than the input or output totals:

```text
EGamma C:
  50,000 central events → 3,189 repaired HWW events → 208 Ele30 Z selections
```

### Step 4: count and weight selected MC events

MC reports both the number of selected simulated events and their signed
weighted contribution.

| MC column | Meaning |
| --- | --- |
| MC / category | DY flavor/sample and selected trigger/flavor category. |
| Historical N | Number of selected events from historical HWW. |
| Repaired N | Number of selected events from repaired HWW. |
| ΔN / historical | `100 × (N_repaired − N_historical) / N_historical`. |
| Historical Σw at 1 fb⁻¹ | Historical selected weight sum at the stated luminosity projection. |
| Repaired Σw at 1 fb⁻¹ | Repaired selected weight sum at the same projection. |
| ΔΣw / historical | `100 × (sumw_repaired − sumw_historical) / sumw_historical`. |

#### MC: complete individual DY files, selected counts and signed weights

| MC / category | Historical N | Repaired N | ΔN / historical | Historical Σw at 1 fb⁻¹ | Repaired Σw at 1 fb⁻¹ | ΔΣw / historical |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ee / Ele30 | 15,033 | 15,261 | +1.52% | 59.565510 | 60.618720 | +1.77% |
| ee / Ele23–Ele12 | 13,774 | 13,982 | +1.51% | 54.403805 | 55.396279 | +1.82% |
| μμ / IsoMu24 | 32,559 | 35,043 | +7.63% | 137.409340 | 149.380820 | +8.71% |
| μμ / Mu17–Mu8 | 31,373 | 33,782 | +7.68% | 132.131206 | 143.675053 | +8.74% |

The ee rows use the 158,487-entry DY→ee file and select ee Z candidates.
The μμ rows use the 222,331-entry DY→μμ file and select μμ candidates.
Their net count changes are **+228, +208, +2,484 and +2,409** in table order.

#### Where the MC weight comes from

The preserved component weight uses:

```text
XSWeight × METFilter_Common × puWeight × SelectedLeptonSF_Z × TriggerSF_Z
XSWeight = baseW × genWeight
```

| Factor | Purpose |
| --- | --- |
| baseW | Retained full-source cross-section normalization. |
| genWeight | Generator weight, including its sign. |
| METFilter_Common | Event-quality factor. |
| puWeight | Pileup correction. |
| SelectedLeptonSF_Z | Lepton SF product for the selected Z pair. |
| TriggerSF_Z | Historical trigger correction evaluated on the selected pair. |

The compiled analysis uses **109.08 fb⁻¹**. The reducer divides each selected
MC row weight by that luminosity, then sums:

```python
weights = [row["weight"] / config["lumi"] for row in rows]
events = len(rows)
sumw = sum(weights)
sumw2 = sum(w * w for w in weights)
```

Thus `60.618720` is **this one DY→ee file's selected contribution at
1 fb⁻¹**, using the existing full-source baseW. It is neither a count of
60 simulated events nor the prediction from the complete DY dataset.
No new Runs scan, selected-event normalization or partial-file denominator
was introduced.

Weights vary between events and can be negative. Therefore the count and
weight percentages need not agree. For μμ / IsoMu24:

```text
Count:   35,043 − 32,559 = 2,484                 → +7.63%
Weight: 149.3808198634 − 137.4093404058 = 11.9714794576 → +8.71%
```

Percentages use the unrounded JSON values; displayed sums are rounded.

#### What Σw² means

The repaired values below correspond to the four MC rows in table order:

| MC / category | Repaired Σw² at the same 1 fb⁻¹ projection |
| --- | ---: |
| ee / Ele30 | 0.618482 |
| ee / Ele23–Ele12 | 0.562286 |
| μμ / IsoMu24 | 1.674378 |
| μμ / Mu17–Mu8 | 1.613938 |

Σw² means **sum of squared individual weights**, `sum(w*w)`, not the
square of the total weight sum. It is the weighted histogram variance
contribution. Exact signed sums, squared sums and class contributions are
in [repair-results.json][results].

### Step 5: check the ledgers against the ROOT histograms

Each view/category produces selected rows and a Z-mass histogram. The local
replay directory contains:

- `selected-events.jsonl`: category, full key, source entry, weight, Z mass and producer-outcome label.
- `z-mass.root`: the category histograms.
- `replay.json`: counts, weight sums, provenance and artifact hashes.

The reducer obtains N, Σw and Σw² from the selected rows. Independent ROOT
reopening checks histogram contents and variances, including flows,
against those rows. MC comparisons restore factors of **109.08** and
**109.08²** because the ROOT histograms retain the original analysis
luminosity while the summary is at 1 fb⁻¹.

Each replay used one RDF graph. Key checks reject duplicates within a
category and verify source-entry and producer-outcome mapping.

**Categories overlap.** One event can pass both single- and double-lepton
trigger rows. Do not add those rows to claim a unique-event count.

#### Reproduce one paired comparison from the saved output

From the pinned repair checkout, activate the supported ROOT runtime as in
the [repair README][repair-readme]. The retained compiled pickle and
historical input must be accessible. For example:

```bash
diag=PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations
production=/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/hww-repair-demo-20260930/final-repaired-dy_mumu

python "$diag/repair_replay.py" --role dy_mumu \
  --production-dir "$production" \
  --output-dir /absolute/new/replay-repaired-dy_mumu
python "$diag/repair_replay.py" --role dy_mumu --historical \
  --production-dir "$production" \
  --output-dir /absolute/new/replay-historical-dy_mumu
```

Use fresh output paths. The first command reads the repaired ROOT output;
the second reads the historical paired file but uses the same production
receipt to define the central key domain. Read each output's
`replay.json` → `categories` → `events`, `sumw`, `sumw2` for the table
values. Repeat with the corresponding production directory for another
role. This replays existing outputs; it does not rerun the producer.

### Why fewer producer entries can give more selected Z events

The MC gate removes many false production acceptances, but none of the
removed events enters these historical Z categories. That was checked
from the selected ledgers, including removed events with two or more
leptons; it was not inferred only from singleton counts.

Only part of the rescued class passes the final analysis. Events accepted
by both gates can also change analysis selection:

| Repaired category | Selected from pass-both | Selected from rescued | Net Δ within pass-both | Total Δ selected |
| --- | ---: | ---: | ---: | ---: |
| ee / Ele30 | 15,103 | 158 | +70 | **+228** |
| ee / Ele23–Ele12 | 13,843 | 139 | +69 | **+208** |
| μμ / IsoMu24 | 33,349 | 1,694 | +790 | **+2,484** |
| μμ / Mu17–Mu8 | 32,142 | 1,640 | +769 | **+2,409** |

For μμ / IsoMu24:

```text
Historical selected:                        32,559
Repaired selected from pass-both:            33,349
Repaired selected from rescued:              1,694
Repaired total:                              35,043

Net gain = (33,349 − 32,559) + 1,694 = 790 + 1,694 = 2,484
```

The 790 is a net change within the common production class, not 790 proven
one-way recoveries. Pair choice, IDs, coordinates, kinematics and weights
can change even for events present in both outputs.

The IsoMu24 weighted gain is **11.971479**, consisting of **8.557196** from
rescued events and **3.414284** net change in pass-both. Components use
unrounded values and are rounded independently.

The ee producer writes 25,083 fewer events overall while its selected Z
counts rise. Total ntuple entries and selected Z yields measure different
populations.

### What these yield changes establish

The final replay measures the observed downstream result of repaired
versus actual historical outputs under one fixed analysis policy. It does
not isolate every causal contribution.

MC common-event random draws were **not held equal**. Electron smearing
uses sequential static TRandom3; muon smearing and unseeded TrigMaker use
shared gRandom. Changed survival shifts subsequent draws, including
trigger-period and weight assignments. Historical producer/payload
differences are also not fully recoverable.

DATA scale corrections are deterministic, but exact historical source and
payload-byte equality remain unavailable there too.

Accordingly:

- The **controlled pre-smearing gate comparison** isolates association/slot effects.
- The **final historical-versus-repaired replay** reports descriptive analysis changes.
- The **larger local muon changes** are consistent with the earlier flavor pattern and the established association/acceptance failures.
- No exact full-year attribution, universal defect fraction or campaign correction factor follows from these six inputs.

## Shared producer changes

The repair preserves existing WP cuts, thresholds, isolation/MVA choices,
all-WP gate policy and nominal calibration formulas. It corrects how
values follow their physical objects.

### One retained-object mapping for every stage-created decision

The [original LeptonSel][original-selection] computes tight decisions
before retention, then filters only:

```python
branches = ["pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx"]
```

The [repair][repaired-selection] binds the retained positions once:

```python
df = df.Define(
    "LeptonSel_keepIdx",
    "ROOT::VecOps::Nonzero(LeptonMaskHyg_Ele && LeptonMaskHyg_Mu)",
)
for column in lepton_columns:
    df = df.Redefine(column, f"ROOT::VecOps::Take({column}, LeptonSel_keepIdx)")
```

Here `lepton_columns` includes all six core fields, `isLoose` and all
13 configured tight vectors. Raw Electron/Muon and VetoLepton are preserved.

The pT > 8 requirement remains an event requirement for at least one
hygiene-passing object. Final retention still uses hygiene alone.
The active Loose route's `isLoose` OR already yields true at ordinary
single-flavor positions because its other-flavor hygiene default is true.
The repair preserves that meaning while fixing length and association.
This leaf does not consume `isLoose` directly; no measured historical
RunStability loss is assigned to it.

### Guard the two-slot gate

The [repaired gate][repaired-gate] first applies:

```python
df = df.Filter("Lepton_pt.size() >= 2")
```

It then evaluates the unchanged per-slot all-WP OR on aligned decisions.
The retention fix determines whose bit is read; the guard ensures both
retained slots exist.

### Apply the correction permutation once and keep it immutable

The [original loop][original-scale] includes `Lepton_sorting` itself:

```python
for branch in df.GetColumnNames():
    if branch.startswith("Lepton_") and branch != "Lepton_pt":
        df = df.Redefine(branch, f"Take({branch}, Lepton_sorting)")
```

For a swap `p=[1,0]`, reordering the permutation gives `Take(p,p)=[0,1]`.
Later fields can receive a different mapping. The already sorted
`Lepton_rochesterSF` can also be ordered twice; `isLoose` is omitted.

The [repaired module][repaired-scale] captures genuine flat per-lepton
arrays before defining the permutation, includes `isLoose`, and excludes
temporaries, the permutation, already sorted products and generated
variation columns. Each captured nominal field receives the immutable
mapping once. Existing pT variations are reordered explicitly; registered
SF variations follow nominal redefinition.

Real outputs qualify nominal associations. Synthetic checks additionally
exercise variation and MET propagation; full systematic production is
not qualified by this demonstration.

### Separate DATA JEC configuration correction

The DATA payload lacks the requested `Regrouped_*` uncertainty entries,
so lookup raised `map::at` although DATA variations were disabled.
The separate [`68a082c` change][jec-revision] sets DATA `jes_unc=[]` in
[Steps_cfg.py][repaired-steps]. Nominal JEC, sorting, cleaning and
`do_JER=False`, `store_nominal=True`, `store_variations=False`,
`isMC=False` are retained. MC source configuration is unchanged.
This removes an execution blocker; it is not an association repair.

## What remains unresolved

| Question | Evidence boundary |
| --- | --- |
| Exact old eta-only operation and tight-vector shortening? | Historical dirty worktree unavailable; direct stored-file failures are established, exact source attribution is not. |
| Other campaigns, years and channels affected? | Demonstrated scope is the pinned 2024 inputs; actual producer and consumer inventory is still required. |
| Exact share of full-year Coffea differences? | Coverage and selection policies differ; MC draws were not controlled. No full-year 12.4%, 2.8% or 6.66% attribution was measured. |
| Ordinary production fully qualified? | Nominal local Events and synthetic variation checks were exercised; full systematics, auxiliary metadata and publication were not. |
| Nominal JetSelMask also defective? | Earlier index allegation was withdrawn for the active sorted-prefix order. A conditional JES variation concern requires its own input-order audit. |
| Full unsigned event-ID serialization fixed? | Native ≥2⁶³ conversion remains an expected failure. No high-bit key occurs in these six ranges; a signed bridge was checked separately. |

These limits do not make the demonstrated wrong historical associations
usable for dependent analyses. They describe what additional conclusions
and production uses still need evidence.

## Required follow-up for analysis use

1. Review and integrate the shared producer repair; documentation adoption does not change production.
2. Identify affected recipes, executable revisions, campaigns and consumers.
3. Regenerate affected HWWNano from parent NanoAOD, including missing MC acceptance, and validate the ordinary output path, required variations and metadata.
4. Recompute dependent histograms with validated inputs and the intended analysis policies.

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
[inspected-zh-revision]: https://github.com/TheQuantiser/mkShapesRDF/commit/44bd97884666a3cb8262a2e4727e58198ba1893e
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

[inputs]: https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/inputs.json
[repair-replay]: https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair_replay.py
