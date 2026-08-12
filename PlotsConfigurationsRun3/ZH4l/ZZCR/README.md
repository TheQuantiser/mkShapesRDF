# ZZCR production leaf

This is the nominal four-lepton production configuration. It contains the
inclusive `ZZCR`, its `4e`, `4mu`, and `2e2mu` projections, plus `SR_XSF` and
`SR_XDF`. The selections are written directly in `cuts.py` from `validZX`,
`pass4lPt`, `veto5l`, `minMll4l`, `bVeto`, Z/X flavor and mass, MET, and
quartet kinematics.

MC uses one coherent correction domain:

```text
XSWeight × METFilter_Common × puWeight
× LepSF_ZX × TriggerSF_ZX × bVetoSF
```

Data uses its validated stream de-duplication triggers and `METFilter_DATA`.
The nine nominal variables are explicit in `variables.py`; there are 54
nominal histogram actions. The leaf uses native `runnerFile = "default"`.

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
