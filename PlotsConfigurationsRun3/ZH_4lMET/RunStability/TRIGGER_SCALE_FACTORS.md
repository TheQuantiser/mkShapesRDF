# Selected-Z trigger scale factor

RunStability applies the canonical mkShapesRDF TrigMaker calculation to
exactly the two leptons selected as `Z0_idx`. The generic all-lepton result and
stored leading-lepton branches are diagnostics, not nominal weights. This
leaf is DY-only; no four-lepton ZZCR or SR trigger-weight contract is public.

## Ownership and implementation

| File | Responsibility |
| --- | --- |
| `year_config.json` | Owns the era's canonical `l2tight_era` and physical HLT path strings |
| `run_stability_profiles.json` | Owns trigger aggregate joins, stable category IDs/labels/luminosity sources, and TrigMaker-family names |
| `selection_config.py` | Validates TrigMaker DATA/MC paths and joins each profile aggregate/ordinal to one year-owned path |
| `selected_trigger_adapter.py` | Declares canonical TrigMaker payload readers and C++ functions for that era |
| `macros/run_stability_helpers.cc` | Aligns pre-smearing production pT and PDG ID with final selected-lepton indices and supplies local DY helpers |
| `macros/selected_trigger_wrappers.cc` | Validates, compacts, sorts, and evaluates the selected pair |
| `aliases.py` | Publishes the selected-pair trigger result and `TriggerSF_Z` |
| `samples.py` | Applies the selected-lepton and trigger corrections once to MC |

The local wrapper reuses the canonical TrigMaker payload and algebra; it does
not copy the era payload. Physical HLT strings occur only in the year JSON.
The profile contains no repeated path string: each concrete category joins an
aggregate and ordinal to the year-owned ordered list, with exact-once coverage.

## Selected-pair calculation

TrigMaker runs before lepton scale smearing, so the final `Lepton` order may
differ from the source order. The aliases first construct production-aligned
pT and PDG-ID vectors in final-index order. The selected-pair wrapper then:

1. requires exactly two usable `Z0_idx` entries;
2. rejects negative, out-of-range, duplicate, nonfinite, or unsupported-flavor
   inputs;
3. compacts only those two leptons;
4. sorts them by production-aligned pT while applying the same permutation to
   eta, phi, and PDG ID;
5. evaluates the canonical single/double leg, DZ, global, and angular terms;
6. exposes the canonical nominal/up/down efficiency and scale-factor result.

The public nominal MC correction is `TriggerSF_Z`. If the selected inputs or
canonical result are invalid, diagnostic values remain finite and the
validity projection records the neutral fallback. DATA trigger scale factors
are one; DATA weights instead enforce the configured MET filter and exclusive
stream trigger de-duplication.

## Nominal weight placement

The RUN_STABILITY MC sample weight is the configured common MC weight times:

```text
puWeight * SelectedLeptonSF_Z * TriggerSF_Z
```

The selected trigger correction is applied exactly once. `TriggerSF_event`
and stored leading-lepton trigger weights are not nominal corrections.
`ENABLE_SYSTEMATICS=0` is part of the public RunStability contract; no
trigger-variation production is exposed here.

This event-weight correction is distinct from trigger-effective luminosity.
The MC event weight corrects simulated efficiency. The run projection uses the
certified, dataset-covered component-trigger/category-trigger conjunction as
its exposure denominator. See
[LUMINOSITY_PROPAGATION.md](LUMINOSITY_PROPAGATION.md).

## Validation

After changing selected-object alignment, TrigMaker result mapping, or weight
placement, run the focused leaf tests and a bounded real-input MC pilot:

```bash
source start.sh
python -m pytest -q \
  PlotsConfigurationsRun3/ZH_4lMET/RunStability/tests
```

Inspect the compiled sample weight, selected-pair expression, validity
projection, and produced ROOT histogram. A finite fallback or passing unit
test alone does not establish payload coverage or physics correctness.
