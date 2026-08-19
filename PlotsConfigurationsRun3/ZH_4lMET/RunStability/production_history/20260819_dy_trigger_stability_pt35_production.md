# 2026-08-19 strict selected-Z 35/35 GeV run-stability production

> **Historical production and retained-reproduction record.** The first sections preserve
> the superseded `Z0_mass`-only and five-observable submissions and their exact
> cancellation evidence. They are not valid inputs for retained pT35 results.
> The completed replacement campaign used
> `RUN_STABILITY_OBSERVABLES=dy_lepton_kinematics`, resolving in exact order to
> `Z0_mass,Z0_pt,lZ1_pt,lZ2_pt,lZ1_eta,lZ2_eta` for the same 48 categories. No
> historical tag or pickle was reused. The completed five-era obs6 production,
> merged files, and promoted plot galleries are recorded after the canceled
> evidence.
> Its five exact pickles and merged ROOT files remain the current
> `plot_reproduction.json` inputs, but the redesigned live JSON/Python source is
> a future-production contract and must not be reconstructed from these dated
> generated artifacts.
> The original mass-only artifacts are also selection-invalid: their
> RUN_STABILITY parent override omitted `Passes2lOrderedPt`, so the configured
> 35/35 GeV alias never entered the compiled DY cut. They must not be reused
> even for a mass-only result.

## Scope and scientific identity

This campaign repeats the focused DY trigger-stability matrix after requiring
both leptons in the already selected closest-OSSF `Z0_idx` pair to satisfy
strict ordered thresholds `pT > 35 GeV` and `pT > 35 GeV`. A selected lepton
exactly at 35 GeV fails. Candidate construction remains unchanged.

The runtime override is `SELECTION_PROFILE=run_stability_zpt35`. It is
leaf-local, RUN_STABILITY-only, and DY-only. It deliberately leaves
`year_config.json` unchanged because that file owns DATA membership and is a
frozen luminosity-audit input. The profile and thresholds are serialized in
the exact pickle, analysis contract, compressed worker payload, generated
worker script, and tag.

The shared local identity is:

```text
JOB_CAMPAIGN=DY_TRIGGER_STABILITY_PT35_20260819T002748Z
```

Every era uses `Z0_mass`, the canonical ordered 48-category selector,
`SAMPLE_PROFILE=presentation`, `FILES_PER_JOB=10`, nominal systematics only,
and no sample, file, DATA stream, or DATA run filters. The exact frozen audit
is:

```text
/uscms_data/d3/mwadud/private/mkShapesRDF_devel/lumi/audits/ZZ_CR_RunStability_BCD_afa86d85_conjunction_20260818T200415Z/results
```

Its manifest, passing validation report, provenance, and live
`year_config.json` SHA-256 values are respectively:

```text
62e24cbe5db00035810f0d6a550a958668b998c65505b9e4fad652caa2ce3ec7
efadd80d3dbeb9c21e9896d3a02e3a5428631a21ab05a3ee1e616d5df96dfb13
528a25a1167e41eed3c4fd5d880e198b86685fb640f3708e0771b30cacaf2c1c
afa86d851cd46c01b57598c9b865e7d9a8e6cbbb1dd2db7e1aa894e8d6ba3ba2
```

## Runtime mechanism and validation

The implementation adds `run_stability_zpt35` to the leaf-owned runtime
profile registry rather than the year configuration. It resolves to
`ordered_2l_pt_mins=(35.0, 35.0)` and retains the ordinary four-lepton
thresholds `(25.0, 15.0, 10.0, 10.0)`. The compiled alias expression is:

```text
FourLepton::passesOrdered2lPtThresholdsFromPair(Lepton_pt, Z0_idx, 35.0, 35.0)
```

The existing C++ helper sorts only the selected pair and compares with strict
`>`. The focused profile tests include the boundary: 35.0/35.0 fails and
35.001/35.001 passes.

The dry-run and live-submission workflow was intentionally split. First,
`mkShapesRDF -c 1 --submit -dR 1` compiled and expanded the plan without
submission. The newly created pickle was reopened and checked. Only then was
the same snapshot submitted with
`mkShapesRDF -c 0 --submit -dR 0 -config <exact-pickle>`.

