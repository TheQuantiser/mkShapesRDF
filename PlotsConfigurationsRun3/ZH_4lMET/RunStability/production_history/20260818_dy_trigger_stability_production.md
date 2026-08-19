# 2026-08-18 DY trigger-stability production

> **Historical production receipt.** The campaigns, selectors, configured MC
> source luminosities, paths, and plot styles below describe their exact dated
> artifacts. They are not the live RunStability source contract. Use
> [README.md](README.md) for the status index and reproduce a retained product
> only through the leaf's hash-pinned `plot_reproduction.json`.

## Scope

This record owns the replacement five-era production requested for DY run
stability by broad stream, positive trigger family, and concrete HLT path.
The first common local control identity was:

```text
JOB_CAMPAIGN=DY_TRIGGER_STABILITY_20260818T175629Z
```

That attempt used a distinct remote identity
`DY_TRIGGER_STABILITY_<era>_20260818T175629Z`. Before submission, all five
remote parents and the common local parent were verified absent.

The current production target is one observable and this exact 48-category
selector:

```bash
export RUN_STABILITY_OBSERVABLES=Z0_mass
export RUN_STABILITY_CATEGORIES=DY_ALL,DY_ZEE,DY_ZMM,DY_STREAM_MUONEG,DY_STREAM_MUON,DY_STREAM_EGAMMA,DY_STREAM_MUONEG_ZEE,DY_STREAM_MUONEG_ZMM,DY_STREAM_MUON_ZEE,DY_STREAM_MUON_ZMM,DY_STREAM_EGAMMA_ZEE,DY_STREAM_EGAMMA_ZMM,DY_TRGFAM_ELMU,DY_TRGFAM_SINGLEMU,DY_TRGFAM_DOUBLEMU,DY_TRGFAM_SINGLEEL,DY_TRGFAM_DOUBLEEL,DY_HLT_MU23_ELE12,DY_HLT_MU12_ELE23,DY_HLT_MU8_ELE23,DY_HLT_MU17_MU8,DY_HLT_ISOMU24,DY_HLT_ELE23_ELE12,DY_HLT_ELE30,DY_TRGFAM_ELMU_ZEE,DY_TRGFAM_ELMU_ZMM,DY_TRGFAM_SINGLEMU_ZEE,DY_TRGFAM_SINGLEMU_ZMM,DY_TRGFAM_DOUBLEMU_ZEE,DY_TRGFAM_DOUBLEMU_ZMM,DY_TRGFAM_SINGLEEL_ZEE,DY_TRGFAM_SINGLEEL_ZMM,DY_TRGFAM_DOUBLEEL_ZEE,DY_TRGFAM_DOUBLEEL_ZMM,DY_HLT_MU23_ELE12_ZEE,DY_HLT_MU23_ELE12_ZMM,DY_HLT_MU12_ELE23_ZEE,DY_HLT_MU12_ELE23_ZMM,DY_HLT_MU8_ELE23_ZEE,DY_HLT_MU8_ELE23_ZMM,DY_HLT_MU17_MU8_ZEE,DY_HLT_MU17_MU8_ZMM,DY_HLT_ISOMU24_ZEE,DY_HLT_ISOMU24_ZMM,DY_HLT_ELE23_ELE12_ZEE,DY_HLT_ELE23_ELE12_ZMM,DY_HLT_ELE30_ZEE,DY_HLT_ELE30_ZMM
```

Its canonical executable order is `DY_ALL,DY_ZEE,DY_ZMM`; three stream
parents; six stream-flavor children; five trigger-family parents; seven
concrete-path parents; ten family-flavor children; and fourteen path-flavor
children.
`DY_ALL`, `DY_ZEE`, and `DY_ZMM` are `Trigger_Any` OR reference
projections. Every flavor child inherits its flavor-stripped parent's
`trigger_any`, `trigger_*`, or `hlt_*` luminosity source. Flavor is an
event category, not an exposure, and does not justify a separate denominator.

`SAMPLE_PROFILE=presentation`, `FILES_PER_JOB=10`, and all sample, stream,
run, and per-sample file filters are cleared. The exact documented submission
entry point is `mkShapesRDF -c 1 --submit ... -l -1 -q workday` after sourcing
the framework and the leaf-local FNAL packaged environment.

