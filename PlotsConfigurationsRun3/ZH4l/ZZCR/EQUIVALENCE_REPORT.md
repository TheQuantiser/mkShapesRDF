# ZZCR legacy-to-ZH4l equivalence report

Validation completed on 2026-08-12 with
`validate_equivalence.py --events 10000`. The validator copied the protected
legacy source into ignored temporary space, ran legacy and new configurations
against the same first real ROOT file for each logical sample, and deleted the
temporary source copies afterward. Nothing below `ZH_4lMET` was edited or used
as an output directory.

## Compared contract

For every event passing the common preselection, the validator compared:

- `run`, `luminosityBlock`, and `event` identity;
- both selected Z indices and both selected X indices;
- `mZ`, `mX`, `m4l`, `ptZ`, `ptX`, `pt4l`, `PuppiMET_pt`, and `minMll4l`;
- `pass4lPt`, `veto5l`, `bVeto`, and `nLepton10`;
- membership in `ZZCR`, its `4e`, `4mu`, and `2e2mu` projections,
  `SR_XSF`, and `SR_XDF`;
- the complete nominal event weight, including luminosity and the selected-ZX
  lepton, trigger, pileup, MET-filter, and b-veto correction domain.

It then independently rebuilt and compared all 54 nominal distributions: six
categories times the nine production observables, using the restored validated
variable edges and fold policies.

## Real-input coverage and results

| ERA | logical sample | events passing preselection | ZZCR | SR XSF | SR XDF | result |
|---|---|---:|---:|---:|---:|---|
| 2022 | `ZZ` | 865 | 5 | 0 | 0 | exact |
| 2022 | `ZH_Hto2Wto2L2Nu_M125` | 2,963 | 0 | 14 | 18 | exact |
| 2022EE | `ZZ` | 2,348 | 19 | 0 | 0 | exact |
| 2022EE | `ZH_Hto2Wto2L2Nu_M125` | 5,430 | 0 | 29 | 34 | exact |
| 2023 | `ZZ` | 6,489 | 44 | 1 | 0 | exact |
| 2023 | `ZH_Hto2Wto2L2Nu_M125` | 1,872 | 0 | 11 | 10 | exact |
| 2023BPix | `ZZ` | 6,430 | 51 | 3 | 0 | exact |
| 2023BPix | `ZH_Hto2Wto2L2Nu_M125` | 818 | 0 | 4 | 4 | exact |
| 2024 | `ZZ` | 6,530 | 47 | 0 | 0 | exact |
| 2024 | `ZH_Zto2L_Hto2Wto2L2Nu_M125` | 424 | 0 | 5 | 12 | exact |

Across all five eras and both representative physics samples:

- preselection event-key sets were identical;
- every integer and boolean value was identical;
- the maximum absolute difference for every floating observable and nominal
  event weight was `0`;
- all region entries and weighted yields were identical;
- the maximum bin-content difference over all 540 compared sample/era/category
  distributions was `0`.

The full validation took 261.51 seconds wall time and peaked at 987,480 kB RSS
for the orchestration process. Per-era legacy/new snapshot wall times were:

| ERA | legacy | new |
|---|---:|---:|
| 2022 | 31.34 s | 21.33 s |
| 2022EE | 30.33 s | 21.59 s |
| 2023 | 29.15 s | 21.37 s |
| 2023BPix | 29.77 s | 20.93 s |
| 2024 | 28.52 s | 20.87 s |

These are validation-snapshot timings, not nominal production histogram
benchmarks. They demonstrate that the new graph did not regress relative to
the legacy graph under the same bounded event and file scope.