The focused four-test profile suite passed. After correcting stale positive
test fixtures to use this frozen B--D audit and updating the current `all_dy`
inventory from 48/1,200 to 96/2,400 categories/paths, the complete leaf suite
passed: 134 tests in 37.99 seconds. The legacy workspace-luminosity manifest
remains covered by a separate fail-closed test.

## 2022 submission ledger

The 2022 remote identity is:

```text
PRODUCTION_CAMPAIGN=DY_RUN_STABILITY_PT35_2022_20260819T002748Z
```

The remote parent was absent before submission, and the proxy had 583,645
seconds remaining. The exact DATA inventory contains the required ten B--D
components and 739 files: MuonEG B/C/D, SingleMuon B/C, Muon C/D, and EGamma
B/C/D with their sample-specific de-duplication weights. The compiled plan has
170 runs, 48 selected categories, one observable, 14 luminosity sources, 29
metadata paths, 48 auxiliary DATA paths, and 511 Condor splits.

| Field | Exact value |
| --- | --- |
| Pickle | `configs/config_26-08-18_19_37_13.pkl` |
| Pickle SHA-256 | `d482e41e359671dd3e039b000b1a575426e1cfbdd9566dad67073b3bf480c0b0` |
| Tag | `FourLepton_2022_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-custom-be24d1ac1df9_SEL-run-stability-zpt35_20260819_003658` |
| Cluster | `30093815` |
| Schedd | `lpcschedd5.fnal.gov` |
| Submitted jobs | 511, ProcIds 0--510 |
| Analysis contract SHA-256 | `5dc768842c1311c02204536d59082fb295e315a53d071007a2fe73cef0868a94` |
| Worker payload SHA-256 | `9a7583b995d8e69f69dec6c9cc6de56fd1a0d95f7f465776ad54eb6da4de99b6` |
| Submit receipt SHA-256 | `0feed3bab4c6d9cd8082fea44ed39a9408c9ade66391e96846c1db7719beaec4` |

The framework's direct `condor_submit` execution returned local `ENOEXEC`;
its existing argument-safe `/bin/sh /usr/local/bin/condor_submit` fallback
then succeeded. The durable receipt records `30093815.0 - 30093815.510`, the
submit stderr receipt is empty, and the scheduler GlobalJobId identifies
`lpcschedd5.fnal.gov`.

At `2026-08-19T00:44:57Z`, 506 jobs remained in the live queue: 421 idle and
85 running, with no holds observed. A subsequent exact-schedd history query
found seven completed records, all `JobStatus=4` and `ExitCode=0`; queue and
history snapshots are transient and can overlap while the scheduler updates.
Submission is therefore established, but completion, exact remote split-set
equality, ROOT reopening, merging, plotting, and physics interpretation are
not yet validated. No deletion, merge, plot production, or remote cleanup was
performed in this lane.

## Cancellation and replacement contract

The `Z0_mass`-only campaign was stopped before scientific promotion. On
`lpcschedd5.fnal.gov`, the exact job working directories first established
that clusters `30093815` (2022), `30093858` (2022EE), `30093863` (2023), and
the additional exact campaign match `30093869` (2023BPix) all belonged to
`JOB_CAMPAIGN=DY_TRIGGER_STABILITY_PT35_20260819T002748Z`. Immediately before
removal, the active states were one running job in 2022; 791 idle and 158
running jobs in 2022EE; 707 idle jobs in 2023; and 455 idle jobs in 2023BPix,
with no held jobs. The exact four clusters were removed with `condor_rm`.
The final exact-campaign query found zero idle, running, or held jobs. Removed
ClassAds briefly remained visible with `JobStatus=3` while the schedd completed
queue cleanup; scheduler history records `via condor_rm (by user mwadud)`.
No 2024 cluster had been submitted on that schedd under this campaign identity.
No local job directory or remote output was deleted during cancellation.

Future pT35 campaigns must use the canonical selector:

```bash
export RUN_STABILITY_OBSERVABLES=dy_lepton_kinematics
```

It resolves to six ordered observables: `Z0_mass`, `Z0_pt`, `lZ1_pt`,
`lZ2_pt`, `lZ1_eta`, and `lZ2_eta`. With the canonical 48 categories this
produces 288 ordinary MC TH1 slots and 288 matching DATA run-resolved TH2
paths per era. The original selector string and the resolved six-name sequence are retained
in the compiled contract, and the tag contains
`OBS-dy-lepton-kinematics`. A future submission must use a new collision-free
local and remote campaign identity; the cancelled tags and pickles above must
not be reused.

