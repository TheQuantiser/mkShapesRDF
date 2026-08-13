import cuts
import variables


def test_default_plan_is_sparse_histogram_only_and_within_budget():
    assert len(cuts.cuts) == 54
    assert len(cuts.cuts) <= 60
    assert variables.HISTOGRAM_ACTION_COUNT == 295
    assert variables.HISTOGRAM_ACTION_COUNT <= 300
    assert not any("tree" in definition for definition in variables.variables.values())
    assert sum(map(len, variables.CATEGORY_VARIABLES.values())) == variables.HISTOGRAM_ACTION_COUNT


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

    for observable in ("Z0_mass", "Z0_pt", "phiEtaStar", "PuppiMET_pt"):
        zz = definition("S0_ZZCR", observable)
        dy = definition("D1_DY_ALL_CURRENT", observable)
        assert zz["resolutionClass"] == "coarse"
        assert dy["resolutionClass"] == "fine"
        assert dy["range"][0] > zz["range"][0]


def test_compact_physics_binning_contract():
    expected_fine = {
        "Z0_mass": (60, 30.0, 150.0),
        "Z0_pt": (70, 0.0, 140.0),
        "phiEtaStar": (50, 0.0, 0.5),
        "Z_lead_pt": (40, 0.0, 100.0),
        "Z_sublead_pt": (40, 0.0, 100.0),
        "Z_lead_absEta": (50, 0.0, 2.5),
        "PuppiMET_pt": (40, 0.0, 100.0),
        "PV_npvsGood": (80, 0.0, 80.0),
    }
    expected_coarse = {
        "Z0_mass": (14, 75.0, 110.0),
        "Z0_pt": (7, 0.0, 140.0),
        "phiEtaStar": (10, 0.0, 0.5),
        "PuppiMET_pt": (20, 0.0, 100.0),
        "X_mass": (12, 60.0, 120.0),
        "X_pt": (7, 0.0, 140.0),
        "m4l": (22, 160.0, 600.0),
        "minSelectedPairMass": (15, 0.0, 60.0),
        "selected4lPt1": (15, 0.0, 150.0),
    }

    def definition(category, name):
        return next(
            item for item in variables.variables.values()
            if item.get("outputName") == name and category in item["cuts"]
        )

    flavor_leaf_observables = {
        "Z_lead_pt", "Z_sublead_pt", "Z_lead_absEta", "PV_npvsGood"
    }
    for name, configured_range in expected_fine.items():
        category = "D1_DY_ALL_CURRENT_ZEE" if name in flavor_leaf_observables else "D1_DY_ALL_CURRENT"
        assert definition(category, name)["range"] == configured_range
    for name, configured_range in expected_coarse.items():
        assert definition("S0_ZZCR", name)["range"] == configured_range

    assert definition("N1_NO_ZWINDOW", "Z0_mass")["range"] == (24, 30.0, 150.0)
    assert definition("S7_FOURL_BRIDGE", "X_mass")["range"] == (20, 0.0, 200.0)
    assert definition("N1_NO_XMASS", "X_mass")["range"] == (20, 0.0, 200.0)
    assert definition("S7_FOURL_BRIDGE", "m4l")["range"] == (26, 80.0, 600.0)
    assert definition("S0_ZZCR_4E", "m4l")["range"] == (11, 160.0, 600.0)
    assert definition("S7_FOURL_BRIDGE_4E", "m4l")["range"] == (13, 80.0, 600.0)
    assert definition("S0_ZZCR", "X_pt")["range"] == definition("S0_ZZCR", "Z0_pt")["range"]