## Historical first-attempt source and preflight evidence

The following snapshot describes the first `175629Z` preparation, not the
current B--D/48-category submission. The child checkout was at HEAD
`a67e3fca9171012502c092a3ceed2b2f7a20d00e` on branch `ZH_devel`. The analysis
leaf is untracked in that checkout, so the numerical source identity is also
recorded directly:

| File | SHA-256 |
| --- | --- |
| `category_config.py` | `0f37c40cb30713bf9f681a3c440dad9804887a2c231cf60de0d4cfd967c2b17f` |
| `run_stability_config.py` | `a0f7be2d9c6a3bbdb6614c8ac804381e37753b7f907cccfa9079d1ac2d522314` |
| `run_stability_runner.py` | `ac2ba2c081a1b17b5d6a25cbc6996cae3cfe1169bbbeb4bb94313539bec4f759` |
| `plot_run_stability.py` | `f6586c2eaf55d27f10f54db441c4d8525fcbcdf713f36cf6535c49ecd365ccf0` |
| `configuration.py` | `de99b6eb76dbbf964af3c0d912545a1164cd57eb0ef8474828e0a7e0279b4706` |

At `2026-08-18T17:56:29Z`, the CMS proxy had 519,045 seconds remaining. That
attempt still referenced the historical workspace `lumi/results/` identity and
predated the final B--D audit. Its 112-test result and hashes are retained as
historical evidence only; they do not validate the later submission.

The five exact compiled pickle identities, tags, clusters, schedds, expanded
job counts, completed split sets, merged-file identities, and derived-plot
receipts are appended below as those gates complete.

## Corrected early-2022 DATA completeness audit

The earlier conclusion in this record was wrong: agreement among the aligned
DY reference, original `ZZ_CR`, this leaf, the compiled pickle, and the pinned
luminosity inventory established only that the same incomplete six-component
contract had propagated through all consumers.

The authoritative processor catalog
`mkShapesRDF/processor/framework/samples/Run2022_ReReco_nAODv12.py`, live DAS,
the Golden JSON, and the exact HWWNano materialization establish that this
production covers Run2022B, C, and D. The required matrix has ten components
and 739 materialized files:

| Primary dataset | Logical stream | Run2022B | Run2022C | Run2022D | Total |
| --- | --- | ---: | ---: | ---: | ---: |
| `MuonEG` | `MuonEG` | 6 | 28 | 16 | 50 |
| `SingleMuon` | `Muon` | 12 | 35 | -- | 47 |
| `Muon` | `Muon` | -- | 124 | 82 | 206 |
| `EGamma` | `EGamma` | 14 | 313 | 109 | 436 |
| **All DATA** | | **32** | **500** | **207** | **739** |

There is no `Muon_Run2022B` and no `SingleMuon_Run2022D`. The processor step
labels the upstream correction chain as Run2022BCD, while the leaf BTV payload
path is named `Run3-22CD...`; Run2022B therefore also requires explicit
downstream correction-domain validation before scientific release.

The component weights are also sample-specific. SingleMuon B and C receive
`!Trigger_ElMu && Trigger_sngMu`; Muon C and D receive
`!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)`. Encoding one global
dataset list for B--D either omits valid components or invents unsupported
Muon B and SingleMuon D components, while assigning only a stream-wide default
would erase the primary-dataset acceptance distinction.

The first historical exact pickle contained six C--D components and 672 DATA
files. A later C--D correction added SingleMuon C but still excluded B; the
exact stale pickle
`PlotsConfigurationsRun3/ZH_4lMET/RunStability/configs/config_26-08-18_14_25_41.pkl`
contains seven components and 707 DATA files. Neither contract is complete.
Nonzero `DY_ALL` bins prove that some DATA survived, not that the missing
stream and period were present. The retained luminosity inventory also names
the original `ZH_4lMET/ZZ_CR/year_config.json`, not the live RunStability leaf,
and classified B as unconfigured. It cannot authorize a B--D submission.

Missing SingleMuon C and then all of B removes DATA while the inclusive MC
template remains normalized to positive trigger exposure from the available
union. This biases affected ratios low. The former adaptive x-axis tick
selection did hide the first run label, but it did not cause the low ratios.
Likewise, historical zero muon-path exposures calculated from incomplete
owning-stream coverage must not be interpreted as physical path inactivity.

