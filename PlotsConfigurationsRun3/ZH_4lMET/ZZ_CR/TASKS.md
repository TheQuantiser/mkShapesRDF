# ZH_4lMET ZZ CR setup tasks

1. Wire the correct Run 3 production tags and base directory in `samples.py`.
2. Replace placeholder weights (`XSWeight*SFweight`) with the official ZZ and data weights.
3. Confirm the b-tagging loose working point for the target era and update `btag_WP_loose`.
4. Validate the lepton ordering or implement a robust Z0/X pairing algorithm in `aliases.py`.
5. Run `mkShapesRDF -c 1` and validate the compiled config.
6. Produce histograms for ZZ and data to check the expected ZZ-dominant purity.
