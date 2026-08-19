"""Validation helpers for compiled RunStability analysis contracts."""

import hashlib
import json


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def contract_digest(contract):
    payload = dict(contract)
    payload.pop("contract_sha256", None)
    return hashlib.sha256(canonical_json(payload).encode()).hexdigest()


def validate_analysis_contract(
    contract,
    *,
    cuts,
    preselections,
    variables,
    category_metadata,
    category_variables,
    expected_context=None,
):
    errors = []
    if contract.get("contract_sha256") != contract_digest(contract):
        errors.append("contract_sha256 does not match canonical contract content")
    if contract.get("preselection") != preselections:
        errors.append("preselection diverges from executable configuration")
    if set(contract.get("categories", {})) != set(category_metadata):
        errors.append("contract categories diverge from executable categories")
    if set(contract.get("variables", {})) != set(variables):
        errors.append("contract variables diverge from executable variables")

    for category_id, metadata in category_metadata.items():
        compiled = contract.get("categories", {}).get(category_id, {})
        for key in ("full_cut_expression", "category_weight_factor", "weight_domain"):
            if compiled.get(key) != metadata.get(key):
                errors.append(f"{category_id}: {key} diverges")
        if compiled.get("active_variables") != list(category_variables[category_id]):
            errors.append(f"{category_id}: active_variables diverge")
        region, split = category_id.split("_", 1)
        executable_cut = (
            f"({preselections}) && ({cuts[region]['expr']})"
            f" && ({cuts[region]['categories'][split]})"
        )
        if compiled.get("full_cut_expression") != executable_cut:
            errors.append(f"{category_id}: full cut is not mechanically executable")

    for name, definition in variables.items():
        compiled = contract.get("variables", {}).get(name, {})
        if compiled.get("expression") != definition.get("name"):
            errors.append(f"{name}: expression diverges")
        if canonical_json(compiled.get("range")) != canonical_json(
            definition.get("range")
        ):
            errors.append(f"{name}: binning diverges")
        if compiled.get("fold") != definition.get("fold", 0):
            errors.append(f"{name}: fold diverges")
        if compiled.get("categories") != list(definition.get("categories", [])):
            errors.append(f"{name}: category applicability diverges")

    for key, expected in (expected_context or {}).items():
        if contract.get(key) != expected:
            errors.append(
                f"context {key} diverges: {contract.get(key)!r} != {expected!r}"
            )
    if errors:
        raise AssertionError("; ".join(errors))
    return True
