# Physics-selection audit

Sources reviewed: AN2019/238 v9, Section 7 and Tables 37--39, and the
four-lepton-related material in AN2019/125 v11. Exact PDF/document page
references and the distinction between the rendered AN row and the current
Run-3 implementation are recorded in `SELECTION_SOURCE_NOTE.md`.

## Current implementation

The selection constructs an OSSF `Z0` closest to the Z mass and constructs
`X` from the remaining selected leptons. It requires four distinct selected
indices, zero four-lepton charge, a fifth-lepton veto at 10 GeV, ordered
selected-lepton thresholds of 25, 15, 10, and 10 GeV, a 15 GeV Z window, and
the era-specific loose fixed-WP b veto for jets above 20 GeV.

The physical ZZCR/SR common selection requires
`minSelectedPairMass > 12 GeV`. The minimum is computed over all six unordered
pairs made from exactly `Z0_idx[0:2] + X_idx[0:2]`; invalid, duplicate,
non-finite, or nonphysical selected inputs return a negative sentinel and fail
closed. DY does not require a valid X pair and deliberately does not apply
this four-lepton minimum-mass veto.

Table 37 renders its low-mass row as `mll(Z0) > 12 GeV`. The six-pair
requirement is therefore an explicit Run-3 study choice, not a claim that the
AN text contains that exact expression. The independent Z window remains
active after the minimum-pair veto.

The signal-reference definitions match Table 37: XSF has
`10 < X_mass < 65 GeV`, MET above 35 GeV, and `m4l > 140 GeV`; XDF has
`10 < X_mass < 70 GeV`, MET above 20 GeV, and no m4l threshold. The XSF upper
edge remains 65 GeV.

## ZZ-control correction retained from the category refactor

The earlier audit found that the old ZZ-control expression did not explicitly
require the second pair to be same flavor:

```text
old: PHYSICAL_COMMON && 75 < X_mass < 105 && PuppiMET_pt < 35
new: PHYSICAL_COMMON && X_isSF && 75 < X_mass < 105 && PuppiMET_pt < 35
```

AN2019/238 Section 7.4 calls X the second Z and Table 39 specifies its
75--105 GeV mass window. The current expression therefore retains `X_isSF`
and offers only `4E`, `4MU`, and `2E2MU` flavor refinements for ZZCR.

The later six-pair veto is the only subsequent physics-selection change
relative to that category-refinement audit. Sample profiles affect process
activation only and do not alter any event selection.

## Enriched DY projection

`DY_ENRICHED` and every `DY_ENRICHED_*` subcategory apply
`abs(Z0_mass - 91.1876) < 15` on top of their corresponding ordinary DY view.
They intentionally remain children of the DY parent: they do not require a
valid X pair and do not inherit `minSelectedPairMass > 12 GeV`, the b veto, or
the ZZCR/SR X-mass and MET requirements. The Enriched DY hierarchy is an
overlapping Z-window projection for direct comparison with the physical
four-lepton regions, not a fourth physics region.
