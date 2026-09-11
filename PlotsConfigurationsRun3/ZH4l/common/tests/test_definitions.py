"""Definition graphs and synthetic object-policy checks."""

import pytest

from common.definitions import Analysis
from common.observables import OBSERVABLES, select_observables
from common.presets import nominal_pairs
from common.eras import load_selected_era


def _source(analysis):
    return analysis.source(
        "lep",
        "lepton",
        {
            "pt": "pt",
            "eta": "eta",
            "phi": "phi",
            "pdg_id": "pdg",
            "electron_tight": "tight",
            "muon_tight": "tight",
            "electron_sf_tight": "sf",
            "muon_sf_tight": "sf",
        },
        lineage="synthetic mechanics fixture",
    )


def test_lazy_definitions_preserve_independent_views_and_weight_inheritance(ROOT):
    a = Analysis()
    source = _source(a)
    pool = a.view("pool", source, electron_wp="tight", muon_wp="tight")
    z = a.pair("z", pool, min_pt=(25, 10))
    x = a.pair("x", pool, policy="highest_pt", min_pt=(10, 10), flavor="any", exclude=z)
    z_mass = a.pair_observable("z_mass", z, "mass")
    a.column("unused_payload", "missing_input")
    sf_z = a.lepton_sf("sf_lepton_z", z)
    sf_x = a.lepton_sf("sf_lepton_x", x)
    recipe = a.weight("nominal", sf_z, sf_x)
    region = a.region("selected", str(z.valid), dependencies=(z.valid,), weight=recipe)
    child = a.region("child", "true", parent=region)
    assert child.weight is recipe
    a.histogram("mass", z_mass, (0, 50, 100, 150), regions=[child])
    a.tree(
        "events",
        {"mass": z_mass, "z": z.indices, "x": x.indices},
        regions=[child],
        weight=recipe,
    )
    plan = a.compile()
    assert "unused_payload" not in plan["aliases"]
    frame = ROOT.RDataFrame(1)
    for name, expr in {
        "pt": "ROOT::RVecF{45.6f,45.6f,30.f,20.f,9.f}",
        "eta": "ROOT::RVecF(5,0.f)",
        "phi": "ROOT::RVecF{0.f,3.14159265f,0.5f,2.5f,1.f}",
        "pdg": "ROOT::RVecI{-11,11,-13,13,11}",
        "tight": "ROOT::RVecB{true,true,true,true,false}",
        "sf": "ROOT::RVecF{2.f,3.f,4.f,5.f,6.f}",
        "weight": "2.0",
    }.items():
        frame = frame.Define(name, expr)
    for name, definition in plan["aliases"].items():
        for line in definition.get("linesToAdd", ()):
            assert ROOT.gInterpreter.Declare(line)
        frame = frame.Define(name, definition["expr"])
    row = frame.AsNumpy(["z_lepton_index", "x_lepton_index", "nominal"])
    assert list(row["z_lepton_index"][0]) == [0, 1]
    assert list(row["x_lepton_index"][0]) == [2, 3]
    assert row["nominal"][0] == 240.0
    with pytest.raises(ValueError, match="twice"):
        a.weight("double", sf_z, sf_z)


def test_z_only_and_unrequested_outputs_do_not_require_x_or_corrections(monkeypatch):
    monkeypatch.setenv("ERA", "2024")
    monkeypatch.delenv("YEAR", raising=False)
    _, era, _ = load_selected_era()
    a = Analysis()
    z, x = nominal_pairs(a, era, with_x=False)
    assert x is None
    mass = a.pair_observable("mass", z, "mass")
    region = a.region("zregion", str(z.valid), dependencies=(z.valid,))
    a.histogram("mass_hist", mass, (0, 50, 100), regions=[region])
    unused = a.column("tree_only", "unavailable_branch")
    a.tree("tree", {"extra": unused}, regions=[region])
    plan = a.compile(mode="histograms")
    source = repr(plan)
    assert "tree_only" not in source and "unavailable_branch" not in source
    assert "TotSF" not in source and "btag" not in source and "GenPart" not in source


