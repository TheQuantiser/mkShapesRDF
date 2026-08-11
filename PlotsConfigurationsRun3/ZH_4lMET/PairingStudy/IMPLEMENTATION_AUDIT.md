# ZH4l and ZZ pairing implementation audit

This note records the implementation that was inspected before the independent
pairing study was written.  The authoritative local revision is
`1a44b3143560703146039f03a1b6118e9a769243` on `ZH_devel`.  References to line
numbers below refer to that revision.

## Audited study domains

The reconstruction algorithm is shared, but the study contains two distinct
truth domains whose correctness definitions must not be conflated.

The ZH domain is resolved from the intersection of
`year_config.json:141-150` (`plot_groups["HWW_signal"]["samples"]`) with the
selected year's MC inventory.  At the audited revision this gives
`ZH_Hto2Wto2L2Nu_M125` and `GluGluZH_Hto2Wto2L2Nu_M125` in
2022--2023BPix, and the corresponding explicitly Z-to-2L names
`ZH_Zto2L_Hto2Wto2L2Nu_M125` and
`GluGluZH_Zto2L_Hto2Wto2L2Nu_M125` in 2024.  These samples contain a
physically distinguished associated Z and a Higgs-decay system, so the Z label
has truth meaning.

The ZZ domain is resolved independently from the intersection of
`year_config.json:173-178` (`plot_groups["ZZ"]["samples"]`) with the same
per-year MC inventory.  It resolves to the logical `ZZ` sample in every era
(`year_config.json:300-315`, `403-418`, `507-522`, `620-635`, and
`730-745`). In a direct four-lepton ZZ/Zgamma*/gamma*gamma* decay, the two
hard generator-record neutral-current lineages are exchange symmetric for this
reconstruction question. Truth therefore defines an **unlabeled partition
into two daughter pairs**, not a unique object called the selected Z.

## Live Run-3 `ZZ_CR` implementation

The executable aliases are wired in
`../ZZ_CR/aliases.py:231-256`.  `Z0_idx` calls
`FourLepton::bestZ0IdxWithID`; `X_idx` then calls
`FourLepton::xPairIdxWithID` with the chosen Z indices.  The arguments are the
common `Lepton` kinematics and PDG IDs, the selected electron and muon tight-WP
masks, the minimum number of tight leptons in each pair, and the pair-level
transverse-momentum thresholds.

The live configuration is resolved by `../ZZ_CR/selection_config.py:129-141`
from `../ZZ_CR/year_config.json:866-890`.  At the audited revision, all five
eras use:

- electron WP `mvaWinter22V2Iso_WP90_tthMVA_Run3`;
- muon WP `cut_TightID_pfIsoTight_HWW_tthmva_67`;
- `Z0_minPass = X_minPass = 2`;
- candidate-pair leading/subleading thresholds of `(10, 10)` GeV for both Z
  and X; and
- physical ordered-four-lepton thresholds of `(25, 15, 10, 10)` GeV.

The tight decision is flavor aware.  `leptonPassesPairWP` dispatches electrons
and muons to their respective masks, and `pairPassesIDRequirement` requires the
configured number of passing objects (`../ZZ_CR/macros/four_lepton_helpers.cc:
831-864`).  `pairPassesPtRequirement` first orders a pair by transverse
momentum and applies inclusive `>=` candidate thresholds
(`four_lepton_helpers.cc:866-888`).

### Current Z rule and exact tie breaking

`bestZ0IdxWithID` is implemented in
`../ZZ_CR/macros/four_lepton_helpers.cc:891-932`:

1. Let `n` be the minimum available size of `Lepton_pt`, `Lepton_eta`,
   `Lepton_phi`, and `Lepton_pdgId`.
2. Enumerate every unordered pair in increasing lexicographic index order,
   `i = 0..n-1`, `j = i+1..n-1`.
3. Require `pdgId[i] == -pdgId[j]`, which is exactly opposite-sign,
   same-flavor for the supported electrons and muons.
4. Require both objects to pass the configured tight WP and require their
   pT-ordered values to be at least 10 and 10 GeV.
5. Construct `PtEtaPhiMVector`s using electron mass 0.000511 GeV or muon mass
   0.105658 GeV (`four_lepton_helpers.cc:760-762`).
6. Minimize

   ```text
   abs(mll - 91.1876 GeV).
   ```

The best candidate is updated only for a strict improvement, `diff <
bestDiff`.  Therefore, an exactly equal score does not replace the incumbent:
the lexicographically first `(i,j)` candidate wins.  The returned pair is
pT-ordered by `orderPairByPt` (`four_lepton_helpers.cc:806-816`); an exact pT
tie preserves the earlier input index.

