# FNAL compact-production refactor: pre-edit audit

Recorded 2026-08-09 before source edits.

- Branch: `ZH_devel`
- Starting commit: `b7d701b6bb7dbd2fd899cc53ba54c1bcbeeba7f6`
- `origin/master`: `3d98fb4b5a01c576f9884c7b7a2f2f28a003e77c`
- Starting worktree: clean
- `ANALYSIS_PASS=ALL` parent cuts: 4
- Final categories: 46 (`inclusive_z_dy`: 8, `four_lepton_base`: 16,
  `zz_control_region`: 16, `signal_region`: 6)
- Active histogram variables with `HISTOGRAM_DETAIL=all`: 509
- Rectangular cut/category x variable actions: 23,414

The starting configuration already has the two mechanisms that should be
preserved: a single nominal `ANALYSIS_PASS=ALL` and a configuration-local
runner that redefines `weight` independently below each final cut.  Its main
remaining problems are the stream x Z-flavor x X-flavor category product,
the all-variable default, rectangular histogram booking, and the absence of a
durable generated analysis contract.

Planned design changes:

1. Materialize clean `DY`, `ZZCR`, and `SR` categories from one declarative
   category registry, with bounded `minimal`, `flavor`, `stream`, `trigger`,
   and `debug` profiles and no implicit Cartesian products.
2. Retain every supported histogram definition and binning in an immutable
   registry, then resolve compact per-region activation from histogram
   profiles and exact include/exclude overrides.
3. Extend `zz_cr_runner.py` locally so it books and saves only approved
   category-variable pairs while retaining variations and independent
   category weights.
4. Generate a hashed `analysis_contract.json` from the same runtime
   dictionaries used by the executable configuration, and add an inspection
   command with fail-closed category/action budgets.
5. Make CERN xrdcp stage-in and FNAL EOS stage-out the explicit packaged FNAL
   default, then validate the local and bounded Condor paths.