The superseding source contract also restricts the RUN_STABILITY DY parent to
strict `Z0_mass > 60. && Z0_mass < 120.` and gives the named selector uniform
axes: `Z0_mass` 60--120/1 GeV, `Z0_pt` 0--100/5 GeV, both selected-Z lepton
pT axes 35--100/5 GeV, and both eta axes -2.5--2.5/0.1. Mass/eta use
`fold=0`; `Z0_pt` and lepton pT use overflow-only `fold=2`, leaving sub-35
GeV lepton entries in underflow and folding values above 100 GeV into the last
95--100 GeV bin. Ordinary TH1s and DATA TH2 y axes
share these definitions. This is scoped to the named selector; the
full `all_dy` profile, explicit CSV selectors, non-RUN_STABILITY axes, and
FOURL/ZZCR/SR selections retain their previous behavior. No jobs were
submitted for this revised source contract.

The compile used branch `ZH_devel` at Git revision
`6f9b4ff164ec985575aa1c4da7c3c73839446001` with `git_dirty=true`. The
scientific numerical identity is carried by the exact pickle and hashes above;
it must not be reconstructed from the mutable worktree or a `latest` alias.

### Final scheduler accounting and 2024 dry-run state

The following exact accounting completes the cancellation record above. No
job from the original `DY_TRIGGER_STABILITY_20260818T214258Z` campaign was
included.

The four submitted snapshots were:

| Era | Exact pickle | Pickle SHA-256 | DATA files | Runs | Condor jobs | Cluster |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 2022 | `config_26-08-18_19_37_13.pkl` | `d482e41e359671dd3e039b000b1a575426e1cfbdd9566dad67073b3bf480c0b0` | 739 | 170 | 511 | `30093815` |
| 2022EE | `config_26-08-18_19_46_15.pkl` | `1843fe58253ce0cbc620f56044b099aeac70a734a29ae0c03d69a3bc5afebe3e` | 1,507 | 190 | 1,216 | `30093858` |
| 2023 | `config_26-08-18_19_51_44.pkl` | `fb9a166b2124aacb4572feb2dcd772496d282959b16ddbdd9c4973dedd923813` | 1,260 | 126 | 707 | `30093863` |
| 2023BPix | `config_26-08-18_19_58_29.pkl` | `1d2f99ed6a4b7ad097a6987b333cb42996742f916d1cedd47be152f9e4422007` | 621 | 43 | 455 | `30093869` |

All four receipts identify `lpcschedd5.fnal.gov`. Exact `condor_rm -name
lpcschedd5.fnal.gov <cluster>` requests were accepted for clusters `30093815`,
`30093858`, `30093863`, and `30093869`. After the removal queue drained, an
exact-cluster query returned no queue records and therefore no idle, running,
held, or pending-removal jobs. The final scheduler history was:

| Cluster | Final history records | `JobStatus=4, ExitCode=0` | `JobStatus=3` |
| ---: | ---: | ---: | ---: |
| `30093815` | 511 | 510 | 1 |
| `30093858` | 1,216 | 267 | 949 |
| `30093863` | 707 | 0 | 707 |
| `30093869` | 455 | 0 | 455 |

Within the removed records, cluster `30093815` had one undefined exit code;
cluster `30093858` had 908 undefined exit codes and 41 recorded zero exit
codes; all removed records in clusters `30093863` and `30093869` had undefined
exit codes. These are scheduler terminal-state facts, not validation of any
partial remote ROOT products. Exact live and history searches on
`lpcschedd4.fnal.gov` and `lpcschedd6.fnal.gov` found no matching
`DY_TRIGGER_STABILITY_PT35_20260819T002748Z` ads.

The 2024 dry-run compile was interrupted on explicit operator instruction by
terminating its task-owned local `mkShapesRDF` process before submission. It
created `config_26-08-18_20_05_21.pkl` with SHA-256
`77775d0d272a21452624e8fa768fed0afbfc385fc9855eed5954beefd9b21694` and
the tag
`FourLepton_2024_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-custom-be24d1ac1df9_SEL-run-stability-zpt35_20260819_010508`.
The snapshot records 456 runs, 48 categories, `Z0_mass`, 10,671 DATA files,
and the strict `(35.0, 35.0)` selected-pair thresholds. Batch expansion had
not produced a `submit.jdl` or submit receipt, so no 2024 cluster existed.

