# ZH(H→WW) → 4ℓ + MET ZZ control region

This configuration implements the ZZ control region definition from AN2019_238_v9,
aligned to the 2024 Run-3 (`2024_v15`) production conventions used in
`PlotsConfigurationsRun3` control-region setups.

## Dataset / normalization conventions

- MC production: `Summer24_150x_nAODv15_Full2024v15`
- Data production: `Run2024_ReRecoCDE_PromptFGHI_nAODv15_Full2024v15`
- Data streams: `MuonEG`, `Muon0`, `Muon1`, `EGamma0`, `EGamma1`
- Integrated luminosity: `109.08 fb^{-1}`

## ZZ CR definition

Preselection:
- 4 leptons with pT thresholds 25/15/10/10 GeV
- 5th lepton veto at 10 GeV
- Z0 mass > 12 GeV
- b-jet veto (DeepJet loose, update WP as needed)
- sum of lepton charges = 0

ZZ CR selection:
- |m(Z0) − mZ| < 15 GeV
- 75 < m(X) < 105 GeV
- PuppiMET pT < 35 GeV

Categories:
- XSF: X dilepton is same-flavor
- XDF: X dilepton is different-flavor

## Notes
- The Z0/X pairing follows the AN rule: choose the OSSF pair closest to mZ and
  assign the remaining two leptons to X.
- `WZ`, `DY`, and `top` are enabled as sub-leading backgrounds for closure checks.
