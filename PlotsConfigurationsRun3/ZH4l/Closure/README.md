# DY-to-ZZ closure study

This independent nominal study owns the diagnostic bridge that does not belong
in ZZCR production: DY and four-lepton cumulative stages, N−1 releases,
flavor/topology splits, trigger-family partitions, data-stream partitions,
and extra-tight-lepton counts.

Common Z/X objects, era/process materialization, observables, selected
corrections, and b tagging are consumed from `common`. Closure-only rapidity,
`z_phi_eta_star`, anchor-pT, extra-lepton, and partition quantities remain in this
leaf. The default graph has 54 categories and a sparse 295-action histogram
plan. Its local runner delegates sparse cut-variable booking,
stage/variable-specific factors and event snapshots to `common.runner`.

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

`ZH4L_OUTPUT_MODE=trees` or `both` enables one event tree per selected stage.
The default tree `weight` includes that stage's nominal correction factor;
`weight_base` retains the native normalization before the stage factor.
Overlapping stages repeat events deliberately and preserve original identity.
An exact `SAMPLE_FILTER` takes precedence over `CLOSURE_SAMPLE_PROFILE=major`.

The current category-parent map fixes the former S0 topology-child omission of
`sf_b_veto`: S0's 4e, 4mu and 2e2mu children now inherit the parent's correction.
This intentionally changes their MC yields while retaining their selections
and axes. N-minus-one veto removal has its own explicit correction policy.
[NAMING.md](../NAMING.md) defines the current derived-column/output vocabulary;
historical study results predate this correction and schema migration.

Correction counters now use public histogram names `yield_base`, `yield_lepton`,
`yield_lepton_trigger`, and `yield_nominal` within each stage directory.
