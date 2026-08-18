# Per-run luminosity propagation in the DY stability plot

This document specifies how `plot_run_stability.py` converts each era-level
prompt-MC template into the denominator for one run-number point. It applies
to both the individual-run observable plot and the multi-era Data/MC
ratio-versus-run plot.

## Inputs and normalization boundary

The merged ordinary MC histogram for process `p` and analysis era `e`,
`H[p,e](y)`, has already been filled with the standard configuration weight.
That weight already contains the era-configured luminosity. The exact value is
serialized as `RUN_STABILITY_CONTRACT["mc_source_lumi_fb"]` and copied into
the merged ROOT file as:

```text
run_stability/metadata/mc_source_lumi_fb
```

This value is called `L_source[e]` below. The plotting code verifies that the
compiled-config and ROOT values agree and that `L_source[e]` is positive. It
does not multiply the MC by the full era luminosity a second time.

The DATA run histogram and the compiled recorded-luminosity definitions are
stored independently:

```text
run_stability/<category>/<observable>/histo_DATA
run_stability/metadata/<source>_recorded_lumi_fb
```

The tool checks the complete ordered run labels and every luminosity value
against the exact compiled contract before calculating a ratio. It never
substitutes one luminosity definition for another.

## DATA-membership provenance gate

Numerical propagation is valid only if the DATA histogram and luminosity
denominator were built from the same complete dataset contract. Require the
luminosity dataset-inventory manifest's `year_config` to name the live
RunStability `year_config.json`, and require `year_config.sha256` to match its
current bytes. Rebuild the dataset run/lumisection inventory, luminosity
tables, validation report, and provenance after any primary-dataset, run-tag,
logical-stream, or trigger-weight change. Internal result hashes do not make a
manifest from another or older configuration applicable.

Reconcile that live configuration against the matching processor sample
catalog, an aligned external analysis configuration, the materialized HWWNano
components/files, and the exact compiled pickle. The compiled campaign must
contain every component and file in the reconciled expected set. A missing
configured, reference, processor-catalogued, or materialized member invalidates
both DATA completeness and any luminosity-scaled ratio; do not submit or plot
around it.

Run2022 requires a sample-specific primary-dataset transition. The Muon logical
stream owns both `SingleMuon_Run2022C-ReReco-v1` and
`Muon_Run2022C-ReReco-v1`, while Run2022D owns `Muon` but not `SingleMuon`.
Their trigger expressions remain sample-specific: `SingleMuon` uses
`!Trigger_ElMu && Trigger_sngMu`, while `Muon` uses
`!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)`. The historical
six-component inventory omitted the Run2022C `SingleMuon` component. Its
early-run luminosity and ratio products are therefore stale for the corrected
seven-component DATA population.

## Source registry and category routing

The compiler materializes all 14 source keys below from the hash-validated
nominal, trigger-combination, and concrete-HLT-path tables:

| Source key | Lumi table scope | Automatically routed categories |
| --- | --- | --- |
| `nominal` | `certified_configured_input` | no category default; explicit diagnostic override only |
| `trigger_any` | `Trigger_Any` | ordinary DY reference, flavor, stream, and their enriched mirrors |
| `trigger_elmu` | `Trigger_ElMu` | `DY_TRGFAM_ELMU` and its enriched mirror |
| `trigger_sngmu` | `Trigger_sngMu` | `DY_TRGFAM_SINGLEMU` and its enriched mirror |
| `trigger_dblmu` | `Trigger_dblMu` | `DY_TRGFAM_DOUBLEMU` and its enriched mirror |
| `trigger_sngel` | `Trigger_sngEl` | `DY_TRGFAM_SINGLEEL` and its enriched mirror |
| `trigger_dblel` | `Trigger_dblEl` | `DY_TRGFAM_DOUBLEEL` and its enriched mirror |
| `hlt_mu23_ele12` | `HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL` | `DY_HLT_MU23_ELE12` and its enriched mirror |
| `hlt_mu12_ele23` | `HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ` | `DY_HLT_MU12_ELE23` and its enriched mirror |
| `hlt_mu8_ele23` | `HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ` | `DY_HLT_MU8_ELE23` and its enriched mirror |
| `hlt_mu17_mu8` | `HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8` | `DY_HLT_MU17_MU8` and its enriched mirror |
| `hlt_isomu24` | `HLT_IsoMu24` | `DY_HLT_ISOMU24` and its enriched mirror |
| `hlt_ele23_ele12` | `HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL` | `DY_HLT_ELE23_ELE12` and its enriched mirror |
| `hlt_ele30` | `HLT_Ele30_WPTight_Gsf` | `DY_HLT_ELE30` and its enriched mirror |

Use `--luminosity-source auto` for ordinary production plots. `auto` resolves
the category's compiled source and, for a multi-era ratio, requires the same
source key in every exact pickle. An explicit key from the table is permitted
for a diagnostic override; the override is not an alternative fallback and
changes the output stem and receipt.

`Trigger_Any`, family unions, and concrete-path exposures are positive
recorded-luminosity objects. The logical-NOT terms in the DATA primary-stream
priority are event de-duplication rules and never define an exclusive
luminosity by subtraction.

## Per-run MC scale

For run `r` in era `e` and selected luminosity source `s`, the scale factor is

```text
s[e,r] = L_recorded[s,e,r] / L_source[e].
```

For observable bin `k`, the process yield and its MC statistical variance are

```text
M[p,e,r,k] = s[e,r] * H[p,e,k]
V[p,e,r,k] = s[e,r]^2 * Sumw2[p,e,k].
```

