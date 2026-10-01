"""Software regressions using synthetic NanoAOD arrays and real ROOT/mRDF."""

import pytest


ERA = "Full2024v15"
CORE = ["pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx"]


@pytest.fixture(scope="module")
def root():
    return pytest.importorskip("ROOT")


def _rows(frame, columns):
    arrays = frame.AsNumpy(columns)
    return [
        {
            name: value.tolist() if hasattr(value, "tolist") else value
            for name, value in ((name, arrays[name][i]) for name in columns)
        }
        for i in range(len(arrays[columns[0]]))
    ]


@pytest.fixture(scope="module")
def selected(root):
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.modules.LeptonMaker import LeptonMaker
    from mkShapesRDF.processor.modules.LeptonSel import LeptonSel

    electron = {
        "eta": 0.5,
        "phi": 0.3,
        "pdgId": 11,
        "cutBased": 3,
        "convVeto": True,
        "dxy": 0.001,
        "dz": 0.001,
        "sieie": 0.01,
        "eInvMinusPInv": 0.001,
        "mvaIso_WP90": True,
        "pfRelIso03_all": 0.02,
        "promptMVA": 0.95,
    }
    muon = {
        "eta": 0.4,
        "phi": 0.2,
        "pdgId": 13,
        "tightId": True,
        "dxy": 0.001,
        "dz": 0.001,
        "pfRelIso04_all": 0.02,
        "pfIsoId": 4,
        "pnScore_prompt": 0.995,
        "pnScore_tau": 0.001,
        "promptMVA": 0.95,
    }

    def e(pt, **overrides):
        return dict(electron, pt=pt, **overrides)

    def m(pt, **overrides):
        return dict(muon, pt=pt, **overrides)

    def recipe_only(pt):
        return e(pt, mvaIso_WP90=False, promptMVA=0.0)

    # Leading and interleaved rejection; low-pT objects remain in the hygiene
    # collection. Cases 1/2 bracket testrecipes' strict Electron_pt > 10 cut.
    cases = [
        (
            [
                e(80, dxy=0.3),
                recipe_only(30),
                e(20, promptMVA=0.5),
                recipe_only(10),
                e(5),
            ],
            [m(40), m(12, tightId=False)],
        ),
        ([recipe_only(20), recipe_only(10)], []),
        ([recipe_only(20), recipe_only(10.001)], []),
        ([e(40), e(30, dxy=0.3)], []),
        ([e(20, dxy=0.3)], []),
        ([e(20)], [m(30)]),
    ]
    frame = mRDF().readRDF(len(cases)).Define("case_id", "int(rdfentry_)")
    for index, (flavor, defaults) in enumerate(
        [("Electron", electron), ("Muon", muon)]
    ):
        frame = frame.Define(
            "n" + flavor,
            "ROOT::RVecI{"
            + ",".join(str(len(c[index])) for c in cases)
            + "}[rdfentry_]",
        )
        for field, default in dict(defaults, pt=0.0).items():
            if isinstance(default, bool):
                kind, render = "B", lambda value: str(value).lower()
            elif isinstance(default, int):
                kind, render = "I", str
            else:
                kind, render = "F", lambda value: repr(float(value)) + "f"
            literals = [
                "ROOT::RVec"
                + kind
                + "{"
                + ",".join(render(obj[field]) for obj in c[index])
                + "}"
                for c in cases
            ]
            expression = (
                " ".join(
                    f"if (rdfentry_ == {i}) return {literal};"
                    for i, literal in enumerate(literals[:-1])
                )
                + f" return {literals[-1]};"
            )
            frame = frame.Define(flavor + "_" + field, expression)
    values = []
    before = LeptonMaker().runModule(frame, values)
    after = LeptonSel("Loose", 1, ERA).runModule(before, values)
    return before, after


