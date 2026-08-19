# Bounded category design

> **LEGACY / HISTORICAL EVIDENCE.** This file preserves the former multi-region
> `ZH_4lMET` category design. Its `ALL`, ZZCR, SR, enriched-DY, profile-count,
> wrapper, and production statements are not the active DY-only RunStability
> contract. Names and paths below may no longer exist. Use
> [README.md](../README.md), [ARCHITECTURE.md](../ARCHITECTURE.md), and
> [CONFIGURATION.md](../CONFIGURATION.md) for supported behavior.

This document's 47-category tables describe the ordinary
`ANALYSIS_PASS=ALL` graph. `ANALYSIS_PASS=RUN_STABILITY` extends only the DY
graph and has its own contract below; the two profiles must not be compared by
category count without naming the analysis pass.

## Decision

The recommended `standard` profile contains 47 diagnostic projections and
1,043 category-variable actions. It retains the three rich region-inclusive
views and mirrors every declared DY flavor, stream, and stream-by-flavor view
inside the overlapping `DY_ENRICHED` signal-Z window.
No code constructs a general Cartesian product.

| Region | Inclusive/projection | Flavor/topology | Stream | Curated intersection | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| DY | 2 | 4 | 6 | 12 | 24 |
| ZZCR | 1 | 3 | 3 | 5 | 12 |
| SR | 1 | 7 | 3 | 0 | 11 |
| Total | 4 | 14 | 12 | 17 | 47 |

The current `detailed` production profile contains the standard inventory plus
the six SR stream-by-X-flavor projections. Its exact 53 directory IDs are:

```text
DY_ALL
DY_ENRICHED
DY_ZEE
DY_ZMM
DY_STREAM_MUONEG
DY_STREAM_MUON
DY_STREAM_EGAMMA
DY_STREAM_MUONEG_ZEE
DY_STREAM_MUONEG_ZMM
DY_STREAM_MUON_ZEE
DY_STREAM_MUON_ZMM
DY_STREAM_EGAMMA_ZEE
DY_STREAM_EGAMMA_ZMM
DY_ENRICHED_ZEE
DY_ENRICHED_ZMM
DY_ENRICHED_STREAM_MUONEG
DY_ENRICHED_STREAM_MUON
DY_ENRICHED_STREAM_EGAMMA
DY_ENRICHED_STREAM_MUONEG_ZEE
DY_ENRICHED_STREAM_MUONEG_ZMM
DY_ENRICHED_STREAM_MUON_ZEE
DY_ENRICHED_STREAM_MUON_ZMM
DY_ENRICHED_STREAM_EGAMMA_ZEE
DY_ENRICHED_STREAM_EGAMMA_ZMM

ZZCR_ALL
ZZCR_4E
ZZCR_4MU
ZZCR_2E2MU
ZZCR_STREAM_MUONEG
ZZCR_STREAM_MUON
ZZCR_STREAM_EGAMMA
ZZCR_STREAM_EGAMMA_4E
ZZCR_STREAM_MUON_4MU
ZZCR_STREAM_MUONEG_2E2MU
ZZCR_STREAM_MUON_2E2MU
ZZCR_STREAM_EGAMMA_2E2MU

SR_ALL
SR_XSF
SR_XDF
SR_4E
SR_4MU
SR_2E2MU
SR_3E1MU
SR_1E3MU
SR_STREAM_MUONEG
SR_STREAM_MUON
SR_STREAM_EGAMMA
SR_STREAM_MUONEG_XSF
SR_STREAM_MUONEG_XDF
SR_STREAM_MUON_XSF
SR_STREAM_MUON_XDF
SR_STREAM_EGAMMA_XSF
SR_STREAM_EGAMMA_XDF
```

This is 24 DY, 12 ZZCR, and 17 SR directories. The names are generated from
the registry; this list documents the executable result and is not a second
source of category definitions.

`DY_ENRICHED` is selected by `abs(Z0_mass - 91.1876) < 15`, using the same
constant as the physical ZZCR/SR parent. It is not an exclusive partition
member: it overlaps `DY_ALL` by design. Each ordinary DY subcategory is
mechanically mirrored as `DY_ENRICHED_*`; it conjoins the same shared window
with the ordinary split and inherits its view type, histogram tier, weight,
and within-family exclusivity.

DY keeps its full 3-by-2 stream-priority versus selected-Z-flavor closure
matrix. This is the one region where every leaf directly diagnoses dataset
stream/trigger closure. The cross-flavor stream leaves are logically possible
because DY does not veto extra leptons; their zero occupancy in some bounded
samples is itself a useful contamination check.

ZZCR keeps the expected pure-flavor leaves `EGAMMA_4E` and `MUON_4MU`, plus
all three stream-priority views of `2E2MU`. The four remaining members of a
blind 3-by-3 matrix are omitted. Fifth-lepton vetoes and trigger legs make
MuonEG/Muon 4e and MuonEG/EGamma 4mu either logically incompatible with the
selected final state under normal trigger behavior or useful only as raw
trigger-path anomalies; the stream and topology marginals already expose
those anomalies at lower cost. The two zero-occupancy mixed-topology fallback
leaves remain because they test a concrete priority/de-duplication failure
mode and are logically possible when the cross trigger is inefficient.

SR keeps both X-flavor marginals and a mechanically exclusive/exhaustive
five-topology partition built only from selected `Z0` and `X` flavors. The
six stream-by-X-flavor views are useful in `detailed`, where bounded ZH
occupancy populated five of six leaves, but are not needed in `standard`.
The 15 stream-by-topology leaves are omitted from every ordinary profile.

