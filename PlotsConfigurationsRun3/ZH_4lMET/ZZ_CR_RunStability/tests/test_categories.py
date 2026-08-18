import pytest


def test_minimal_category_ids_exact(load_state):
    state = load_state()
    assert tuple(state["CATEGORY_METADATA"]) == (
        "DY_ALL",
        "DY_ENRICHED",
        "ZZCR_ALL",
        "SR_ALL",
    )
    assert len(state["CATEGORY_METADATA"]) == len(set(state["CATEGORY_METADATA"]))


def test_flavor_profile_is_physical(load_state):
    state = load_state(category="flavor")
    assert tuple(state["CATEGORY_METADATA"]) == (
        "DY_ALL",
        "DY_ENRICHED",
        "DY_ZEE",
        "DY_ZMM",
        "DY_ENRICHED_ZEE",
        "DY_ENRICHED_ZMM",
        "ZZCR_ALL",
        "ZZCR_4E",
        "ZZCR_4MU",
        "ZZCR_2E2MU",
        "SR_ALL",
        "SR_XSF",
        "SR_XDF",
        "SR_4E",
        "SR_4MU",
        "SR_2E2MU",
        "SR_3E1MU",
        "SR_1E3MU",
    )
    assert not any(
        "XDF" in name for name in state["CATEGORY_METADATA"] if name.startswith("ZZCR")
    )
    assert "X_isSF" in state["cuts"]["ZZCR"]["expr"]


def test_stream_is_not_flavor_cartesian(load_state):
    state = load_state(category="stream")
    names = tuple(state["CATEGORY_METADATA"])
    assert len(names) == 16
    assert not any("ZEE" in name or "ZMM" in name or "XSF" in name for name in names)


def test_trigger_profile_is_bounded(load_state):
    state = load_state(category="trigger")
    assert len(state["CATEGORY_METADATA"]) == 24
    assert all(item["display_label"] for item in state["CATEGORY_METADATA"].values())
    assert all(
        "triggerFamilyPriority ==" in item["split_expression"]
        for name, item in state["CATEGORY_METADATA"].items()
        if "TRGPRIO" in name
    )
    assert not any(
        item["split_expression"] in ("Trigger_ElMu", "Trigger_sngMu")
        for item in state["CATEGORY_METADATA"].values()
    )


def test_run_stability_adds_direct_routed_trigger_families_and_paths(load_state):
    metadata = load_state(category="standard", analysis_pass="RUN_STABILITY")[
        "CATEGORY_METADATA"
    ]
    assert len(metadata) == 48
    assert {
        "DY_TRGFAM_ELMU",
        "DY_TRGFAM_SINGLEMU",
        "DY_TRGFAM_DOUBLEMU",
        "DY_TRGFAM_SINGLEEL",
        "DY_TRGFAM_DOUBLEEL",
        "DY_HLT_MU23_ELE12",
        "DY_HLT_MU12_ELE23",
        "DY_HLT_MU8_ELE23",
        "DY_HLT_MU17_MU8",
        "DY_HLT_ISOMU24",
        "DY_HLT_ELE23_ELE12",
        "DY_HLT_ELE30",
    } <= set(metadata)
    single_mu = metadata["DY_TRGFAM_SINGLEMU"]
    assert single_mu["split_expression"] == "Trigger_sngMu"
    assert single_mu["run_stability_luminosity_source"] == "trigger_sngmu"
    iso_mu = metadata["DY_HLT_ISOMU24"]
    assert iso_mu["split_expression"] == "HLT_IsoMu24"
    assert iso_mu["run_stability_luminosity_source"] == "hlt_isomu24"
    assert not iso_mu["is_exclusive_within_family"]


def test_standard_projection_inventory_and_metadata(load_state):
    state = load_state(category="standard")
    metadata = state["CATEGORY_METADATA"]
    assert len(metadata) == 47
    assert sum(name.startswith("DY_") for name in metadata) == 24
    assert sum(name.startswith("ZZCR_") for name in metadata) == 12
    assert sum(name.startswith("SR_") for name in metadata) == 11
    for item in metadata.values():
        assert item["view_type"] in {
            "inclusive",
            "flavor",
            "stream",
            "stream_flavor",
            "trigger",
            "debug",
        }
        assert item["partition_family"]
        assert isinstance(item["is_exclusive_within_family"], bool)
        assert isinstance(item["is_overlapping_projection"], bool)
        assert item["diagnostic_purpose"]


def test_detailed_adds_only_curated_sr_stream_x_flavor(load_state):
    standard = load_state(category="standard")
    detailed = load_state(category="detailed")
    added = set(detailed["CATEGORY_METADATA"]) - set(standard["CATEGORY_METADATA"])
    assert added == {
        f"SR_STREAM_{stream}_{flavor}"
        for stream in ("MUONEG", "MUON", "EGAMMA")
        for flavor in ("XSF", "XDF")
    }


@pytest.mark.parametrize("analysis_pass", ("ALL", "ZPARENT", "FOURL_BASE", "CONTROL"))
def test_debug_requires_explicit_large_plan(load_state, analysis_pass):
    with pytest.raises(RuntimeError, match="ALLOW_LARGE_PLAN"):
        load_state(category="debug", analysis_pass=analysis_pass)
    state = load_state(
        category="debug", analysis_pass=analysis_pass, ALLOW_LARGE_PLAN="1"
    )
    assert state["CATEGORY_METADATA"]


