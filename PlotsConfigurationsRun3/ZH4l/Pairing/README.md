# Z/X pairing study

This leaf asks whether alternative four-lepton pairing scores improve the
validated nominal Z/X assignment for ZH and ZZ events. The baseline Z/X and
tight-lepton contract comes from `common`; `macros/pairing.cc` locally owns
candidate enumeration, truth recovery, alternative scores, topology codes,
and cached per-event study results.

The two denominators are `PAIRING_OBJECT_BASE` and `PAIRING_PHYS_BASE`.
Topologies and algorithm choices are histogram axes rather than multiplied cut
categories. Raw, signed, and absolute counts are booked from one event graph.
The small `runner.py` entry point delegates scalar/vector weight booking and
snapshots to `common.runner`, which subclasses native RunAnalysis.

```bash
source start.sh
export PAIRING_CAMPAIGN=pairing_check
export LIMIT_FILES_PER_SAMPLE=1
PlotsConfigurationsRun3/ZH4l/Pairing/run_all_eras.sh compile
PlotsConfigurationsRun3/ZH4l/Pairing/run_all_eras.sh pilot
PlotsConfigurationsRun3/ZH4l/Pairing/run_all_eras.sh summary
PlotsConfigurationsRun3/ZH4l/Pairing/run_all_eras.sh plots
```

`pairing_config.py` preserves the validated ZH/ZZ inventory and exposes `ERA`.
`make_summary.py` keeps the historical JSON field names where consumers depend
on them. Detailed algorithm/truth definitions and interpretation guidance are
in [PAIRING_STUDY.md](PAIRING_STUDY.md).

`ZH4L_OUTPUT_MODE=trees` or `both` enables event snapshots for both denominators.
They retain `pairing_quartet_lepton_index`, candidate-choice and selected-mass
vectors, `weight_raw`, `weight_nominal`, and `weight_abs_nominal`; the default
exported `weight` is `weight_nominal`. Vector entries share an event and are
not independent flattened rows. `SAMPLE_FILTER` accepts an exact subset of the
resolved ZH/ZZ inventory for bounded checks; it does not redefine that inventory.
Use [NAMING.md](../NAMING.md) for current alias/output names. Historical study
results and stable summary JSON keys retain their recorded vocabulary.