### Current X rule and exact tie breaking

`xPairIdxWithID` is implemented in
`../ZZ_CR/macros/four_lepton_helpers.cc:934-993`:

1. Reject a malformed Z pair.
2. Enumerate all `i<j` pairs not containing either selected Z index.
3. Require `pdgId[i] * pdgId[j] < 0`.  Thus X must be opposite sign, but it may
   be same flavor or different flavor.
4. Require both X objects to pass their flavor's configured tight WP and the
   pT-ordered inclusive 10/10 GeV candidate thresholds.
5. Maximize lexicographically

   ```text
   (leading-lepton pT, subleading-lepton pT).
   ```

The first score component is compared strictly.  At equal leading pT, only a
strictly larger subleading pT replaces the incumbent.  A complete score tie
therefore retains the lexicographically first enumerated candidate.  X is
returned in descending pT order.

## Current four-lepton and fifth-lepton contract

The executable region algebra is in `../ZZ_CR/category_config.py:36-60`.
It is important that this live route does **not** start from a pairing-agnostic
quartet:

- `DY_PARENT` already requires a valid selected Z, `Z0_mass > 30 GeV`, and
  strict selected-Z pT thresholds above 10/10 GeV.
- `FOURL_PARENT` additionally requires at least four leptons, a valid and
  distinct X, `X_mass > 4 GeV`, strict selected-X pT thresholds above 10/10
  GeV, positive `m4l`, and total selected charge zero.
- `PHYSICAL_COMMON` adds the fifth-lepton veto, the all-six-selected-pair
  minimum mass above 12 GeV, the physical b veto, the 15 GeV selected-Z
  window, and strict ordered-quartet pT thresholds above 25/15/10/10 GeV.

`fifthLeptonVeto` counts **every object in the common `Lepton` collection**
with `pt >= 10 GeV`, not only objects passing the study's tight WP, and accepts
at most four (`../ZZ_CR/macros/four_lepton_helpers.cc:613-623`; exposed at
`../ZZ_CR/aliases.py:1039-1041`).  Since a physical event also contains four
distinct selected Z+X leptons with pT strictly above 10 GeV, an accepted event
has exactly four common-`Lepton` objects at or above 10 GeV.  Additional
objects may exist only below 10 GeV.

Distinctness is checked in `fourSelectedIndicesDistinct`
(`four_lepton_helpers.cc:708-723`) and again by the ordered-four-pT helper
(`four_lepton_helpers.cc:1015-1051`).  It is defensive for the live X helper,
which already excludes both Z indices.  The selected charge is computed from
the signs of the four PDG IDs in `sumLeptonChargeFromPairs`
(`four_lepton_helpers.cc:1272-1286`).  The all-six-pair minimum is evaluated on
exactly the four selected objects and fails closed for invalid inputs
(`four_lepton_helpers.cc:764-803`).

### Why X ranking becomes the complement

Let the accepted quartet charges be `q1,...,q4`, with each `qi` equal to
`+1` or `-1`.  Total charge zero means that the quartet contains two positive
and two negative leptons.  Any eligible OS Z removes one positive and one
negative lepton.  The two remaining leptons must therefore also consist of one
positive and one negative lepton, so the complementary X is automatically OS.

After the fifth-lepton contract there are only four objects eligible for the
10 GeV pair construction.  Once Z has been chosen, exactly two eligible
objects remain.  Consequently there is exactly one X candidate: the
complement.  The `(leading pT, subleading pT)` ranking performs no choice in
events satisfying the physical contract.  It can matter only before that
contract, when more than four eligible objects are present.

## Fixed-quartet flavor topologies

All five electron/muon flavor multisets must remain in the reconstructed study.
Given total charge zero and an eligible OS-SF Z, X flavor is fixed by the
quartet topology even though the individual Z indices may be ambiguous.  Their
truth interpretation differs materially between ZH and ZZ.