## Metadata semantics

Every category records `view_type`, `partition_family`,
`is_exclusive_within_family`, `is_overlapping_projection`, and
`diagnostic_purpose`. Flavor, stream, topology, trigger-priority, and DY
stream-by-flavor families are exclusive internally. The curated ZZ family is
also mutually exclusive but intentionally not exhaustive. Families overlap
one another as projections: an event may simultaneously appear in an
inclusive, flavor, stream, and curated-intersection view.

The trigger profile uses the exclusive integer `triggerFamilyPriority`
partition. It does not filter on overlapping raw `Trigger_*` bits.

## Run-stability DY extension

The `RUN_STABILITY` standard profile contains 96 DY categories: a 48-category
base graph and 48 `DY_ENRICHED_*` mirrors. The base graph contains the
`DY_ALL,DY_ZEE,DY_ZMM` `Trigger_Any` reference trio; three stream parents and
six stream-by-selected-Z-flavor children; five positive trigger-family
parents and ten flavor children; and seven positive concrete-HLT-path parents
and fourteen flavor children.

Unlike the ordinary `trigger` profile, the run-stability family and path
categories are direct, positive, overlapping `Trigger_*`/`HLT_*` projections;
they are not the exclusive `triggerFamilyPriority` partition. Each category
records its luminosity-source key. A `_ZEE` or `_ZMM` child inherits the
flavor-stripped parent's exposure because selected-Z flavor partitions events,
not delivered time. The full 25-observable graph has 2,400 actions and uses
the run-stability-specific budgets of 100 categories and 2,500 actions. The
maintained focused production selects the 48 un-enriched categories and
`Z0_mass`, for 48 actions.

## Variable tiers

Activation is keyed by `(physics_region, view_type)`:

| View | DY variables/category | ZZCR/SR variables/category | Purpose |
| --- | ---: | ---: | --- |
| inclusive | 25 | 50 | Full normal analysis view |
| flavor/topology | 19 | 31 | Physics closure without recoil/angular duplication |
| stream | 17 | 25 | Trigger/stream acceptance diagnostics |
| stream-flavor | 15 | 15 | Focused intersection check |
| trigger priority | 17 | 25 | Exclusive trigger-family acceptance |

Definitions, binning, folds, and registry hashes remain immutable. Exact
`VARIABLE_INCLUDE` bypasses the normal view tier for requested variables but
still respects region applicability; `VARIABLE_EXCLUDE` removes requested
entries without altering definitions.

## Occupancy evidence

`category_occupancy.json` records Filter/Count results from staged CERN
NanoAOD: ZZ files for all five eras, a 2024 ZH file, and 2024 MuonEG DATA.
The study covers four v12 MC samples, two v15 MC samples, one v15 DATA sample,
and 45,376 examined entries. It dependency-sliced the graph to selection
aliases and booked no histograms or correction weights.

The bounded ZZ samples populate the expected `EGAMMA_4E`, `MUON_4MU`, and
`MUONEG_2E2MU` leaves in every era with sufficient ZZCR occupancy. The
Muon/EGamma fallback `2E2MU` leaves were zero in this proxy but remain standard
because logical possibility and de-duplication diagnostic value take priority
over a bounded zero. SR stream-by-X-flavor occupancy supports retaining those
six leaves only in `detailed`. A bounded zero is never treated as proof of
logical impossibility.

## Algebra and cost

Truth-table tests prove the DY flavor/stream/intersection identities, ZZCR
topology partition and curated intersections, and the SR topology/X-flavor
identities. The final nominal action counts are:

| Profile | Categories | Category budget | Actions | Action budget |
| --- | ---: | ---: | ---: | ---: |
| minimal | 4 | 6 | 150 | 200 |
| standard | 47 | 50 | 1,043 | 1,100 |
| flavor | 18 | 20 | 536 | 700 |
| stream | 16 | 20 | 402 | 500 |
| trigger | 24 | 30 | 570 | 700 |
| detailed | 53 | 60 | 1,133 | 1,200 |
| debug | 73 | 50 | 1,553 | 1,200 |

Debug exceeds both defaults by design and requires
`ALLOW_LARGE_PLAN=1`. Every ordinary production profile fits within its
profile-specific fail-closed margin.

Standard is 6.953 times the minimal action count but 22.449 times smaller
than the former 23,414-action rectangle. It remains one nominal `ALL` job set
with unchanged region-specific weight factors.

## Current execution boundary

Category projection and sample activation are independent axes. The default
`commissioning` sample profile activates DATA plus the live DY and ZZ outputs;
`presentation` activates every logical output owned by the live plot groups.
Neither profile changes the 47-category/1,043-action standard histogram graph,
and `SAMPLE_FILTER` remains a stronger exact override.

The current physical ZZCR/SR parent includes
`minSelectedPairMass > 12 GeV`, evaluated over the six unordered pairs made
from exactly the selected Z0+X leptons. DY deliberately does not include that
requirement. This subsequent selection update does not alter the category
families, their algebra, or the sparse action counts documented above.

Ordinary FNAL validation and packaged production read CERN inputs directly
through XRootD. The staged files described in the occupancy evidence are
historical bounded inputs; whole-file stage-in remains an explicit fallback,
not the production default.

The 2026-08-10 full-event reference production used
`detailed + analysis + presentation + nominal` for all five eras. Its split
inventories were 505, 1,216, 707, 455, and 3,895 ROOT files for 2022, 2022EE,
2023, 2023BPix, and 2024. All five inventories were merged successfully by
streaming the remote split files through XRootD; no whole-campaign copy was
used.
