# ZH4l selection source record

The authoritative source for this configuration is
`AN2019_238_v9.pdf` (AN2019/238 v9), Section 7, “ZH (H → WW) → 4l + MET.”
The signal-region requirements are in Table 37 on PDF page 120 (document page
118). The ZZ control-region requirements are in Section 7.4 and Table 39 on
PDF page 132 (document page 130).

## Signal regions — Table 37

- XSF flavor condition: the selected X pair is same flavor (`X_isSF`).
- XSF X-mass window: `10 < X_mass < 65 GeV`.
- XSF MET threshold: `PuppiMET_pt > 35 GeV`.
- XSF four-lepton mass threshold: `m4l > 140 GeV`.
- XDF flavor condition: the selected X pair is different flavor (`X_isDF`).
- XDF X-mass window: `10 < X_mass < 70 GeV`.
- XDF MET threshold: `PuppiMET_pt > 20 GeV`.
- XDF four-lepton mass threshold: none.
- Four-lepton ordered pT thresholds: `25, 15, 10, 10 GeV`.
- Fifth-lepton veto: no fifth selected lepton at or above `10 GeV`.
- Z window: `abs(Z0_mass - mZ) < 15 GeV`.
- Charge: the four selected leptons have total charge zero.
- b veto: DeepB loose working point for jets above `20 GeV` in the Run-2
  source. The Run-3 implementation uses the era-specific official loose
  working point configured in `year_config.json`, applied at the same `20 GeV`
  jet threshold.

Table 37 renders the low-mass row as `mll(Z0) > 12 GeV`. The executable Run-3
reproduction applies the explicit selected-four-lepton requirement requested
for this study: `minSelectedPairMass > 12 GeV`, where the minimum is taken over
all six unordered pairs formed from exactly the selected `Z0_idx + X_idx`
leptons. Invalid, duplicate, non-finite, or nonphysical selected inputs return
a failing sentinel. This requirement is used only in the physical ZZCR/SR
common selection and is not applied to DY.

## ZZ control region — Section 7.4 and Table 39

- X flavor condition: same flavor (`X_isSF`), so the selected X pair forms the
  second-Z candidate described in Section 7.4.
- X-mass window: `75 < X_mass < 105 GeV`.
- MET threshold: `PuppiMET_pt < 35 GeV`.
- Z window and the Table 37 preselection remain active.

The XSF upper edge remains `65 GeV` because Table 37 in the explicitly
authoritative AN2019/238 v9 states `10 GeV < mX < 65 GeV`. No selection was
changed to follow a later public source with a different edge.
