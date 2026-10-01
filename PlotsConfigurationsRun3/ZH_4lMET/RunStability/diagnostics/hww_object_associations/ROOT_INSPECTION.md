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
script is byte-identical to the committed script, SHA-256
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
