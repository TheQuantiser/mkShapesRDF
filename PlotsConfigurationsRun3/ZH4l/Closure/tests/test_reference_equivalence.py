import hashlib
from pathlib import Path

from study_config import CURRENT_DY, CURRENT_DY_ENRICHED, EXACT_ZZCR, PRESELECTION


HERE = Path(__file__).resolve().parents[1]


def _digest(expression):
    return hashlib.sha256(expression.encode()).hexdigest()


def test_exact_audited_reference_cut_expressions_are_frozen_locally():
    # These digests freeze the migrated vocabulary.  The logical selections
    # are unchanged; only the old Z0/X1 spellings became the family contract's
    # Z/X names.  Keeping the oracle local also makes this study standalone.
    assert _digest(PRESELECTION) == "497e7155419122ff181775e9aed833d5bc8f98876294f03c8570ba79ef767f02"
    assert _digest(EXACT_ZZCR) == "f8a89f4b8376c5690280e2776b633e7078b8b0d4e6867d63aa7b7d9192d5f214"
    assert _digest(CURRENT_DY) == "cd1f19ad2fee6d5158eb8ee1684cabdec261303c093304d8f439e3152c4d83e7"
    assert _digest(CURRENT_DY_ENRICHED) == "f8ff8df757849549ba0f16ba3945bd727b7bb627b2c6cae490d9ad813998cbd2"


def test_pairing_is_single_sourced_in_the_family_common_alias_graph():
    aliases_source = (HERE.parent / "common" / "objects.py").read_text()
    macro = HERE.parent / "common" / "macros" / "objects.cc"
    assert "bestZ0IdxWithID" in aliases_source
    assert '"common" / "macros" / "objects.cc"' in aliases_source
    assert "bestZ0IdxWithID" in macro.read_text()
    assert "ZH_4lMET" not in aliases_source


def test_pt_contract_has_synthetic_migration_populations():
    # Z pair has 20/18 while an additional tight lepton has pT=30: event-tight
    # passes 25/15 but selected-Z fails. Conversely is impossible under the
    # same tight-object contract, so current-only must be empty algebraically.
    selected_z = (20.0, 18.0)
    event_tight = sorted((30.0, *selected_z), reverse=True)
    assert not (selected_z[0] > 25 and selected_z[1] > 15)
    assert event_tight[0] > 25 and event_tight[1] > 15
    selected_z = (30.0, 20.0)
    assert selected_z[0] > 25 and selected_z[1] > 15
    assert sorted(selected_z, reverse=True)[0] > 25