| Quartet topology | Valid-Z structure and complementary X | ZH truth meaning | Direct-ZZ truth meaning |
|---|---|---|---|
| `4e` | With two charges of each sign, four OS-SF electron candidates exist; X is always `ee` and therefore XSF.  The four candidates represent two unlabeled complete pair partitions. | All four candidates can compete, but exactly the pair matched to the associated-Z daughters is label-correct.  Selecting the Higgs-system pair as Z is wrong even when the resulting unordered two-pair partition is unchanged. | A recoverable direct `ZZ -> 4e` event has two truth `ee` pairs.  Correctness is the unordered pair partition, so swapping which truth boson is called Z is not an error.  The ambiguity is between the two distinct complete OS-SF partitions. |
| `4mu` | With two charges of each sign, four OS-SF muon candidates exist; X is always `mumu` and therefore XSF.  The four candidates represent two unlabeled complete pair partitions. | The unique associated-Z daughter pair defines the correct Z label; choosing the Higgs-system pair as Z is wrong. | A recoverable direct `ZZ -> 4mu` event is evaluated by its unlabeled two-`mumu` partition.  Boson-label exchange is correct; choosing the other complete partition is not. |
| `2e2mu` | If an eligible Z exists, charge zero implies both the `ee` and `mumu` pairs are OS.  Either can be labeled Z, while the complement is the other SF pair, so X is always XSF. | The associated Z may be either `ee` or `mumu`; choosing the other flavor as Z is a genuine associated-Z label error even though the complete partition is unchanged. | There is only one flavor-compatible OS-SF complete partition, `{ee, mumu}`.  Choosing `ee` versus `mumu` as the selected Z is only a label swap and must be counted correct. |
| `3e1mu` | The eligible Z must be an OS `ee` pair; two such choices exist for a charge-balanced quartet.  The remaining OS `e mu` pair is XDF. | This is a valid XDF ZH signal topology and must not be discarded.  Associated-Z truth distinguishes the correct one of the competing `ee` candidates. | It cannot be a truth-recoverable direct `ZZ -> 4e/4mu/2e2mu` decay because one direct Z daughter pair would be different flavor.  It may appear in the reconstructed inclusive ZZ sample through non-direct decays, unmatched or replacement leptons, but not in the direct-double-Z pairing-efficiency denominator. |
| `1e3mu` | The eligible Z must be an OS `mumu` pair; two such choices exist for a charge-balanced quartet.  The remaining OS `e mu` pair is XDF. | This is a valid XDF ZH signal topology and must not be discarded.  Associated-Z truth distinguishes the correct one of the competing `mumu` candidates. | Like `3e1mu`, it is not recoverable under the direct two-Z-to-electron/muon-pairs truth definition and remains outside that ZZ truth-efficiency denominator. |

It follows that an alternative algorithm operating on the same fixed quartet
and the same OS-SF Z candidate set cannot produce an `XSF <-> XDF` migration.
That migration rate is identically zero by flavor counting.  Alternative Z
choices can still migrate selected-Z flavor in `2e2mu`, selected masses and
momenta, Z-window acceptance, and SR/ZZCR acceptance.

## Domain-specific truth correctness

### ZH: unique associated-Z label

For ZH and ggZH, identify the hard-process associated Z, excluding a Z that is
a Higgs descendant, and follow generator-copy chains before identifying its
direct prompt electron or muon daughters.  A truth-recoverable event requires
those two daughters to match one-to-one to two objects in the fixed study
quartet.  If their matched unordered reco-index set is `T_Z`, a reconstructed
candidate is correct exactly when

```text
unordered(selected Z indices) == T_Z.
```

The complement is then the reconstructed Higgs-system X pair.  This definition
is intentionally label sensitive: in an XSF event, exchanging the associated-Z
pair and the Higgs pair is a misassignment even if it leaves the same unordered
partition of four leptons.  The ZH truth oracle may therefore select a unique
candidate label whenever the associated Z is recoverable.

Generic 2022--2023BPix ZH samples need an explicit denominator category for a
direct associated `Z -> ee/mumu`; `Z -> tautau -> e/mu` must not be silently
treated as direct associated-Z truth.  The 2024 sample name encodes the forced
Z-to-2L production but the event-level ancestry and reco match must still be
validated.

### ZZ: label-invariant two-boson partition

For the ZZ sample, there is no physically privileged associated Z. A direct
truth-recoverable event instead requires two distinct hard Z/gamma*
neutral-current lineages, each with a direct prompt `ee` or `mumu` daughter
pair, and a one-to-one match of all four daughters to the fixed study quartet.
Only same-PDG lepton copy chains are accepted between the final lepton and its
boson; FSR/conversion photons and nonleptonic intermediate decays are rejected.
After following accepted copy chains and matching reco objects, define the
truth object as the unordered set of two unordered pairs,

```text
T_ZZ = { unordered(T_1), unordered(T_2) }.
```

A reconstructed candidate with selected pair `P` and complementary pair
`Pbar` is correct exactly when

```text
{ unordered(P), unordered(Pbar) } == T_ZZ.
```