The retained Golden JSON contains 19 certified B runs from 355374 through
355769. The final B--D audit contains 4,633 calibrated Run2022B lumisections
and 0.096513459664 fb^-1. Added arithmetically to the prior C--D recorded
exposure of 7.980315198255002 fb^-1 this gives 8.076828657919002 fb^-1, matching
the rebuilt nominal B--D result. That agreement is only a cross-check: all
nominal, trigger-family, and path-specific products were regenerated from the
exact ten-component contract rather than patched from the two subtotals.

The full storage-catalog receipt is
`/uscms_data/d3/mwadud/private/mkShapesRDF_devel/lumi/audits/MAKE_SAMPLE_CATALOG_FULL_20260818T194800Z/catalog.json`.
The initial part0-only receipt omitted two target-step components:
`MuonEG_Run2022B-ReReco-v1` under `DATAl2loose2022v12__l2loose` and
`MuonEG_Run2022F-Prompt-v1` under `DATAl2loose2022EEv12__l2loose`. Each exact
identity has part1 but no part0.
The current `make_sample_catalog.py crawl` default discovers parts 0 and 1 and
selects part0-else-part1 per exact identity; `--part 0` deliberately disables
the fallback, while `--all-parts` is required for complete file counts. The
catalog must be reconciled against the processor catalog and live all-parts
materialization. It may neither suppress a processor component nor invent a
component unsupported by the processor catalog.

The corrected release gate is fail-closed: reconcile the live leaf against
the processor catalog, aligned external configuration, materialized HWWNano
components/files, and exact compiled pickle; rebuild luminosity inputs from
the live leaf and require its exact path and SHA-256 in the manifest; submit
only with zero unresolved missing or unexpected components and files.

## Submission and completion ledger

The first attempted common local identity was
`DY_TRIGGER_STABILITY_20260818T175629Z`. Its 2022 preparation was interrupted
during runtime-archive creation after the missing
`SingleMuon_Run2022C-ReReco-v1` defect was identified. No `submit.jdl` was
finalized and `condor_submit` was never called; owner-wide queries on the three
relevant LPC schedds returned no live job. That partial identity is failed
pre-submission evidence and must not be reused. A corrected campaign requires
a fresh collision-resistant local and remote identity after the DATA catalog
and luminosity provenance gates pass.

The later C--D-only pre-submit compile used tag timestamp `20260818_192528`
and exact pickle
`PlotsConfigurationsRun3/ZH_4lMET/RunStability/configs/config_26-08-18_14_25_41.pkl`.
Its seven-component/707-file graph is also failed evidence because it excludes
Run2022B. It must not be submitted or reused as the basis of a B--D luminosity
audit, merge, or plot.

The later 16-parent-only campaign
`DY_TRIGGER_STABILITY_20260818T210648Z` was superseded by the exact
48-category matrix above. Condor clusters `30089855`, `30089856`,
`30089857`, and `85179186` were cancelled; the 2024 preparation stopped
before submission. Only the local
`jobs/DY_TRIGGER_STABILITY_20260818T210648Z` directory was deleted. Remote
EOS partial outputs were neither deleted nor audited, so their existence,
contents, and scientific usability remain unverified and they must not be
reused as validated production.

## Current 48-category B--D submission

The corrected campaign uses exactly one local parent:

```text
JOB_CAMPAIGN=DY_TRIGGER_STABILITY_20260818T214258Z
jobs/DY_TRIGGER_STABILITY_20260818T214258Z/
```

It was compiled at Git revision
`6f9b4ff164ec985575aa1c4da7c3c73839446001` with `git_dirty=true` and the
explicit frozen luminosity results directory:

```text
/uscms_data/d3/mwadud/private/mkShapesRDF_devel/lumi/audits/ZZ_CR_RunStability_BCD_afa86d85_conjunction_20260818T200415Z/results
```

