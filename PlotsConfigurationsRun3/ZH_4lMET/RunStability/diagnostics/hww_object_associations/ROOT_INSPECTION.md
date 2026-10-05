# Direct ROOT inspection of historical lepton associations

This is a read-only event display of **actual historical 2024 HWWNano
part0 files and their pinned central NanoAOD parents**. It uses PyROOT
`TFile`, `TTree.GetEntry` and integer leaves; it does not run a producer,
analysis selection or Coffea. It does not apply a repair.

The [script](root_inspect.py) recomputes the two full named working points
from each indexed **raw HWW object**, then displays that result beside its
stored `Lepton_isTight*` bit and coordinates. Central raw objects are printed
separately to distinguish an association error from changed raw inputs.
These are offline working-point decisions, not HLT bits.

## Opening display for the association-bug talk

From the existing installation's repository root:

```bash
source start.sh
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/root_inspect.py \
  --case egamma_i_both --all-lepton-fields
```

This reuses `CASES["egamma_i_both"]`: EGamma0 Run2024I, key
**`(386509,735,1539152813)`**, central entry **46209**, historical HWW
entry **3325**. It opens the manifest's exact parent
`07df45e1-d7a2-4dc4-b4db-e0ea381a3e3b.root` and historical
`nanoLatino_EGamma0_Run2024I-Prompt-v1__part0.root`. Full URLs remain in
the unchanged [manifest](inputs/inputs.json) and are printed with the
verified ROOT UUIDs. No discovery or producer run is involved. Complete
integer-key scans reject missing, duplicate or incorrectly located keys;
they read identity branches only. Object branches are read for this event.

### Complete inventory and four separate collection domains

Comprehensive mode discovers the **union of every `Electron_*` and
`Muon_*` branch in both actual Events schemas**. Names choose a display
section only; no heuristic decides inclusion. All raw objects, including
removed leptons, receive grouped vertical field comparisons. Availability
is listed as both, Central-only, HWW-only, or required by a configured WP
but unavailable in either input.

| Domain | Identity and meaning |
| --- | --- |
| A. Central raw Electron/Muon | Original collection index in the pinned central event. |
| B. Historical raw Electron/Muon | Raw index in that historical HWW event; compared with A. |
| C. Historical `VetoLepton` | Prefilter joined collection, with its own sorted positions and raw indices. |
| D. Historical `Lepton` | Retained, corrected joined collection, with its own positions and raw indices. |

Raw-object membership and positions are found through stored
`electronIdx`/`muonIdx`. Retained checks use those raw indices, not
positional agreement or coordinate matching as an identity oracle. Every
stored `Lepton_*` and `VetoLepton_*` field is printed in full, including
all **13 tight vectors**. `isLoose`, `isVeto`, `isWgs` and any standalone
`hygiene*` fields are shown when available. Actual vector lengths remain
separate from retained multiplicity; mismatched vectors are not truncated.

Missing branches/objects are **UNAVAILABLE**, never false or zero. Missing
required named-WP inputs or configured tight vectors still fail clearly.
Bools/integers compare exactly; common finite raw floats compare exactly,
with differences and values printed at 17 significant digits. Nested
values are untruncated. A prefix branch with a non-object length fails
explicitly. Coordinate checks retain the `1e-6` eta/wrapped-phi tolerance.
Corrected pT changes alone are not labeled bugs.

### Configured formulas versus recomputed decisions

The script embeds a **machine-extracted, cuts-only snapshot** of the
original [Full2024v15 configuration at `69ff2dad`](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/data/LeptonSel_cfg.py).
The complete source file's SHA-256 is
`dfe253af96dfa5a1caaff5c6f5e78ce9fc14dc466a7abb6d07db58d8c1d754b2`.
Every guard and predicate in `VetoObjWP`, `FakeObjWP/HLTsafe` and
`TightObjWP` is shown with indexed raw inputs; dependency labels come
from these expressions. Each guard implies the AND of its cuts, and
all guarded groups are ANDed. This frozen reference neither changes the
producer policy nor imports its mutable package or calibration payloads.

**Only the two existing named WPs in `cuts()` are recomputed.** Every
active named-WP cut has its raw input, threshold and PASS/FAIL printed
for both raw collections. Other WPs are labeled **DEFINITION/INPUTS
ONLY**, not recomputed. Seven electron and six muon tight WPs are shown.