This comparison is invariant under `P <-> Pbar` and under exchange of the two
truth neutral-current lineages. In particular, the two candidate labels
`Z=ee, X=mumu` and
`Z=mumu, X=ee` in `2e2mu` represent the same correct partition and must not be
double-counted as different algorithms or counted as one correct and one
wrong.  Similarly, in `4e` or `4mu`, choosing either member of the correct
truth partition as the labeled Z is correct; choosing a cross-paired partition
is wrong.

ZZ truth summaries must consequently report partition correctness and
partition-recoverable efficiency, not “associated-Z recovery.”  An oracle for
ZZ is a diagnostic ceiling over unlabeled candidate partitions.  If both
labels of one partition occur in the candidate enumeration, the implementation
may retain the nearest-mZ label deterministically for storage, but the truth
decision and event counts must be deduplicated at partition level.

## Historical Run-2 implementation

The source inspected is the official Latinos configuration at commit
`7a1b6dc4e2077365a814a6c43a550c7cf57e5a1b`:

<https://github.com/latinos/PlotsConfigurations/blob/7a1b6dc4e2077365a814a6c43a550c7cf57e5a1b/Configurations/ZH4l/nano_config/v7/l4kin_patch.cc>

The literal historical behavior is:

- Lines 71-75 construct massless four-vectors for exactly `Lepton[0..3]`.
- Lines 79-94 enumerate `i<j` inside those four, require
  `pdgId[i] + pdgId[j] == 0`, and minimize
  `abs(mll - 91.1876)` with a strict `<` update.  It therefore uses the same
  first-encounter tie convention as the live nearest-mZ rule.
- Lines 106-112 assign the two indices not used by Z directly to X; there is
  no X ranking.
- Lines 153-160 require at least four leptons, first-four total charge zero,
  and first-four pT strictly above 25/15/10/10 GeV.  If a fifth lepton exists,
  it is vetoed only when its pT is strictly greater than 10 GeV, so a fifth
  lepton exactly at 10 GeV passed this historical boundary.
- Lines 67-70 additionally require positive, finite-range MET before any
  requested output, including the pair observables.

The selected leptons were implicitly the first four analysis leptons; the
pair helper did not itself apply the current per-flavor tight-WP masks.

## Core mkShapesRDF four-lepton methods

The current core implementation is
`mkShapesRDF/processor/modules/l4KinProducer.py`.

### `getZXLepIdx`

`getZXLepIdx` (`l4KinProducer.py:10-37`) is the direct core equivalent of the
historical rule.  It examines exactly indices 0 through 3, requires
`pdgId[i] + pdgId[j] == 0`, minimizes `abs(mll - 91.1876)` with a strict `<`
update, and fills X with the two complementary indices in increasing input
order.  Core constructs all `Lepton_4DV` objects with mass zero
(`l4KinProducer.py:83-87`).

The core `isAllOk` gate (`l4KinProducer.py:106-111`) requires valid positive
MET, exactly four common leptons with `pt >= 10 GeV`, leading pT strictly above
25/15 GeV, and first-four charge zero.  Unlike the live `ZZ_CR` physical
selection, this gate does not itself apply the specific tight WP or explicitly
require the third and fourth values to be strictly greater than 10 GeV.

### Why `getZAZBLepIdx` is not a comparator

`getZAZBLepIdx` (`l4KinProducer.py:41-65`) is an auxiliary same-flavor,
charge-zero cross-pair diagnostic, not an alternative associated-Z assignment
algorithm.  Starting from the already chosen Z/X split, it attempts to form
the other OS cross-pair partition and label its nearer-mZ pair `ZA`.

It must not be executed as a PairingStudy comparator for two additional
reasons:

1. The source explicitly says that it is retaining a bug to reproduce the
   legacy `l4Kin` output (`l4KinProducer.py:44-45`): the assignment at line 59
   is not the correct complementary fourth index and can duplicate an object.
2. The validity check at line 52 compares the `-9999` sentinel against
   positive `9999`, so it does not reject an invalid `ZXLepIdx` as intended.

Exhaustive enumeration of the fixed quartet already supplies all candidates,
partitions, the best candidate, and the second-best score without relying on
this malformed diagnostic.  No other core four-lepton Z/X assignment method
was found; similarly named nearest-Z methods in `l3KinProducer.py` are
three-lepton utilities and are outside this study.

## Equivalence of current, core, and Run-2 nearest-mZ rules

For a fixed quartet `Q`, define the common eligible set

```text
C(Q) = {(i,j): 0 <= i < j < 4 and pdgId[i] == -pdgId[j]}.
```

If all quartet objects already satisfy the live tight and 10 GeV requirements,
the current, core, and historical candidate sets are the same.  If they also
use the same four-vectors, all three return

```text
argmin_(i,j in C(Q)) abs(m(i,j) - 91.1876),
```