The cancelled campaign's local control material was preserved under the
workspace `.codex-trash/DY_TRIGGER_STABILITY_PT35_20260819T002748Z` identity
rather than destroyed. After the queue reached zero, one small residual 2022EE
control subtree reappeared under the leaf's cancelled campaign directory; the
coordinator moved it separately to
`.codex-trash/DY_TRIGGER_STABILITY_PT35_20260819T002748Z-post-drain-residual`.
The leaf's `jobs/` directory then contained exactly the original
`DY_TRIGGER_STABILITY_20260818T214258Z` campaign. No remote-output deletion
was performed. Consequently, scheduler cancellation and recoverable local
cleanup are established, while disposition or validation of any partial
remote outputs remains a separate, unfinished action.

## Correction: replacement tag identity

The future-tag statement at lines 147--149 predates the concise tag contract.
The superseding six-observable, 48-category, strict-35/35 source now uses
`DYRS_<YEAR>_pt35_m60to120_obs6_cat48-be24d1ac_<UTCmicro>Z`, where the
timestamp is compact UTC with microseconds. This correction does not alter any
cancelled tag, pickle, cluster, scheduler record, or remote-output identity
above. Before a replacement submission, contract writing must validate that
the concise label matches the resolved mass cut, `Passes2lOrderedPt`, selected
profile, six axes, observable order, and canonical category order/hash.

## Superseded obs5 submission and final cancellation

The first concise five-observable 2022 replacement was compiled under:

```text
JOB_CAMPAIGN=DYRS_PT35_M60TO120_OBS5_20260819T014838Z
PRODUCTION_CAMPAIGN=DYRS_PT35_M60TO120_OBS5_2022_20260819T014838Z
```

One preliminary configuration load used a manually pasted category selector
with six duplicate names. The leaf rejected it before writing a pickle, JDL,
submit receipt, or scheduler cluster. The subsequent dry run extracted the
canonical 48-name selector verbatim and produced this exact identity:

| Field | Exact value |
| --- | --- |
| Pickle | `configs/config_26-08-18_20_51_15.pkl` |
| Pickle SHA-256 | `06a47537d263900fdab4c7a04bbe214f583338518b0bb86a3049f8926af9c929` |
| Tag | `DYRS_2022_pt35_m60to120_obs5_cat48-be24d1ac_20260819T015100469898Z` |
| Schedd | `lpcschedd5.fnal.gov` |
| Cluster | `30094065`, ProcIds 0--510 |
| Submit receipt SHA-256 | `d55f9e2f625513c65dec5ed1d5525598a0afe8c1aa9097346c34c93ba9cc35e3` |
| Runtime archive SHA-256 | `bea0b33344a36a93db511614d8acb432e0d8b4b9fd92a86358da7507e7bfbdfd` |

Before submission, all 4,850 configured input-file occurrences were shown to
appear exactly once across 511 generated worker scripts, with at most ten
files per job. The plan had the corrected ten-component B--D DATA matrix (739
DATA files), 48 categories, the five ordered observables
`Z0_mass,lZ1_pt,lZ2_pt,lZ1_eta,lZ2_eta`, and 240 category-variable paths.
Contract and worker tag identities agreed. The strict DY parent contained
`Z0_mass > 60. && Z0_mass < 120.` and `Passes2lOrderedPt`; the selected-pair
thresholds were `(35.0, 35.0)`. The frozen luminosity contract passed and
retained 8.0 fb^-1 as the configured MC source denominator while its nominal
2022 B--D extraction was 8.076828657919002 fb^-1. The exact live
`year_config.json` SHA-256 was
`afa86d851cd46c01b57598c9b865e7d9a8e6cbbb1dd2db7e1aa894e8d6ba3ba2`.

The exact pickle was submitted once. The framework's argument-safe fallback
handled local `condor_submit` `ENOEXEC`, and the scheduler accepted
`30094065.0 - 30094065.510`. This obs5 campaign was then declared superseded
and removed with `condor_rm` before scientific promotion. The final
exact-schedd queue query returned zero records. Scheduler history contained
exactly 511 unique ProcIds, 0 through 510 once each; every record had
`JobStatus=3` and removal reason `via condor_rm (by user mwadud)`. There were
therefore no idle, running, held, or pending-removal jobs after drain, and no
completed split set is claimed.