The [original `LeptonSel` semantics](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/modules/LeptonSel.py#L49-L147)
map `Loose → isLoose → FakeObjWP`, which supplies hygiene retention.
Veto is a different definition. This era has no `WgStarObjWP`; none is
fabricated. Original `isLoose` used the OR of propagated hygiene masks
with true defaults for the opposite flavor, before filtering. It is not
equivalent to the raw fake-WP decision or guaranteed aligned by its name.

The separately printed **OR of all 13 stored tight vectors at each
position** describes the original MC production predicate: OR at slot 0
AND OR at slot 1. It is not the named electron WP or a recomputed all-WP
decision. **This DATA recipe did not apply that MC `l2tight` skim.**
The separate DY→ee entry-174 erroneous MC-rejection example remains in
the [repair report](REPAIR_REPORT.md) and its
[pinned witness evidence](https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-witnesses.json).
This command does not execute that gate or read an absent MC event.

### Opening event and recorded repaired counterpart

Prefilter order is **Muon 0, Electron 0, Electron 1**. Muon 0 has
`tightId=false` and `abs(dz)>=0.1`, fails hygiene and is absent from
retained `Lepton`. Both retained raw electrons pass every named tight
cut. Retained indices `[0,1]` have stored named tight **`[false,true]`**
instead of the correctly associated `[true,true]`. Historical eta follows
raw identities **`[1,0]`**, while indices and phi follow **`[0,1]`**.
These exact patterns are asserted against the fresh ROOT read.

The displayed repaired column comes from
`/roles/egamma_i/evidence/witnesses/2` in
[repair-witnesses.json at `8d940abc`](https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-witnesses.json),
SHA-256 `1248b7ecac3e2b1f6ccf10ac2a5174ef9e6fe94c8d998ac43a128cce95b260eb`.
It is explicitly **recorded JSON evidence**, not freshly read ROOT.
This command opens no repaired ROOT file.

| Field | Historical HWW (fresh read) | Repaired snapshot (recorded evidence) |
| --- | --- | --- |
| Electron indices | `[0,1]` | `[1,0]` |
| pT | `[39.5183181763,38.9780960083]` | Same values |
| eta | `[1.73095703125,0.612670898438]` | Same values |
| phi | `[1.408203125,-1.76171875]` | `[-1.76171875,1.408203125]` |
| pdgId | `[11,-11]` | `[-11,11]` |
| Named electron tight | `[false,true]` | `[true,true]` |

Corrected pT reverses the order. The repair makes indices, coordinates,
charge/flavor and decisions follow that order together: **it is not
simply swapping eta back**. Historical pT/eta equality with the recorded
repaired arrays is checked explicitly. The exact operation in the dirty
historical producer causing the coordinate mismatch remains unresolved.
Current-code reproduction and historical file observations remain separate
evidence classes. These few objects do not establish a full-year rate.

### Executed comprehensive display — 5 October 2026

The command above ran on `cmslpc-el9-heavy02.fnal.gov`, using the existing
`start.sh`, Python **3.13.11** and ROOT **6.38.00**. It returned exit
code **0**, with **49.30 s wall time**, **12.56 s user CPU** and **0.50 s
system CPU**. The identity-only scans covered all **657,356 central** and
**44,596 historical HWW** entries and located the fixed full key uniquely
at entries 46209 and 3325. No other event's object branches were displayed.

| Coverage | Central | Historical HWW | Displayed union |
| --- | ---: | ---: | ---: |
| Raw electrons | 2 | 2 | Both original indices |
| Electron fields | 72 | 71 | 72 per electron |
| Raw muons | 1 | 1 | Removed raw Muon 0 included |
| Muon fields | 75 | 75 | 75 for the muon |
| Configured stored tight vectors | Not a central joined collection | 13 | Every vector, length and value |

The complete comparison has **219 object/field rows**. All **217 common
raw values match exactly**. `Electron_seediEtaOriX` is Central-only;
no HWW-only raw electron/muon fields or missing configured-WP dependencies
were found. The post-run static coverage check required each schema-union
field to occur exactly once for every raw object, including the removed
muon. The formerly omitted shower-shape, MVA WP80, cut-based, isolation
and ParticleNet inputs are present in the output.

All seven stored electron tight vectors are `[false,true]`; all six muon
tight vectors are `[false,false]`, each of length two. The stored per-slot
OR is `[false,true]`. `isLoose` is **`[1,1,1]` of length three** while the
retained collection has two leptons; this displays the prefilter-domain
length problem directly without assigning its third element to a retained
object. `isVeto` and `isWgs` are unavailable. The two expected mismatch
classes, **tight** and **eta**, were reproduced. The repaired arrays remain
the labeled pinned evidence rather than a fresh repaired-file read.

Read the [complete fresh transcript](all-lepton-fields-transcript-20261005.txt)
and [stderr/timing](all-lepton-fields-stderr-20261005.txt). Only trailing
table padding was removed from stdout; no fields, objects or lines were
removed. Auxiliary CMS metadata dictionary warnings are preserved in
stderr. They did not prevent reading the required Events branches.

The executed script SHA-256 is
`5700839dd952381152c9fc32f83ababd5d55a3f05948c8b1a82abc9705191c6d`;
the committed transcript SHA-256 is
`6284df37f724606be0f50f34fa53cf02d1634fcaa7a8cea11f27e1b4d2573f71`.
The executed script is byte-identical to this revision's inspector.
The fresh local run directory is
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/all-lepton-fields-20261005-owyT5b/`,
retaining untrimmed stdout, stderr, timing, exit status and the executed
script. The base revision was `58dc702c7f9f45e01e2f2440d4b882ae91b0dc4b`.
An unrelated pre-existing skill edit was preserved and not published.

No producer, selection, calibration, manifest or ROOT input changed.
This verifies display completeness and the fixed historical inconsistency;
it does not certify all other WPs, events, years or systematic branches.

## Show the previously identified DATA witnesses

The script uses the original fixed events: Muon C entry **234**, EGamma C
entry **20774**, and EGamma I entries **27025** and **46209**. Their original
full event keys and historical HWW entries are checked before displaying
the arrays. The [four-event transcript](original-four-transcript.txt)
contains their newly executed direct ROOT reads. The additional MC witness
is separate from this command.

After activating the existing ROOT runtime, display just those four events:

```bash
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/root_inspect.py \
  --case muon_c --case egamma_c --case egamma_i_eta --case egamma_i_both
```

For entries 234, 20774 and 46209, both retained raw objects pass every cut
in the full named WP, but the first stored tight bit is **false**. Entry
27025 demonstrates a different error: both tight bits are correct, while
the stored eta values belong to the other indexed electron. The
[actual observations](#actual-observations) below show these exact failures.

**Executed on 2026-10-01**, from `ZH_devel` revision
`864dca0d6e09b1e28803098e096a132171b7b505`, with the unchanged script and
pinned manifest. The command above completed with exit code **0** in
**102.57 seconds** wall time (50.17 seconds user CPU, 0.54 seconds system
CPU), ending with:

```text
PASS: all 4 fixed observations reproduced; elapsed=100.90s
```

All four raw-input comparisons were exactly equal between central NanoAOD
and historical HWW. Their complete event-display sections also match the
earlier seven-case run exactly. The new transcript trims only trailing
table padding. [original-four-stderr.txt](original-four-stderr.txt) preserves
ROOT's auxiliary CMS metadata dictionary warnings. The local run directory is
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/original-four-root-inspection-20261001-EZYiXR/`;
it also retains timing, exit status and the executed script.

## One-command reproduction

From the repository root, activate the existing ROOT/CMS runtime, then run:

```bash
source start.sh
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/root_inspect.py
```

`start.sh` is supplied by the existing supported installation, not this
diagnostic. A clean checkout may instead source the `start.sh` of an
already installed mkShapesRDF runtime. No new dependencies are needed;
the script imports only Python's standard library and PyROOT. Remote
XRootD access to the pinned central and CERN HWW files must work with the
user's existing CMS credentials. The observed environment was LPC,
Python 3.13.11 and ROOT 6.38.00.

To show a single case:

```bash
python PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/root_inspect.py --case egamma_i_eta
```

The default invocation displays all seven cases below. A complete
**identity-only** scan of each involved tree checks that each requested key
occurs exactly once at the pinned entry. Only the selected entries' object
branches are read. This checks the displayed keys, not global DATA
deduplication. Identity scans use one small embedded C++ `TTree::GetEntry`
loop to avoid Python overhead; no external analysis helper is loaded.

## Pinned files and events

[inputs/inputs.json](inputs/inputs.json) is an exact copy of the
[original manifest at `69ff2dad`](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/inputs.json).
Its `pfn` and `hww_part0_pfn` fields give the physical files. The script
checks the manifest SHA-256, central and HWW UUIDs and complete entry counts;
it prints each URL and UUID. Older prefix limits and paths in the copied
manifest are provenance, not dependencies or processing instructions here.
The [parent-pair evidence](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/inputs/parent-pair-evidence.json)
records the original lineage checks.

### Explicit historical HWWNano filenames and paths

The file configuration is [inputs/inputs.json](inputs/inputs.json).
For each `files[]` record, **`hww_part0_pfn` is the literal historical
HWWNano read URL**; `pfn` is its central NanoAOD parent. The script opens
`hww_part0_pfn` directly and reads the `Events` tree. It does not discover
another file, choose a newly repaired snapshot or expand a sample wildcard.
These names and URLs are copied below from the manifest.

| Manifest role | Historical HWWNano filename | Manifest field |
| --- | --- | --- |
| `dy_ee` | `nanoLatino_DYto2E-2Jets_MLL-50__part0.root` | `files[].hww_part0_pfn` |
| `dy_mumu` | `nanoLatino_DYto2Mu-2Jets_MLL-50__part0.root` | `files[].hww_part0_pfn` |
| `muon_c` | `nanoLatino_Muon0_Run2024C-ReReco-v1__part0.root` | `files[].hww_part0_pfn` |
| `muon_i` | `nanoLatino_Muon0_Run2024I-Prompt-v1__part0.root` | `files[].hww_part0_pfn` |
| `egamma_c` | `nanoLatino_EGamma0_Run2024C-ReReco-v1__part0.root` | `files[].hww_part0_pfn` |
| `egamma_i` | `nanoLatino_EGamma0_Run2024I-Prompt-v1__part0.root` | `files[].hww_part0_pfn` |

Exact full read URLs:

```text
dy_ee:
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/nanoLatino_DYto2E-2Jets_MLL-50__part0.root

dy_mumu:
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/nanoLatino_DYto2Mu-2Jets_MLL-50__part0.root

muon_c:
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15_Muon/DATAl2loose2024v15__l2loose/nanoLatino_Muon0_Run2024C-ReReco-v1__part0.root

muon_i:
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15_Muon/DATAl2loose2024v15__l2loose/nanoLatino_Muon0_Run2024I-Prompt-v1__part0.root

egamma_c:
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15_EGamma/DATAl2loose2024v15__l2loose/nanoLatino_EGamma0_Run2024C-ReReco-v1__part0.root

egamma_i:
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15_EGamma/DATAl2loose2024v15__l2loose/nanoLatino_EGamma0_Run2024I-Prompt-v1__part0.root
```

The four-event command opens `muon_c`, `egamma_c` and `egamma_i` only.
`muon_i` remains in the original six-file manifest but is not part of that
command. MC examples use the separately listed `dy_ee` and `dy_mumu` files.
The pinned manifest itself is preserved byte for byte.

**Entries are zero-based TTree positions; they are not event numbers.**

| Script case | Manifest role | Central entry | Historical HWW entry | Full `(run, luminosityBlock, event)` | Required observation |
| --- | --- | ---: | ---: | --- | --- |
| `muon_c` | `muon_c` | 234 | 65 | `(379416,147,131724611)` | Wrong named muon tight bit. |
| `egamma_c` | `egamma_c` | 20774 | 991 | `(379729,907,1396820419)` | Wrong named electron tight bit. |
| `egamma_i_eta` | `egamma_i` | 27025 | 1936 | `(386509,159,333332716)` | Eta is swapped; phi and named tight bits agree with the indices. |
| `egamma_i_both` | `egamma_i` | 46209 | 3325 | `(386509,735,1539152813)` | Tight-bit and eta/index discrepancies coexist. |
| `dy_ee_singleton` | `dy_ee` | 8 | 2 | `(1,384532,2060317109)` | One retained lepton in historical MC `__l2tight` output. |
| `dy_mumu_singleton` | `dy_mumu` | 102 | 39 | `(1,260002,1443526295)` | One retained lepton in historical MC `__l2tight` output. |
| `dy_ee_association` | `dy_ee` | 1480 | 632 | `(1,404199,2165694222)` | Retained raw electron 2 passes the named WP; its stored bit is false. |

The final MC association witness was located by reading historical DY→ee
entries 0–632, stopping at the first named-WP mismatch with at least two
retained leptons. Its key was then located uniquely at central entry 1480.
Subsequent invocations read this fixed witness directly. The earlier gate
ledger's central entry 346 / HWW 151 **did not** exhibit a mismatch in the
two requested named WPs; it was rejected as the association witness. A
production-gate discrepancy alone is not proof of a particular stored ID
error.

## Working-point and coordinate checks

The definitions are frozen from the inspected
[Full2024v15 `LeptonSel_cfg.py` at `69ff2dad`](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/mkShapesRDF/processor/data/LeptonSel_cfg.py)
and checked against the earlier
[historical inspection](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/historical.py).
They are evaluated using raw inputs before momentum correction:

| Named WP | Full decision implemented in the display |
| --- | --- |
| Electron `mvaWinter22V2Iso_WP90_tthMVA_Run3` | `abs(eta)<2.5`, `mvaIso_WP90`, `convVeto`, `pfRelIso03_all<0.06`, `promptMVA>0.90`; for `abs(eta)<=1.479`, `abs(dxy)<0.05` and `abs(dz)<0.1`, otherwise `abs(dxy)<0.1` and `abs(dz)<0.2`. No extra pT cut belongs to this named WP. |
| Muon `cut_TightID_pfIsoTight_HWW_tthmva_67` | `abs(eta)<2.4`, `tightId`, `abs(dz)<0.1`, `pfIsoId>=4`, `promptMVA>0.67`; `abs(dxy)<0.01` at raw `pT<=20 GeV`, otherwise `<0.02`. |

Every raw cut input and its pass/fail result is printed for both collections.
For a retained slot, the script uses `Lepton_electronIdx` or
`Lepton_muonIdx`, checks flavor/charge and compares eta and wrapped phi to
that indexed raw HWW object with absolute tolerance **1e-6**. Corrected pT
and its raw-to-stored ratio are displayed; a pT change is not called an
association error. All stored tight-vector lengths and values are printed
in full, including the other WPs. They are neither truncated nor repaired.

The script rejects changed UUID/counts, missing branches, unreadable entries,
duplicate or wrong keys, invalid raw identities and nonfinite inputs. It
returns nonzero if a case's required observation is not reproduced. Its
`PASS` means the fixed observations were reproduced; it does **not** certify
every stored WP or the validity of the file. Central/HWW raw differences,
if any, are reported separately rather than automatically called bugs.
Event IDs remain integers throughout; a signed HWW event number is mapped
back to its unsigned 64-bit identity without floating-point conversion.

## Actual observations

The full terminal output, including file URLs, UUIDs, raw-input tables,
individual WP cuts, `VetoLepton`, retained objects and vector lengths, is
retained in [root-inspection-transcript.txt](root-inspection-transcript.txt).
Only trailing table padding was trimmed from the committed transcript;
all lines, values and decisions are preserved.
The compact rows below are extracted from that direct read. The run on
**2026-10-01** returned exit code 0 after **172.55 seconds** wall time
(57.05 seconds user CPU, 0.61 seconds system CPU). Its final line is:

```text
PASS: all 7 fixed observations reproduced; elapsed=170.80s
```

The elapsed value inside the script excludes Python/ROOT startup. All seven
central-versus-HWW raw-input comparisons were **exactly equal**. The executed
script is the original inspector at pinned `864dca0`, SHA-256
`b669ecdd5158d8779d88a8002be0e2a4144ff6a8acafcf424d426b405841764d`;
the transcript SHA-256 is
`a0a814a5e26836aba7a514ff4ba7e9ee9ab8de7d17a91f2d752ec827df28c1af`.
[root-inspection-stderr.txt](root-inspection-stderr.txt) preserves timing
and ROOT warnings about missing dictionaries for auxiliary CMS metadata
classes (`edm::Hash`, `ParameterSetBlob`, `ProcessHistory`,
`ProcessConfiguration`). The required Events branches were readable and
all stated checks passed; the warnings are retained rather than suppressed.

| Case / slot | Indexed raw object | Expected named tight | Stored named tight | Coordinate result |
| --- | --- | --- | --- | --- |
| Muon C / 0 | Muon 1 | true | **false** | Eta and phi agree. |
| Muon C / 1 | Muon 2 | true | true | Eta and phi agree. |
| EGamma C / 0 | Electron 0 | true | **false** | Eta and phi agree. |
| EGamma C / 1 | Electron 1 | true | true | Eta and phi agree. |
| EGamma I 27025 / 0 | Electron 0 | true | true | Raw eta `-0.93359375`; stored **`-2.05712890625`**. Phi agrees. |
| EGamma I 27025 / 1 | Electron 1 | true | true | Raw eta `-2.05712890625`; stored **`-0.93359375`**. Phi agrees. |
| EGamma I 46209 / 0 | Electron 0 | true | **false** | Raw eta `0.612670898438`; stored **`1.73095703125`**. Phi agrees. |
| EGamma I 46209 / 1 | Electron 1 | true | true | Raw eta `1.73095703125`; stored **`0.612670898438`**. Phi agrees. |
| DY→ee association / 1 | Electron 2 | true | **false** | Raw eta `0.0373611450195`, phi `-2.62060546875`; retained coordinates agree. |

For the Muon C event the retained raw indices are `[1,2]`, so the expected
named tight vector is `[true,true]`; the file stores `[false,true]`. For
EGamma C, `VetoLepton` begins with a muon, followed by electrons 0 and 1;
only the two electrons remain in `Lepton`, but the electron tight vector
still starts with false. This shows why object identity must accompany a
decision through a filter, even when the stored vector length looks correct.

In the retained MC association witness, prefilter electron indices
`[0,1,2]` have named tight decisions `[false,false,true]`; the retained
indices `[0,2]` require `[false,true]`, but the file stores `[false,false]`.
The retained raw electron 2 has `mvaIso_WP90=true`, `convVeto=true`, isolation
`0`, prompt MVA `0.970703125`, `dxy=0.00267791748047` and
`dz=-0.00122165679932`: every cut in its full named WP passes. Its raw pT
is only 16.26 GeV, so this wrong-bit witness is **not** a claim that the
event enters the 35/35 GeV RunStability Z category.

Both MC singleton cases directly establish `nLepton=1` and one-element
tight vectors in the historical `__l2tight` part0. Their remaining lepton's
requested named bit agrees with its raw inputs. **They are not the wrong-bit
witnesses.** This display does not execute the old production predicate or
identify its exact historical acceptance operation. The separate retained
DY→ee association case supplies the requested direct MC wrong-bit example.

## Evidence boundary

These are stored-file facts reproduced by fresh ROOT reads. The earlier
[complete-file investigation](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/README.md)
and [repair report](REPAIR_REPORT.md) establish current-code mechanisms and
counterfactual population changes. They are different evidence from this
display. The historical producer's dirty worktree is unavailable; in
particular, the eta-only event does not identify its historical producing
operation. No producer source, working-point policy, historical file or
analysis output is changed here. These examples do not measure a full-year
frequency or explain a particular fraction of the published yield difference.

The measured local output is
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/direct-root-inspection-20261001-ElmnFX/`.
It retains the executed script, stdout and stderr; these are local LPC
files, not a portable runtime dependency. Two earlier attempts were kept
beside it: `direct-root-inspection-20261001-5MkBmR` was stopped after
219.67 seconds when per-entry leaf lookups made the identity check slow;
`direct-root-inspection-20261001-ca21U5` exited 1 after 127.15 seconds
because the proposed MC entry 346 lacked the required named-WP mismatch.
Neither is a successful demonstration. Caching identity leaves once and
selecting a directly verified MC witness resolved those two issues; no
producer replay or broad test campaign was run.
