import cuts
import variables


def test_default_plan_is_sparse_histogram_only_and_within_budget():
    assert len(cuts.cuts) == 54
    assert len(cuts.cuts) <= 60
    assert variables.HISTOGRAM_ACTION_COUNT == 295
    assert variables.HISTOGRAM_ACTION_COUNT <= 300
    assert not any("tree" in definition for definition in variables.variables.values())
    assert (
        sum(map(len, variables.CATEGORY_VARIABLES.values()))
        == variables.HISTOGRAM_ACTION_COUNT
    )


def test_every_histogram_axis_uses_uniform_binning():
    for name, definition in variables.variables.items():
        configured_range = definition["range"]
        assert isinstance(configured_range, tuple), name
        assert len(configured_range) == 3, name
        bins, low, high = configured_range
        assert isinstance(bins, int) and bins > 0, name
        assert low < high, name


def test_dy_axes_are_finer_than_four_lepton_axes():
    def definition(category, observable):
        return next(
            item
            for item in variables.variables.values()
            if item.get("outputName") == observable and category in item["cuts"]
        )

    for observable in ("z_mass", "z_pt", "z_phi_eta_star", "PuppiMET_pt"):
        zz = definition("S0_ZZCR", observable)
        dy = definition("D1_DY_ALL_CURRENT", observable)
        assert zz["resolutionClass"] == "coarse"
        assert dy["resolutionClass"] == "fine"
        assert dy["range"][0] > zz["range"][0]


def test_compact_physics_binning_contract():
    expected_fine = {
        "z_mass": (60, 30.0, 150.0),
        "z_pt": (70, 0.0, 140.0),
        "z_phi_eta_star": (50, 0.0, 0.5),
        "z_lepton_lead_pt": (40, 0.0, 100.0),
        "z_lepton_sublead_pt": (40, 0.0, 100.0),
        "z_lepton_lead_abs_eta": (50, 0.0, 2.5),
        "PuppiMET_pt": (40, 0.0, 100.0),
        "PV_npvsGood": (80, 0.0, 80.0),
    }
    expected_coarse = {
        "z_mass": (14, 75.0, 110.0),
        "z_pt": (7, 0.0, 140.0),
        "z_phi_eta_star": (10, 0.0, 0.5),
        "PuppiMET_pt": (20, 0.0, 100.0),
        "x_mass": (12, 60.0, 120.0),
        "x_pt": (7, 0.0, 140.0),
        "zx_mass": (22, 160.0, 600.0),
        "zx_min_pair_mass": (15, 0.0, 60.0),
        "zx_lepton_rank1_pt": (15, 0.0, 150.0),
    }

    def definition(category, name):
        return next(
            item
            for item in variables.variables.values()
            if item.get("outputName") == name and category in item["cuts"]
        )

    flavor_leaf_observables = {
        "z_lepton_lead_pt",
        "z_lepton_sublead_pt",
        "z_lepton_lead_abs_eta",
        "PV_npvsGood",
    }
    for name, configured_range in expected_fine.items():
        category = (
            "D1_DY_ALL_CURRENT_ZEE"
            if name in flavor_leaf_observables
            else "D1_DY_ALL_CURRENT"
        )
        assert definition(category, name)["range"] == configured_range
    for name, configured_range in expected_coarse.items():
        assert definition("S0_ZZCR", name)["range"] == configured_range

    assert definition("N1_NO_ZWINDOW", "z_mass")["range"] == (24, 30.0, 150.0)
    assert definition("S7_FOURL_BRIDGE", "x_mass")["range"] == (20, 0.0, 200.0)
    assert definition("N1_NO_XMASS", "x_mass")["range"] == (20, 0.0, 200.0)
    assert definition("S7_FOURL_BRIDGE", "zx_mass")["range"] == (26, 80.0, 600.0)
    assert definition("S0_ZZCR_4E", "zx_mass")["range"] == (11, 160.0, 600.0)
    assert definition("S7_FOURL_BRIDGE_4E", "zx_mass")["range"] == (13, 80.0, 600.0)
    assert (
        definition("S0_ZZCR", "x_pt")["range"] == definition("S0_ZZCR", "z_pt")["range"]
    )