The remote tag directory existed after drain but was empty: zero entries and
zero bytes. Its remote parent contained only that tag directory. No remote
object or directory was deleted. The complete local campaign control tree
(1,032 files; 87,189,794 bytes), together with the separately preserved empty
failed-precompile directory, was moved recoverably to:

```text
.codex-trash/DYRS_PT35_M60TO120_OBS5_20260819T014838Z_cancelled_cluster30094065_20260819T020115Z
```

The leaf `jobs/` directory again contains only the older
`DY_TRIGGER_STABILITY_20260818T214258Z` campaign. The trash directory owns a
`CANCELLATION_RECEIPT.md` with the scheduler, local-artifact, and remote-audit
facts. This obs5 submission is cancelled evidence and must not be reused as a
completed production input.

## Completed six-observable replacement

The final replacement used one local campaign directory for all five analysis
eras:

```text
JOB_CAMPAIGN=DYRS_PT35_M60TO120_OBS6_20260819T021244Z
```

Every tag, merged file, and promoted gallery named in the sections below is a
child of `jobs/DYRS_PT35_M60TO120_OBS6_20260819T021244Z/` unless an absolute
path is stated explicitly.

Each era used its matching
`PRODUCTION_CAMPAIGN=DYRS_PT35_M60TO120_OBS6_<ERA>_20260819T021244Z`, the
frozen luminosity audit named above, and the unchanged live
`year_config.json` SHA-256
`afa86d851cd46c01b57598c9b865e7d9a8e6cbbb1dd2db7e1aa894e8d6ba3ba2`.
The exact contract selected 48 un-enriched DY categories and the six ordered
observables `Z0_mass,Z0_pt,lZ1_pt,lZ2_pt,lZ1_eta,lZ2_eta`. It required strict
selected-pair pT thresholds above 35 GeV, strict `60 < Z0_mass < 120 GeV`, and
the focused uniform axes documented in `README.md`. The product was 288
category/observable paths per era. No ZZCR or SR category was included.

Compilation and submission were serialized by era. Every dry-run pickle was
deserialized and matched one-to-one to its tag, local campaign, remote
campaign, generated JDL, and submit receipt before the exact snapshot was
submitted. The complete identity ledger is:

| Era | Tag | Exact pickle (SHA-256) | Input-registry SHA-256 | DATA / all input files | Runs | Cluster / jobs |
| --- | --- | --- | --- | ---: | ---: | --- |
| 2022 | `DYRS_2022_pt35_m60to120_obs6_cat48-be24d1ac_20260819T021326317830Z` | `config_26-08-18_21_13_41.pkl` (`5e1b8858659375adba2c683a8b840b7dcad32fd63f429f8f6f841711ffb2549f`) | `f0c4ca3e179968ac5d6d2e7efee8f68232a67421d2ab5118b9ea58d5f4dca9ad` | 739 / 4,850 | 170 | `30094111` / 511 |
| 2022EE | `DYRS_2022EE_pt35_m60to120_obs6_cat48-be24d1ac_20260819T022010672391Z` | `config_26-08-18_21_20_27.pkl` (`5c1ebaf35b0db8b1a12f5b48de7c952c5062a3937d642065139d905f82a11050`) | `7fcd9c547398630a78cb2bc72d6bd9b3a935ab3e71c3dfd3cf2ad090d22123c4` | 1,507 / 11,885 | 190 | `30094116` / 1,216 |
| 2023 | `DYRS_2023_pt35_m60to120_obs6_cat48-be24d1ac_20260819T022654108304Z` | `config_26-08-18_21_27_20.pkl` (`e78c841d41f38c40b0b7077def01a73eabc25fbc2aff5dcd135043c224a81568`) | `be89bd2ea5b03028ee4f482a2d7dc0c56f479acc4a369753727ec8de2ece8a78` | 1,260 / 6,816 | 126 | `30094137` / 707 |
| 2023BPix | `DYRS_2023BPix_pt35_m60to120_obs6_cat48-be24d1ac_20260819T023256488564Z` | `config_26-08-18_21_33_11.pkl` (`6bb9da23ae1da462f2e2fa2ff1c3c6b59d9ecc01310100392d82b23194dc6551`) | `b31f4bfaba2709d52d83b15f3e569f8315777c011f61413e1b07eb854b7aa35c` | 621 / 4,309 | 43 | `30094169` / 455 |
| 2024 | `DYRS_2024_pt35_m60to120_obs6_cat48-be24d1ac_20260819T023826650284Z` | `config_26-08-18_21_38_40.pkl` (`6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef`) | `93565a5c38dda99d4cab32009c727c0048bd90724f6a788a50f93f04ad295a67` | 10,671 / 39,394 | 456 | `30094594` / 3,967 |

