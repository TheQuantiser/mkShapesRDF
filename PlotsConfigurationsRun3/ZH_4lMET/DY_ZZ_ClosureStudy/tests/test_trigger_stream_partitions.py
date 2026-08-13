from study_config import build_categories, load_live_json


def trigger_priority(elmu, single_mu, double_mu, single_el, double_el):
    for code, fired in enumerate((elmu, single_mu, double_mu, single_el, double_el), 1):
        if fired:
            return code
    return 0


def stream_priority(elmu, single_mu, double_mu, single_el, double_el):
    if elmu:
        return 1
    if single_mu or double_mu:
        return 2
    if single_el or double_el:
        return 3
    return 0


def test_trigger_and_stream_priorities_are_exclusive_and_exhaustive():
    for mask in range(32):
        bits = tuple(bool(mask & (1 << index)) for index in range(5))
        trigger = trigger_priority(*bits)
        stream = stream_priority(*bits)
        assert 0 <= trigger <= 5
        assert 0 <= stream <= 3
        assert (trigger > 0) == any(bits)
        assert (stream > 0) == any(bits)


def test_live_data_deduplication_rule_exactly_matches_priority():
    cfg = load_live_json()
    assert cfg["data_stream_triggers"] == {
        "MuonEG": "Trigger_ElMu",
        "Muon": "!Trigger_ElMu && (Trigger_sngMu || Trigger_dblMu)",
        "EGamma": "!Trigger_ElMu && !Trigger_sngMu && !Trigger_dblMu && (Trigger_sngEl || Trigger_dblEl)",
    }


def test_cat_txt_split_matrix_is_materialized_as_literal_categories():
    categories = set(build_categories())

    flavor = {
        f"{parent}_{suffix}"
        for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT", "D1_DY_ALL_CURRENT")
        for suffix in ("ZEE", "ZMM")
    }
    topology = {
        f"{parent}_{suffix}"
        for parent in ("S0_ZZCR", "S7_FOURL_BRIDGE")
        for suffix in ("4E", "4MU", "2E2MU")
    }
    trigger = {
        f"{parent}_{suffix}"
        for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT")
        for suffix in (
            "TRGPRIO_ELMU",
            "TRGPRIO_SINGLEMU",
            "TRGPRIO_DOUBLEMU",
            "TRGPRIO_SINGLEEL",
            "TRGPRIO_DOUBLEEL",
        )
    }
    stream = {
        f"{parent}_{suffix}"
        for parent in ("S8_Z_BRIDGE", "D0_DY_ENRICHED_CURRENT")
        for suffix in ("STREAM_MUONEG", "STREAM_MUON", "STREAM_EGAMMA")
    }
    extra = {"S8_EXTRA0", "S8_EXTRA1", "S8_EXTRA2P"}

    requested = flavor | topology | trigger | stream | extra
    assert requested <= categories
    assert len(flavor) == 6
    assert len(topology) == 6
    assert len(trigger) == 10
    assert len(stream) == 6
    assert len(extra) == 3