Any configured per-process plotting scale is applied before the processes are
summed. The prompt-MC total is therefore

```text
M[e,r,k] = sum_p M[p,e,r,k]
V[e,r,k] = sum_p V[p,e,r,k],
```

where the variance sum assumes statistically independent process samples.
For the Z-mass stability point, the code then sums all visible Z-mass bins:

```text
M[e,r] = sum_k M[e,r,k]
V[e,r] = sum_k V[e,r,k].
```

The corresponding DATA count `D[e,r]` is the visible-y-axis integral of the
DATA run-resolved TH2 row. DATA must be an unweighted nonnegative integer
count with `Sumw2 = D`; otherwise the plot fails rather than assigning a
Poisson interpretation to weighted DATA.

## Ratio and point uncertainty

The plotted central value is

```text
R[e,r] = D[e,r] / M[e,r].
```

DATA uses the central 68.2689492137% Garwood Poisson interval
`[D_low, D_high]`. The independently propagated MC statistical term is

```text
delta_MC = D[e,r] * sqrt(V[e,r]) / M[e,r]^2.
```

The asymmetric point errors are

```text
delta_low  = sqrt(((D - D_low)  / M)^2 + delta_MC^2)
delta_high = sqrt(((D_high - D) / M)^2 + delta_MC^2).
```

The asymmetric `TGraphAsymmErrors` in the output ROOT file and the CSV
`ratio_error_low`/`ratio_error_high` columns retain these values. Restricting
the rendered y-axis to `0.5 <= Data/MC <= 1.5` does not truncate the stored
ratio or uncertainty. Directional triangles mark central values outside that
display interval.

## Correlation from reusing one era template

Every run in an era reuses the same finite era-level MC histogram. The MC
statistical component is therefore correlated between run points in the same
era. For runs `r` and `q` in era `e`, the stored MC-only ratio covariance is

```text
Cov_MC(R[e,r], R[e,q])
  = R[e,r] * R[e,q] * V_source[e] / M_source[e]^2.
```

Here `M_source[e]` and `V_source[e]` are the visible era-template prompt-MC
yield and Sumw2 before the per-run luminosity scale. The luminosity factors
cancel in the relative MC variance. MC templates from distinct eras are
treated as independent, so their cross-era covariance is zero.

The symmetric total covariance adds the Poisson approximation for DATA only
on the diagonal:

```text
Cov_total[r,r] = Cov_MC[r,r] + D[r] / M[r]^2.
```

The ROOT product retains both matrices as
`ratio_covariance_mcstat` and `ratio_covariance_total_symmetric`. The
asymmetric Garwood graph remains the authoritative visual point-uncertainty
representation.

## Zero and invalid denominators

- If `L_recorded[s,e,r]` is zero, the per-run MC denominator is zero and the
  ratio is recorded as invalid with reason `zero_luminosity`. No alternate
  luminosity source is substituted.
- A zero concrete-path exposure does not by itself imply that the run or DATA
  is missing. It is interpretable only after the owning primary-dataset
  coverage passes the provenance gate above. The historical 2022 product's
  early double- and single-muon zero exposures were computed without
  `SingleMuon_Run2022C-ReReco-v1`; do not report them as physical path
  inactivity or reuse them for the corrected campaign.
- If an era/category has a nonpositive total prompt-MC source yield, the
  complete plot stem fails before any partial output is written.
- Missing processes, luminosity metadata, run labels, or auxiliary DATA paths
  also fail validation before plotting.

## Interpretation

This procedure assumes that the prompt-MC shape and composition within an era
do not vary by run; only the exposure is changed. It is appropriate for the
requested stability comparison, where MC remains era-inclusive. It does not
model run-dependent detector conditions or regenerate MC for individual
runs. Such effects would require a different source-template contract.

The trigger-family and concrete-path categories are direct positive event
projections:

```text
family category = positive Trigger_* family
path category   = concrete HLT branch
```

The luminosity audit associates MuonEG with the three electron-muon paths, the
Muon logical stream (`SingleMuon` or `Muon`, according to the sample-specific
run contract) with the double- and single-muon paths, and EGamma with the
double- and single-electron paths. DATA primary-dataset copies are already
de-duplicated by per-component sample weights before the category cut. Several
paths can fire in the same event, so path categories remain overlapping diagnostics.
Their matching luminosity is the positive path exposure from the owning
primary-dataset coverage, not an exclusive-stream exposure.

If a DATA primary-dataset component is missing while the MC template is scaled
to a positive exposure supplied by the remaining trigger union, DATA loses the
component's selected events but MC does not acquire a corresponding reduction.
The resulting Data/MC ratio is biased low. This is the failure observed for
the historical early-2022 inclusive and especially muon-channel ratios after
the Run2022C `SingleMuon` omission removed single-muon-accepted events; it is
not caused by adaptive run-label selection.

The MC histogram used in every DY category retains the standard selected-Z
weight, including `TriggerSF_Z`. That correction describes the selected-Z
aggregate trigger algebra. This leaf does not implement or validate an
individual-HLT-path scale factor, and choosing an `hlt_*` luminosity source
does not turn `TriggerSF_Z` into one. Consequently, a concrete-path Data/MC
ratio is a stability diagnostic of the positive HLT selection plus the existing
aggregate correction. It must not be reported as a measurement or validation
of a path-specific trigger scale factor.

Each JSON plot receipt records the exact config/input identities, selected
luminosity source, renderer/style provenance, display range, out-of-range
run inventory, invalid runs, and output hashes. The CSV and ROOT files retain
the complete numerical result independently of presentation choices.