All five clusters ran on `lpcschedd5.fnal.gov`. Exact queue/history
reconciliation found every expected ProcId terminal with `JobStatus=4` and
`ExitCode=0`. The generated split set equaled the durable remote split set,
and every split ROOT file independently reopened. Close-time XRootD warnings
reported by the framework checker were therefore retained as transport
evidence and were not used to duplicate successful jobs.

Each era was merged only with the exact pickle in the table. The merged files
were independently reopened and checked for the exact 48-by-6 ordinary and
DATA auxiliary matrix, the expected run axis, and one copy of all 29
luminosity metadata objects. Their durable local identities are:

| Era | Merged bytes | SHA-256 | Adler-32 |
| --- | ---: | --- | --- |
| 2022 | 17,463,861 | `852508b2c1d2192ed7b37f10d12a99d1e0338ea651fa640d0ff08d423f83888e` | `9181b85f` |
| 2022EE | 19,398,911 | `8c4e9f8b659488a80e6b3b50d2d9391fede4ac051bbbcea04fd175b8736a7900` | `c529becb` |
| 2023 | 17,264,029 | `3519375dae64fa82b2d94d25510c93e0d9f5a76d7f6494911a779c97ae863290` | `bf18c1d0` |
| 2023BPix | 14,295,393 | `63d59b58cd79e46fc8ef62c5122f323abc13ed4c9c97aa1d64f1aefe0b3cf2b0` | `a7408fe7` |
| 2024 | 30,014,031 | `6b6a189a71b3c05ef2aad467e42014150a791469591f5d854420b36a213161f9` | `12242fce` |

## Promoted physical-period DATA/MC galleries

The supported Python/Matplotlib `period-plot` renderer produced every
physical-period, category, and focused-observable combination. Each stem has
PNG, PDF, CSV, JSON, and ROOT products. The retained galleries are:

| Physical periods | Directory | Stems | Science artifacts |
| --- | --- | ---: | ---: |
| 2022B--2022G | `period_datamc_2022_2022EE_FINAL_20260819T035902579974818Z` | 1,728 | 8,640 |
| 2023C--2023D | `period_datamc_2023C_2023D_final_20260819T035549316101466Z` | 576 | 2,880 |
| 2024C--2024I | `period_datamc_2024_PROMOTED_20260819T035835837179Z` | 2,016 | 10,080 |
| **Total** |  | **4,320** | **21,600** |

For the independently audited 2023C--2023D set, the aggregate SHA-256 is
`329692216948838d6aa3590492c22a89822b769f0ed2034ae96ef556ab05ae10`.
That audit first reduces every science file to a
`<file SHA-256><two spaces><basename>` line, sorts the complete lines
lexicographically with `LC_ALL=C` (therefore primarily by hash), and hashes
the resulting line stream. A basename-first manifest has a different digest
and is not the recorded oracle.

The independent artifact and visual audits passed for all three galleries.
The upper pad contains exactly the compiled DY process group plus its disjoint
`Others` complement. The MC stacks are solid, edge-free fills; the aggregate
is a `Total MC` step with a same-color transparent uncertainty band. The
legend reports DATA, DY, Others, and Total MC yields with DATA Poisson and MC
Sumw2 uncertainties. The lower pad is labelled `Data/MC`, uses DATA-only
Garwood bars plus the separate MC Sumw2 band, and records every adaptive-range
decision and clipped marker. The final images have no top/right ticks and
passed the six-pixel canvas-boundary/collision audit.

## Promoted Z-mass ratio-versus-run gallery

The final multi-era gallery is:

