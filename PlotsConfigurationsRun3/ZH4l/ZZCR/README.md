# ZZCR configuration leaf

This is the development family’s nominal four-lepton configuration. It contains the
inclusive `ZZCR`, its `4e`, `4mu`, and `2e2mu` projections, plus `SR_XSF` and
`SR_XDF`. The selections are written directly in `cuts.py` from `zx_is_valid`,
`zx_pass_ordered_pt`, `event_pass_extra_lepton_veto`, `zx_min_pair_mass`, `event_pass_b_veto`, Z/X flavor and mass, MET, and
quartet kinematics.

MC uses one coherent correction domain:

```text
XSWeight × METFilter_Common × puWeight
× sf_lepton_zx × sf_trigger_zx × sf_b_veto
```

Data uses its validated stream de-duplication triggers and `METFilter_DATA`.
The nine nominal variables are explicit in `variables.py`; there are 54
nominal histogram actions. The seven retained legacy observables preserve
their validated variable-bin axes and flow policies; `zx_min_pair_mass` and
`veto_lepton_count` have explicit family-owned axes. Nominal runs use the shared histogram/tree adapter; the existing full nuisance
route uses native `runnerFile = "default"`.

`SAMPLE_PROFILE=full` is the production default and includes the complete
configured MC inventory plus `DATA`. Use `SAMPLE_PROFILE=quick` for the
bounded DY+ZZ+DATA scope. Legacy profile names `presentation` and
`commissioning` remain aliases for `full` and `quick`. An exact
`SAMPLE_FILTER` overrides either profile.

Bounded local run from the repository root:

```bash
source start.sh
source PlotsConfigurationsRun3/ZH4l/env/lxplus.sh
export ERA=2024 SAMPLE_FILTER=ZZ LIMIT_FILES_PER_SAMPLE=1
export ENABLE_SYSTEMATICS=0 ZH4L_CAMPAIGN=zzcr_smoke
mkShapesRDF -c 1 -o 0 -b 0 \
  -f PlotsConfigurationsRun3/ZH4l/ZZCR -l 100
```

Set `ENABLE_SYSTEMATICS=1` for the full nuisance model. For a dry batch
compile, replace `-o 0 -b 0` with `--submit -dR 1`; inspect the timestamped
pickle and JDL before submitting. Output/config/batch/plot locations can be
overridden with `ZH4L_OUTPUT_FOLDER`, `ZH4L_CONFIGS_FOLDER`,
`ZH4L_BATCH_FOLDER`, and `ZH4L_PLOT_PATH`.

Reproduce the protected legacy-vs-new validation on one real ZZ and ZH file
per era with:

```bash
source start.sh
source PlotsConfigurationsRun3/ZH4l/env/lxplus.sh
python PlotsConfigurationsRun3/ZH4l/ZZCR/validate_equivalence.py \
  --events 10000
```

The validator copies the legacy source into ignored temporary space; it never
edits or writes output beneath `ZH_4lMET`. See `EQUIVALENCE_REPORT.md` for the
curated results from the completed migration validation.

`ZH4L_OUTPUT_MODE=both` adds one event tree per region to the same ROOT file;
`trees` exports only trees. These modes require `ENABLE_SYSTEMATICS=0`.
The projection includes original event/source identity, selected Z/X indices
and kinematics, jet/MET inputs, correction factors and total `weight`.
See [the naming contract](../NAMING.md) before consuming newly generated files.
