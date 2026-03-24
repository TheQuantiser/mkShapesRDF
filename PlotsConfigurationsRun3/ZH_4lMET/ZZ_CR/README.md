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

## Optional EOS-user output with x509 on Condor

This configuration now supports an **optional** mode to write per-job `output.root`
files directly to EOS user space from Condor jobs.

- Default behavior is unchanged: local output folder under the configuration path.
- To enable EOS output, set `useEOSUserOutput = True` in `configuration.py`.
- To enable x509-aware Condor submission, set `useX509Proxy = True` in
  `configuration.py`.
- The default EOS destination for this mode is under:
  `/eos/cms/store/user/<user>/mkShapesRDF_rootfiles/<tag>/rootFile/`.
- The submission workflow automatically discovers the active proxy path via
  `voms-proxy-info -path` and stages it for Condor transfer.
- Before submitting jobs, it also creates the EOS destination directory via
  `xrdfs` and uses `xrdcp` with the proper xrootd namespace path.
- If EOS output is requested but no valid proxy is available (at least 1 hour),
  submission stops and asks you to run:

  ```bash
  voms-proxy-init --voms cms -valid 192:0
  ```