The audit manifest SHA-256 is
`62e24cbe5db00035810f0d6a550a958668b998c65505b9e4fad652caa2ce3ec7`;
the passing validation report SHA-256 is
`efadd80d3dbeb9c21e9896d3a02e3a5428631a21ab05a3ee1e616d5df96dfb13`;
the provenance SHA-256 is
`528a25a1167e41eed3c4fd5d880e198b86685fb640f3708e0771b30cacaf2c1c`;
and the manifest names the live `year_config.json` SHA-256
`afa86d851cd46c01b57598c9b865e7d9a8e6cbbb1dd2db7e1aa894e8d6ba3ba2`.
The audit passed the component-trigger/category-trigger conjunction and
independent-reproduction gates with no partial files.

Every exact compiled contract selects `Z0_mass`, the ordered 48-category base
matrix, 14 luminosity sources, 29 metadata paths, and 48 auxiliary DATA paths.
All 32 `_ZEE`/`_ZMM` categories inherit their flavor-stripped parent's
exposure. The exact submission identities are:

| Era | Exact pickle (SHA-256) | Exact tag | Cluster / schedd | Jobs |
| --- | --- | --- | --- | ---: |
| 2022 | `config_26-08-18_16_47_33.pkl` (`d628f9d9f96d5ce969862fd40c5a7087275b3cd8b2262c8f3da453ed75d5dc01`) | `FourLepton_2022_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-custom-be24d1ac1df9_20260818_214717` | `30090854` / `lpcschedd5.fnal.gov` | 511 |
| 2022EE | `config_26-08-18_16_47_13.pkl` (`04affc3d23a9afff5c90d9f08b499bb2250906d8fa958b0d43935bb3771a5380`) | `FourLepton_2022EE_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-custom-be24d1ac1df9_20260818_214653` | `30090855` / `lpcschedd5.fnal.gov` | 1,216 |
| 2023 | `config_26-08-18_16_47_31.pkl` (`655fe19581b82fba66c1ef5b2a520d371b119983c5170f45eb9b778f882bd4e2`) | `FourLepton_2023_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-custom-be24d1ac1df9_20260818_214705` | `30090853` / `lpcschedd5.fnal.gov` | 707 |
| 2023BPix | `config_26-08-18_16_55_21.pkl` (`b683d4fdf47b5338185e4d116d8c528ac250eaa145ed73191bf98069f83adb3f`) | `FourLepton_2023BPix_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-custom-be24d1ac1df9_20260818_215501` | `3865065` / `lpcschedd4.fnal.gov` | 455 |
| 2024 | `config_26-08-18_16_50_27.pkl` (`db94a6f7a845bd11508f89d6f0b3770f0fcd70da87045a43a898e145a50d2004`) | `FourLepton_2024_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-custom-be24d1ac1df9_20260818_215013` | `85179188` / `lpcschedd6.fnal.gov` | 3,967 |

The tag-local scientific contracts and submission receipts are independently
hashed below. For each row, the remote output LFN is
`/store/user/mwadud/mkShapesRDF_rootfiles/<production campaign>/<exact tag>`;
the write endpoint is `root://cmseos.fnal.gov`.

| Era | Production campaign | `analysis_contract.json` SHA-256 | `submit.receipt.txt` SHA-256 |
| --- | --- | --- | --- |
| 2022 | `DY_RUN_STABILITY_2022_20260818T214258Z` | `37a364c3ca80994f9c72e56e8e224724551ddaf12a90de97d03ed313a3c30ca2c` | `b328e2f8ac50e8b9997834b7d61850a2f1b5f54e2e4e3c453121bcd1a24fa247` |
| 2022EE | `DY_RUN_STABILITY_2022EE_20260818T214258Z` | `fc8a18d94fc6491022ce30aba9f216da9dd9062f4845d540d9e6b1caa7e4972c` | `c43dcae5f9b7cab2027cc9aba9cc5e857a60c1cb968433c60ea982c9ba358a4a` |
| 2023 | `DY_RUN_STABILITY_2023_20260818T214258Z` | `bb32558b92c81a070802e6732eeb65f4377b28532ae90dbbb36f7cf0ddcc7f5f` | `b3dd613ee24c04c60e8b3cfe11007dbf1f5ad236b523cfed235896424c497e99` |
| 2023BPix | `DY_RUN_STABILITY_2023BPix_20260818T214258Z` | `33722444975e927d8c2325cb0924974a5b78bbeb0f6ed36ee298fca28fc705b6` | `b87523f6b70aa934b2d67cf44ce5368bbdf7023797093a62beba5d9244392a9e` |
| 2024 | `DY_RUN_STABILITY_2024_20260818T214258Z` | `8f464e51dce127f8189b0810a2fcc8c81dad3ac6e5f5555e57de3725ff596e05` | `c67bca2b4941aa4a512143630e4f0f5f8ff743cae1013710fa1b4946832c050d` |