def test_all_tight_vectors_and_isloose_follow_retained_indices(selected):
    from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP

    after = selected[1]
    names = [
        f"Lepton_isTight{flavor}_{wp}"
        for flavor, registry in [("Electron", ElectronWP), ("Muon", MuonWP)]
        for wp in registry[ERA]["TightObjWP"]
    ]
    rows = _rows(after.df, ["case_id", "Lepton_pt", "isLoose"] + names)
    assert [row["case_id"] for row in rows] == [0, 1, 2, 3, 5]
    expected_electron = {
        "wp90iso": [False, False, True, False, True],
        "testrecipes": [False, True, True, False, False],
        "mvaWinter22V2Iso_WP90": [False, False, True, False, True],
        "mvaWinter22V2Iso_WP90_tthMVA_Run3": [False, False, False, False, True],
        "mvaWinter22V2Iso_WP90_tthMVA_HWW": [False, False, True, False, True],
        "cutBased_MediumID_tthMVA_Run3": [False, False, False, False, True],
        "cutBased_MediumID_tthMVA_HWW": [False, False, True, False, True],
    }
    assert rows[0]["Lepton_pt"] == [40, 30, 20, 10, 5]
    for row in rows:
        assert row["isLoose"] == [True] * len(row["Lepton_pt"])
        for name in names:
            assert len(row[name]) == len(row["Lepton_pt"]), name
    for wp, expected in expected_electron.items():
        assert rows[0][f"Lepton_isTightElectron_{wp}"] == expected
    for wp in MuonWP[ERA]["TightObjWP"]:
        assert rows[0][f"Lepton_isTightMuon_{wp}"] == [True, False, False, False, False]
    recipe = "Lepton_isTightElectron_testrecipes"
    assert rows[1][recipe] == [True, False]
    assert rows[2][recipe] == [True, True]
    for wp in ElectronWP[ERA]["TightObjWP"]:
        assert rows[-1][f"Lepton_isTightElectron_{wp}"] == [False, True]
    for wp in MuonWP[ERA]["TightObjWP"]:
        assert rows[-1][f"Lepton_isTightMuon_{wp}"] == [True, False]


def test_core_raw_and_vetolepton_columns_survive_full_snapshot(
    selected, tmp_path, root
):
    before, after = selected
    output = tmp_path / "all_selection_columns.root"
    columns = sorted(after.GetColumnNames())
    after.df.Snapshot("Events", str(output), columns)
    reopened = root.RDataFrame("Events", str(output))
    assert set(map(str, reopened.GetColumnNames())) == set(columns)
    rows = _rows(reopened, ["case_id"] + ["Lepton_" + prop for prop in CORE])
    assert rows[0]["Lepton_electronIdx"] == [-1, 1, 2, 3, 4]
    assert rows[0]["Lepton_muonIdx"] == [0, -1, -1, -1, -1]
    assert rows[0]["Lepton_pdgId"] == [13, 11, 11, 11, 11]
    assert rows[0]["Lepton_eta"] == pytest.approx([0.4, 0.5, 0.5, 0.5, 0.5])
    assert rows[0]["Lepton_phi"] == pytest.approx([0.2, 0.3, 0.3, 0.3, 0.3])
    preserved = [
        col for col in columns if col.startswith(("Electron_", "Muon_", "VetoLepton_"))
    ]
    original = {r["case_id"]: r for r in _rows(before.df, ["case_id"] + preserved)}
    for row in _rows(reopened, ["case_id"] + preserved):
        assert row == original[row["case_id"]]
    for row in _rows(
        reopened,
        ["Lepton_pt", "isLoose"]
        + [name for name in columns if name.startswith("Lepton_isTight")],
    ):
        assert all(len(value) == len(row["Lepton_pt"]) for value in row.values())


def test_l2tight_guards_short_collections_before_evaluating_flags(root):
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.modules.L2TightSelection import L2TightSelection

    module = L2TightSelection(ERA)
    frame = mRDF().readRDF(3).Define("Lepton_pt", "ROOT::RVecF(rdfentry_, 20.f)")
    for flavor, registry in [("Electron", module.ElectronWP), ("Muon", module.MuonWP)]:
        for wp in registry[ERA]["TightObjWP"]:
            frame = frame.Define(
                f"Lepton_isTight{flavor}_{wp}",
                'if (Lepton_pt.size() < 2) throw std::runtime_error("unguarded tight access");'
                " return ROOT::RVecB(Lepton_pt.size(), true);",
            )
    assert module.runModule(frame, []).Count().GetValue() == 1


def test_l2tight_retains_every_configured_wp_in_both_slots(root):
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.modules.L2TightSelection import L2TightSelection

    module = L2TightSelection(ERA)
    names = [
        f"Lepton_isTight{flavor}_{wp}"
        for flavor, registry in [
            ("Electron", module.ElectronWP),
            ("Muon", module.MuonWP),
        ]
        for wp in registry[ERA]["TightObjWP"]
    ]
    # Each row passes through one WP alone in both slots; the last row fails.
    frame = mRDF().readRDF(len(names) + 1).Define("Lepton_pt", "ROOT::RVecF{20.f,15.f}")
    for i, name in enumerate(names):
        frame = frame.Define(name, f"ROOT::RVecB(2, rdfentry_ == {i})")
    assert module.runModule(frame, []).Count().GetValue() == len(names)


def test_l2tight_uses_retained_flags_and_strict_testrecipes_boundary(selected):
    from mkShapesRDF.processor.modules.L2TightSelection import L2TightSelection

    result = L2TightSelection(ERA).runModule(selected[1], [])
    assert [row["case_id"] for row in _rows(result.df, ["case_id"])] == [0, 2, 5]
