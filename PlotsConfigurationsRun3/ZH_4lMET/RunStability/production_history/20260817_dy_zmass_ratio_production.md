# 2026-08-17 DY Z-mass ratio production

> **Historical receipt.** This campaign used the incomplete 151-run Run2022
> C--D population. It is superseded for early-2022 stability by the validated
> ten-component, 739-file, 170-run B--D contract. Preserve its artifacts as
> evidence, but do not reuse its 2022 ratios as current results.

## Objective and authorization

This receipt records the then-current all-era production needed for DATA/MC
ratio-versus-run plots in DY categories. The user explicitly authorized a new
submission after inspection established that the completed historical
campaign contained only `run_stability/ZZCR_*` DATA TH2 objects.

The production is intentionally narrow in histogram space and complete in
input space:

- eras: `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`;
- region: `DY` only;
- observable: `Z0_mass`;
- categories: all 24 standard DY categories;
- samples: the complete `presentation` DATA and prompt-MC population;
- files: every configured file, with ten input files per Condor job;
- nuisances: nominal only;
- input: direct CERN XRootD;
- output: packaged workers staging to FNAL EOS.

No sample, DATA stream, DATA run, or per-sample file filter is permitted.

## Fixed submission command

After sourcing `start.sh` and `fnal_lpc_packaged_env.sh`, selecting one era,
the fixed analysis selectors, and a fresh campaign identity, each era uses:

```bash
mkShapesRDF -c 1 --submit \
  -f PlotsConfigurationsRun3/ZH_4lMET/RunStability \
  -l -1 -q workday
```

## Live state

Preflight at `2026-08-17T21:46:41Z` established:

- checkout branch `ZH_devel`, HEAD
  `a67e3fca9171012502c092a3ceed2b2f7a20d00e`;
- a valid CMS proxy with 591,693 seconds remaining;
- `condor_submit` and `xrdfs` available;
- the historical merged files are incompatible because their auxiliary DATA
  matrix is ZZCR rather than DY;
- no new submission had occurred at this point.

| Era | Campaign | Exact pickle | Tag | Cluster / schedd | Jobs | State |
| --- | --- | --- | --- | --- | ---: | --- |
| 2022 | `DY_ZMASS_RATIO_2022_20260817T214641Z` | `config_26-08-17_16_48_43.pkl` | `FourLepton_2022_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-all-dy_20260817_214831` | `85161141` / `lpcschedd6.fnal.gov` | 505 | submitted; 379 idle, 126 running at first query |
| 2022EE | `DY_ZMASS_RATIO_2022EE_20260817T214641Z` | `config_26-08-17_16_54_48.pkl` | `FourLepton_2022EE_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-all-dy_20260817_215432` | `30077980` / `lpcschedd5.fnal.gov` | 1,216 | submitted; 1,216 idle at first query |
| 2023 | `DY_ZMASS_RATIO_2023_20260817T214641Z` | `config_26-08-17_16_57_42.pkl` | `FourLepton_2023_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-all-dy_20260817_215717` | `85161142` / `lpcschedd6.fnal.gov` | 707 | submitted; 675 idle, 32 running at first query |
| 2023BPix | `DY_ZMASS_RATIO_2023BPIX_20260817T214641Z` | `config_26-08-17_17_00_09.pkl` | `FourLepton_2023BPix_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-all-dy_20260817_215953` | `30078011` / `lpcschedd5.fnal.gov` | 455 | submitted; 455 idle at first query |
| 2024 | `DY_ZMASS_RATIO_2024_20260817T214641Z` | `config_26-08-17_17_02_38.pkl` | `FourLepton_2024_RUN_STABILITY_standard_analysis_presentation_HIST_NOMINAL_DY_OBS-z0-mass_CAT-all-dy_20260817_220220` | `85161143` / `lpcschedd6.fnal.gov` | 3,967 | submitted; 3,872 idle, 95 running at first query |

