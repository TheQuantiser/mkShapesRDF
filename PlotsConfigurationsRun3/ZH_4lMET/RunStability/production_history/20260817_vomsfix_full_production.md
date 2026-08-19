# 2026-08-17 VOMS-fix full production

> **Historical transport receipt.** Successful proxy handling and worker
> stage-out do not make this campaign's incomplete 2022 DATA population a
> current luminosity or physics reference. Preserve the scheduler and transport
> evidence, but use the validated B--D contract for current run stability.

This record describes the fresh all-era replacement production submitted after
the worker VOMS trust failure recorded in
`20260817_initial_submission_failure.md`. The production used every configured
sample and file in the `RUN_STABILITY` `standard`/`analysis`/`presentation`
nominal profile, with ten input files per job, direct CERN XRootD reads,
packaged FNAL workers, and FNAL EOS stage-out.

The exact submission command for each freshly compiled era was:

```bash
mkShapesRDF -c 1 --submit \
  -f PlotsConfigurationsRun3/ZH_4lMET/RunStability \
  -l -1 -q workday
```

The environment was reset with `fnal_lpc_packaged_env.sh` before the analysis
profile and unique era campaign were selected. The serialized worker setup
included:

```text
X509_VOMS_DIR=/cvmfs/grid.cern.ch/etc/grid-security/vomsdir
```

## Submission and completion manifest

| Era | Exact pickle | Logical outputs / source components / input files | Cluster and schedd | Jobs | Final history | Remote split ROOT files |
| --- | --- | ---: | --- | ---: | --- | ---: |
| 2022 | `config_26-08-17_13_16_31.pkl` | 53 / 75 / 4,783 | `3850141` on `lpcschedd4.fnal.gov` | 505 | 505 status 4, exit 0 | 505 |
| 2022EE | `config_26-08-17_13_17_56.pkl` | 53 / 78 / 11,885 | `3850143` on `lpcschedd4.fnal.gov` | 1,216 | 1,216 status 4, exit 0 | 1,216 |
| 2023 | `config_26-08-17_13_19_42.pkl` | 53 / 89 / 6,816 | `30071844` on `lpcschedd5.fnal.gov` | 707 | 707 status 4, exit 0 | 707 |
| 2023BPix | `config_26-08-17_13_21_32.pkl` | 53 / 77 / 4,309 | `85155838` on `lpcschedd6.fnal.gov` | 455 | 455 status 4, exit 0 | 455 |
| 2024 | `config_26-08-17_13_23_21.pkl` | 55 / 99 / 39,394 | `3850144` on `lpcschedd4.fnal.gov` | 3,967 | 3,967 status 4, exit 0 | 3,967 |

The exact contracts report `sample_selection_source=profile`; no sample,
stream, run, or per-sample file limit was active. All 6,850 jobs were absent
from the live queue after completion. Exact-JDL
filename comparison found no missing or unexpected split outputs. A later
independent `xrdfs` listing found the complete split inventory and exactly one
merged `mkShapes__<tag>.root` in each remote campaign directory.

## Merge and artifact checks

Each era was checked and merged with its exact pickle:

```bash
mkShapesRDF -c 0 --check -b 1 \
  -f PlotsConfigurationsRun3/ZH_4lMET/RunStability \
  -config PlotsConfigurationsRun3/ZH_4lMET/RunStability/configs/config_<exact>.pkl

mkShapesRDF -c 0 --histoadd -b 0 \
  -f PlotsConfigurationsRun3/ZH_4lMET/RunStability \
  -config PlotsConfigurationsRun3/ZH_4lMET/RunStability/configs/config_<exact>.pkl
```

Every status check reported every logical sample finished and zero running.
Every merge returned success, produced a readable local ROOT file, and staged
one merged ROOT file to the corresponding FNAL EOS directory.

| Era | Merged bytes | Ordinary TH1 | DATA run-stability TH2 | Luminosity metadata TH1 | Run bins | First/last run |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 2022 | 7,243,593 | 16,483 | 84 | 5 | 151 | 355862 / 357900 |
| 2022EE | 7,356,473 | 16,483 | 84 | 5 | 190 | 359569 / 362760 |
| 2023 | 7,288,726 | 16,483 | 84 | 5 | 126 | 367095 / 368823 |
| 2023BPix | 7,191,547 | 16,483 | 84 | 5 | 43 | 369927 / 370790 |
| 2024 | 7,968,320 | 17,105 | 84 | 5 | 456 | 379416 / 386951 |

For every era, the representative `run_stability/ZZCR_ALL/Z0_mass/histo_DATA`
x-axis labels matched the audited first and last runs, x underflow and overflow
were empty, and no auxiliary MC TH2 was present.

## Ordinary one-dimensional plots

The standard `mkPlot` workflow was run against each exact merged file and
pickle. The compiled plot graph has 311 category-variable actions. The three
standard plot types (`c`, `cratio`, and `cdifference`), each in linear and log
form, produced 1,866 nonempty PNG files plus `plotter.html` per era.

The 2024 `cratio_ZZCR_ALL_Z0_mass.png` was visually inspected: the luminosity
label was 109.08 fb^-1, the Data/MC stack, axes, legend, and ratio panel were
readable, and the DATA and ZZ yields were populated.

These are era-level one-dimensional plots from the ordinary histogram
hierarchy. They are not luminosity-scaled per-run comparisons. The auxiliary
TH2s and luminosity metadata preserve the inputs for that later workflow, but
the choice between nominal and trigger-effective recorded luminosity remains
explicitly unresolved and no default scaling was applied.
