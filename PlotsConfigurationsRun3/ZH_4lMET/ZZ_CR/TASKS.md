# ZH_4lMET ZZ CR setup tasks

- [x] Wire the Run-3 2024v15 production tags and base directory in `samples.py`.
- [x] Replace placeholder MC/data setup with active 2024 dataset streams and trigger partitioning.
- [x] Add active `groupPlot` / `plot` entries for enabled samples.
- [x] Keep `structure.py` synchronized with active sample keys.
- [x] Add minimal 2024 nuisance model (`lumi_2024`, auto MC stat).
- [ ] Confirm the final object/analysis weight expression with analysis conveners.
- [ ] Confirm the b-tagging loose working point for the target era and update `bVeto`/WP if needed.
- [ ] Run `mkShapesRDF -c 1` and validate yields/plots on EOS inputs.
- [ ] Validate ZZ CR purity and kinematic shapes vs expectations.