The contract path is `<job campaign>/<exact tag>/analysis_contract.json`.
The receipt is below that same tag at
`condor/<exact tag>/submit.receipt.txt`. The contracts establish scientific
and runtime semantics but do not currently serialize `tag`, `JOB_CAMPAIGN`,
or `PRODUCTION_CAMPAIGN`; those mappings are verified from the exact pickle,
generated directory/JDL, and receipt rather than inferred from the contract.

All five scheduler receipts were accepted, all generated split counts equal
the submitted counts, and no held jobs were observed in the
`2026-08-18T22:11Z` scheduler reconciliation. At that snapshot the queue/
history accounting was: 2022 142 idle, 290 running, 79 completed; 2022EE 1,216
idle; 2023 66 running, 641 completed; 2023BPix 325 idle, 46 running, 84
completed; and 2024 3,398 idle, 144 running, 425 completed. These are scheduler
states, not durable-output validation.

At `2026-08-18T22:36:16Z`, the 2022, 2022EE, 2023, and 2023BPix clusters had
left their live queues. Their exact history queries returned respectively 511,
1,216, 707, and 455 records, all `JobStatus=4` with `ExitCode=0`. The 2024
cluster was still active with 848 idle and 585 running jobs and no held status;
its raw history query returned 2,627 `4/0` records, which can include retry
records and was not yet promoted to a unique-ProcId completion claim. No merge
or durable split-set validation had started at that snapshot.

An earlier note associated the 2023 tag with the 2024 pickle
`config_26-08-18_16_50_27.pkl`. Direct deserialization disproved that
bookkeeping claim: the retained 2023 pickle is
`config_26-08-18_16_47_31.pkl`, and all five current pickles have distinct
filenames and matching era/tag/campaign identities. No 2023 cancellation or
resubmission was required. The generic one-second filename collision risk
remains, so future same-leaf era compiles must be serialized and each pickle
reopened and mapped immediately.

The complete 125-test leaf suite passed against the frozen B--D luminosity
audit before the final flavor-category source edits. After those edits, the
focused category regression passed. A post-edit full-suite run was not
performed because the operator requested submission without extensive
testing. Completion, remote split-set equality, merged ROOT readability,
merging, plotting, and scientific Data/MC interpretation remain later gates.

## Failure chronology and durable decisions

The following sequence distinguishes causal defects from symptoms and from
superseded evidence:

1. The first DY Z-mass ratio production inherited a six-component, 672-file
   Run2022 C--D DATA catalog. Its early run bins were not empty: other primary
   datasets supplied events. The old adaptive labelling selected run 356434 as
   the first visible text label, which made earlier points easy to overlook,
   but the low ratios were real and were not caused by the axis.
2. File/catalog inspection found the causal DATA defect: Run2022C
   `SingleMuon` was absent while the MC template was still normalized to
   positive luminosity. Adding SingleMuon C produced a seven-component,
   707-file C--D plan and corrected the early Muon-stream transition, but it
   did not establish full 2022 completeness.
3. Running the complete sample-catalog workflow and reconciling it with the
   processor catalog plus live all-parts HWWNano listings showed that Run2022B
   is also part of the production. The final B--D matrix has ten components
   and 739 files. It includes SingleMuon B/C and Muon C/D, with no invented
   Muon B or SingleMuon D. A separate catalog bug was exposed because valid
   MuonEG Run2022B and Run2022F identities have part1 but no part0; the durable
   representative policy is part0-else-part1, while file completeness always
   uses all parts.
4. The first corrected luminosity audit covered SingleMuon C but was still a
   C--D identity. The final immutable B--D audit rebuilt dataset/LS masks,
   nominal and 13 trigger-routed sources, component-baseline/category-trigger
   conjunctions, full-year diagnostics, schema evidence, reproduction, and
   provenance from the live ten-component configuration. Historical top-level
   `lumi/results` and the earlier audit are not interchangeable with it.
