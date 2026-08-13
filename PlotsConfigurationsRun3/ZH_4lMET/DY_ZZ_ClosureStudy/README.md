# DY–ZZ closure bridge

This directory is a self-contained, histogram-only Run-3 diagnostic that
locates where DATA/prompt-MC closure changes while moving from the exact ZH
four-lepton ZZ control region to inclusive DY.  It does not modify or replace
the production `ZZ_CR` analysis.

The source, helper macros, era/sample catalog, trigger logic, stream
de-duplication, pairing, scale-factor code, tests, runner, summaries, and plots
needed at runtime are vendored here.  No operational import or include points
to a sibling configuration.  The frozen implementation was audited against
starting commit `3659c2e930d58b8a3df387ca9080c9443bb528e8`; this local copy is
deliberate because the user explicitly requested that this study be
self-contained.

## Physics graph

```text
S0 exact ZZCR
 -> S1 no MET
 -> S2 no X-mass window
 -> S3 no X-flavor requirement
 -> S4 no b veto
 -> S5 no all-pair low-mass veto
 -> S6 no fifth-lepton veto
 -> S7 clean four-lepton bridge
 -> S8 common Z bridge
                    <- D0 current enriched DY
                              -> D1 current inclusive DY
                              -> D2 event-tight-pT diagnostic
```

`S8_Z_BRIDGE` uses the current selected Z, a ±15 GeV Z window, candidate
10/10 GeV guards, and an event-level tight-lepton 25/15 GeV requirement.  It is
a genuine parent of both exact ZZCR and current enriched DY.  The broad D1 and
D2 categories are separate branches; no false S8–D1 subset relation is used.

The default sparse plan contains 54 literal categories and 295
category-variable actions.  The small documented excess over the original
40/250 target is caused by materializing all `cat.txt` sentinel trigger and
stream splits as real categories and by retaining the required S8 pileup
shape.  The hard default limits are 60 categories and 300 actions.  There are
no trees and no systematics.

## Binning contract

Every axis is uniform.  Fine axes are used for Z/DY categories; coarse axes are
used for S0–S7, their topology leaves, and all N−1 categories.  This is based
only on `histo_DATA` in the latest completed 2024 full-profile job
`FourLepton_2024_ALL_detailed_analysis_presentation_HIST_NOMINAL_20260810_202324`:

- `DY_ALL`: 94,683,755 DATA events;
- `DY_ENRICHED`: 86,317,021;
- `ZZCR_ALL`: 611;
- ZZCR 4e/4mu/2e2mu: 86/239/286;
- DY MuonEG/Muon/EGamma streams: 336,470/60,305,881/34,041,404.

The final user-specified visible ranges are 140 GeV for Z/X pT, 100 GeV for
selected-Z lepton pT and MET, and 150 GeV for ordered selected-4l lepton pT.
Residual tails are folded.  Fine axes remain bounded by detector resolution
and an interpretable modeling scale: for example, 2 GeV rather than 1 GeV in
`mZ`, and 0.01 rather than 0.002 in `phiEtaStar`.  No MC histogram was
consulted to choose binning.

The Freedman--Diaconis widths inferred from the binned DATA distributions are
0.029/0.091/0.087 GeV for DY `mZ`/`pT(Z)`/MET and 0.80/12.98/3.40 GeV for the
same inclusive ZZCR observables.  Detector resolution, cut-edge alignment,
and robustness of the 86-event 4e leaf set the rounded adopted widths: DY uses
2 GeV in `mZ` and `pT(Z)`, 2.5 GeV in lepton pT and MET, 0.05 in lepton
absolute eta, and one bin per PV count; four-lepton categories use 2.5 GeV in
the on-window Z mass, 20 GeV in Z/X pT, and 5 GeV in MET.  The ZZCR `m4l`
DATA have an FD width near 20 GeV and begin around 160 GeV, so S0 uses
20 GeV bins over 160--600 GeV; its low-statistics topology leaves use 40 GeV.
The relaxed S7 bridge retains the same widths over 80--600 GeV.  A 150 GeV
upper edge for `m4l` would place all observed S0 DATA in overflow, so 150 GeV
is applied to ordered four-lepton lepton pT, not the four-lepton invariant
mass.

## Profiles and limitations

- `CLOSURE_SAMPLE_PROFILE=major`: DATA, DY, ZZ, WZ, Vγ/Vγ*, top, and ttV/tZ;
- `CLOSURE_SAMPLE_PROFILE=full`: every current configured prompt group;
- `CLOSURE_PROFILE=default`: the required sparse diagnostic matrix;
- `CLOSURE_PROFILE=focused_cross`: adds only ZEE×EGamma and ZMM×Muon leaves.

**Nonprompt/fake background is not included.**  This limitation becomes more
important when the low-mass, b-veto, fifth-lepton, or four-lepton requirements
are released.

## Run and validate

From the repository root:

```bash
source start.sh
python3 -m pytest -q \
  PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/tests

export CLOSURE_CAMPAIGN=my_campaign
export CLOSURE_SAMPLE_PROFILE=full
export FILES_PER_JOB=10

PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/run_all_eras.sh inspect
PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/run_all_eras.sh compile
PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/run_all_eras.sh submit
PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/run_all_eras.sh check
PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/run_all_eras.sh merge
PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/run_all_eras.sh summary
PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/run_all_eras.sh plots
```

`submit` forcibly clears pilot filters, selects `full`, removes event/file
limits, enables the FNAL-compatible runtime package, and performs a fresh
compile for each era.  It never reuses a pilot pickle.  `check` and `merge`
use the newest timestamped pickle inside each era-specific campaign directory.

The supported eras are `2022`, `2022EE`, `2023`, `2023BPix`, and `2024`.
Summaries additionally build `combined_2022`, `combined_2023`, `2024`, and
`ALL_RUN3` views.
