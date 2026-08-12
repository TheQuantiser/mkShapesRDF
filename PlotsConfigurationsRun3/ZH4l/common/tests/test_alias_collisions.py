import ast
from pathlib import Path

from common.alias_contract import (
    COMMON_PUBLIC_ALIASES,
    FORBIDDEN_NATIVE_COLLISIONS,
    classify_alias,
)
from common.corrections import PUBLIC_CORRECTION_ALIASES
from common.objects import PUBLIC_OBJECT_ALIASES
from common.observables import PUBLIC_OBSERVABLE_ALIASES


FAMILY_DIR = Path(__file__).resolve().parents[2]
LEAVES = ("ZZCR", "Pairing", "Closure")


def _literal_alias_assignments(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Subscript):
            continue
        if not isinstance(node.value, ast.Name) or node.value.id != "aliases":
            continue
        key = node.slice
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            names.add(key.value)
    return names


def test_common_owners_are_disjoint_and_forbidden_native_names_are_absent():
    owners = (PUBLIC_OBJECT_ALIASES, PUBLIC_CORRECTION_ALIASES, PUBLIC_OBSERVABLE_ALIASES)
    for index, left in enumerate(owners):
        for right in owners[index + 1:]:
            assert left.isdisjoint(right)
    assert COMMON_PUBLIC_ALIASES.isdisjoint(FORBIDDEN_NATIVE_COLLISIONS)
    assert classify_alias("bVeto") == "intentional-identical-reuse"
    assert classify_alias("ZH4l_sourceIdx") == "family-private"
    assert classify_alias("mll") == "collision/error"


def test_leaves_consume_common_aliases_instead_of_redefining_them():
    for leaf in LEAVES:
        path = FAMILY_DIR / leaf / "aliases.py"
        source = path.read_text()
        assert "build_object_aliases" in source
        locally_assigned = _literal_alias_assignments(path)
        accidental = locally_assigned & COMMON_PUBLIC_ALIASES
        assert not accidental, f"{leaf} independently redefines {sorted(accidental)}"
        assert not (locally_assigned & FORBIDDEN_NATIVE_COLLISIONS)