5. A first trigger-stability preparation was interrupted before submission
   when stale DATA/luminosity provenance was detected. A later 16-parent
   campaign was accepted by Condor but then deliberately cancelled because it
   lacked the requested selected-Z flavor children. Its local controls were
   removed only after scheduler reconciliation; its remote partial outputs
   remain unaudited and are not current inputs.
6. Adding `_ZEE`/`_ZMM` children expanded the complete run-stability registry
   to 96 categories. The focused production intentionally selects the 48
   un-enriched reference, stream, family, path, and flavor categories. An
   initially supplied 48-name order grouped parents with children and failed
   closed in `cuts.py` before submission. Reordering the same set to the
   executable registry order resolved the compile without weakening the
   ordering guard.
7. The five canonical retries were submitted beneath one local campaign
   parent. A subsequent report incorrectly mapped the 2023 tag to the 2024
   pickle and raised a possible overwrite alarm. Direct deserialization and
   contract comparison located the distinct 2023 pickle and disproved a loss
   in this campaign. The underlying one-second filename hazard remains real,
   so future same-leaf compiles are serialized and mapped immediately.

The scientifically relevant current identities are therefore the live
`year_config.json`, the reconciled processor/catalog/materialized file matrix,
the frozen B--D luminosity audit, the ordered 48-category selector, each exact
pickle and tag-local contract, and the scheduler/durable-output evidence for
that exact tag. Historical ratios, sparse tick labels, a successful transport
receipt, `config.json`, `latest`, or another era's pickle do not substitute for
any of those identities. Plotting style and out-of-range markers are a later
presentation gate; they cannot repair missing DATA or a wrong luminosity
denominator.

## Final completion, merge, and stability gallery

This section supersedes the live scheduler snapshots above. The five corrected
48-category clusters all drained from their exact schedds. Exact unique ProcId
and history reconciliation found no missing or duplicate process identities;
every process was `JobStatus=4` with `ExitCode=0`:

| Era | Cluster and schedd | Unique ProcIds |
| --- | --- | ---: |
| 2022 | `30090854` on `lpcschedd5.fnal.gov` | 511 (`0-510`) |
| 2022EE | `30090855` on `lpcschedd5.fnal.gov` | 1,216 (`0-1215`) |
| 2023 | `30090853` on `lpcschedd5.fnal.gov` | 707 (`0-706`) |
| 2023BPix | `3865065` on `lpcschedd4.fnal.gov` | 455 (`0-454`) |
| 2024 | `85179188` on `lpcschedd6.fnal.gov` | 3,967 (`0-3966`) |

The generated job-directory identities and remote split ROOT basenames agree
exactly for all five eras. The framework checker nevertheless proposed 72
retries because stderr contained a close-time
`TNetXNGFile::Close: [ERROR] Socket timeout` warning: 30 in 2022, zero in
2022EE, 22 in 2023, nine in 2023BPix, and 11 in 2024. Every one of those 72
exact remote files independently reopened over XRootD as non-zombie,
unrecovered, nonempty, with a valid END. They were successful stage-outs, so
no warning-driven resubmission was made.

Each era was merged with its recorded exact pickle using the documented
`--histoadd -b 0` command. Local and remote merged products were independently
reopened and have matching size and Adler-32 identity:

| Era | Bytes | SHA-256 | Adler-32 |
| --- | ---: | --- | --- |
| 2022 | 1,742,748 | `3fcf78ef0b7704e711fe70a9814c02ff6c1e98fa23ba79d90a352487190e5132` | `75e4c9c2` |
| 2022EE | 1,821,253 | `bc9c00372478cc097c7f2dfe421ee49cbe234c6530a362cea8524da6fc3a44d8` | `94a79ed4` |
| 2023 | 1,708,296 | `f5a09293b5047fcc541a23d93a4f765d265f9ec57d361c4a66503d57ee8fa724` | `7ff2fb3c` |
| 2023BPix | 1,559,613 | `f6f1b1d7c89c800cc7fa9b13d3d0fa282fc4967465570d72f709584a6e0fe096` | `859a17c1` |
| 2024 | 2,667,362 | `e8ae7966912780b87d30ab8f5f94550ffb206010f2cef81fd40c66a5ccdfb745` | `e089fba9` |