```text
stability_ratio_zmass_FINAL_20260819T052000000000000Z
```

It contains exactly 48 stems and 240 science artifacts: one PNG, PDF, CSV,
JSON, and ROOT product for every selected category. The aggregate science-file
digest recorded by the independent audit is
`118d9762d79b306ed22ad60237d9b3783543db88f3b09bd2875f22aafb2dfdfe`.
It uses the same reproducible full-checksum-line convention documented for the
2023C--2023D gallery above, restricted to the 240 CSV/JSON/PDF/PNG/ROOT
science files.
Every stem contains 985 ordered run rows (170 + 190 + 126 + 43 + 456), for
47,280 reconstructed CSV rows in the gallery. The ROOT covariance matrices
have the full 985-by-985 shape, retain shared-template covariance within an
era, and have zero cross-era MC covariance.

The final schema-4 presentation uses DATA-only Garwood point bars, one
era-specific MC relative-Sumw2 band around unity, and the exact legend entries
`Data`, `MC`, `Out of range`, and `Zero lumi.`. Forty-four categories used the
five-point uncertainty-aware median/MAD range; four used the documented sparse
fallback. The run-period lane, short separators, transparent period labels,
dynamic unity tick, in-axis category/legend placement, and directional
out-of-range markers all passed the independent full-size visual audit. These
presentation decisions did not alter any stored ratio or covariance value.

## Promoted reduced-chi-square-versus-run gallery

The final six-observable, 48-category gallery is:

```text
stability_chi2_obs6_FINAL_v2_20260819T053450604464Z
```

Before any writer started, its structured preflight silently reopened all five
exact compiled pickles and required the ordered unique 48-category contract,
the exact selector SHA-256
`be24d1ac1df9a8b1f91b05187031c1e83fee2825c10cee0c690e73121f3d03a5`,
and the ordered six-observable tuple. The resulting 288-command Cartesian
product produced exactly 288 each of JSON, CSV, ROOT, PNG, and PDF: 1,440
science files totaling 7,987,542,789 bytes. Every PNG is 3,000 by 1,560 pixels,
all eight generation shards completed, and their stderr streams were empty.

The aggregate science-file SHA-256 is
`21695602f129f39cd028e9678a50471336c51a08cba66a4ac39cddc121096459`.
Unlike the textual-manifest digests recorded above, this digest is a binary
tuple stream. Iterate the 1,440 science files in basename order and, for each
file, append its UTF-8 basename, one NUL byte, and its raw 32-byte SHA-256
digest to one aggregate SHA-256 accumulator. The exact reproducer is:

```python
import hashlib

h = hashlib.sha256()
science = {".json", ".csv", ".root", ".png", ".pdf"}
for path in sorted(output_directory.iterdir(), key=lambda item: item.name):
    if path.suffix not in science:
        continue
    h.update(path.name.encode("utf-8"))
    h.update(b"\0")
    h.update(hashlib.sha256(path.read_bytes()).digest())
print(h.hexdigest())
```

The schema-2 receipts use
`focused_reduced_chi2_informative_core_v2`. Independent reconstruction closed
all 9,739,680 serialized observable-bin rows and 283,680 run rows, including
the linear luminosity scale on MC Sumw and the squared scale on MC Sumw2.
Every one of the 288 ROOT files reopened with 15 expected objects, and every
serialized ROOT cell agreed with its JSON/CSV counterpart. The final
inventories contain 64,605 top-clipped markers, no bottom-clipped markers,
and 3,744 invalid run points; clipping affects presentation only.

The plots contain no run-point error bars. They use a horizontal reference at
one, the approximate $1 \pm \sqrt{2/\mathrm{ndf}}$ expectation band, the visible
mathtext label `$\chi^2_{\mathrm{red}}$`, the physical-period lane, and an
opaque in-axis legend. All ranges start at zero. Across categories, their
upper limits span 1.296--5 for `Z0_mass`, 1.421526--5 for `Z0_pt`,
1.503611--5 for each selected-lepton pT, and 1.296--5 for each selected-lepton
eta. Six original-resolution PNGs spanning inclusive, flavor, stream,
trigger-family, concrete-path, dense, sparse, outlier, and invalid-point cases
passed the final visual audit with the complete 2022 region centered and
visible.

