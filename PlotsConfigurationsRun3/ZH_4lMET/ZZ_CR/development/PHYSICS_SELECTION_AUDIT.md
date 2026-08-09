# Physics-selection audit

Sources reviewed: AN2019/238 v9, section 7 and Tables 37--39, and the
four-lepton-related material in AN2019/125 v11.

The active implementation correctly constructs an OSSF `Z0` closest to the Z
mass, constructs `X` from the remaining selected leptons, requires four
distinct selected indices, zero four-lepton charge, a fifth-lepton veto at
10 GeV, the configured ordered lepton thresholds (25, 15, 10, 10 GeV),
`m(Z0)>12 GeV`, a 15 GeV Z window, and a loose fixed-WP b veto for jets above
20 GeV.  The signal-reference definitions match Table 37: XSF has
`10<m(X)<65 GeV`, MET above 35 GeV and `m4l>140 GeV`; XDF has
`10<m(X)<70 GeV` and MET above 20 GeV.

One discrepancy was found in the old ZZ-control expression:

```text
old: PHYSICAL_COMMON && 75 < X_mass < 105 && PuppiMET_pt < 35
new: PHYSICAL_COMMON && X_isSF && 75 < X_mass < 105 && PuppiMET_pt < 35
```

AN2019/238 section 7.4 calls X the “second Z” and Table 39 specifies its
75--105 GeV mass window.  A physical Z decay is same-flavor, so XDF is not a
physical ZZ-control category.  The refactor therefore makes `X_isSF`
explicit and offers only `4E`, `4MU`, and `2E2MU` flavor refinements for ZZCR.
No other physics selection is changed by the category refactor.