All five submissions were accepted, for 6,850 jobs in total. On this LPC
host the direct `condor_submit` execution returned `ENOEXEC`; the framework's
argument-safe `/bin/sh /usr/local/bin/condor_submit` compatibility fallback
then completed successfully for every era. Each row above is pinned to the
fresh pickle and scheduler receipt created by that accepted submission.

## Completion and merge evidence

All five exact clusters subsequently left their schedds. Exact history
reconciliation found 6,850 unique process IDs, covering every submitted proc,
with `JobStatus=4` and `ExitCode=0`; there were no missing, duplicate, held,
active, or nonzero-exit records. The exact-pickle `--check` command also
reported every split finished before any merge was launched.

The documented exact-pickle `--histoadd` command completed for every era. The
durable FNAL EOS directory for each campaign contains its complete split-file
set plus exactly one merged ROOT file. Each local and remote merged file was
reopened independently and was readable, non-zombie, and non-recovered.

| Era | Logical outputs / components / configured files | Runs | Remote members after merge | Merged bytes | Local SHA-256 | Exact object result |
| --- | --- | ---: | ---: | ---: | --- | --- |
| 2022 | 53 / 75 / 4,783 | 151 | 506 | 809,346 | `2003ff3f4222a43d1440bbfd896b96ef274e9671da573062e599e2fe9be68e1c` | 1,301 expected and observed |
| 2022EE | 53 / 78 / 11,885 | 190 | 1,217 | 854,412 | `8b1f157a709ed71c2b657e7e5da0e934086c51792efc59ac4ef26714a58f8f5e` | 1,301 expected and observed |
| 2023 | 53 / 89 / 6,816 | 126 | 708 | 809,156 | `370af450e975406eec74be43d36673a64a3cb3d6c436f5d89d3dba1c7ec018a6` | 1,301 expected and observed |
| 2023BPix | 53 / 77 / 4,309 | 43 | 456 | 748,978 | `c5c2da93a77a1fd88add3214f3116c0d044f21db2529ccb97199c18913bab03c` | 1,301 expected and observed |
| 2024 | 55 / 99 / 39,394 | 456 | 3,968 | 1,235,738 | `2abfd1372c6a48574aa2f7a910f8a10d8e6f8bc41b7ad0eaa4bac24f6f2b9243` | 1,349 expected and observed |

The era-specific object expectation is derived from each exact pickle rather
than assumed constant. The first four eras contain 53 logical outputs and
therefore 1,272 ordinary TH1 objects, 24 DATA auxiliary TH2 objects, and five
metadata TH1 objects. The 2024 pickle contains 55 logical outputs, so its
correct counts are 1,320 ordinary TH1 objects, 24 DATA auxiliary TH2 objects,
and five metadata TH1 objects. Every era had zero missing and zero unexpected
objects. All auxiliary run labels, run-axis flows, observable binning, DATA
TH2-to-ordinary-TH1 closure, four luminosity arrays, and the retained MC source
luminosity matched the serialized contract.

During durable validation, the documented `list` and `validate` subcommands
exposed a source bug: their parsers do not define `luminosity_source`, but the
shared helper accessed it unconditionally. `_single_dataset` now uses an
explicit `None` for subcommands that do not select a luminosity source, and a
CLI regression test covers both commands. The focused plotting test module
passes with four tests.

## 2022EE recorded-DATA dataset audit

This audit is explicitly about recorded DATA primary datasets, not MC. The
exact submitted pickle contains the complete nine-component matrix expected
by the read-only 2022EE configuration family:

| Primary dataset | Run2022E Prompt-v1 | Run2022F Prompt-v1 | Run2022G Prompt-v1 |
| --- | ---: | ---: | ---: |
| `MuonEG` | 29 | 93 | 26 |
| `Muon` | 147 | 359 | 88 |
| `EGamma` | 188 | 490 | 87 |