`plot_run_stability.py validate` passed against every exact pickle and merged
file. The run axes are 170, 190, 126, 43, and 456 bins for 2022, 2022EE, 2023,
2023BPix, and 2024. Each merged file contains all 48 auxiliary DATA TH2
histograms. The 2022--2023BPix files contain exactly 2,621 recursive objects
(2,573 TH1D and 48 TH2D); 2024 contains 2,717 (2,669 TH1D and 48 TH2D).

The final five-era `Z0_mass` ratio gallery is under
`jobs/DY_TRIGGER_STABILITY_20260818T214258Z/ratio_vs_run`. Exactly 47 of the 48
submitted categories produced the complete PNG, PDF, CSV, JSON, and ROOT set:
235 files totaling 206,535,440 bytes. Every successful CSV contains 985 rows
in the exact five-era order, and all 188 receipt-addressed output hashes match.
Every ROOT ratio product has the exact seven-object contract, 985-bin labelled
histograms, a 985-point asymmetric graph, and two finite symmetric 985-by-985
covariance matrices. MC covariance is exactly zero across era templates, and
the total-minus-MC off-diagonal covariance is zero.

`DY_STREAM_EGAMMA_ZMM` is the only absent stem. The plotter and the artifact
audit fail closed because its 2023BPix prompt-MC total is nonpositive. No
partial product exists. This is a scientific undefined-ratio guard, not a
transport or plotting failure; the era was not removed and another luminosity
source was not substituted.

The initial parallel gallery command contained a hand-written merged-path
error: it omitted the nested tag directory and `mkShapes__` prefix for some
eras. Those lanes failed while opening inputs and were interrupted before they
wrote category products. The corrected matrix derived every input from its
exact tag and preflighted all five paths before plotting.

Full-size visual inspection of inclusive `DY_ALL` and sparse
`DY_HLT_MU8_ELE23_ZMM` plots found one presentation defect: consecutive last-
run/first-run labels at era boundaries overlapped. The Matplotlib renderer now
staggers the following era's first label onto a second row while preserving all
points and the first/last label of every era. The focused plotting suite passed
9/9 after this change. All 47 successful products were refreshed; their
receipts record staggered bins 171, 361, 487, and 530. Post-refresh receipt,
hash, CSV, ROOT-structure, covariance, and guarded-stem checks all passed, and
both representative plots were visually reopened without clipping. The
deterministic digest of the sorted SHA-256 lines for the 235 gallery files is
`9894cfb311c493922dc7347bc165f472264f4ac35a9f4f98b0ef380aebcfb6ee`.

This final gate establishes scheduler completion, split-set completeness,
remote readability for every warning-flagged split, exact-pickle merging,
merged ROOT contract integrity, and the stated derived plotting artifacts. It
does not convert the concrete-HLT plots into path-specific trigger-SF
measurements: the compiled MC weight still uses aggregate `TriggerSF_Z`, as
documented in `LUMINOSITY_PROPAGATION.md`.

## DATA-only point errors and era-specific MC-band presentation refresh

The completed merged products above were not reprocessed and no batch jobs
were submitted for this refresh. `plot_run_stability.py` was changed locally
and the existing five exact merged inputs were used to regenerate the derived
gallery.

The ratio central value remains `D/M`. Each DATA point now carries only the
central 68.2689492137% Garwood interval divided by `M`; MC uncertainty is no
longer folded into the displayed point error. The selected category's relative
MC Sumw2 uncertainty is instead drawn around `y = 1` as one independent band
segment per compiled analysis era. The band and dashed central line use the
same blue, with transparency and diagonal hatching on the band, and share one
legend entry named `DY MC`. The numerical MC covariance matrices remain in the
ROOT product for downstream use.

For the inclusive `DY_ALL` product, the five independently serialized relative
MC uncertainties are:

| Era | Run-axis bins | Relative MC uncertainty |
| --- | ---: | ---: |
| 2022 | 1--170 | 0.000436846539 |
| 2022EE | 171--360 | 0.000223559001 |
| 2023 | 361--486 | 0.000307218558 |
| 2023BPix | 487--529 | 0.000446035555 |
| 2024 | 530--985 | 0.000110665842 |

