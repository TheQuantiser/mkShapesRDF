# HWWNano object-association investigation: history, evidence and conclusions

**Reconstructed on 2 October 2026 from the retained reports, result files and Git histories of both repositories.** This page recounts the investigation; it does not report a new production run. Commit dates in the ledger are UTC. The original terminal messages often used CDT, so an evening run on 29 or 30 September can have a Git date of the following day.

The investigation started with a 2024 RunStability discrepancy between Coffea and mkShapesRDF. Matching the same events exposed faults in the **shared HWWNano producer's association of per-lepton information**, with consequences for both stored objects and MC preselection. A separate repair branch then demonstrated correct associations and corrected MC acceptance in fresh nominal snapshots. RunStability supplied the observation and downstream example; the producer defect is a framework issue affecting analyses that consume the affected lepton information.

The strongest conclusions are:

- Historical 2024 files contain offline tight-ID bits attached to the wrong retained leptons, and separate electron coordinate/index inconsistencies.
- In two complete DY MC files, the original current-code `l2tight` gate accepts **exactly the same event keys** as the historical HWW files. Aligning all configured tight bits changes that acceptance in both directions, including removing wrongly accepted one-lepton events.
- Current source also has a correction-ordering defect: a permutation can be changed while it is being used to reorder related arrays. A live demonstration reproduced inconsistent object associations.
- Repairs on `fix-demo/2024-hwwnano-object-associations` correct the demonstrated association and gate failures on the executed inputs. **The checked `ZH_devel` branch contains the documentation and historical-file inspection, but still has the original producer modules.**
- These results establish real producer failures and their local selection consequences. They do not assign an exact fraction of the full-year discrepancy to each failure, establish the exact dirty historical operation behind the electron eta mismatch, or certify all 2022–2024 productions.

For the detailed code blocks and impact discussion, read [KNOWN_HWWNANO_ISSUES.md](../../KNOWN_HWWNANO_ISSUES.md). The [repair report](REPAIR_REPORT.md) records the executed fixes and measurements. [ROOT_INSPECTION.md](ROOT_INSPECTION.md) provides a direct read of the historical witnesses without Coffea or a producer replay.

## 1. What we were trying to reproduce

The immediate comparison concerned four low-pT categories: **Ele30 with a selected ee Z, Ele23–Ele12 with ee, IsoMu24 with μμ, and Mu17–Mu8 with μμ**. The category trigger is AND'ed with the selected Z flavor. The eμ trigger category was excluded. High-pT, non-isolated trigger studies of probe-input distributions were a separate objective; they were not the subject of this paired low-pT investigation.

Earlier Coffea development dealt with sample catalogs, DATA stream ownership, correction and exposure conventions, cached preparation, MC normalization, and faster split/on-demand plotting. The user moved the main objective away from tag-and-probe fits toward stability histograms. The initial submission-wrapper failure, XRootD timeouts, candidate-Parquet schema failure and negative signed-MC template bins belonged to that earlier operational/fit work. They were not evidence of the HWWNano association bugs.

By the completed Coffea v5 campaign, the processing used central NanoAOD, EGamma/Muon flavor domains, and deferred MC normalization from the physics jobs' uncut `Events.genWeight` sums, applied at complete-source merge. The missing semileptonic-top contribution had also been addressed. The comparison was therefore made against the completed selected-source campaign, rather than the earlier partial non-TT gallery.

