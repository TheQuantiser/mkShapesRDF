# RunStability production-history index

This directory contains dated evidence, not executable configuration. The
active source contract is owned by the leaf's `README.md`, `ARCHITECTURE.md`,
`CONFIGURATION.md`, JSON declarations, and Python materializers. Never copy a
historical selector, luminosity, path, pickle, or generated job directory into
a new campaign without validating it against the active source.

| Record | Status | Correct use |
| --- | --- | --- |
| [20260817_initial_submission_failure.md](20260817_initial_submission_failure.md) | Failed | Diagnose the original FNAL trust/transport failure only |
| [20260817_vomsfix_full_production.md](20260817_vomsfix_full_production.md) | Historical transport success; incomplete 2022 population | Transport and scheduler evidence only |
| [20260817_dy_zmass_ratio_production.md](20260817_dy_zmass_ratio_production.md) | Superseded 151-run 2022 C--D campaign | Preserve as incomplete early evidence |
| [20260818_dy_trigger_stability_production.md](20260818_dy_trigger_stability_production.md) | Historical trigger-stability campaigns | Reproduce only with their exact recorded identities |
| [20260819_dy_trigger_stability_pt35_production.md](20260819_dy_trigger_stability_pt35_production.md) | Retained completed obs6 campaign plus canceled predecessors | Source of the five exact `plot_reproduction.json` pickle/ROOT pairs |
| [20260819_runstability_architecture_redesign.md](20260819_runstability_architecture_redesign.md) | Current live-source redesign | Architecture, ownership, binding, validation, and handoff evidence |

The retained obs6 campaign remains valid for hash-pinned manual plot
reproduction. The current live source is a redesigned future-production
contract. No new campaign has yet been compiled or submitted from that live
contract.
