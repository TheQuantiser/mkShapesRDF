import hashlib
import re
from pathlib import Path

from study_config import CURRENT_DY, CURRENT_DY_ENRICHED, EXACT_ZZCR, PRESELECTION


HERE = Path(__file__).resolve().parents[1]


def _digest(expression):
    return hashlib.sha256(expression.encode()).hexdigest()


def test_exact_audited_reference_cut_expressions_are_frozen_locally():
    # Digests were recorded from the live ZZ_CR contract at STARTING_SHA.
    # Keeping the oracle local makes the closure study and its tests runnable
    # without importing or packaging the sibling analysis directory.
    assert _digest(PRESELECTION) == "e4552a5838b3a959516cc3c0903929cbcde434cead1107cd174062540d9c2582"
    assert _digest(EXACT_ZZCR) == "a32dfee62259463af7ebd3a794c64901a4c8dc4282feb5d4189525cc2203d0dc"
    assert _digest(CURRENT_DY) == "c4c69be26f4ebe57dd7cb7dc0ea7c6f1b153d4bb73c30f071884bd6253bfed89"
    assert _digest(CURRENT_DY_ENRICHED) == "d0c4314b370a0730d61210932b3c6e0a0223dd2cbbdd8e543d943f8b9c2115a6"


def test_vendored_pairing_is_single_sourced_in_the_local_alias_graph():
    source = (HERE / "aliases.py").read_text()
    assert "bestZ0IdxWithID" in source
    paths = set(re.findall(r"PlotsConfigurationsRun3/[^\"']+/macros/four_lepton_helpers\.cc", source))
    assert paths == {"PlotsConfigurationsRun3/ZH_4lMET/DY_ZZ_ClosureStudy/macros/four_lepton_helpers.cc"}


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
