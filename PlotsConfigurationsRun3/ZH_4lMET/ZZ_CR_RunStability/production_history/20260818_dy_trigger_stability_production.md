# 2026-08-18 DY trigger-stability production

## Scope

This record owns the replacement five-era production requested for DY run
stability by broad stream, positive trigger family, and concrete HLT path.
The common local control identity is:

```text
JOB_CAMPAIGN=DY_TRIGGER_STABILITY_20260818T175629Z
```

Each era uses a distinct remote identity
`DY_TRIGGER_STABILITY_<era>_20260818T175629Z`. Before submission, all five
remote parents and the common local parent were verified absent.

The exact matrix is one observable and 16 categories:

```text
Z0_mass

DY_ALL
DY_STREAM_MUONEG
DY_STREAM_MUON
DY_STREAM_EGAMMA
DY_TRGFAM_ELMU
DY_TRGFAM_SINGLEMU
DY_TRGFAM_DOUBLEMU
DY_TRGFAM_SINGLEEL
DY_TRGFAM_DOUBLEEL
DY_HLT_MU23_ELE12
DY_HLT_MU12_ELE23
DY_HLT_MU8_ELE23
DY_HLT_MU17_MU8
DY_HLT_ISOMU24
DY_HLT_ELE23_ELE12
DY_HLT_ELE30
```

`SAMPLE_PROFILE=presentation`, `FILES_PER_JOB=10`, and all sample, stream,
run, and per-sample file filters are cleared. The exact documented submission
entry point is `mkShapesRDF -c 1 --submit ... -l -1 -q workday` after sourcing
the framework and the leaf-local FNAL packaged environment.

## Source and preflight evidence

The child checkout was at HEAD
`a67e3fca9171012502c092a3ceed2b2f7a20d00e` on branch `ZH_devel`. The analysis
leaf is untracked in that checkout, so the numerical source identity is also
recorded directly:

| File | SHA-256 |
| --- | --- |
| `category_config.py` | `0f37c40cb30713bf9f681a3c440dad9804887a2c231cf60de0d4cfd967c2b17f` |
| `run_stability_config.py` | `a0f7be2d9c6a3bbdb6614c8ac804381e37753b7f907cccfa9079d1ac2d522314` |
| `zz_cr_runner.py` | `ac2ba2c081a1b17b5d6a25cbc6996cae3cfe1169bbbeb4bb94313539bec4f759` |
| `plot_run_stability.py` | `f6586c2eaf55d27f10f54db441c4d8525fcbcdf713f36cf6535c49ecd365ccf0` |
| `configuration.py` | `de99b6eb76dbbf964af3c0d912545a1164cd57eb0ef8474828e0a7e0279b4706` |

At `2026-08-18T17:56:29Z`, the CMS proxy had 519,045 seconds remaining. The
luminosity contract consumes the hash-validated nominal, positive-family, and
concrete-path tables in the workspace `lumi/results/` directory. The full leaf
test suite passed with 112 tests before submission. This establishes the
tested software invariants; it does not establish batch completion, ROOT
output validity, or physics agreement.

The five exact compiled pickle identities, tags, clusters, schedds, expanded
job counts, completed split sets, merged-file identities, and derived-plot
receipts are appended below as those gates complete.

## Corrected early-2022 DATA completeness audit

The earlier conclusion in this record was wrong: agreement among the aligned
DY reference, original `ZZ_CR`, this leaf, the compiled pickle, and the pinned
luminosity inventory established only that the same incomplete six-component
contract had propagated through all consumers.

The authoritative processor catalog
`mkShapesRDF/processor/framework/samples/Run2022_ReReco_nAODv12.py` contains
both `SingleMuon_Run2022C-ReReco-v1` and `Muon_Run2022C-ReReco-v1`, followed by
`Muon_Run2022D-ReReco-v1`. A live `root://eoscms.cern.ch` listing of the exact
configured HWWNano production and step found 35
`SingleMuon_Run2022C-ReReco-v1` files, zero `SingleMuon_Run2022D` files, 124
`Muon_Run2022C` files, and 82 `Muon_Run2022D` files. The required
period-dependent DATA matrix therefore has seven components and 707 currently
materialized files rather than the historical 672:

| Primary dataset | Logical stream | Run2022C | Run2022D |
| --- | --- | ---: | ---: |
| `MuonEG` | `MuonEG` | required | required |
| `SingleMuon` | `Muon` | required | not applicable |
| `Muon` | `Muon` | required | required |
| `EGamma` | `EGamma` | required | required |

The component weights are also sample-specific. `SingleMuon_Run2022C` receives
`!Trigger_ElMu && Trigger_sngMu`; `Muon` receives
`!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)`. Encoding one global
dataset list for C and D either omits `SingleMuon_Run2022C` or invents an
unsupported `SingleMuon_Run2022D`, while assigning only a stream-wide default
would erase the primary-dataset acceptance distinction.

The historical exact pickle contains only the other six components and 672
DATA files. Its 38 nonzero early-run `DY_ALL` bins prove that some DATA from
other streams survived, not that the Muon stream was complete. The pinned
luminosity inventory also names the original `ZH_4lMET/ZZ_CR/year_config.json`,
not the live RunStability leaf. Although its recorded SHA-256 happened to match
the copied pre-correction file, that identity becomes stale as soon as the
RunStability DATA contract is corrected and cannot authorize submission.

Missing `SingleMuon_Run2022C` removes early single-muon-accepted events,
including affected dimuon events, from DATA while the inclusive MC template
remains normalized to positive trigger exposure from the available union.
This biases the inclusive ratio low and has a larger effect in muon-channel
and muon-trigger categories. The former adaptive x-axis tick selection did
hide the first run label, but it did not cause the low ratios. Likewise, the
historical zero double- and single-muon path exposures for the first 35 runs
were calculated from incomplete owning-stream coverage and must not be
interpreted as physical path inactivity.

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
