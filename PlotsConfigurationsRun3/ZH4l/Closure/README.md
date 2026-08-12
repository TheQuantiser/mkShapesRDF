# DY-to-ZZ closure study

This independent nominal study owns the diagnostic bridge that does not belong
in ZZCR production: DY and four-lepton cumulative stages, N−1 releases,
flavor/topology splits, trigger-family partitions, data-stream partitions,
and extra-tight-lepton counts.

Common Z/X objects, era/process materialization, observables, selected
corrections, and b tagging are consumed from `common`. Closure-only rapidity,
`phiEtaStar`, anchor-pT, extra-lepton, and partition quantities remain in this
leaf. The default graph has 54 categories and a sparse 295-action histogram
plan. Its local runner is required for sparse cut-variable booking and
stage/variable-specific weight factors.

```bash
source start.sh
export CLOSURE_CAMPAIGN=closure_check
export CLOSURE_SAMPLE_PROFILE=major   # or full
export LIMIT_FILES_PER_SAMPLE=1
PlotsConfigurationsRun3/ZH4l/Closure/run_all_eras.sh compile
PlotsConfigurationsRun3/ZH4l/Closure/run_all_eras.sh pilot
PlotsConfigurationsRun3/ZH4l/Closure/run_all_eras.sh summary
PlotsConfigurationsRun3/ZH4l/Closure/run_all_eras.sh plots
```

This study intentionally contains no nuisance variations and no nonprompt fake
background. See [CLOSURE_STUDY.md](CLOSURE_STUDY.md) for the stage algebra,
binning, inference boundaries, and interpretation.
