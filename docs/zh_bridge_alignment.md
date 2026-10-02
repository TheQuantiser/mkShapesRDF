# zh-bridge upstream alignment — 2026-10-01

`zh-bridge` integrates the reviewed upstream history while preserving the
personal framework's inline worker contract. **This is an integration branch.
Tree-output and native ZZCR systematic acceptance remain incomplete, so it has
not been promoted to `ZH_devel`.**

## Revisions and scope

| Role | Revision |
| --- | --- |
| Personal baseline, `ZH_devel` | [`22cca33c7c39a573037e904c8422ce83f9572303`](https://github.com/TheQuantiser/mkShapesRDF/commit/22cca33c7c39a573037e904c8422ce83f9572303) |
| Reviewed upstream, `latinos/master` | [`c043c418645b765ca181dbd2e2bc1d0cc9627185`](https://github.com/latinos/mkShapesRDF/commit/c043c418645b765ca181dbd2e2bc1d0cc9627185) |
| Common ancestor | [`3cebbe4397981e406789d79ed44cda72fc5fbd6a`](https://github.com/latinos/mkShapesRDF/commit/3cebbe4397981e406789d79ed44cda72fc5fbd6a) |

The histories contain 46 personal and seven upstream commits since that
ancestor. The merge retains both histories. Seven incoming processor/catalog
files are imported byte-for-byte from the pinned upstream tree.

All `PlotsConfigurationsRun3` source, shared processor modules, production
steps, native analysis runner, CLI launcher, and runtime/remote-I/O libraries
remain identical to the personal baseline. In particular:

- `ZH_4lMET` remains the production compatibility reference during the ZH4l
  transition. The independent ZH4l leaves and shared nominal adapter remain.
- ZH, DY, ZZ and DATA membership, working points, corrections, cuts, weights,
  luminosities, histogram axes and event-tree contracts are unchanged.
- The separately demonstrated HWWNano producer repairs are **not integrated**.
  See [the RunStability issues record](../PlotsConfigurationsRun3/ZH_4lMET/RunStability/KNOWN_HWWNANO_ISSUES.md).

## Worker integration

[BatchSubmission.py](../mkShapesRDF/shapeAnalysis/BatchSubmission.py) adopts
upstream's sample-scoped alias/nuisance selection and sample-specific
`folderUp`/`folderDown` resolution. Filtering happens **before** runtime path
tokenization. Shared entries are retained; unrelated sample entries are removed;
the original configuration is protected through deep copies.

The filter also retains this job's actual flattened subsample names. Native
weight/envelope nuisances and `afterNuis` aliases consume child names after
`splitSubsamples()`. A filter considering only the parent would silently drop
those entries. Child names follow the native `flatten_samples_map` contract,
with `<parent>_<child>` as its existing default. Parent-only scopes remain
parent-only.

Both default and custom runners continue receiving the final in-memory
configuration inline in `script.py`, including extra `batchVars`, `job_id`,
the full original sample metadata, `remoteIO` and `limitEvents`. The native
worker still passes `limit=limitEvents` and
`remote_io_settings=remoteIO` to `RunAnalysis`.

The existing archive/extraction bootstrap, additional includes, relocated
paths, separate proxy transfer, validated JDL file lists, local output remaps,
stage-in/friend handling, cleanup, ROOT-handle release, remote stage-out policy,
submission fallback and checked receipts remain unchanged. See
[Condor and remote-I/O documentation](condor_remote_io.rst).

**Shared JSON worker loading is deferred.** The upstream `config.json` handoff
is not enabled here. A future implementation must serialize the final selected
configuration after CLI overrides, relocate JSON contents, and preserve custom
globals and explicit precedence. Transferring a previous compile's JSON would
not meet that contract.

## Imported catalogue limitations

The five incoming era catalogues preserve every pre-existing dataset mapping.
All 199 pre-existing cross-section entries retain their values. The 411 incoming
cross-section records round-trip through the one-sample serialization. `BaseW`
and its formula remain unchanged.

The import adds 152 catalogue entries in each 2022/2023 era and 212 in 2024.
The explicit ZH4l source lists have no intersection with these new keys.
**An unfiltered `mkPostProc` invocation does expand its default sample scope**;
catalogue additions are not automatically qualified analysis inputs.

These upstream issues were identified and preserved for a separate catalogue
correction:

| Incoming issue | Consequence before using the new entry |
| --- | --- |
| Inclusive `TWDMsimpSpin0` and `TBDMsimpSpin0` `_ps` keys point to `-s` datasets, and `_s` keys to `-ps`, in all five catalogues | Dataset type and logical cross-section key disagree for 56 keys per era; audit/correct the mappings before selecting them. |
| Summer24 has `ZH-HToNon2B`; the cross-section database has `ZH-HtoNon2B` | The new per-sample lookup raises `KeyError` for this added catalogue key. |
| `processor.py` now evaluates `xs_db[sampleName]` eagerly for every MC job | Existing missing keys also fail during generation for steps that do not consume `BaseW`; the serialization change has this additional compatibility limit. |

The relevant pinned sources are the
[2024 catalogue](https://github.com/latinos/mkShapesRDF/blob/c043c418645b765ca181dbd2e2bc1d0cc9627185/mkShapesRDF/processor/framework/samples/Summer24_150x_nAODv15.py#L551-L591),
[cross-section database](https://github.com/latinos/mkShapesRDF/blob/c043c418645b765ca181dbd2e2bc1d0cc9627185/mkShapesRDF/processor/framework/samples/samplesCrossSections_13p6TeV.py#L179),
and [sample serialization](https://github.com/latinos/mkShapesRDF/blob/c043c418645b765ca181dbd2e2bc1d0cc9627185/mkShapesRDF/processor/framework/processor.py#L434-L438).
No new sample was added to a personal analysis by this integration.

## Executed acceptance

Host: `cmslpc-el9-heavy02.fnal.gov`; Python 3.13.11, ROOT 6.38.00,
LCG 109 / EL9 / GCC 13. The existing original `start.sh` activated the runtime;
bridge commands explicitly selected the bridge package through `PYTHONPATH`.
No environment installation or dependency upgrade was performed.

| Check | Observed result |
| --- | --- |
| Focused generated-worker regression | Five tests pass: default/custom runners, packaged/shared modes, selected folders, relocated includes, limits, remote I/O, extra globals, metadata, immutability and child scopes. The four parent cases failed before filtering; the child case failed before the compatibility adjustment. |
| Existing ZH4l suite | 108 passed, 37.54 s. |
| Existing Z-pT suite | 50 passed, 1.93 s. |
| RunStability suite | 142 passed in the bridge. One historical-fixture test initially failed because ignored outputs are absent from a fresh worktree. All ten original fixtures matched their manifest hashes; the identical test passed from its original artifact location with the bridge framework already imported. No fixture was regenerated or test weakened. |
| Real CLI handoff | Two fresh compilations; latest and explicit older pickle selections preserved distinct custom markers. CLI limits 19/29, stage-in mode and output overrides reached generated inline workers. Preparation only; no event file opened or submission. |
| Pinned DY native local, baseline versus bridge | First 100 events; 74 pass preselection; all 228 histogram names, entries, axes, bin contents/errors and sumw2, including flows, agree exactly. |
| Packaged local worker | Fresh scratch, only declared transfers, no inherited checkout/environment paths; 228 histograms agree exactly with local execution. The archive had 667 members and no transferred proxy inside it. Payload execution took 18.519 s. |
| One actual LPC worker | `30573610.0` on `lpcschedd5.fnal.gov`: history records JobStatus 4, ExitCode 0, ExitBySignal false, wall time 56 s; queue empty. Independently reopened returned output: 228 histograms exactly match local, 149,810 bytes. |

The real DY input was exactly:

```text
root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/Summer24_150x_nAODv15_Full2024v15/MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight/nanoLatino_DYto2Mu-2Jets_MLL-50__part0.root
```

The executed final worker's `BatchSubmission.py` SHA-256 is
`f02e7744d6d421789bed8f2c550263a69b89f1fd7ea8bc51b0b1f60f736547a4`;
its runtime archive SHA-256 is
`56c2d9751c37e04b76024e3f3d083f4595068be815345207c92b54838e25e6e6`.
The returned ROOT SHA-256 is
`9fce1334ef3807f6e6a43faa6782cf67664d5f1ca07ce3175443f47156e2e4ff`.
The archive's producer file was checked against the final integration source.

### Remaining acceptance limits

- **ZH4l Example tree output:** the documented first-500-entry, two-file
  `both` run timed out at 300 s in baseline and bridge. The unchanged baseline
  also timed out with inputs staged locally (180 s) and with output moved to
  local `/tmp` (120 s). Snapshot actions were booked and graph execution did
  not finish. These observations do not identify the cause; remote streaming
  or shared output alone is insufficient to explain it. No completed tree
  artifact was available for the requested real-input identity/weight closure.
- **Native ZZCR systematics:** one pinned ZZ file, a 25-entry analysis limit and the
  canonical 100-entry capability inspection; 28 nuisance records retained
  (2 lnN, 10 weight, 15 suffix, 1 auto) with 30 exact suffix friends. Dataframe,
  alias, systematic and histogram/cut setup completed, then execution timed
  out at 180 s before a preselection count or output returned. No missing-friend
  diagnostic was recorded. Varied-output equivalence remains unverified.
- No full campaign, production-scale throughput, all-era event equivalence,
  full DATA coverage/deduplication, remote publication, or scientific
  normalization/statistical acceptance was established by the 100-event DY
  checks. Promotion to `ZH_devel` requires resolving the remaining gates.

## Reproduction and retained evidence

The owning [Z-pT workflow](../PlotsConfigurationsRun3/ZpTreweighting/workflow.py)
pins the DY file and bypasses discovery. After activating the supported runtime
and selecting this checkout's package, a new task-owned directory can run:

```bash
evidence_dir=$(mktemp -d /tmp/zh-bridge-check-XXXXXXXX)
python PlotsConfigurationsRun3/ZpTreweighting/workflow.py \
  --runs-dir "$evidence_dir/runs" smoke local --events 100
python PlotsConfigurationsRun3/ZpTreweighting/workflow.py \
  --runs-dir "$evidence_dir/runs" smoke packaged --batch --events 100
```

The second command is a dry-run preparation. Inspect the exact pickle, JDL,
transfers, package manifest and output mapping before any worker execution.
The existing [Z-pT validation instructions](../PlotsConfigurationsRun3/ZpTreweighting/VALIDATION.md)
describe scratch-only execution. A submitted job requires history, return-file
inspection and numerical verification before being treated as successful.

All exact commands, full logs, generated configurations, comparison code,
package identities, scheduler JSON and preserved failed outputs for this
integration are local under:

```text
/uscms_data/d3/mwadud/private/mkShapesRDF_devel/codex_analysis/zh-bridge-20261001/
```

These local artifacts are not distributed by Git. Start with `PLAN.md`,
`root-comparison.json`, `site-root-comparison.json`, `handoff-results.json`,
`final-package-inspection.json`, and `zzcr_systematics_dl83ace1/outcome.json`.
`task-config-relocation.json` records the unchanged hashes and final locations
of this task's Example pickles after moving them into the evidence directory.
The integration worktree is the visible sibling `mkShapesRDF-zh-bridge`.
The original `ZH_devel` checkout and its pre-existing RunStability skill edit
were preserved; Coffea and the read-only reference checkout were untouched.
