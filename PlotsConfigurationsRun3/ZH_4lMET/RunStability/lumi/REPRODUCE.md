# Reproduce the RunStability luminosity audit

This is the manual sequence for verifying the retained luminosity evidence or
building a fresh audit identity. The RunStability leaf owns the analysis
configuration, active binding, copied audit inputs, normtag, results, and
receipts. The generic BRIL/DBS audit engine remains the workspace service at
`lumi/scripts/`; it is not duplicated inside the analysis configuration.

The retained audit is immutable:

```text
RunStability/lumi/audits/
  ZZ_CR_RunStability_BCD_afa86d85_conjunction_20260818T200415Z/
```

Its historical name and old source path are part of its identity. Do not edit
them. The live bridge is `lumi/run_stability_luminosity_binding.json`.

## 1. Establish the environment and a fresh identity

Work from the development workspace. Use an already initialized CMS
authentication context, and never copy or log a proxy.

```bash
workspace=/uscms_data/d3/mwadud/private/mkShapesRDF_devel
repo="$workspace/mkShapesRDF"
leaf="$repo/PlotsConfigurationsRun3/ZH_4lMET/RunStability"
engine="$workspace/lumi/scripts"
year_config="$leaf/year_config.json"
audit_root="$leaf/lumi/audits/RunStability_$(date -u +%Y%m%dT%H%M%SZ)"

test -f "$year_config"
test -d "$engine"
test ! -e "$audit_root"
sha256sum "$year_config"
```

Never use the retained audit as `LUMI_OUTPUT_ROOT`. A fresh query must write a
new directory. Only `build_inputs.py` and `reuse_compatible_raw.py` implement
an argparse `--help`; the other producers execute immediately, so inspect
their source instead of probing them with `--help`.

## 2. Reconcile samples before computing luminosity

Run a fresh representative catalog and a separate all-parts catalog with the
leaf-local `make_sample_catalog.py`. Compare them with `year_config.json`, the
processor catalogs under `mkShapesRDF/processor/framework/samples/`, and the
live target directories. The default representative policy is part 0, falling
back to part 1 for an exact identity when part 0 is absent.

For 2022 the required DATA matrix is exactly:

```text
MuonEG:     B C D
SingleMuon: B C
Muon:         C D
EGamma:     B C D
```

There is no Muon B and no SingleMuon D. The ten components contain 739
materialized files in the retained inventory. Any unresolved missing or
unexpected component vetoes a fresh audit.

## 3. Build masks and the dataset run/lumisection inventory

This stage copies the official Golden JSONs and PHYSICS normtag, resolves the
central datasets from processor catalogs, queries DBS for exact `(run, LS)`
membership, and builds the certified intersections.

```bash
python3 "$engine/build_inputs.py" \
  --year-config "$year_config" \
  --output-root "$audit_root"
```

For a strict reconstruction, do not reuse an older inventory. Verify the
generated manifest, 89 dataset/run-tag records, component counts
10/9/20/10/40, nonempty certified intersections, and exact input hashes.

The retained audit used:

```text
inputs/normtag/normtag_PHYSICS.json
SHA-256 693ef4b360a1debb2aa667fa4178c3f4dece9539d9cf3ffee1ea60f157823548
```

## 4. Run direct BRIL queries

The official CMS BRIL environment is sourced by the wrapper from
`/cvmfs/cms-bril.cern.ch/cms-lumi-pog/brilws-docker/brilws-env`. It executes
`brilcalc lumi -c web`, uses the audit-local PHYSICS normtag, requests `/fb`
with precision `12f`, writes `.partial`, and promotes only a nonempty result.
Use one query writer for a conservative manual repeat:

```bash
LUMI_OUTPUT_ROOT="$audit_root" bash --noprofile \
  --rcfile "$HOME/.bashrc" -ic \
  "LUMI_MAX_PARALLEL=1 bash '$engine/run_brilcalc.sh'"
```

Require 40 direct outputs: five nominal queries and seven concrete paths for
each of five eras. Do not add path luminosities to emulate a trigger OR.