using a strict-improvement update over the same lexicographic enumeration.
Their unordered selected-Z index sets and complementary X sets are therefore
mathematically identical, including exact-score tie breaking.  Under that
normalized convention, `historical_run2` and `core_l4kin` are the same rule and
share one parameterized executable selector; the two output labels preserve
their distinct source provenance without duplicating the pair loop.

There is one literal-source caveat: historical Run-2 and core `l4KinProducer`
use massless lepton four-vectors, while live `ZZ_CR` uses the electron and muon
masses.  Thus the source implementations minimize slightly different numeric
mass scores and are not strictly identical for an arbitrarily close score
tie. The executable study therefore retains the live physical-mass baseline
and a literal massless selector exposed under both core and historical
provenance labels. This directly measures the residual mass-convention
difference while keeping the candidate loop shared. The historical
strict fifth-lepton boundary at exactly 10 GeV is also different from the live
`>= 10 GeV` veto, but that affects denominator membership rather than the
nearest-mZ ranking once a quartet is fixed.

## Pairing-dependent and pairing-invariant quantities

The classification below assumes that every algorithm receives exactly the
same valid quartet and the same OS-SF candidate set.

| Component | Dependence on Z assignment | Reason |
|---|---|---|
| Selected Z and X indices | Dependent | Z is the algorithm output; X is its complement. |
| `mZ`, `pT(Z)`, Z eta/phi, Z deltaR/deltaPhi | Dependent | These use the selected Z pair. |
| `mX`, `pT(X)`, X eta/phi, X deltaR/deltaPhi | Dependent | These use the complementary pair. |
| Z flavor | Potentially dependent | It can swap between `ee` and `mumu` in `2e2mu`.  This is a truth-relevant label change for ZH but only boson-label exchange for ZZ. |
| Full quartet flavor topology | Invariant | The four input flavors do not change. |
| XSF versus XDF | Invariant on the fixed quartet | It is fixed by the five-topology table above for every eligible OS-SF Z. |
| Selected-Z mass window and `Z0_mass > 30` | Dependent | They test the algorithm-selected Z. |
| `X_mass > 4`, ZZCR X window, and SR X windows | Dependent | They test the complementary X mass. |
| ZZCR/SR acceptance | Dependent | Z and X mass cuts and pair observables can migrate, even though the XSF/XDF branch cannot.  For ZZ this reconstruction migration is separate from label-invariant partition correctness. |
| ZH associated-Z correctness | Dependent | The selected Z must equal the uniquely matched associated-Z daughter pair. |
| ZZ two-boson partition correctness | Dependent on the partition, invariant under Z/X label exchange | The unordered reconstructed pair-of-pairs is compared with the unordered truth pair-of-pairs. |
| Ordered four-lepton pT and total charge | Invariant | They are symmetric functions of the fixed quartet. |
| Fifth-lepton veto | Invariant | It counts the full common `Lepton` collection, not a pairing. |
| `m4l`, `pT4l`, `phi4l`, and four-lepton recoil | Invariant | Four-vector addition is commutative for the same quartet. |
| Minimum of all six quartet pair masses | Invariant | Every unordered pair in the same quartet is included regardless of the Z label. |
| MET, trigger-family OR, L2 gate, horn veto, and b veto | Invariant | These are event- or jet-level decisions. |
| `SelectedLeptonSF_ZX` | Invariant | It is the commutative product over the four selected indices (`aliases.py:717-765`; helper lines 654-665). |
| `TriggerSF_ZX` | Invariant | `selectedFourResult` compacts the same four and pT-sorts them before evaluation (`selected_trigger_wrappers.cc:188-200`). |
| Z-only DY lepton and trigger corrections | Dependent | They dereference only the algorithm-selected Z pair. |

Because the live `FOURL_PARENT` contains selected-Z and selected-X mass cuts,
it is not suitable as the principal pairing denominator.  The independent
study must first construct its tight, charge-balanced, pT-ordered quartet and
apply its fifth-lepton contract without consulting `Z0_idx`, `X_idx`, `mZ`,
`mX`, X flavor, MET, or SR/ZZCR membership.  Only then should every pairing
algorithm be evaluated on the shared exhaustive candidate cache.

The truth layer must then branch by sample domain. ZH uses the unique
associated-Z reco-index pair and label-sensitive correctness. ZZ uses two
matched direct hard Z/gamma* daughter pairs and label-invariant partition
correctness.
Events that do not satisfy the relevant truth-recoverability definition may
remain in reconstructed diagnostics, but they must not enter that domain's
truth-efficiency denominator.
