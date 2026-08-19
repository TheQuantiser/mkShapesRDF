# 2026-08-19 RunStability architecture redesign

## Objective

Replace the cloned, patch-oriented `ZZ_CR_RunStability` leaf with a coherent
`RunStability` configuration whose public purpose is nominal DY stability.
The redesign had to preserve retained production evidence and plot
reproducibility while eliminating duplicate runtime authorities.

No new batch campaign, remote write, merge, or plot gallery was produced in
this redesign. Existing generated artifacts were treated as immutable inputs
or historical evidence.

## Filesystem and public boundary

The active filesystem leaf is:

```text
PlotsConfigurationsRun3/ZH_4lMET/RunStability
```

The sole public graph is `ANALYSIS_PASS=RUN_STABILITY`, region `DY`, nominal
histograms only. ZZCR, SR, CONTROL, FOURL, tree-output, b-tag, recoil, and
four-lepton execution routes were removed. Non-DY MC samples remain as the
disjoint `Others` background needed by Data/MC plots.

## Single-source ownership

- `year_config.json` owns eras, campaigns, DATA components, run tags, streams,
  stream triggers, physical HLT paths, MC samples, and exact nominal recorded
  luminosity results. It contains no analysis selection or histogram axes.
- `run_stability_profiles.json` owns the selected-Z construction and final
  thresholds, strict mass window, observable order, compact uniform axes,
  category definitions, logical trigger joins, expected category identity,
  and active luminosity-binding path.
- `lumi/run_stability_luminosity_binding.json` binds the live configuration to
  immutable copied audit evidence without rewriting the audit's old path or
  identity.
- Python validates and materializes those declarations. It does not maintain a
  second numerical registry.
- `plot_reproduction.json` owns only retained historical pickle/merged-ROOT
  identities. It is not an input to future production.

The compact uniform-axis schema is `[number_of_bins, lower_bound,
upper_bound]`. The loader derives exactly `number_of_bins + 1` edges and
validates positive integral bin count, increasing bounds, mass-window/axis
agreement, and selected-lepton-threshold/axis agreement.

## Current numerical contract

The active selected event requires both selected leptons to satisfy strict
`pT > 35 GeV` and strict `60 < Z0_mass < 120 GeV`. The candidate-building
threshold `[10, 10]` and final ordered analysis threshold `[35, 35]` are
separate semantics, not duplicate definitions.

The exact observable order is:

```text
Z0_mass, Z0_pt, lZ1_pt, lZ2_pt, lZ1_eta, lZ2_eta
```

The exact axes are mass 60 bins over 60--120 GeV, Z pT 20 bins over 0--100
GeV, each lepton pT 13 bins over 35--100 GeV, and each eta 50 bins over
-2.5--2.5. pT axes fold overflow only; mass and eta do not fold.

The category tuple contains 48 ordered entries with SHA-256:

```text
be24d1ac1df9a8b1f91b05187031c1e83fee2825c10cee0c690e73121f3d03a5
```

Every era therefore resolves 288 category/observable actions. Partial or
reordered category and observable overrides fail closed.

## Trigger and weight authority

Physical HLT strings occur only in `year_config.json`. The profile owns stable
IDs, labels, luminosity sources, trigger aggregates, TrigMaker-family names,
and aggregate/ordinal joins. `selection_config.py` requires exact DATA/MC
TrigMaker equality and exact-once physical-path coverage; categories consume
the declared source instead of rebuilding it from labels.

The year configuration owns the common MC and DATA weights. The selected-Z
correction is materialized once as:

```text
puWeight*SelectedLeptonSF_Z*TriggerSF_Z
```

Category weights are `1.f`. Speculative duplicate full-weight strings were
removed from category metadata and their regression coverage was replaced by
a test of the actual composition path.

## Luminosity binding

The exact live nominal luminosities are:

| Era | Recorded luminosity [fb\(^{-1}\)] | Runs |
| --- | ---: | ---: |
| 2022 | 8.076828657919002 | 170 |
| 2022EE | 26.671325997159986 | 190 |
| 2023 | 18.062658998219003 | 126 |
| 2023BPix | 9.693130030386998 | 43 |
| 2024 | 109.72830897472497 | 456 |

These are nominal certified-and-dataset-covered results, not Trigger-OR
exposures. The live binding requires exact live-file and semantic-projection
hashes, exact immutable audit manifest/provenance/result hashes, exact
configured-to-audited nominal equality, and exact runtime `lumi` equality.

The retained audit uses `inputs/normtag/normtag_PHYSICS.json`, SHA-256
`693ef4b360a1debb2aa667fa4178c3f4dece9539d9cf3ffee1ea60f157823548`.
Its original `ZZ_CR_RunStability...` identity remains immutable historical
evidence. `lumi/REPRODUCE.md` records the current manual DBS/BRIL sequence.

Final live identities at this redesign gate were:

```text
year_config.json
3a6ad5de15c76c2b46d709134be363813d3db7614b63d8b9e995825914cd9e18

run_stability_profiles.json
2d961d6ce5d8ad43b84d2edf7ebdd5cc56196a5d2287055a319a95514ea47405

lumi/run_stability_luminosity_binding.json
a8f1d7069e3de62a2e4f23fc88bb84b2158708d6367270632b7c610ef1476e9c
```

## Source-first campaign rule

Future numerical changes must modify the owning JSON or source, extend
validation when needed, and compile a fresh exact pickle. Generated pickles,
contracts, payloads, JDLs, job directories, ROOT files, plot receipts, and
images must never be manually patched to emulate a configuration change.

Compile eras serially because the framework pickle filename has one-second
resolution. Reopen each exact pickle, bind it one-to-one to its tag, contract,
payload, JDL, campaign identities, and eventual receipt, then submit only
after separate authorization.

## Validation evidence

The final redesign gates were:

- framework `install.sh --check`: passed;
- full leaf suite: 143 passed;
- focused weight/year/luminosity suite: 27 passed;
- Black and Flake8 over active Python source/tests: passed;
- five era plan inspection: one DY region, 48 categories, six observables,
  288 nominal actions, zero systematic actions;
- all-era category hash and trigger-join equality: passed;
- wrong runtime-luminosity mutation: failed closed as intended;
- five retained pickle/merged-ROOT SHA pairs: validated;
- local skill quick validation: passed;
- active Markdown links, fences, whitespace, and shell-block syntax: passed;
- `git diff --check`: passed.

This establishes local software, configuration, identity, luminosity-binding,
and retained-input reproducibility. It does not establish a new remote input
inventory, new real-event yield closure, or a new batch production.

## Cleanup and Git state

Two Python cache trees containing 82 stale bytecode files and four verified
empty compile/job stubs were removed. Historical pickles, the five
reproduction-bound pickles, merged ROOT files, promoted galleries, immutable
luminosity evidence, and the recovery archive were preserved.

The filesystem rename was not staged or committed. At this gate Git reported
66 tracked deletions under the old leaf and one untracked `RunStability/` tree,
with no unrelated status entry. A future Git handoff must intentionally stage
and review the complete rename; no commit or push was authorized here.