## 5. Prove partial trigger exposure by lumisection

```bash
LUMI_OUTPUT_ROOT="$audit_root" \
  python3 "$engine/prepare_adaptive_queries.py"

LUMI_OUTPUT_ROOT="$audit_root" bash --noprofile \
  --rcfile "$HOME/.bashrc" -ic \
  "LUMI_MAX_PARALLEL=1 bash '$engine/run_adaptive_byls.sh'"
```

The retained audit classified 6,895 run/path pairs as 6,229 fully exposed,
91 inactive, and 575 requiring LS-level proof, producing 33 adaptive outputs.

## 6. Aggregate and close the full-Golden partition

```bash
LUMI_OUTPUT_ROOT="$audit_root" python3 "$engine/aggregate_results.py"
LUMI_OUTPUT_ROOT="$audit_root" python3 "$engine/audit_run_periods.py"

LUMI_OUTPUT_ROOT="$audit_root" bash --noprofile \
  --rcfile "$HOME/.bashrc" -ic \
  "bash '$engine/run_full_year_supplement.sh'"

LUMI_OUTPUT_ROOT="$audit_root" \
  python3 "$engine/aggregate_full_year_audit.py"
```

Configured analysis exposure and excluded full-year exposure must be disjoint
and reconstruct the pinned Golden JSON. Never add supplemental exposure to
the configured analysis denominator.

## 7. Validate source, schema, reproduction, and results

First run the current leaf tests against the fresh results:

```bash
cd "$repo"
source start.sh
RUN_STABILITY_LUMI_DIR="$audit_root/results" \
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest -q -p no:cacheprovider \
  PlotsConfigurationsRun3/ZH_4lMET/RunStability/tests
```

Record the actual command, revision, UTC time, collected/passed/failed counts,
environment, and limitations in the fresh source-validation receipt; never
copy the retained passing receipt into a new identity.

Run the representative real-file schema check with an explicit file:

```bash
LUMI_OUTPUT_ROOT="$audit_root" \
LUMI_REPRESENTATIVE_FILE=/store/group/phys_higgs/cmshww/amassiro/HWWNano/Run2022_ReReco_nAODv12_Full2022v12/DATAl2loose2022v12__l2loose/nanoLatino_SingleMuon_Run2022B-ReReco-v1__part0.root \
python3 "$engine/check_representative_schema.py"
```

Then independently repeat the selected BRIL queries and run the final local
validator:

```bash
LUMI_OUTPUT_ROOT="$audit_root" bash --noprofile \
  --rcfile "$HOME/.bashrc" -ic \
  "bash '$engine/run_reproducibility_check.sh'"

LUMI_OUTPUT_ROOT="$audit_root" \
  python3 "$engine/check_reproducibility.py"
LUMI_OUTPUT_ROOT="$audit_root" \
  python3 "$engine/validate_results.py"
```

Accept only a passed validation report, complete component/category trigger
conjunction proof, zero unsupported LS, zero partial files, and exact
independent reproduction. Independently hash and reopen all retained outputs.

## 8. Bind a validated fresh audit

Do not rewrite the old binding or audit in place. After a fresh audit passes,
update `run_stability_luminosity_binding.json` with the new live config hash,
semantic BRIL-input projection hash, source audit path, and exact source
manifest/provenance/result hashes. Compilation will also require every
`year_config.json` `lumi_fb` and the runtime `lumi` to equal the exact nominal
recorded analysis-era result.

The current validated nominal targets are:

| Era | Recorded luminosity [fb\(^{-1}\)] | Runs |
| --- | ---: | ---: |
| 2022 | 8.076828657919002 | 170 |
| 2022EE | 26.671325997159986 | 190 |
| 2023 | 18.062658998219003 | 126 |
| 2023BPix | 9.693130030386998 | 43 |
| 2024 | 109.72830897472497 | 456 |

These are nominal certified-and-dataset-covered denominators. Trigger-OR,
family, and concrete-path effective luminosities remain separate compiled
sources and must be selected category by category.
