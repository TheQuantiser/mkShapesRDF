# Luminosity propagation and statistical definitions

This document defines how the DY RunStability leaf projects one
era-inclusive MC template to a physical run or period. It distinguishes the
MC source normalization from the category-effective DATA exposure; confusing
those quantities biases Data/MC ratios.

## Provenance and compile-time binding

The canonical `dy` profile names the active receipt:

```text
lumi/run_stability_luminosity_binding.json
```

That receipt has kind `run_stability_luminosity_binding` and binds the live
year-config path, whole-file hash, semantic projection hash, immutable
source-audit path, manifest hash, provenance hash, and nominal-era-result hash.
The source audit itself remains:

```text
lumi/audits/ZZ_CR_RunStability_BCD_afa86d85_conjunction_20260818T200415Z/
```

The legacy-looking identifier is immutable historical evidence, not the
current leaf name or active binding identity. With `RUN_STABILITY_LUMI_DIR`
unset, compilation validates the binding before consuming this bundle. An
explicit absolute results directory is permitted only as a validated override;
the default binding comparison is then recorded as not applied, while all
audit and numerical checks still run.

The audit manifest SHA-256 must match its copied `inputs/year_config.json`.
The copied and live configurations must then have identical canonical
BRIL-input projections. That projection includes:

- each DATA dataset, run tag, logical stream, and component trigger rule;
- `data_stream_triggers`;
- the era's processing identifier;
- the configured concrete HLT paths.

It excludes `lumi_fb`, because nominal recorded luminosity is a BRIL result,
not a query input. Every live `lumi_fb` is bound separately by exact equality
to the corresponding validated `luminosity_by_analysis_era.csv` result. The
selected runtime `lumi` must equal that configured/audited value exactly.
Default mode additionally requires the live whole-file and projection hashes
to match the active binding receipt. A projected-input change requires a new
audit; a nonprojected live-file change requires a refreshed binding receipt.

## MC source luminosity

The ordinary MC TH1 is already normalized to the full-precision nominal
recorded luminosity in `year_config.json`:

| Era | `L_MC` [fb^-1] |
| --- | ---: |
| 2022 | 8.076828657919002 |
| 2022EE | 26.671325997159986 |
| 2023 | 18.062658998219003 |
| 2023BPix | 9.693130030386998 |
| 2024 | 109.72830897472497 |

These are source normalizations, not necessarily the exposure of a trigger
category. They are stored in the compiled contract and in the one-bin ROOT
metadata object `mc_source_lumi_fb`.

## Trigger-effective sources

The recommended plotting option is `--luminosity-source auto`. Its compiled
category map selects:

- positive Trigger-OR exposure for inclusive, flavor, and stream categories;
- the corresponding family exposure for a trigger-family category;
- the corresponding concrete-path exposure for an HLT category;
- the same parent source for a selected-Z-flavor child.

For DATA component `c`, run `r`, and category trigger `T`, the effective
lumisections satisfy all of:

```text
Golden JSON
AND dataset/lumisection coverage for c
AND the component's baseline/de-duplication trigger
AND T
```

The category source is the positive union over the configured components
after stream de-duplication. In particular, a `SingleMuon` contribution to a
double-muon category requires `Trigger_sngMu AND Trigger_dblMu`; applying only
the requested double-muon path over the dataset mask is not equivalent.

Zero exposure is meaningful and remains zero. It is never replaced with
nominal luminosity or another trigger source. Nominal DATA coverage, positive
Trigger-OR exposure, family exposure, and concrete-path exposure must remain
separate quantities.

## Run and period projection

Let `H[p,e,k]` be the ordinary MC bin content for process `p`, era `e`, and
observable bin `k`, already normalized to `L_MC[e]`. Let
`W2[p,e,k]` be its `Sumw2`. For a run `r` and the source selected for category
`c`, define

```text
s[e,r,c] = L_eff[e,r,c] / L_MC[e]
M[p,e,r,c,k] = s[e,r,c] * H[p,e,k]
V[p,e,r,c,k] = s[e,r,c]^2 * W2[p,e,k].
```

For a physical period `P`, replace `L_eff[e,r,c]` by the exact sum over runs
mapped to that period. The era luminosity is not multiplied a second time.

Compiled presentation scales are applied process by process before grouping:

```text
H'[p,k] = a[p] * H[p,k]
V'[p,k] = a[p]^2 * V[p,k].
```

Independent process variances are then summed. Period plots obtain the `DY`
group from exact compiled `groupPlot` membership and call the disjoint
complement `Others`; substring classification is not allowed.

## Data/MC ratios and uncertainties

For DATA count `D` and scaled total MC `M`, the central ratio is

```text
R = D / M.
```

DATA must be a finite, nonnegative integer-like count with `Sumw2 = D`.
The point's asymmetric error is the central 68.2689492137% Garwood Poisson
interval for `D`, divided by `M`. MC uncertainty is not propagated into the
DATA point.

The MC uncertainty is shown separately around unity:

```text
sigma_MC / M = sqrt(V_MC) / M.
```

Because all runs in an era reuse the same finite-MC template, their MC ratio
uncertainties are correlated. The serialized MC covariance is

```text
Cov_MC(R_i,R_j) = R_i * R_j * V_MC / M_MC^2
```

for runs `i` and `j` in the same era and zero between eras. The serialized
symmetric total covariance adds `D_i / M_i^2` to each diagonal. This covariance
is diagnostic metadata; the displayed DATA bars remain Garwood-only.

Nonpositive luminosity or total MC makes the ratio undefined. Numerical
outputs retain invalid entries explicitly. Presentation-only adaptive ranges
use boundary markers for clipped values; they never modify the stored central
values or uncertainties.

## Reduced chi-square by run

For each visible observable bin, the diagnostic uses the same run-projected MC
content and variance. The symmetric DATA scale is half the central Garwood
interval width:

```text
sigma_D,k = (Garwood_high - Garwood_low) / 2
q_k = (D_k - M_k)^2 / (sigma_D,k^2 + V_MC,k).
```

The per-run result is

```text
chi2_red = (sum over valid visible bins q_k) / ndf,
ndf = number of contributing bins.
```

No parameter is fitted. Bins with nonfinite inputs, negative MC variance, or
nonpositive total variance are excluded and recorded. The plot shows no point
error bars; it shows a horizontal reference at one and the approximate
`1 +/- sqrt(2/ndf)` expectation band. Display clipping is marked explicitly.

This is an interval-based Pearson-style stability diagnostic, not a likelihood
fit. The available histograms do not encode the full bin/process covariance,
and shared era MC makes run points correlated. Interpret large or small values
as diagnostics, not as calibrated independent p-values.

## Manual reproduction

Validate the pinned historical inputs before generating a plot:

```bash
cd PlotsConfigurationsRun3/ZH_4lMET/RunStability
python reproduce_plots.py validate
python reproduce_plots.py ratio-vs-run \
  --category DY_ALL --observable Z0_mass \
  --output-dir /absolute/new/ratio --execute
```

The wrapper always selects `--luminosity-source auto`. It verifies exact
pickle and merged-ROOT hashes and confines inputs to the leaf. See
[USAGE.MD](USAGE.MD) for chi-square and period examples and
[lumi/README.md](lumi/README.md) for audit regeneration.
