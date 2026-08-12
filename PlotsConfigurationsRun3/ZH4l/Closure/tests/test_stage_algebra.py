from study_config import NMINUS1, PRIMARY_STAGES, ZZ_TERMS, build_categories


def _passes(stage, event):
    # Representative Boolean realization of the declarative graph. Numeric
    # guards are represented by their named truth decisions.
    required = {
        "S0_ZZCR": ("fourl", "met", "xmass", "xflavor", "bveto", "lowmass", "fifth", "fourlpt", "zwindow"),
        "S1_NO_MET": ("fourl", "xmass", "xflavor", "bveto", "lowmass", "fifth", "fourlpt", "zwindow"),
        "S2_NO_XMASS": ("fourl", "xflavor", "bveto", "lowmass", "fifth", "fourlpt", "zwindow"),
        "S3_NO_XFLAVOR": ("fourl", "bveto", "lowmass", "fifth", "fourlpt", "zwindow"),
        "S4_NO_BVETO": ("fourl", "lowmass", "fifth", "fourlpt", "zwindow"),
        "S5_NO_LOWMASS": ("fourl", "fifth", "fourlpt", "zwindow"),
        "S6_NO_FIFTHVETO": ("fourl", "fourlpt", "zwindow"),
        "S7_FOURL_BRIDGE": ("fourl", "fourlpt", "zwindow"),
        "S8_Z_BRIDGE": ("zvalid", "z10", "zwindow", "anchorpt"),
        "D0_DY_ENRICHED_CURRENT": ("zvalid", "z10", "zwindow", "currentpt", "zmass30"),
        "D1_DY_ALL_CURRENT": ("zvalid", "z10", "currentpt", "zmass30"),
    }[stage]
    return all(event.get(key, False) for key in required)


def test_cumulative_ladder_and_dy_relations_on_representative_events():
    stages = tuple(name for name in PRIMARY_STAGES if name.startswith("S"))
    events = []
    base = {key: True for key in ("fourl", "met", "xmass", "xflavor", "bveto", "lowmass", "fifth", "fourlpt", "zvalid", "z10", "zwindow", "anchorpt", "currentpt", "zmass30")}
    events.append(base)
    for released in ("met", "xmass", "xflavor", "bveto", "lowmass", "fifth"):
        item = dict(base); item[released] = False; events.append(item)
    for event in events:
        occupancy = [_passes(stage, event) for stage in stages]
        assert occupancy == sorted(occupancy)
        assert not _passes("S0_ZZCR", event) or _passes("S8_Z_BRIDGE", event)
        assert not _passes("D0_DY_ENRICHED_CURRENT", event) or _passes("S8_Z_BRIDGE", event)
        assert not _passes("D0_DY_ENRICHED_CURRENT", event) or _passes("D1_DY_ALL_CURRENT", event)


def test_each_nminus1_removes_exactly_one_term_and_met_reuses_s1():
    assert set(NMINUS1) == {"N1_NO_XMASS", "N1_NO_XFLAVOR", "N1_NO_BVETO", "N1_NO_LOWMASS", "N1_NO_FIFTHVETO", "N1_NO_4LPT", "N1_NO_ZWINDOW"}
    assert "PuppiMET_pt < 35." not in PRIMARY_STAGES["S1_NO_MET"]
    for key, term in ZZ_TERMS.items():
        if key == "met":
            continue
        expression = NMINUS1[f"N1_NO_{'4LPT' if key == 'fourlpt' else {'xmass':'XMASS','xflavor':'XFLAVOR','bveto':'BVETO','lowmass':'LOWMASS','fifth':'FIFTHVETO','zwindow':'ZWINDOW'}[key]}"]
        assert term not in expression
        for other_key, other_term in ZZ_TERMS.items():
            if other_key != key:
                assert other_term in expression


def test_no_unproven_s8_to_broad_dy_relation_is_encoded():
    categories = build_categories()
    assert "S8_Z_BRIDGE" in categories and "D1_DY_ALL_CURRENT" in categories
    assert PRIMARY_STAGES["S8_Z_BRIDGE"] != PRIMARY_STAGES["D1_DY_ALL_CURRENT"]