def test_sort_union_and_quartet_policy_preserve_original_indices(ROOT):
    a = Analysis()
    source = _source(a)
    ordered = a.view(
        "ordered",
        source,
        f"{source['pt']}>10.f",
        dependencies=(source["pt"],),
        order="pt",
        electron_wp="tight",
        muon_wp="tight",
    )
    quartet = a.quartet("quartet", ordered)
    union = a.union("union", ordered, quartet)
    region = a.region("all", "true")
    a.tree(
        "events",
        {"order": ordered.indices, "quartet": quartet.indices, "union": union.indices},
        regions=[region],
    )
    frame = ROOT.RDataFrame(1).Define("pt", "ROOT::RVecF{12.f,40.f,8.f,30.f,20.f,35.f}")
    for name, cfg in a.compile()["aliases"].items():
        for line in cfg.get("linesToAdd", ()):
            assert ROOT.gInterpreter.Declare(line)
        frame = frame.Define(name, cfg["expr"])
    values = frame.AsNumpy([str(v.indices) for v in (ordered, quartet, union)])
    assert list(values[str(ordered.indices)][0]) == [1, 5, 3, 4, 0]
    assert list(values[str(quartet.indices)][0]) == [1, 5, 3, 4]
    assert list(values[str(union.indices)][0]) == [1, 5, 3, 4, 0]


def test_definitions_and_axes_cannot_overwrite_each_other():
    a = Analysis()
    a.column("value", "1.f")
    with pytest.raises(ValueError, match="Conflicting"):
        a.column("value", "2.f")
    axes = select_observables("z_mass")
    axes["z_mass"]["range"][0][0] = -1
    assert OBSERVABLES["z_mass"]["range"][0][0] == 30


def test_preselection_dependencies_and_selection_boundaries(ROOT):
    from common.selections import window, ordered_pt, all_of

    a = Analysis()
    pool = a.view("pool", _source(a))
    pt = ordered_pt(a, "event_pass_pt", pool, (25.0, 10.0))
    scalar = a.column("mass", "91.f")
    mass = window(a, "z_pass_mass", scalar, 75.0, 105.0)
    preselection = all_of(a, "event_pass_preselection", pt, mass)
    region = a.region("all", "true")
    a.histogram("mass", scalar, (75, 105), regions=[region])
    compiled = a.compile(preselections=preselection)
    assert str(pt) in compiled["aliases"]
    assert str(preselection) in compiled["aliases"]
    frame = ROOT.RDataFrame(2).Define(
        "pt", "rdfentry_ == 0 ? ROOT::RVecF{25.f,15.f} : ROOT::RVecF{26.f,15.f}"
    )
    for name, cfg in compiled["aliases"].items():
        for line in cfg.get("linesToAdd", ()):
            assert ROOT.gInterpreter.Declare(line)
        frame = frame.Define(name, cfg["expr"])
    assert list(frame.AsNumpy([str(pt)])[str(pt)]) == [False, True]


def test_different_working_points_keep_independent_correction_targets():
    a = Analysis()
    source = a.source(
        "leptons",
        "lepton",
        {
            "pt": "pt",
            "eta": "eta",
            "phi": "phi",
            "pdg_id": "pdg",
            "electron_tight": "tight",
            "muon_tight": "tight",
            "electron_loose": "loose",
            "muon_loose": "loose",
            "electron_sf_tight": "sf_tight",
            "muon_sf_tight": "sf_tight",
            "electron_sf_loose": "sf_loose",
            "muon_sf_loose": "sf_loose",
        },
        lineage="synthetic WP fixture",
    )
    z = a.pair("z", a.view("z_pool", source, electron_wp="tight", muon_wp="tight"))
    x = a.pair(
        "x", a.view("x_pool", source, electron_wp="loose", muon_wp="loose"), exclude=z
    )
    with pytest.raises(ValueError, match="different-WP"):
        a.lepton_sf("sf_lepton_zx", a.union("zx", z, x))
    sf_z, sf_x = a.lepton_sf("sf_lepton_z", z), a.lepton_sf("sf_lepton_x", x)
    z_weight = a.weight("weight_z", sf_z)
    with pytest.raises(ValueError, match="twice"):
        a.weight("weight_double", sf_z, base=z_weight)
    weight = a.weight("weight_zx", sf_x, base=z_weight)
    assert weight.factors == (sf_z, sf_x)
    other = a.source(
        "shifted", "lepton", {"pt": "shifted_pt"}, lineage="different kinematics"
    )
    with pytest.raises(ValueError, match="kinematic"):
        a.union("invalid_union", z, a.view("shifted", other))
