# RunStability luminosity binding

The canonical profile points to:

```text
lumi/run_stability_luminosity_binding.json
```

For the exact producer sequence and a fresh-audit checklist, see
[REPRODUCE.md](REPRODUCE.md).

This active receipt has kind `run_stability_luminosity_binding`. It binds the
renamed live leaf to a checked-in immutable historical audit without rewriting
that audit's original paths or bytes.

## Two evidence layers

The active binding records:

- live `year_config.json` path and whole-file SHA-256;
- live semantic BRIL-input projection SHA-256;
- immutable source-audit path;
- exact source manifest, provenance, and
  `luminosity_by_analysis_era.csv` hashes.

The source audit under `lumi/audits/` retains the Golden JSON, normtag,
dataset-coverage and trigger-query inputs; copied year-config snapshot;
nominal, Trigger-OR, family, and concrete-path tables; validation diagnostics;
and result hashes. Its historical identifier is an artifact identity, not the
current leaf name. Never rename or rewrite it.

## Compile-time acceptance

In default mode, compilation requires:

1. binding schema, kind, status, paths, and all bound hashes to match;
2. every required audit file and provenance result hash to close;
3. the audit manifest to hash its copied `inputs/year_config.json`;
4. live and audited BRIL-input projections to match exactly;
5. each live `lumi_fb` to equal the exact validated nominal recorded result;
6. selected runtime `lumi` to equal that configured/audited value exactly;
7. run order, effective source rows, aggregates, and category routing to pass.

The BRIL-input projection includes DATA components, run tags, streams and
component trigger rules; `data_stream_triggers`; processing-era identifiers;
and physical HLT paths. It excludes `lumi_fb`: luminosity is a validated query
result, not a BRIL input. Exact nominal-result equality is checked separately
against `luminosity_by_analysis_era.csv`.

## Override

For a deliberately different validated audit, set an absolute results path:

```bash
export RUN_STABILITY_LUMI_DIR=/absolute/path/to/AUDIT_ID/results
```

The compiled contract records `explicit_absolute_override` and that the
default binding comparison was not applied. The override does not bypass audit
manifest/provenance, semantic projection, exact nominal-result, runtime-lumi,
run-set, source, or aggregate checks. Never use a workspace convenience result
directory as an implicit fallback.

## Update boundary

- If a BRIL-input projection field changes, generate and validate a fresh
  audit under a new immutable ID, then update the binding's source hashes.
- If only `lumi_fb` changes, it must first match the exact validated nominal
  audit result; do not patch it independently.
- If another live-file field changes without affecting the projection or
  nominal result, retain the audit and refresh the active binding's live-file
  hash.
- After any binding edit, validate every path/hash and compile-time equality
  gate before production.

The compiled pickle and worker payload contain the accepted rows and identity.
Workers and retained plot reproduction do not reopen this directory.