@pytest.mark.parametrize(
    ("analysis_pass", "regions", "correction"),
    (
        ("ZPARENT", ("DY",), "SelectedLeptonSF_Z*TriggerSF_Z"),
        ("FOURL_BASE", ("FOURL",), "SelectedLeptonSF_ZX*TriggerSF_ZX"),
        (
            "CONTROL",
            ("ZZCR", "SR"),
            "SelectedLeptonSF_ZX*TriggerSF_ZX*BTagVetoSF",
        ),
    ),
)
def test_focused_pass_places_correction_in_sample_weight(
    load_state, analysis_pass, regions, correction
):
    state = load_state(analysis_pass=analysis_pass)
    assert tuple(state["cuts"]) == regions
    assert state["preselections"] == state["PRESELECTION"]
    for category in state["CATEGORY_METADATA"].values():
        assert category["category_weight_factor"] == "1.f"
        assert correction in category["sample_base_mc_weight"]
        assert category["full_nominal_mc_weight"].count(correction) == 1


def test_enriched_dy_uses_signal_z_window_as_overlapping_inclusive_view(load_state):
    state = load_state(category="standard")
    enriched = state["CATEGORY_METADATA"]["DY_ENRICHED"]
    zzcr = state["CATEGORY_METADATA"]["ZZCR_ALL"]
    sr = state["CATEGORY_METADATA"]["SR_ALL"]

    assert enriched["display_label"] == "Inclusive Z/DY: Enriched DY"
    assert enriched["split_expression"] == "abs(Z0_mass - 91.1876) < 15."
    assert enriched["split_expression"] in zzcr["parent_expression"]
    assert enriched["split_expression"] in sr["parent_expression"]
    assert enriched["view_type"] == "inclusive"
    assert enriched["partition_family"] == "DY:signal_z_window_projection"
    assert not enriched["is_exclusive_within_family"]
    assert enriched["is_overlapping_projection"]


def test_ordered_two_lepton_pt_requirement_is_attached_only_to_dy_registry(load_state):
    state = load_state(category="detailed")
    assert state["cuts"]["DY"]["expr"].endswith("&& Passes2lOrderedPt")
    assert "Passes2lOrderedPt" not in state["cuts"]["ZZCR"]["expr"]
    assert "Passes2lOrderedPt" not in state["cuts"]["SR"]["expr"]
    for category in state["CATEGORY_METADATA"].values():
        if category["physics_region"] == "DY":
            assert "Passes2lOrderedPt" in category["parent_expression"]
        else:
            assert "Passes2lOrderedPt" not in category["parent_expression"]

    fourl = load_state(category="minimal", analysis_pass="FOURL_BASE")
    assert tuple(fourl["cuts"]) == ("FOURL",)
    assert "Passes2lOrderedPt" not in fourl["cuts"]["FOURL"]["expr"]


@pytest.mark.parametrize(
    ("profile", "expected_ordinary"),
    (
        ("standard", 11),
        ("flavor", 2),
        ("stream", 3),
        ("trigger", 5),
        ("detailed", 11),
        ("debug", 16),
    ),
)
def test_enriched_dy_mirrors_every_ordinary_dy_subcategory(
    load_state, profile, expected_ordinary
):
    extra = {"ALLOW_LARGE_PLAN": "1"} if profile == "debug" else {}
    metadata = load_state(category=profile, **extra)["CATEGORY_METADATA"]
    ordinary = {
        name: item
        for name, item in metadata.items()
        if name.startswith("DY_")
        and name not in ("DY_ALL", "DY_ENRICHED")
        and not name.startswith("DY_ENRICHED_")
    }
    assert len(ordinary) == expected_ordinary
    for name, item in ordinary.items():
        enriched_name = name.replace("DY_", "DY_ENRICHED_", 1)
        enriched = metadata[enriched_name]
        assert enriched["split_expression"] == (
            f"({metadata['DY_ENRICHED']['split_expression']})"
            f" && ({item['split_expression']})"
        )
        assert enriched["view_type"] == item["view_type"]
        assert enriched["is_exclusive_within_family"] == (
            item["is_exclusive_within_family"]
        )
        assert enriched["partition_family"].startswith("DY:enriched:")
        assert enriched["category_weight_factor"] == item["category_weight_factor"]


def test_full_cut_is_mechanical(load_state):
    state = load_state(category="flavor")
    item = state["CATEGORY_METADATA"]["ZZCR_4E"]
    assert item["full_cut_expression"] == (
        f"({state['preselections']}) && ({item['parent_expression']})"
        f" && ({item['split_expression']})"
    )


def test_selected_pair_low_mass_veto_is_physical_four_lepton_only(load_state):
    state = load_state(category="minimal")
    dy = state["cuts"]["DY"]["expr"]
    zzcr = state["cuts"]["ZZCR"]["expr"]
    sr = state["cuts"]["SR"]["expr"]
    assert "minSelectedPairMass > 12." not in dy
    assert "minSelectedPairMass > 12." in zzcr
    assert "minSelectedPairMass > 12." in sr
    assert "Z0_mass > 12." not in zzcr
    assert "Z0_mass > 12." not in sr
    assert "abs(Z0_mass - 91.1876) < 15." in zzcr
    assert "abs(Z0_mass - 91.1876) < 15." in sr


def test_an2019_238_region_edges_remain_exact(load_state):
    state = load_state(category="minimal")
    zzcr = state["cuts"]["ZZCR"]["expr"]
    sr = state["cuts"]["SR"]["expr"]
    assert "X_isSF && X_mass > 75. && X_mass < 105. && PuppiMET_pt < 35." in zzcr
    assert (
        "X_isSF && X_mass > 10. && X_mass < 65."
        " && PuppiMET_pt > 35. && m4l > 140." in sr
    )
    assert "X_isDF && X_mass > 10. && X_mass < 70. && PuppiMET_pt > 20." in sr


def test_category_budget_fails_closed(load_state):
    with pytest.raises(RuntimeError, match="MAX_CATEGORIES"):
        load_state(category="trigger", MAX_CATEGORIES="3")
