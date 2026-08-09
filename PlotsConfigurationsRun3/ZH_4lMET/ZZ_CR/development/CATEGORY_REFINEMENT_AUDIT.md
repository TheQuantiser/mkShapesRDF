# Category-refinement audit

## Starting state

- Audit date: 2026-08-09
- Branch: `ZH_devel`
- Starting HEAD: `0de38da3c3977ae2030e4ee7d95e6d8edc24e0ee`
- Starting HEAD was clean and matched `origin/ZH_devel`.
- The running 2024 minimal production uses an immutable package compiled from
  this starting commit and is independent of the source changes in this task.

The executable starting profile sizes for `ANALYSIS_PASS=ALL`,
`HISTOGRAM_PROFILE=analysis`, and nominal histograms were:

| Profile | Final categories | Category-variable actions |
| --- | ---: | ---: |
| `minimal` | 3 | 125 |
| `flavor` | 10 | 425 |
| `stream` | 12 | 500 |
| `trigger` | 18 | 750 |
| `debug` | 34 | 1,425 |

The starting profiles applied the same region-level variable set to every
view. They had no first-class view/family metadata, no `standard` or
`detailed` use-case profile, and the trigger profile selected overlapping raw
trigger bits. The refinement below records final design choices, occupancy,
action budgets, runtime evidence, and the ten requested review answers.

## Final executable plan

| Profile | Final categories | Actions | Linear + log plots |
| --- | ---: | ---: | ---: |
| `minimal` | 3 | 125 | 250 |
| `standard` | 35 | 839 | 1,678 |
| `flavor` | 15 | 473 | 946 |
| `stream` | 12 | 326 | 652 |
| `trigger` | 18 | 460 | 920 |
| `detailed` | 41 | 929 | 1,858 |
| `debug` | 56 | 1,264 | 2,528 |

Standard breaks down as 12 DY, 12 ZZCR, and 11 SR categories. By view it has
3 inclusive, 12 flavor/topology, 9 stream, and 11 curated stream-flavor
categories. Its actions break down as 204 DY, 293 ZZCR, and 342 SR; by view
they are 125 inclusive, 348 flavor, 201 stream, and 165 stream-flavor.

Standard is 6.712 times minimal and the old graph is 27.907 times standard.
The default safety limits are profile-aware; debug deliberately exceeds its
normal category/action budgets and requires `ALLOW_LARGE_PLAN=1`.

## Evidence

- Thirty-four focused tests pass, including explicit truth tables for every
  requested DY, ZZCR, and SR algebra identity.
- A real staged 2024 ZZ run over 100 events completed in 55.64 s with
  1,109,000 kB login-node maximum RSS and wrote a healthy 523,253-byte ROOT
  file with exactly 35 category directories.
- The real output has 25/50-variable inclusive views, 19/31-variable flavor
  views, 17/25-variable stream views, and 15-variable intersections.
  `DY_STREAM_MUON_ZEE/X_mass` is absent while
  `ZZCR_STREAM_EGAMMA_4E/X_mass` exists.
- The occupancy study staged seven CERN inputs spanning all five eras, v12,
  v15, ZZ, ZH, MC, and DATA. It examined 45,376 events with selection-only
  Filter/Count actions. Full evidence and bounded-zero decisions are in
  `category_occupancy.json` and `CATEGORY_DESIGN.md`.
- Ten packaged FNAL jobs in clusters 85068324--85068327 all exited zero:
  2024 v15 ZZ, 2024 v15 ZH, 2022 v12 ZZ, and seven 2024 v15 MuonEG DATA
  splits. Logs map CERN sources into `/srv/mkShapesRDF_stagein_*`; all outputs
  were staged only to FNAL EOS and all ten ROOT files passed the exact sparse
  directory checks. Peak Condor `MemoryUsage` was 647 MB versus the previous
  minimal peak of 566 MB, a 14.3% increase for 6.712 times as many actions.
  Standard pilot outputs are 509,871--637,210 bytes per 100-event split.
  Exact contracts, resources, paths, and comparison are in
  `fnal_category_pilot_receipt.json`.

## Requested final review

1. **What was missing?** The three inclusives could not localize flavor,
   dataset-stream, trigger-priority, or selected-four-lepton topology closure
   failures.
2. **Why is every standard category useful?** Inclusive views retain broad
   physics distributions; flavor/topology leaves isolate selected-object
   composition; stream marginals test exclusive dataset acceptance; DY's six
   leaves test its complete trigger/stream closure matrix; ZZ's five leaves
   test expected pure-flavor routing and all mixed-topology fallback streams.
3. **What was omitted?** Four unhelpful pure-flavor ZZ stream crosses, all 15
   SR stream-by-topology leaves, trigger-path crosses, and every implicit
   higher-dimensional product. SR stream-by-X-flavor is detailed-only.
4. **Which families are exclusive?** DY Z flavor, every stream-priority
   family, every trigger-priority family, ZZ topology, SR X flavor, SR
   topology, DY stream-flavor leaves, and the curated ZZ leaves are internally
   exclusive. Inclusive/flavor/stream/intersection families overlap one
   another as projections; curated ZZ is not exhaustive.
5. **Actions per profile?** Minimal/standard/flavor/stream/trigger/detailed/
   debug use 125/839/473/326/460/929/1,264 actions.
6. **Standard versus minimal?** 6.712 times as many actions.
7. **Standard versus old?** 27.907 times smaller than 23,414 actions and more
   than an order of magnitude below it.
8. **One nominal job set?** Yes. `ALL + standard + analysis + nominal` creates
   all 35 projections in one graph and one split-job set.
9. **Semantic changes?** No physical cuts, selected-index trigger logic,
   fixed-WP b-tag logic/corrections, sample overlap, weights, input staging,
   output endpoint, histogram-only rule, or nominal-only ALL rule changed.
10. **Files outside scope?** No tracked source outside
    `PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR` was changed.
