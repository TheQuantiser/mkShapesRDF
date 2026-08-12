def _one_event(ROOT, definitions, results):
    frame = ROOT.RDataFrame(1)
    for name, expression in definitions:
        frame = frame.Define(name, expression)
    for name, expression in results.items():
        frame = frame.Define(name, expression)
    return {
        name: frame.Take["bool" if name.startswith("pass") else "float"](name).GetValue()[0]
        for name in results
    }


def test_zx_candidate_and_boundary_semantics(ROOT):
    result = _one_event(
        ROOT,
        (
            ("pt", "ROOT::RVecF{45.6f,45.6f,30.f,20.f,9.999f}"),
            ("eta", "ROOT::RVecF{0.f,0.f,0.f,0.f,0.f}"),
            ("phi", "ROOT::RVecF{0.f,3.14159265f,0.5f,2.5f,1.f}"),
            ("pdg", "ROOT::RVecI{-11,11,-13,13,11}"),
            ("tight", "ROOT::RVecB{true,true,true,true,false}"),
            ("z", "FourLepton::bestZ0IdxWithID(pt,eta,phi,pdg,tight,tight,2,25.f,10.f)"),
            ("x", "FourLepton::xPairIdxWithID(z,pt,pdg,tight,tight,2,10.f,10.f)"),
        ),
        {
            "z0": "float(z[0])",
            "z1": "float(z[1])",
            "x0": "float(x[0])",
            "x1": "float(x[1])",
            "pass4l": "FourLepton::passesOrdered4lPtThresholdsFromPairs(pt,z,x,25.f,15.f,10.f,10.f)",
            "passVeto5": "FourLepton::fifthLeptonVeto(pt,10.f)",
            "minimum": "FourLepton::minimumSelectedPairMass(pt,eta,phi,pdg,z,x)",
        },
    )
    assert (result["z0"], result["z1"]) == (0.0, 1.0)
    assert (result["x0"], result["x1"]) == (2.0, 3.0)
    assert result["pass4l"]
    assert result["passVeto5"]
    assert result["minimum"] > 0.0


def test_strict_four_lepton_pt_and_inclusive_fifth_veto_boundaries(ROOT):
    result = _one_event(
        ROOT,
        (
            ("idx0", "ROOT::RVecI{0,1}"),
            ("idx1", "ROOT::RVecI{2,3}"),
            ("at", "ROOT::RVecF{25.f,15.1f,10.1f,10.1f}"),
            ("five", "ROOT::RVecF{25.1f,15.1f,10.1f,10.1f,10.f}"),
        ),
        {
            "passAt": "FourLepton::passesOrdered4lPtThresholdsFromPairs(at,idx0,idx1,25.f,15.f,10.f,10.f)",
            "passFive": "FourLepton::fifthLeptonVeto(five,10.f)",
        },
    )
    assert not result["passAt"]
    assert not result["passFive"]


def test_selected_correction_domains_are_explicit_in_alias_sources():
    from common.corrections import build_correction_aliases

    source = __import__("inspect").getsource(build_correction_aliases)
    assert "selectedLeptonSFProduct(Lepton_pdgId,Z_idx" in source
    assert "selectedLeptonSFProduct4(Lepton_pdgId,Z_idx,X_idx" in source
    assert "selectedPairResult" in source and "selectedFourResult" in source
    assert 'aliases["bVeto"]' in source and ",20.f)" in source
