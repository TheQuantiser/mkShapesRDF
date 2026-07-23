# Tag-Named Output Directories

ZZ_CR output defaults now use the full runtime `tag` as the final output
directory name instead of the old `rootFile` or `rootFiles` leaf.

- Local outputs now go to `jobs/<tag>/<tag>/{root files}`.
- Default test-remote outputs go to
  `/store/user/<user>/mkShapesRDF_rootfiles/<tag>/{root files}`.
- Production remote outputs keep the campaign/site component and add the tag
  leaf: `/store/user/<user>/mkShapesRDF_rootfiles/<campaign>/<tag>/{root files}`.
- The LXPLUS and FNAL preset scripts now set `ZZCR_PRODUCTION_CAMPAIGN` instead
  of forcing a complete `ZZCR_PRODUCTION_OUTPUT_LFN` ending in `rootFile`.
- Exact overrides through `ZZCR_TEST_OUTPUT_LFN`, `ZZCR_PRODUCTION_OUTPUT_LFN`,
  or `mkShapesRDF --output-folder` still take precedence.

The hadd/postprocessing flow consumes `outputFolder`, so split job outputs, the
merged ROOT file, and nuisance postprocessing all target the same tag-named
directory for the selected output mode.