The Matplotlib view has no CMS/year/title banner or explanatory footer. The
legend and a compact two-line selection/flavor annotation are inside the axes.
Directional triangles and zero-luminosity crosses are explained by the concise
`Out of range` and `Zero lumi.` legend entries. Full-size computer-vision
inspection used both `DY_ALL` and sparse `DY_HLT_MU8_ELE23_ZMM`; the latter
also established that the hatched band remains visible when the category's MC
statistics are poorer. The style follows the maintained
`notebooks/mkshapes_analysis_lab` publication-light conventions.

Final post-refresh validation found exactly 47 complete PNG/PDF/CSV/JSON/ROOT
sets and no files for the scientifically guarded `DY_STREAM_EGAMMA_ZMM`
category. All 188 receipt-addressed hashes match. The 47 CSV files contain
46,295 rows: 45,684 valid and 611 explicitly invalid. Every valid row was
independently checked against `D/M` and the DATA-only Garwood formulas. Every
ROOT file reopened with the exact seven-object schema, including the renamed
985-point `ratio_graph_garwood_data`; the former
`ratio_graph_garwood_plus_mcstat` is absent. PDF text extraction over all 47
files found none of the removed banner, footer, old uncertainty, or old legend
terms. The focused plotting suite passed 10/10.

The refreshed gallery contains 235 files totaling 205,907,829 bytes. The
deterministic SHA-256 digest of the sorted per-file SHA-256 lines is
`fa531a25e1852259d786a8fc9ba6b3755b8eac2074952fb143c67f4875f50a4a`.

## Physical-period lane and complete ratio-gallery refresh

No batch job was submitted, no merged ROOT file was replaced, and no physical-
period event/ratio-pad gallery was generated in this refresh. The existing
ratio-versus-run gallery was regenerated from the same five frozen compiled
pickles and matching merged ROOT files recorded above.

The run-axis renderer now derives physical-period membership from the exact
compiled `nominal` luminosity rows. It collapses only version subdivisions of
one year-letter period: `2023C_v1`--`2023C_v4` become `2023C`,
`2023D_v1/v2` become `2023D`, and `2024I_v1/v2` become `2024I`. The resulting
15 spans contain, in order, 19/106/45 runs for 2022 B/C/D, 51/118/21 runs for
2022 E/F/G, 126/43 runs for 2023 C/D, and 43/37/46/121/143/21/45 runs for 2024
C/D/E/F/G/H/I. No unconfigured A period or other period is fabricated. Short
accessible-color separators occupy only the bottom 0.00--0.06 axes fraction;
transparent-background letter labels occupy the same compact lane without
covering the DATA points, era labels, selection annotation, or legend. Every
JSON receipt records the full year-letter identity, first and last run, bin
range, and run count for every span.

All 48 categories were attempted from one prevalidated in-memory load of the
five inputs. Exactly 47 categories produced complete PNG, PDF, CSV, JSON, and
ROOT sets. `DY_STREAM_EGAMMA_ZMM` remains the sole scientifically guarded
stem because its 2023BPix visible MC total is nonpositive; it has no partial
output. The promoted in-place gallery therefore contains exactly 235 files,
47 of each extension, totaling 215,758,908 bytes. All PNG files are
3000-by-1560 pixels. The CSV files contain 45,684 valid rows and 611 explicitly
invalid rows. Independent post-promotion checks passed for every receipt-
addressed SHA-256, the DATA-only Garwood formulas, era-specific MC relative
uncertainties, exact 15-span period membership, the seven-object ROOT schema,
985 bins/graph points per product, finite 985-by-985 covariance matrices, and
zero cross-era MC covariance. PDF text extraction also confirmed that the
previously removed titles, banners, footer explanations, and obsolete legend
terms remain absent.

Full-resolution visual inspection covered both the inclusive
`DY_ALL` result and the sparse `DY_HLT_MU8_ELE23_ZMM` result. It confirmed that
the period lane is legible, the label backgrounds are transparent, the legend
is complete, and the lane does not collide with the era or category text.
After promotion, the focused plotting suite passed 14 tests and the complete
leaf suite passed 135 tests in 37.63 seconds.

The deterministic SHA-256 digest of the sorted per-file SHA-256 lines for this
exact 235-file gallery is
`bce776a67826940934c77cb945609aa70e8be5746f4fc69ec2b7772ada3e3986`.