Two earlier full-gallery attempts remain failed evidence rather than
promoted results. `stability_chi2_obs6_FINAL_v2_20260819T052806256243Z` was
stopped because human-readable diagnostic stdout contaminated the category
array. `stability_chi2_obs6_FINAL_v2_20260819T053019061513Z` was stopped
because it did not assert the exact category tuple and full hash before its
writers began. The earlier
`stability_chi2_obs6_FINAL_20260819T044155478307Z` also failed visual review
because extreme tails flattened the useful range and translucent legend
content overlapped plot marks. These identities are `NOT_PROMOTED`; the fresh
identity above supersedes them without rewriting their evidence.

The focused plotting tests passed 39/39 and the complete leaf suite passed
178/178 after the final layout correction; the renderer SHA-256 exercised by
the gallery is
`3bdb6c896fdee9f4a00ac9655d1ca065555d8790e8d7e04d4fba7f8b859e0207`.
These checks establish the implemented algebra, serialization, file layout,
and documented display behavior. The statistic remains the interval-based
Pearson diagnostic defined in `LUMINOSITY_PROPAGATION.md`, not an exact
Poisson or finite-MC likelihood goodness-of-fit, and its correlated run-point
covariance remains explicitly uncomputed.

## Final local artifact cleanup

After all three promoted plot products passed their independent gates, the
task-owned local cleanup permanently deleted 21 explicit entries: 19
directories and two individual files. Recursively, those targets contained
36,107 regular files, 7,509 directories, no symbolic links, and
10,101,684,541 regular-file content bytes (10,104,441,000 apparent bytes by
the recorded `du -sb` summation). This was direct deletion rather than a move
to trash, so these final-cleanup targets are not locally recoverable. No
remote or EOS object was deleted.

The removed entries were the old
`DY_TRIGGER_STABILITY_20260818T214258Z` campaign; two partial 2023 period
galleries; two ratio-range CV directories; two non-promoted ratio galleries;
the final ratio gallery's driver `commands.log` and empty
`failed_categories.txt`; the first failed chi-square gallery and its logs;
the failed hard-cap CV and its logs; the later successful bounded CV and its
logs after its result had been incorporated; the two failed final-v2
chi-square identities and their logs; the promoted chi-square gallery's
sibling driver logs after audit; and the final 2022--2022EE period gallery's
24-file nested driver/status `_logs` directory. Their scientific and failure
history remains in this ledger even though their transient local artifacts do
not.

The final `jobs/` top level contains exactly one directory:

```text
DYRS_PT35_M60TO120_OBS6_20260819T021244Z
```

That campaign has exactly ten direct children: the five production tags from
the completed-production table, the three promoted physical-period galleries,
`stability_ratio_zmass_FINAL_20260819T052000000000000Z`, and
`stability_chi2_obs6_FINAL_v2_20260819T053450604464Z`. There are no remaining
`NOT_PROMOTED` markers, `commands.log` files, `failed_categories.txt` files,
top-gallery log directories, or plotter processes. The retained gallery file
counts remain 8,640, 2,880, and 10,080 for the three period galleries, 240 for
the ratio gallery, and 1,440 for the reduced-chi-square gallery. The five
merged ROOT files retain the exact byte sizes listed above. The final local
`jobs/` tree contains 50,759 files and 6,888 directories, no symbolic links,
and 10,204,301,285 apparent bytes.

### Post-cleanup credential correction

A final security scan after the artifact-cleanup receipt above found one
task-created X.509 proxy copy in each of the five retained era tag directories.
Each target was an ordinary mode-0600 file of 10,356 bytes. After resolving
those five exact local targets, the coordinator permanently removed them and
verified that no copied proxy remained below the retained campaign. The
operator's source proxy was not touched. No JDL, receipt, archive, manifest,
log, pickle, ROOT file, or remote/EOS output was changed.

This correction is intentionally separate from the preceding cleanup receipt:
that receipt remains an exact account of its first pass. Across both passes,
the cleanup removed 26 explicit local targets, including 36,112 regular files
and 10,101,736,321 regular-file content bytes. The five additional credential
targets contributed exactly 51,780 bytes. The final local `jobs/` tree
therefore now contains 50,754 regular files and the same 6,888 directories;
the one retained campaign still has the ten direct children recorded above.
No removed proxy copy is locally recoverable.