The [full-year period comparison at Coffea `ed9f17c`](https://github.com/TheQuantiser/ZH4l_coffea/blob/ed9f17cd6732054530d134ada15c45cbbe27465a/docs/2024-low-pt-zmass-mkshapes-coffea-period-comparison.md) found:

| Category | Coffea DATA relative to historical mkShapes | Coffea MC relative to historical mkShapes |
| --- | ---: | ---: |
| Ele30 / ee | +2.88% | +2.62% |
| Ele23–Ele12 / ee | +2.83% | +2.61% |
| IsoMu24 / μμ | +12.39% | +6.66% |
| Mu17–Mu8 / μμ | +12.41% | +6.66% |

All 28 matched category/period exposures agreed; the visible mass range agreed and mass flows were zero. Each implementation's source reference luminosity cancels when its MC is projected to the period exposure. Thus a period-luminosity error or an extra reference-luminosity correction did not explain this comparison. A DATA count difference also cannot be caused by MC normalization, pileup or scale factors.

The initial source-only trace identified genuine selection differences: the historical HWW MC skim, RunStability's leading-two gate, global versus path-associated Z arbitration, trigger-object matching, and DATA stream priority. Physics intuition correctly discouraged treating a new matching requirement or a subdominant top contribution as the explanation for four million additional muon DATA events. However, the early emphasis on missing muon input coverage was a **hypothesis**, not a finding. The subsequent event join showed that the locally discrepant DATA events were already in the historical files.

The historical RunStability campaign used a recovered compiled configuration, `config_26-08-18_21_38_40.pkl`, with SHA-256 `6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef`. Its recorded provenance refers to a dirty worktree based on `6f9b4ff`. The clean source audit used `8cd6881` and later pinned descendants. **A clean audited commit is not a recovery of the unavailable historical dirty producer source.**

## 2. The local cutflow investigation that found the first clue

On 29 September, the request was to modify the diagnostics reversibly, process a few fixed inputs locally, and identify the first point of disagreement rather than launch another batch campaign. The resulting study used six paired inputs:

| Input | Central NanoAOD entries examined |
| --- | ---: |
| DY→ee | First 80,000 |
| DY→μμ | First 80,000 |
| Muon0, period C | First 200,000 |
| Muon0, period I | First 200,000 |
| EGamma0, period C | First 200,000 |
| EGamma0, period I | First 200,000 |
| **Total** | **960,000** |

Coffea's actual `matched_z_v2` processor was instrumented with the opt-in `--diagnostic-output` hook. The retained output covers 48 source-entry partitions. It records event identity, evaluated selection decisions, selected raw-object indices, and MC weight components. Events failing early masks remain in the diagnostic; object-dependent fields that were not evaluated are distinguishable from failed decisions.

The other side replayed the historical RunStability contract on the **actual HWW part0 files**, with the pinned compiled configuration and helpers. Central and HWW rows were joined by integer `(run, luminosityBlock, event)` keys. Object indices and raw inputs were inspected separately. The investigation did not match events merely by entry number, corrected pT or an approximate mass.

This was more than a single final cutflow counter: it combined cumulative selection records, independent decisions, selected-object identities and signed weight accounting. The retained [stage comparison](https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/diagnostics/paired-2024-lowpt/stage-comparison.json), [mask audit](https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/diagnostics/paired-2024-lowpt/hww-tight-mask-audit.json) and [weight comparison](https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/diagnostics/paired-2024-lowpt/weight-comparison.json) are the numerical record.

Fresh local current-producer stage ledgers were obtained for the DY prefixes. An attempted fresh DATA chain failed at the separate JEC `Regrouped_*` configuration problem. Therefore the first DATA result came from central Coffea processing plus historical HWW replay, **not a successful fresh full DATA producer run**. The [run record](https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/diagnostics/paired-2024-lowpt/coffea-diagnostic-note.md) identifies the actual completed replay versions and the unused redundant/interrupted attempts.

### The muon finding

Across the two Muon prefixes, Coffea selected 4,478 IsoMu24 DATA events and the historical replay selected 3,935: a difference of 543. The Coffea-only events were present in the paired historical HWW files. Among them, 508 failed the historical leading-two decision; **503 had a false stored tight decision for a retained raw muon whose named WP inputs all passed**. In 502 of those 503, the stored vector equalled the beginning of the prefilter decision vector.

Muon C central entry 234, key `(379416,147,131724611)`, historical HWW entry 65, made the association error explicit:

| Collection state | Raw muon identities | Tight decisions |
| --- | --- | --- |
| Before HLT-safe filtering | 0, 1, 2 | false, true, true |
| Retained leptons | 1, 2 | Should be true, true |
| Historical retained-position bits | 1, 2 | Stored as false, true |

The false bit describes removed raw muon 0, while retained position 0 describes raw muon 1. RunStability consumes the stored decision at retained position and rejects a genuine passing pair. These are **offline ID/working-point bits, not trigger bits**.

Thus 503/543, or 92.6%, of the local excess exhibited this concrete mask-association failure. That finding superseded missing DATA coverage as the explanation for those events. It did not measure a 92.6% attribution of the entire year's excess.

The MC prefix also showed upstream losses: for IsoMu24, 632 of 1,098 Coffea-only DY→μμ events were absent from historical HWW; the fresh current-producer ledger put 623 at `l2tight` and nine at `jetSelMask`. For common selected MC events, the recomputed weights agreed to approximately 10⁻⁸ relative precision. This directed attention toward selection and object association rather than a large weight-factor error. The [paired report](https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/2024-paired-lowpt-event-diagnostic-20260929.md) separates retained-event failures from events already removed upstream.

## 3. The electron follow-up separated two failures

The electron follow-up reused the retained traces and historical files. An opt-in replay changed decisions in memory for counterfactual comparisons; it did not alter historical ROOT files or commit a producer repair.

The 60 Coffea-only Ele30 DATA events and 56 Coffea-only Ele23–Ele12 events were all present in the paired EGamma files. Reconstructing the named tight-electron WP from the indexed raw HWW electrons found no failing selected raw electrons in those sets.

The Ele30 final-category counterfactuals partitioned the 60 events as follows:

| Change needed to recover the event | Events |
| --- | ---: |
| Align stored tight bits alone | 39 |
| Remove the historical leading-two gate alone | 18 |
| Both changes | 1 |
| Neither recovers it: historical EGamma stream weight is zero under MuonEG priority | 2 |

For Ele23–Ele12 the corresponding partition was 37, 16, one and two. These are recovery outcomes, not an addition of overlapping counts of bad flags.

EGamma C entry 20774, key `(379729,907,1396820419)`, historical entry 991, showed the same stale-bit problem as the muon witness. The two retained electrons passed their named WP, but the stored vector began `[false,true]`.

EGamma I entry 27025, key `(386509,159,333332716)`, historical entry 1936, showed a different fault: the retained electron indices and phi values agreed, but eta values were swapped between the indexed electrons. The historical leading-two matcher consequently returned no leading pair. Entry 46209, key `(386509,735,1539152813)`, historical entry 3325, showed tight-bit and eta/index inconsistencies together.

DY→ee MC had migrations in both directions. Upstream selection and stale tight bits increased the Coffea yield, while threshold and horn-veto migrations opposed that increase. The prefix's net Ele30 difference was +0.208343 weighted events at 1 fb⁻¹, with negligible common-event weight differences. A net yield alone therefore hid distinct mechanisms.

The [electron report](https://github.com/TheQuantiser/ZH4l_coffea/blob/a5bba58ed10e53df463fec9bf23ca8c002df909e/docs/2024-paired-lowpt-electron-diagnostic-20260929.md) records those examples, signed decomposition and evidence limits. In particular, it did **not** identify the exact historical operation that created the period-I eta mismatch.

## 4. Tracing the shared producer exposed the ordering mechanism

The subsequent audit followed the active 2024 recipes through lepton construction, filtering, jet operations, MC preselection, momentum corrections and Snapshot. The [chain audit](../../chain-audit.md) and [known-issues report](../../KNOWN_HWWNANO_ISSUES.md) give the source references.

`LeptonMaker` constructs a combined pT-sorted collection, stores raw Electron/Muon indices, and preserves a prefilter `VetoLepton` copy. `LeptonSel` computes working-point vectors on that collection, then filters the core lepton arrays. In the original code, it does not apply the same retention mapping to every tight vector or to `isLoose`. Later sorting/truncation cannot recover the removed objects' correct decisions. The MC `l2tight` gate consumes this information **before momentum smearing and before Snapshot**.

The correction step revealed an independent defect. `LeptonScaleSmearing` forms `Lepton_sorting` from corrected pT and loops over columns beginning `Lepton_`. That loop includes `Lepton_sorting` itself. For a swap:

```text
The intended permutation:          p = [1,0]
After reordering the helper itself: Take(p,p) = [0,1]
```

Columns processed before and after that mutation can follow different permutations. Column tracking through `list(set(...))` does not define a reliable physical ordering for this loop. The already ordered `Lepton_rochesterSF` can also be permuted again, and `isLoose` is outside the prefix-based loop. Coordinates, raw indices, decisions and per-lepton scale factors can therefore cease to describe the same object.

An earlier allegation about nominal jet cleaning was corrected during this audit. In the active 2024 sequence, leptons remain in descending pT order when `JetSelMask` runs, before lepton momentum correction. Its pT≥10 subset is a prefix, so the questioned masked-size/unmasked-coordinate expression does not establish a nominal association bug. A separate conditional JES-variation jet-index risk remained a source-level concern with no observed prerequisite in these files; it was not presented as a measured nominal defect or included in the repair demonstration.

## 5. A separate demo branch made the observations executable

The branch `demo/2024-hwwnano-object-associations` was created from `4f48e73`. Commit `bf75c7f` added a bounded, reproducible terminal demonstration using pinned files and recorded event keys. Shared producer modules and historical files remained unchanged.

It combined direct historical reads with live current lepton modules. The live `LeptonSel` retained the selected indices while leaving tight vectors at prefilter length and positions. On EGamma I entry 27025, current momentum correction induced a `[1,0]` reorder and the recorded column loop produced a **phi/index** inconsistency. This demonstrated the current ordering hazard, but did not reproduce the historical file's **eta-only** pattern. Those are distinct evidence statements.

Two fresh one-entry configured MC chains supplied useful controls:

- DY→ee entry 174, key `(1,384532,2060318616)`, had two retained electrons with passing correctly associated decisions and first failed the original `l2tight` gate because the decision positions were stale.
- DY→μμ entry 127, key `(1,260002,1443526502)`, had only one retained muon and legitimately failed a two-tight-lepton requirement.

Both keys were absent from their exact paired historical part0 files. That wording meant **absence from those outputs**, not absence from central NanoAOD or all possible HWW output parts. Absence alone was not proof of a bug: filtering is expected, as the one-muon control demonstrated. This limitation motivated the complete-file investigation.

## 6. The complete two-file MC join made acceptance conclusive

The follow-up in `69ff2dad` joined every event key in each complete central file to every key in its historical part0. There were no duplicate or ambiguous keys and no HWW-only keys:

| File | Central entries | Historical HWW survivors | Central-only entries |
| --- | ---: | ---: | ---: |
| DY→ee | 158,487 | 68,421 | 90,066 |
| DY→μμ | 222,331 | 88,692 | 133,639 |

The current configured producer was then executed once per complete central file through `l2tight`. Stage records and both gate decisions were evaluated in the same analysis of the file. The counterfactual mapped **all configured electron/muon tight WPs** to retained raw-object identities and required at least two retained leptons. It retained the original gate's OR over configured WPs; it did not substitute the narrower RunStability electron/muon WP or redesign the physics selection.

The complete cutflow was:

| Stage | DY→ee | DY→μμ |
| --- | ---: | ---: |
| Input | 158,487 | 222,331 |
| Initial `nElectron+nMuon>1` | 94,106 | 129,548 |
| After LeptonMaker | 93,059 | 127,633 |
| After LeptonSel | 78,696 | 121,809 |
| Immediately before l2tight, after intervening jet stages | 74,938 | 116,303 |
| Original l2tight accepts | 68,421 | 88,692 |
| Aligned l2tight accepts | 43,338 | 89,282 |

**The original accepted event-key sets exactly equalled historical HWW membership in both files.** This strengthened the historical connection from individual missing examples to complete membership agreement. It does not recover the exact executing line of the unavailable dirty historical producer.

The decisive gate comparison was:

| Outcome among events reaching the gate | DY→ee | DY→μμ |
| --- | ---: | ---: |
| Pass original and aligned | 42,732 | 83,368 |
| Rejected by original; pass aligned | **606** | **5,914** |
| Pass original; rejected by aligned | **25,689** | **5,324** |
| Rejected by both | 5,911 | 21,697 |

The original gate can read a true prefilter bit for a lepton that was removed. Historical `__l2tight` files contain 25,638 ee and 5,269 μμ survivors with **only one retained lepton**. The later repair comparison placed these exactly within the false-acceptance populations; another 51 ee and 55 μμ false acceptances had at least two retained leptons.

Conversely, valid retained pairs can be rejected when their passing bits remain at later prefilter positions. The issue is therefore **both erroneous rejection and erroneous acceptance**. The net μμ survivor change of only +590 conceals thousands of changes in each direction. The large negative net ee survivor change chiefly removes events that could not pass a final two-lepton Z selection; it cannot be interpreted as a comparable loss in selected Z yield.

Signed ΣgenWeight and ΣgenWeight² were recorded separately for the outcomes. `Runs` information was used for parent-file lineage checks, not to normalize a partial file as a complete source. The [complete investigation README](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/README.md) and [compact two-file result](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/complete-two-file-summary.json) retain the counts, witnesses, hashes and commands.

## 7. A repair branch demonstrated fresh, correctly associated snapshots

The next request was to identify and repair the shared-source faults on a new branch, then demonstrate the result locally on DATA and MC. The resulting branch was `fix-demo/2024-hwwnano-object-associations`, starting from the complete investigation.

Three commits have different roles:

| Commit | Role |
| --- | --- |
| [68a082c](https://github.com/TheQuantiser/mkShapesRDF/commit/68a082c29b08d85978e9af33e9d194610b19f8a6) | Separate DATA JEC unblock: supported nominal-only JES-source configuration. |
| [9a0e9be](https://github.com/TheQuantiser/mkShapesRDF/commit/9a0e9be35c27e2907e6201460d0a5de58a091651) | Actual association and l2tight repairs in shared producer modules. |
| [8d940ab](https://github.com/TheQuantiser/mkShapesRDF/commit/8d940abcf429f753074121a250db3717434eb2f6) | Reproducible demonstration, retained results and repair documentation. |

The repairs froze a retention map before core-array changes, applied it once to core lepton fields, `isLoose` and all configured tight decisions, guarded `l2tight` against fewer than two retained leptons, and used one immutable correction permutation for genuine per-lepton arrays. Temporary helpers and already reordered quantities were handled explicitly. Raw Electron/Muon arrays and prefilter `VetoLepton` arrays were preserved. WP definitions, isolation/MVA thresholds and the gate's configured-WP policy were unchanged.

The retention helper `LeptonSel_keepIdx` is not accidentally swept into a `Lepton_` sorting loop: the names do not share that exact prefix, the filtering loop uses an explicit column list, and the helper is removed after use. Freezing the map means binding it to the pre-redefinition dependency graph, not assuming ROOT evaluates it eagerly.

The successful demonstration processed **both complete DY files and four 50,000-entry DATA prefixes**, wrote fresh nominal ROOT snapshots and reopened them independently:

| Input | Fresh snapshot entries | Correction-induced nonidentity orderings |
| --- | ---: | ---: |
| DY→ee | 43,338 | 1,419 |
| DY→μμ | 89,282 | 978 |
| EGamma C prefix | 3,189 | 8 |
| EGamma I prefix | 3,590 | 15 |
| Muon C prefix | 11,927 | 2 |
| Muon I prefix | 11,447 | 7 |

All executed snapshots passed the retained association audit: 21 flat per-lepton arrays in each DATA file and 186 in each MC file, including 159 SF arrays. Checks covered lengths, raw identities, coordinates, flavor/charge, expected WP bits, `isLoose`, corrected ordering and correction ratios. No anomalous event was found within those checks. Real reorderings occurred, so this did exercise the permutation repair.

Repaired final MC keys exactly equalled the independently aligned gate's accepted sets, with no downstream loss in these runs. Rescued ee entry 174 and μμ entry 5 were present; falsely accepted singleton examples ee entry 8 and μμ entry 102 were absent; the legitimate one-muon rejection at entry 127 remained rejected.

Five selection/guard regression checks and four scale/reordering checks passed and detected the original faults when run against the original implementations. The separate unsigned-high-bit Snapshot serialization limitation remained documented; no event with that prerequisite occurred in the six executed ranges. This was not a demonstration of every systematic-production, auxiliary-metadata or stage-out path.

### Replaying the historical Z-mass analysis

The same historical RunStability selection and weights were applied to historical and fresh repaired snapshots. This kept the downstream reference fixed for the diagnostic, including its leading-two gate; it did not reintroduce that gate into the intended Coffea analysis.

| MC category | Historical selected events | Repaired selected events | Historical / repaired weighted yield at 1 fb⁻¹ |
| --- | ---: | ---: | ---: |
| Ele30 | 15,033 | 15,261 | 59.56551 / 60.61872 |
| Ele23–Ele12 | 13,774 | 13,982 | 54.40380 / 55.39628 |
| IsoMu24 | 32,559 | 35,043 | 137.40934 / 149.38082 |
| Mu17–Mu8 | 31,373 | 33,782 | 132.13121 / 143.67505 |

The corresponding DATA-prefix counts were Ele30 204→208 in C and 208→215 in I, and IsoMu24 525→604 in C and 434→497 in I. Both double-lepton paths were also replayed and are tabulated in [REPAIR_REPORT.md](REPAIR_REPORT.md).

Histogram values and variances, including flows, agreed with independent event-ledger accounting. Weighted MC yields used retained **full-source** normalization; an individual file or prefix's generator sum was not substituted as the denominator.

These final yield changes are **descriptive**. Changed MC gate acceptance changes subsequent sequential random draws for smearing and trigger-period assignment. The controlled causal result is the pre-smearing gate migration; the final mass/yield differences are not a pure association-only effect. The fresh snapshots demonstrate the repaired associations, including the historical eta witness, while the exact operation that originally produced that historical eta-only pattern remains unresolved.

The [repair README](https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/README.md) and [machine-readable result](https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-results.json) identify the successful runs, receipts, local outputs and limitations. Some large ROOT outputs and ledgers remain at the recorded LPC paths; the Git repository contains compact evidence and hashes, not those complete runtime artifacts.

## 8. Documentation, branch separation and direct ROOT confirmation

The first paired mkShapes diagnostics initially landed on `ZH_devel` as `fa1a1e0` and `2fd798f`. The user subsequently requested that investigations be separated from the working analysis branch. Those commits are preserved in the ancestry of `codex/2024-electron-diagnostic`, which added `7843a7f`; current `ZH_devel` instead continues from `8cd6881` through the known-issues documentation. Its current ancestry does not contain a revert commit for those diagnostic commits. Git history establishes the resulting branch relationship, not the timestamp or precise shell command used to move the ref.

The Coffea paired diagnosis was published on `main` at `062cfea`. Electron follow-up `a5bba58` and initial documentation work `fe0a757`/`44e7ae7` were on its electron diagnostic branch. After the user pointed out that main documentation was unchanged, `2b5ba43` overhauled documentation on `main` without merging the electron investigation branch. Coffea main still retains the earlier paired-diagnostic commit.

mkShapes documentation progressed from `4e6793f` through the corrected producer-order assessment and cross-framework audit. After the repair demonstration, `a3b160a` copied the report and updated references on `ZH_devel`. The subsequent October 1 commits reorganized the conclusions and added read-only ROOT inspection. **Publishing those reports did not merge the repair code.** At the checked heads, `Steps_cfg.py`, `LeptonSel.py`, `L2TightSelection.py` and `LeptonScaleSmearing.py` on `ZH_devel` are byte-identical to the original demo versions and differ from the repaired branch.

The direct [ROOT inspection](ROOT_INSPECTION.md) reads historical files and their central parents using PyROOT alone. The original four DATA witnesses reproduced: wrong named muon/electron tight bits, the separate eta/index swap, and the event containing both. All raw-input comparisons matched the central inputs exactly. Additional MC witnesses showed historical one-lepton survivors and a named tight-electron association error.

The additional MC association witness was verified at central entry 1480 / HWW entry 632, key `(1,404199,2165694222)`. An earlier proposed witness at entry 346 did not show the requested named-WP error and was rejected; a gate discrepancy alone was not treated as proof of that specific stored-ID failure. The verified witness's second electron is below the RunStability 35 GeV threshold, so it demonstrates association corruption, not a selected Z event.

The seven-case direct read exited successfully in 172.55 seconds; the original four-event read was separately rerun in 102.57 seconds. Their retained transcripts provide an independent, reproducible display of historical file contents. Their `PASS` means the specified failures were reproduced, not that the historical files passed a validity audit.

## 9. What the investigation establishes for analyses

### Shared HWWNano production

The named WP's physical formula can be correct while its stored decision belongs to the wrong object. This is an object-association error, not a disagreement about the appropriate ID. Related coordinates, indices and SF arrays must also remain associated under correction-induced reordering.

The demonstrated affected HWWNano information is invalid for analyses depending on those associations. That includes HWW lepton selections, MC preselection, and potentially per-lepton weights and derived kinematics across two-, three- and four-lepton channels. Plausible distributions, a small net event-count change or cancellation between false accepts and rejects do not validate dependent physics results.

For MC, wrongly rejected events are absent from the skim. Changing an alias in the existing output cannot restore them; repairing the event population requires the original input. DATA wrong stored decisions and coordinates can corrupt downstream selection even when the event remains in the file.

This is relevant to ggF, VBF, VH, WH and ZH consumers wherever they use affected production and branches. The executed evidence is from the specified 2024 files and pinned source. It does not prove the prevalence in every sample or establish that all 2022/2023 campaigns used the same faulty chain. That version/recipe boundary must not be replaced with either a blanket certification or an unmeasured all-year failure rate. Original central NanoAOD is not implicated by the demonstrated producer errors.

### Personal RunStability study and Coffea

RunStability's leading-two gate and Z construction exposed the corrupted producer information; they did not create it. The retained-event DATA counterfactuals and final historical-policy replays show concrete consequences for this study.

Coffea evaluates objects through their raw identities and carries associated fields together, avoiding the two HWW positional mechanisms identified here. Common-event weight agreement also argues against a large correction-factor explanation on the paired inputs. This does not establish that Coffea is universally bug-free or exactly reproduces every historical selection convention. Its intentional absence of the leading-two requirement, different candidate arbitration/matching and flavor-specific DATA routing still matter when comparing results.

The demonstrated producer failures provide a concrete, substantial explanation for the observed direction and flavor pattern. **The precise attribution of the full-year +12.4% muon DATA and +6.66% muon MC differences remains unmeasured.** The electron historical eta-only operation also remains unidentified. The conclusive result is the failure of associations and the controlled MC gate acceptance on fixed inputs, followed by their repair on fresh snapshots.

## 10. Where to find and reproduce each part

Use the pinned revision for the corresponding investigation rather than assuming every script exists on every branch.

| Question | Evidence and reproducibility entry point |
| --- | --- |
| What were the original full-year discrepancies? | [Coffea period comparison at ed9f17c](https://github.com/TheQuantiser/ZH4l_coffea/blob/ed9f17cd6732054530d134ada15c45cbbe27465a/docs/2024-low-pt-zmass-mkshapes-coffea-period-comparison.md). |
| Which local cutflow first found the wrong muon bits? | [Paired report](https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/2024-paired-lowpt-event-diagnostic-20260929.md) and its [evidence README](https://github.com/TheQuantiser/ZH4l_coffea/blob/062cfea35ba6a6395b926854228efc94753d02cb/docs/diagnostics/paired-2024-lowpt/README.md); opt-in Coffea hook at 062cfea and mkShapes replay on the electron branch. |
| How were the electron effects separated? | [Electron report](https://github.com/TheQuantiser/ZH4l_coffea/blob/a5bba58ed10e53df463fec9bf23ca8c002df909e/docs/2024-paired-lowpt-electron-diagnostic-20260929.md) and [mkShapes replay description at 7843a7f](https://github.com/TheQuantiser/mkShapesRDF/blob/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f/PlotsConfigurationsRun3/ZH_4lMET/RunStability/HISTORICAL_HWW_DIAGNOSTIC.md). |
| What failed in the shared source? | [Known issues](../../KNOWN_HWWNANO_ISSUES.md), with exact code and conditional scope; [cross-framework chain audit](../../chain-audit.md). |
| What did the live witnesses and complete MC join prove? | [Demo README at 69ff2dad](https://github.com/TheQuantiser/mkShapesRDF/blob/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/README.md) and its input manifests, observed witness summary and complete two-file summary. |
| Which source was actually repaired and executed? | [Producer repair commit 9a0e9be](https://github.com/TheQuantiser/mkShapesRDF/commit/9a0e9be35c27e2907e6201460d0a5de58a091651); [repair reproduction at 8d940ab](https://github.com/TheQuantiser/mkShapesRDF/blob/8d940abcf429f753074121a250db3717434eb2f6/PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/README.md); [repair report on ZH_devel](REPAIR_REPORT.md). |
| How can the actual historical errors be displayed directly? | [ROOT_INSPECTION.md](ROOT_INSPECTION.md), [root_inspect.py](root_inspect.py) and the [pinned input manifest](inputs/inputs.json). |

The existing CMS/ROOT environment, remote-file credentials and recorded calibration/input resources are runtime prerequisites. A committed hash proves which retained artifact was used; it does not make an LPC-local artifact downloadable from GitHub. No fresh NanoAOD reads, DAS queries, Condor work or physics tests were performed to assemble this history.

## 11. Branch map at the documentation preflight

These heads were checked on 2 October 2026 **before adding this page**. Branch links are for navigation; the SHA links pin the state being described.

| Repository / branch | Checked head | Purpose and relationship |
| --- | --- | --- |
| mkShapesRDF `ZH_devel` | [22cca33](https://github.com/TheQuantiser/mkShapesRDF/commit/22cca33c7c39a573037e904c8422ce83f9572303) | Working analysis branch; known issues, repair report and direct ROOT evidence; original producer modules still present. |
| mkShapesRDF `codex/2024-electron-diagnostic` | [7843a7f](https://github.com/TheQuantiser/mkShapesRDF/commit/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f) | Contains fa1a1e0 → 2fd798f → electron counterfactual replay; no producer fix. |
| mkShapesRDF `demo/2024-hwwnano-object-associations` | [69ff2dad](https://github.com/TheQuantiser/mkShapesRDF/commit/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0) | From 4f48e73, then bf75c7f → complete two-file study; original shared producer. |
| mkShapesRDF `fix-demo/2024-hwwnano-object-associations` | [8d940ab](https://github.com/TheQuantiser/mkShapesRDF/commit/8d940abcf429f753074121a250db3717434eb2f6) | From 69ff2dad, then 68a082c → 9a0e9be → repair demonstration. |
| ZH4l_coffea `main` | [2b5ba43](https://github.com/TheQuantiser/ZH4l_coffea/commit/2b5ba43d6a264a441498a6a5c76af6e253dd2847) | Full-year comparison and first paired diagnosis, followed by main documentation overhaul. |
| ZH4l_coffea `codex/2024-electron-diagnostic` | [44e7ae7](https://github.com/TheQuantiser/ZH4l_coffea/commit/44e7ae7b98a894f79c647ae637791feded3ea381) | From 062cfea, then a5bba58 → fe0a757 → 44e7ae7; electron report and initial documentation work. |

The graph proves these relationships and retained content. Git commit timestamps do not prove branch-creation times; older unrelated branches are not claimed as branches created for this investigation.

## 12. Commit ledger

This ledger makes the repository history explicit, including documentation revisions that did not change the producer. It records the mkShapes investigation commits across all three auxiliary branches and `ZH_devel`, plus the complete 47-commit Coffea main history through the checked head and its three additional electron-branch commits. Generic commit titles are preserved rather than given invented meanings. The earlier Coffea operational/architecture commits provide context; they are not all object-association findings.

### mkShapesRDF investigation, demonstration, repair and documentation commits

| Commit timestamp (UTC) | Commit | Recorded title | Role in this investigation |
| --- | --- | --- | --- |
| 2026-09-22 18:08:38 | [8cd6881](https://github.com/TheQuantiser/mkShapesRDF/commit/8cd688101e5f0ac833f476d5b4bcfe1822c0d77f) | codex update | Clean source baseline; predates the paired diagnosis. |
| 2026-09-29 23:33:26 | [fa1a1e0](https://github.com/TheQuantiser/mkShapesRDF/commit/fa1a1e0d2e6cbbbe7b1ce6c50081dc61f3b372ef) | Add opt-in paired 2024 RunStability diagnostics | Initial paired replay/instrumentation; preserved on the electron branch. |
| 2026-09-29 23:35:22 | [2fd798f](https://github.com/TheQuantiser/mkShapesRDF/commit/2fd798f6358f7093bdc166de33a40b6c8d1354a9) | Document HWW tight-mask ordering evidence | Initial tight-mask evidence; preserved on the electron branch. |
| 2026-09-30 01:00:23 | [7843a7f](https://github.com/TheQuantiser/mkShapesRDF/commit/7843a7ff8680f6c9ff48b9372cc0a7784468cb6f) | Add opt-in electron RunStability counterfactual replay | Opt-in electron counterfactual replay; no shared producer repair. |
| 2026-09-30 15:18:42 | [4e6793f](https://github.com/TheQuantiser/mkShapesRDF/commit/4e6793fd315807b7db7823d2612dc1ad705f55bd) | Document historical HWWNano object association issues | Initial known-issues page on ZH_devel. |
| 2026-09-30 16:03:22 | [c064927](https://github.com/TheQuantiser/mkShapesRDF/commit/c0649272854fdd03812af19b6677fc82d6855091) | Clarify HWWNano association risks and 2024 producer order | Producer-order clarification and correction of nominal jet-cleaning claim. |
| 2026-09-30 20:29:14 | [394a929](https://github.com/TheQuantiser/mkShapesRDF/commit/394a929f66ac13ceb690d8b25feac45cea453107) | ongoing overhaul | Adds the cross-framework chain-audit document. |
| 2026-09-30 20:37:14 | [4f48e73](https://github.com/TheQuantiser/mkShapesRDF/commit/4f48e7308270d17cdcc96b3fcde5e9fb74d0fa04) | Show chain audit source references as visible links | Visible source links; base of the demo branch. |
| 2026-09-30 22:47:32 | [bf75c7f](https://github.com/TheQuantiser/mkShapesRDF/commit/bf75c7f50245891ddad20aa3bced35057148fca2) | Add bounded 2024 HWWNano object association demo | Bounded live witnesses and historical-file demonstration. |
| 2026-10-01 00:03:12 | [69ff2da](https://github.com/TheQuantiser/mkShapesRDF/commit/69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0) | Document complete DY HWW membership and l2tight association counterfactual | Complete two-file MC membership/gate investigation. |
| 2026-10-01 03:16:51 | [68a082c](https://github.com/TheQuantiser/mkShapesRDF/commit/68a082c29b08d85978e9af33e9d194610b19f8a6) | Use supported nominal-only JES source configuration for 2024 DATA | Separate nominal-only DATA JEC configuration unblock on repair branch. |
| 2026-10-01 03:21:47 | [9a0e9be](https://github.com/TheQuantiser/mkShapesRDF/commit/9a0e9be35c27e2907e6201460d0a5de58a091651) | Keep HWWNano lepton decisions and corrections aligned with retained objects | Shared producer association and l2tight code repairs. |
| 2026-10-01 05:09:29 | [8d940ab](https://github.com/TheQuantiser/mkShapesRDF/commit/8d940abcf429f753074121a250db3717434eb2f6) | Demonstrate repaired HWWNano snapshots and exact two-file gate acceptance | Fresh snapshots, audits, historical Z replay and reproduction. |
| 2026-10-01 11:14:36 | [a3b160a](https://github.com/TheQuantiser/mkShapesRDF/commit/a3b160a5952e4198e61060b17be64da5b4c445e3) | Document completed HWWNano repair evidence and RunStability impact | Copies repair evidence and updates ZH_devel documentation; no producer merge. |
| 2026-10-01 14:08:56 | [d036a25](https://github.com/TheQuantiser/mkShapesRDF/commit/d036a25754ff1a922a908008ae1d6c0e763cb7c3) | docs: clarify HWWNano validity conclusions and organize repair evidence | Organizes repair evidence and ntuple-validity conclusions. |
| 2026-10-01 15:07:06 | [44bd978](https://github.com/TheQuantiser/mkShapesRDF/commit/44bd97884666a3cb8262a2e4727e58198ba1893e) | docs: consolidate HWWNano investigations, repairs and reproduction guide | Consolidates investigations and reproduction guidance. |
| 2026-10-01 16:21:22 | [0ec60c5](https://github.com/TheQuantiser/mkShapesRDF/commit/0ec60c5009ac438edd47536f3e777d23ad1bfc44) | diagnostics: add direct ROOT displays of historical lepton associations | Adds direct read-only ROOT inspection and transcripts. |
| 2026-10-01 16:28:07 | [864dca0](https://github.com/TheQuantiser/mkShapesRDF/commit/864dca0d6e09b1e28803098e096a132171b7b505) | docs: foreground the original four ROOT association witnesses | Foregrounds the original four DATA witnesses. |
| 2026-10-01 16:29:36 | [de9a616](https://github.com/TheQuantiser/mkShapesRDF/commit/de9a616e713729a33358fc6c7aaa98026b3827b6) | docs: explain HWWNano repair measurements and replay tables step by step | Explains repair measurement/replay tables. |
| 2026-10-01 16:35:50 | [743945d](https://github.com/TheQuantiser/mkShapesRDF/commit/743945dbcc22fc703a768d5e3ddf9c4248e2f10a) | docs: connect repair report to direct ROOT association witnesses | Links repair report to direct historical ROOT witnesses. |
| 2026-10-01 16:41:02 | [22cca33](https://github.com/TheQuantiser/mkShapesRDF/commit/22cca33c7c39a573037e904c8422ce83f9572303) | docs: record original four ROOT reads and explicit HWWNano file paths | Records executed four-event reads and literal input paths. |

### ZH4l_coffea development and investigation commits

| Commit timestamp (UTC) | Commit | Location at preflight | Recorded title |
| --- | --- | --- | --- |
| 2026-09-22 21:52:24 | [802f1a1](https://github.com/TheQuantiser/ZH4l_coffea/commit/802f1a14870dadf7e18952738615d202dcbb7778) | main ancestry | first commit |
| 2026-09-22 23:18:43 | [5c8ba18](https://github.com/TheQuantiser/ZH4l_coffea/commit/5c8ba18adc75c77bd82ca44a7ab8e430d4bad76f) | main ancestry | overhaul |
| 2026-09-22 23:27:28 | [91a5e01](https://github.com/TheQuantiser/ZH4l_coffea/commit/91a5e0136b8fa4aa67d30981b1247db3bfeb1db6) | main ancestry | docs: render equations on GitHub and record 2024 campaign status |
| 2026-09-23 01:00:54 | [4e04961](https://github.com/TheQuantiser/ZH4l_coffea/commit/4e04961175530b21c15cab19a9b699eddc6715ac) | main ancestry | ongoing overhaul |
| 2026-09-23 01:30:16 | [5e214d9](https://github.com/TheQuantiser/ZH4l_coffea/commit/5e214d9b40add13443dc9d1b999b0c8bd460dab5) | main ancestry | ongoing overhaul |
| 2026-09-23 02:34:56 | [7c0c21b](https://github.com/TheQuantiser/ZH4l_coffea/commit/7c0c21b152b4e86969ade7adeda82fd430db9d3e) | main ancestry | ongoing overhaul |
| 2026-09-23 04:21:10 | [21b011e](https://github.com/TheQuantiser/ZH4l_coffea/commit/21b011eb77bde43e17b0343dcb8671e10de236fb) | main ancestry | ongoing overhaul |
| 2026-09-23 16:51:28 | [52f7a61](https://github.com/TheQuantiser/ZH4l_coffea/commit/52f7a61a936bd033c3be0f5b6200217b59b0cf6c) | main ancestry | ongoing overhaul |
| 2026-09-23 16:59:36 | [c8ca3ba](https://github.com/TheQuantiser/ZH4l_coffea/commit/c8ca3baf09ba2cdc9982738ef32f4e89d9b24a0f) | main ancestry | Track reviewed 2024 production performance evidence |
| 2026-09-23 18:49:40 | [57e16a2](https://github.com/TheQuantiser/ZH4l_coffea/commit/57e16a2c285140151e46543c4aa4875eecfbedb5) | main ancestry | ongoing overhaul |
| 2026-09-23 19:16:18 | [09d78d4](https://github.com/TheQuantiser/ZH4l_coffea/commit/09d78d454596909a99a5860ca4cd64e2f8f4636b) | main ancestry | ongoing overhaul |
| 2026-09-23 20:27:49 | [7c21241](https://github.com/TheQuantiser/ZH4l_coffea/commit/7c212410489254c3ad7609f455a6be0cc213136d) | main ancestry | ongoing overhaul |
| 2026-09-23 21:41:50 | [45e4410](https://github.com/TheQuantiser/ZH4l_coffea/commit/45e4410d1b298873c8bfe22309fd9b226fb6ad5f) | main ancestry | ongoing overhaul |
| 2026-09-23 22:10:11 | [21ddd09](https://github.com/TheQuantiser/ZH4l_coffea/commit/21ddd0959b39e8802c7d29f1293f3a5ed416ad5d) | main ancestry | ongoing overhaul |
| 2026-09-23 23:19:24 | [461657c](https://github.com/TheQuantiser/ZH4l_coffea/commit/461657c9711c745d7dc834eafdc154e7fe458ab1) | main ancestry | Record 2024 qualification rates and harden bounded input recovery |
| 2026-09-23 23:36:06 | [97ae546](https://github.com/TheQuantiser/ZH4l_coffea/commit/97ae5466f8994e99a0fd36a746b3890e688956db) | main ancestry | Record completed qualification plots and pending reference allocation |
| 2026-09-24 00:24:15 | [623c192](https://github.com/TheQuantiser/ZH4l_coffea/commit/623c192ba82fd527fad2859be0929730a877c160) | main ancestry | Normalize yield plots to category exposure and document qualification outputs |
| 2026-09-24 01:43:46 | [99cfcbc](https://github.com/TheQuantiser/ZH4l_coffea/commit/99cfcbc4cd0ae809c5b6fced86a9777159581a47) | main ancestry | Add signed MC shape transformations and qualify downstream fits |
| 2026-09-24 03:12:30 | [2ce3585](https://github.com/TheQuantiser/ZH4l_coffea/commit/2ce3585ba84b7aa86182127d0b7fcd3290f80c3e) | main ancestry | ongoing overhaul |
| 2026-09-24 12:44:25 | [56a1f32](https://github.com/TheQuantiser/ZH4l_coffea/commit/56a1f32c1005d464a881ffc322a96c535cdadb67) | main ancestry | Report full-2024 job performance and continue downstream without semileptonic top |
| 2026-09-24 13:16:04 | [fd19f5d](https://github.com/TheQuantiser/ZH4l_coffea/commit/fd19f5d14bc1dae8416ad47a52d8b508efc9cef5) | main ancestry | Document output files, directory depth, and simplification options |
| 2026-09-24 15:13:55 | [918429f](https://github.com/TheQuantiser/ZH4l_coffea/commit/918429f99e5694acbd268c66dbc472fbda6786b7) | main ancestry | Record live 2024 downstream job status |
| 2026-09-24 15:44:18 | [410936b](https://github.com/TheQuantiser/ZH4l_coffea/commit/410936bbb36c0d2a89d02bb52da3bc5e59860bcf) | main ancestry | Add named Run 3 study catalogs and reusable processing entry point |
| 2026-09-24 15:55:13 | [42faa6e](https://github.com/TheQuantiser/ZH4l_coffea/commit/42faa6ed7e4740a2cf6abae4d87c77fc82ebcf4e) | main ancestry | Expose named study coverage and candidate index status |
| 2026-09-24 16:27:33 | [90fe4c4](https://github.com/TheQuantiser/ZH4l_coffea/commit/90fe4c495b437ff1f3167b480f0fcafc379c0561) | main ancestry | Record user-requested stop of 2024 downstream DAG |
| 2026-09-24 18:40:37 | [e215559](https://github.com/TheQuantiser/ZH4l_coffea/commit/e215559544e8e5dbfbc7d0f97660c4f2db0bbaef) | main ancestry | Add parallel RunStability gallery and on-demand PNG rendering |
| 2026-09-24 19:49:01 | [52cb8c5](https://github.com/TheQuantiser/ZH4l_coffea/commit/52cb8c5134ec9f4db602ced6fae20deffb7c1980) | main ancestry | ongoing overhaul |
| 2026-09-24 20:59:35 | [28a72b3](https://github.com/TheQuantiser/ZH4l_coffea/commit/28a72b3784c6236c54fbf17c0ae7a852395fa689) | main ancestry | Align RunStability MC selection and high-trigger yield policy |
| 2026-09-25 00:36:54 | [4bc56b8](https://github.com/TheQuantiser/ZH4l_coffea/commit/4bc56b836471ec1292a3c6dbc5869def8eaef3ac) | main ancestry | Add trigger-matched Run 3 stability study and high-path exposure audit |
| 2026-09-25 14:12:10 | [bb9d22c](https://github.com/TheQuantiser/ZH4l_coffea/commit/bb9d22c2bfadb97f42290182ba04bb2a5ecc2e36) | main ancestry | Record completed 2024 matched stability DAG and output status |
| 2026-09-28 17:23:06 | [ab895fe](https://github.com/TheQuantiser/ZH4l_coffea/commit/ab895fe5cd2ceb2fcc22b7d01d5207fe766343e2) | main ancestry | Align RunStability plot presentation with mkShapesRDF source |
| 2026-09-28 18:11:37 | [20bfe90](https://github.com/TheQuantiser/ZH4l_coffea/commit/20bfe90a73417c3244a81cdafdc52945d138afb2) | main ancestry | ongoing overhaul |
| 2026-09-28 18:40:30 | [b74c3e7](https://github.com/TheQuantiser/ZH4l_coffea/commit/b74c3e7ef6588a039d2178f23960c906a84ac171) | main ancestry | Match RunStability mass comparison legend and layout |
| 2026-09-28 19:41:45 | [19a507d](https://github.com/TheQuantiser/ZH4l_coffea/commit/19a507de5de429448e66c32c0019c4688875e874) | main ancestry | ongoing overhaul |
| 2026-09-28 21:45:30 | [ce809cd](https://github.com/TheQuantiser/ZH4l_coffea/commit/ce809cdb0980d3b6906851f811eaa8cab64f4052) | main ancestry | Implement 2024 trigger probe study with deferred Events normalization |
| 2026-09-28 22:46:11 | [f91cca8](https://github.com/TheQuantiser/ZH4l_coffea/commit/f91cca81ca2d7b1b364762a26e8a5d9ca25a85bb) | main ancestry | Qualify deferred-normalization pilot and harden plot publication |
| 2026-09-28 22:52:57 | [7fd646b](https://github.com/TheQuantiser/ZH4l_coffea/commit/7fd646b2f82d6630aa468eb6d9e0376ff1e0b71c) | main ancestry | Record full v5 study submission |
| 2026-09-28 23:15:43 | [ce33037](https://github.com/TheQuantiser/ZH4l_coffea/commit/ce33037af77c66e159aad328863d9cdbc7d05ba8) | main ancestry | Record first full v5 worker receipts |
| 2026-09-29 05:29:39 | [ecc7d66](https://github.com/TheQuantiser/ZH4l_coffea/commit/ecc7d6660c8a52af684e688f58548dc88c1d1462) | main ancestry | Record full v5 recovery and finalized MC evidence |
| 2026-09-29 06:09:20 | [8d272b1](https://github.com/TheQuantiser/ZH4l_coffea/commit/8d272b194615d6595b9fb8077ed19eac1cdcaf00) | main ancestry | Repair DATA identity XRootD transport and document rescue |
| 2026-09-29 09:16:51 | [4d4aa52](https://github.com/TheQuantiser/ZH4l_coffea/commit/4d4aa520b4cd9dcdfa0ba5c29bdc3c0a65fe4650) | main ancestry | Record recovered DATA ownership and physics checkpoint |
| 2026-09-29 13:31:31 | [0782936](https://github.com/TheQuantiser/ZH4l_coffea/commit/0782936fc1e97f1cbfda686f834a8d4ac7e0d330) | main ancestry | Compact full-year accumulator indexes and recover downstream DAG |
| 2026-09-29 14:14:26 | [3ae0013](https://github.com/TheQuantiser/ZH4l_coffea/commit/3ae001301859f3d3b2d1d1ae5448beb2de3dcf84) | main ancestry | Record completed 2024 trigger-probe production and limits |
| 2026-09-29 17:58:49 | [c5e3e5c](https://github.com/TheQuantiser/ZH4l_coffea/commit/c5e3e5c3e1a555726626e17c5294f9a39d069b49) | main ancestry | Document 2024 trigger-probe outputs and full-year yields |
| 2026-09-29 19:06:39 | [ed9f17c](https://github.com/TheQuantiser/ZH4l_coffea/commit/ed9f17cd6732054530d134ada15c45cbbe27465a) | main ancestry | Compare 2024 low-pT Z yields by period with mkShapesRDF |
| 2026-09-29 23:48:24 | [062cfea](https://github.com/TheQuantiser/ZH4l_coffea/commit/062cfea35ba6a6395b926854228efc94753d02cb) | main ancestry | Publish paired 2024 low-pT event diagnosis |
| 2026-09-30 01:00:24 | [a5bba58](https://github.com/TheQuantiser/ZH4l_coffea/commit/a5bba58ed10e53df463fec9bf23ca8c002df909e) | Electron diagnostic branch | Document paired electron RunStability divergence |
| 2026-09-30 04:20:34 | [fe0a757](https://github.com/TheQuantiser/ZH4l_coffea/commit/fe0a757829f1c6f90759a2524144db0494da07fc) | Electron diagnostic branch | docs: map named study configuration and processing boundaries |
| 2026-09-30 04:59:48 | [44e7ae7](https://github.com/TheQuantiser/ZH4l_coffea/commit/44e7ae7b98a894f79c647ae637791feded3ea381) | Electron diagnostic branch | docs: establish study documentation home and audit history |
| 2026-09-30 12:09:36 | [2b5ba43](https://github.com/TheQuantiser/ZH4l_coffea/commit/2b5ba43d6a264a441498a6a5c76af6e253dd2847) | main ancestry | docs: organize Coffea study guidance on main |
