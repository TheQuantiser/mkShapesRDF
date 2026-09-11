---
name: develop-zh4l
description: Develop or review ZH4l common object, candidate, selection, correction, weight, histogram, and tree tools and their configuration leaves. Use for ZH4l design implementation and compatibility validation.
---

# Develop ZH4l

Read [ARCHITECTURE.md](../../ARCHITECTURE.md) for the supported API/ownership,
[NAMING.md](../../NAMING.md) for current names, and
[DESIGN_PROPOSAL.md](../../DESIGN_PROPOSAL.md) for the original design intent. Verify each
claimed implementation in source/tests; a proposal or historical migration
report does not establish a currently executed workflow. Apply the workspace
inspection/change/validation skills first.

Keep shared tools in `common/`. Leaves remain independent and never import
one another. `ZH_4lMET` remains the production compatibility authority until an
explicit cutover; do not mirror development edits into it.

## Object and correction decisions

- Use lowercase snake_case for ZH4l columns, with object/domain before the
  property, `sf_` for correction factors, `weight_` for composed recipes, and
  `zh4l_internal_` for implementation columns. Preserve retained branch/WP,
  official sample/nuisance and established region identifiers. Migrate
  dynamically assembled names, colon-separated histogram axes, tree fields,
  plot/summary consumers and comparison adapters together. Preserve C++ member
  names and historical evidence; do not install duplicate old/new aliases.
- Distinguish the retained source collection, its kinematic representation,
  an eligible view, a selected candidate, and a final region. Preserve original
  indices through sorting, filtering, union and complement operations.
- Every generic source field must share its declared index namespace. Map
  native Jet tag/flavor fields through CleanJet_jetIdx before selecting or
  sorting a CleanJet view. Test a nontrivial permutation and a removed native
  jet; identity maps cannot detect this mistake.
- Physical source identity survives a change in view name or kinematic
  representation. Declare shared index identity explicitly when adapting the
  same collection twice; do not evade duplicate-component checks by renaming.
- Z-first/X-from-the-complement and quartet-first/pairing-within-the-quartet
  are different policies when extra leptons exist. Preserve their separate
  eligibility, ranking, tie and final-cut decisions.
- Z and X can use distinct WPs. Fail on a requested unavailable WP rather
  than substituting another. A stored total SF cannot be decomposed into
  ID/isolation/reconstruction pieces without matching retained components.
- Bind lepton corrections to exact members/WPs and trigger corrections to the
  selected trigger domain/algebra. Multiplying independent Z and X trigger
  SFs does not create the correction for their union. Bind b-veto correction
  acceptance to its exact jet view, tagger/WP and decision.
- Resolve DATA/MC applicability from sample metadata, not from the numerical
  value of `genWeight`. Inapplicable unit factors and invalid MC corrections
  have different meanings.
- Inherit region weights explicitly. Category-name prefixes are not a stable
  representation of correction scope. Test flavor children against their
  parent, especially veto factors, and keep N-minus-one selection separate
  from correction removal.

## Outputs and execution

Histogram and tree projections must consume the same definitions. Support
compact branch groups with explicit field additions/removals; retain source
indices, validity, and the actual exported weight recipe. A Z-only request
must not pull in X, b-tag payloads, or truth by constructing unused aliases.

Trace the selected runner. Native snapshots exist, but historical/current
study runners can disable them. Sparse weights, raw counts and trees require
checking the native nonzero-weight prefilter, branch/path collisions and
chunk assembly. Keep event rows with vectors distinct from explicitly
flattened candidate rows. Compare trees by identity, not output order.

Nominal-only tools keep the native nuisance field and explicit extension
points. Preserve the established ZZCR nuisance route; do not silently accept
unsupported variations or promise that a nominal skim contains events that
would migrate under shifted kinematics.

Use the owning tests and bounded inputs from the leaf documentation. Check
real source/selection compatibility before claiming physics equivalence.
Small synthetic ROOT inputs can test row identity, normalization algebra,
sparse booking and histogram/tree agreement, but cannot establish physical
performance. Confirm common modules are importable after runtime relocation.
Keep findings in source, tests and concise owning documentation; no new
reporting subsystem is required.

For a complete small toolkit example, use [Example](../../Example/README.md).
It pins real inputs and checks histogram/tree agreement, source mappings and
normalization. Its different Z/X WPs are intentional, not a compatibility
claim for ZZCR. Typed histogram bookings may inherit different region totals
through `regionWeights`; never turn these into multiplicative factors.

Keep snapshot scratch until native `run()` has released its result graphs and
file handles. Removing it during `saveResults()` can leave open `.nfs` files
on shared storage even when the same test passes under `/tmp`. Validate this
lifecycle on the actual output filesystem. For native plotting, inspect the
compiled `plotPath`: the current CLI does not pass `--outputDirPlots` to its
final plotting call.