The inspected read-only DY, 3l, SS, Top, WW, HWW ggH/VBF, and VBS 2022EE
configurations all select these same three primary datasets, three run tags,
`Run2022EE_Prompt_nAODv12_Full2022v12`, and
`DATAl2loose2022EEv12__l2loose`. A live CERN XRootD listing found exactly
1,507 matching HWWNano files. Comparing normalized full paths against all
1,507 file URIs serialized in `config_26-08-17_16_54_48.pkl` produced zero
submitted-only paths and zero materialized-only paths. No 2022EE recorded-DATA
dataset or file is missing from this submission.

## Ratio-versus-run products

The all-era dataset order is `2022`, `2022EE`, `2023`, `2023BPix`, `2024`,
for 966 labelled run rows. Every one of the 24 DY categories was attempted
independently for `nominal` and `trigger_any` recorded luminosity.

Forty-four combinations succeeded: 22 categories times two luminosity
sources. Each writes PNG, PDF, CSV, JSON, and ROOT, for exactly 220 files in
`jobs/DY_ZMASS_RATIO_20260817T214641Z/ratio_vs_run`. The four absent
combinations are:

- `DY_STREAM_EGAMMA_ZMM` with `nominal` and `trigger_any`;
- `DY_ENRICHED_STREAM_EGAMMA_ZMM` with `nominal` and `trigger_any`.

Each failed before output with `Era 2023BPix has nonpositive total prompt-MC
yield`. No partial file exists for those stems, no zero ratio was fabricated,
and 2023BPix was not silently removed from the run axis.

An independent audit found the exact expected 44 stems in all five formats,
176 matching receipt-declared hashes, 966 exact era/run rows per CSV, and 44
readable seven-object ROOT products. Every ROOT summary contains a 966-point
Garwood-plus-MC-stat graph and two `966 × 966` covariance matrices. Across the
22 nominal products all 966 rows are valid. Across the 22 `trigger_any`
products, 963 rows are valid and runs `380126`, `380127`, and `380128` are
explicitly retained as `zero_luminosity` with blank ratio fields. In total the
audit checked 42,504 rows: 42,438 valid and 66 intentionally invalid.

The first rendered plots exposed ROOT's ordinary statistics box and an
unusable 15,996-pixel canvas driven by one visible x label per run. The
analysis-local renderer was subsequently replaced with Matplotlib using the
maintained `notebooks/mkshapes_analysis_lab` publication-light tokens and
ratio-panel grammar. The redesigned fixed-size canvas uses a semantic
`0.5-1.5` range, directional boundary triangles, adaptive run labels,
alternating era lanes, integrated era luminosity labels, an explicit unity
reference, and invalid zero-luminosity markers. Full numerical ratios and
uncertainties remain in CSV/ROOT; JSON receipt schema 2 records the style,
display range, selected labels, era spans, outliers, invalid runs, renderer
versions, and hashes. The exact luminosity propagation is documented in
`LUMINOSITY_PROPAGATION.md`.

## Final validation state

After the renderer change, the latest complete leaf test rerun passed: 104
tests in 75.34 seconds. The focused plotting module passed all five tests in
4.17 seconds, including
CLI `list`/`validate`, Garwood and MC-stat propagation, era-block covariance,
semantic range classification, artifact production, and presentation
metadata. Targeted Black and flake8 checks passed. The final gallery audit
found exactly 44 schema-2 receipts and 220 files, verified all 176
receipt-declared hashes, reopened all 44 seven-object ROOT products, checked
all 44 PDFs, and confirmed that every PNG is exactly `1500 x 840` pixels. The
44 regenerated CSV files are byte-identical to their pre-redesign versions.
Full-gallery contact sheets and representative inclusive and sparse-category
plots were visually inspected for clipping, label collisions, runaway axes,
and misleading error-bar rendering. The leaf does not contain the previously
documented `quick_validate.py`; no such command was therefore run for this
renderer revision.

No mkShapesRDF core, `include/`, `utils/`, original `ZH_4lMET/ZZ_CR`, or
read-only sibling `PlotsConfigurationsRun3` source was modified. In the child
checkout, `.gitignore` remains a pre-existing user modification and this leaf
remains untracked pending an explicit commit decision.
