#!/usr/bin/env python3
"""Direct, read-only ROOT displays of fixed central/HWWNano event pairs."""

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import sys
import time

MANIFEST_SHA256 = "c47bc8fde91a4c06aeead3c488115585df85194331d5886024f6f74333d8ee98"
WPS = {
    "Electron": "mvaWinter22V2Iso_WP90_tthMVA_Run3",
    "Muon": "cut_TightID_pfIsoTight_HWW_tthmva_67",
}
NAMED_INPUTS = {
    "Electron": ("pt", "eta", "phi", "charge", "mvaIso_WP90", "convVeto",
                 "pfRelIso03_all", "promptMVA", "dxy", "dz"),
    "Muon": ("pt", "eta", "phi", "charge", "tightId", "pfIsoId",
             "promptMVA", "dxy", "dz"),
}
# Exact cuts-only snapshot, extracted with ast.literal_eval from Full2024v15.
# No alternate WP evaluator: only the two existing named WPs are recomputed.
WP_REVISION = "69ff2dad8ac45c052e0f3364c35317c8ee7c6fa0"
WP_SOURCE = "mkShapesRDF/processor/data/LeptonSel_cfg.py"
WP_SOURCE_SHA256 = "dfe253af96dfa5a1caaff5c6f5e78ce9fc14dc466a7abb6d07db58d8c1d754b2"
WP_DEFINITIONS = {'Electron': {'VetoObjWP': {'HLTsafe': {'True': ['False']}},
              'FakeObjWP': {'HLTsafe': {'ROOT::RVecB (Electron_pt.size(), true)': ['ROOT::VecOps::abs(Electron_eta) '
                                                                                   '< 2.5',
                                                                                   'Electron_cutBased '
                                                                                   '>= 3',
                                                                                   'Electron_convVeto '
                                                                                   '== 1'],
                                        'ROOT::VecOps::abs(Electron_eta)  <= 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                      '< 0.05',
                                                                                      'ROOT::VecOps::abs(Electron_dz)  '
                                                                                      '< 0.1'],
                                        'ROOT::VecOps::abs(Electron_eta)  > 1.479': ['Electron_sieie  '
                                                                                     '< 0.03',
                                                                                     'ROOT::VecOps::abs(Electron_eInvMinusPInv) '
                                                                                     '< 0.014',
                                                                                     'ROOT::VecOps::abs(Electron_dxy) '
                                                                                     '< 0.1',
                                                                                     'ROOT::VecOps::abs(Electron_dz)  '
                                                                                     '< 0.2']}},
              'TightObjWP': {'wp90iso': {'ROOT::RVecB (Electron_pt.size(), true)': ['ROOT::VecOps::abs(Electron_eta) '
                                                                                    '< 2.5',
                                                                                    'Electron_mvaIso_WP90',
                                                                                    'Electron_convVeto']},
                             'testrecipes': {'ROOT::RVecB (Electron_pt.size(), true)': ['Electron_pt>10']},
                             'mvaWinter22V2Iso_WP90': {'ROOT::RVecB (Electron_pt.size(), true)': ['ROOT::VecOps::abs(Electron_eta) '
                                                                                                  '< '
                                                                                                  '2.5',
                                                                                                  'Electron_mvaIso_WP90',
                                                                                                  'Electron_convVeto',
                                                                                                  'Electron_pfRelIso03_all '
                                                                                                  '< '
                                                                                                  '0.06'],
                                                       'ROOT::VecOps::abs(Electron_eta) <= 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                    '< '
                                                                                                    '0.05',
                                                                                                    'ROOT::VecOps::abs(Electron_dz)  '
                                                                                                    '< '
                                                                                                    '0.1'],
                                                       'ROOT::VecOps::abs(Electron_eta) > 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                   '< '
                                                                                                   '0.1',
                                                                                                   'ROOT::VecOps::abs(Electron_dz) '
                                                                                                   '<  '
                                                                                                   '0.2']},
                             'mvaWinter22V2Iso_WP90_tthMVA_Run3': {'ROOT::RVecB (Electron_pt.size(), true)': ['ROOT::VecOps::abs(Electron_eta) '
                                                                                                              '< '
                                                                                                              '2.5',
                                                                                                              'Electron_mvaIso_WP90',
                                                                                                              'Electron_convVeto',
                                                                                                              'Electron_pfRelIso03_all '
                                                                                                              '< '
                                                                                                              '0.06',
                                                                                                              'Electron_promptMVA '
                                                                                                              '> '
                                                                                                              '0.90'],
                                                                   'ROOT::VecOps::abs(Electron_eta) <= 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                                '< '
                                                                                                                '0.05',
                                                                                                                'ROOT::VecOps::abs(Electron_dz)  '
                                                                                                                '< '
                                                                                                                '0.1'],
                                                                   'ROOT::VecOps::abs(Electron_eta) > 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                               '< '
                                                                                                               '0.1',
                                                                                                               'ROOT::VecOps::abs(Electron_dz) '
                                                                                                               '<  '
                                                                                                               '0.2']},
                             'mvaWinter22V2Iso_WP90_tthMVA_HWW': {'ROOT::RVecB (Electron_pt.size(), true)': ['ROOT::VecOps::abs(Electron_eta) '
                                                                                                             '< '
                                                                                                             '2.5',
                                                                                                             'Electron_mvaIso_WP90',
                                                                                                             'Electron_convVeto',
                                                                                                             'Electron_pfRelIso03_all '
                                                                                                             '< '
                                                                                                             '0.06'],
                                                                  'ROOT::VecOps::abs(Electron_eta) <= 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                               '< '
                                                                                                               '0.05',
                                                                                                               'ROOT::VecOps::abs(Electron_dz)  '
                                                                                                               '< '
                                                                                                               '0.1'],
                                                                  'ROOT::VecOps::abs(Electron_eta) > 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                              '< '
                                                                                                              '0.1',
                                                                                                              'ROOT::VecOps::abs(Electron_dz) '
                                                                                                              '<  '
                                                                                                              '0.2'],
                                                                  'Electron_pt <= 20.0': ['Electron_promptMVA '
                                                                                          '> 0.35'],
                                                                  'Electron_pt > 20.0': ['Electron_promptMVA '
                                                                                         '> 0.90']},
                             'cutBased_MediumID_tthMVA_Run3': {'ROOT::RVecB (Electron_pt.size(), true)': ['ROOT::VecOps::abs(Electron_eta) '
                                                                                                          '< '
                                                                                                          '2.5',
                                                                                                          'Electron_cutBased '
                                                                                                          '>= '
                                                                                                          '3',
                                                                                                          'Electron_promptMVA '
                                                                                                          '> '
                                                                                                          '0.90',
                                                                                                          'Electron_convVeto'],
                                                               'ROOT::VecOps::abs(Electron_eta) <= 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                            '< '
                                                                                                            '0.05',
                                                                                                            'ROOT::VecOps::abs(Electron_dz)  '
                                                                                                            '< '
                                                                                                            '0.1'],
                                                               'ROOT::VecOps::abs(Electron_eta) > 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                           '< '
                                                                                                           '0.1',
                                                                                                           'ROOT::VecOps::abs(Electron_dz) '
                                                                                                           '<  '
                                                                                                           '0.2']},
                             'cutBased_MediumID_tthMVA_HWW': {'ROOT::RVecB (Electron_pt.size(), true)': ['ROOT::VecOps::abs(Electron_eta) '
                                                                                                         '< '
                                                                                                         '2.5',
                                                                                                         'Electron_cutBased '
                                                                                                         '>= '
                                                                                                         '3',
                                                                                                         'Electron_convVeto'],
                                                              'ROOT::VecOps::abs(Electron_eta) <= 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                           '< '
                                                                                                           '0.05',
                                                                                                           'ROOT::VecOps::abs(Electron_dz)  '
                                                                                                           '< '
                                                                                                           '0.1'],
                                                              'ROOT::VecOps::abs(Electron_eta) > 1.479': ['ROOT::VecOps::abs(Electron_dxy) '
                                                                                                          '< '
                                                                                                          '0.1',
                                                                                                          'ROOT::VecOps::abs(Electron_dz) '
                                                                                                          '<  '
                                                                                                          '0.2'],
                                                              'Electron_pt <= 20.0': ['Electron_promptMVA '
                                                                                      '> 0.35'],
                                                              'Electron_pt > 20.0': ['Electron_promptMVA '
                                                                                     '> 0.90']}}},
 'Muon': {'VetoObjWP': {'HLTsafe': {'ROOT::RVecB (Muon_pt.size(), true)': ['ROOT::VecOps::abs(Muon_eta) '
                                                                           '< 2.4',
                                                                           'Muon_pt > 10.0']}},
          'FakeObjWP': {'HLTsafe': {'ROOT::RVecB (Muon_pt.size(), true)': ['ROOT::VecOps::abs(Muon_eta) '
                                                                           '< 2.4',
                                                                           'Muon_tightId',
                                                                           'ROOT::VecOps::abs(Muon_dz) '
                                                                           '< 0.1',
                                                                           'Muon_pfRelIso04_all < '
                                                                           '0.4'],
                                    'Muon_pt <= 20.0': ['ROOT::VecOps::abs(Muon_dxy) < 0.01'],
                                    'Muon_pt > 20.0': ['ROOT::VecOps::abs(Muon_dxy) < 0.02']}},
          'TightObjWP': {'cut_TightID_POG': {'ROOT::RVecB (Muon_pt.size(), true)': ['ROOT::VecOps::abs(Muon_eta) '
                                                                                    '< 2.4',
                                                                                    'Muon_tightId',
                                                                                    'Muon_pt > '
                                                                                    '15.0']},
                         'cut_Tight_HWW': {'ROOT::RVecB (Muon_pt.size(), true)': ['ROOT::VecOps::abs(Muon_eta) '
                                                                                  '< 2.4',
                                                                                  'Muon_tightId',
                                                                                  'ROOT::VecOps::abs(Muon_dz) '
                                                                                  '< 0.1',
                                                                                  'Muon_pfIsoId >= '
                                                                                  '4'],
                                           'Muon_pt <= 20.0': ['ROOT::VecOps::abs(Muon_dxy) < '
                                                               '0.01'],
                                           'Muon_pt > 20.0': ['ROOT::VecOps::abs(Muon_dxy) < '
                                                              '0.02']},
                         'cut_TightID_pfIsoTight_HWW_tthmva_67': {'ROOT::RVecB (Muon_pt.size(), true)': ['ROOT::VecOps::abs(Muon_eta) '
                                                                                                         '< '
                                                                                                         '2.4',
                                                                                                         'Muon_tightId',
                                                                                                         'ROOT::VecOps::abs(Muon_dz) '
                                                                                                         '< '
                                                                                                         '0.1',
                                                                                                         'Muon_pfIsoId '
                                                                                                         '>= '
                                                                                                         '4',
                                                                                                         'Muon_promptMVA '
                                                                                                         '> '
                                                                                                         '0.67'],
                                                                  'Muon_pt <= 20.0': ['ROOT::VecOps::abs(Muon_dxy) '
                                                                                      '< 0.01'],
                                                                  'Muon_pt > 20.0': ['ROOT::VecOps::abs(Muon_dxy) '
                                                                                     '< 0.02']},
                         'cut_TightID_pfIsoLoose_HWW_tthmva_67': {'ROOT::RVecB (Muon_pt.size(), true)': ['ROOT::VecOps::abs(Muon_eta) '
                                                                                                         '< '
                                                                                                         '2.4',
                                                                                                         'Muon_tightId',
                                                                                                         'ROOT::VecOps::abs(Muon_dz) '
                                                                                                         '< '
                                                                                                         '0.1',
                                                                                                         'Muon_pfIsoId '
                                                                                                         '>= '
                                                                                                         '2',
                                                                                                         'Muon_promptMVA '
                                                                                                         '> '
                                                                                                         '0.67'],
                                                                  'Muon_pt <= 20.0': ['ROOT::VecOps::abs(Muon_dxy) '
                                                                                      '< 0.01'],
                                                                  'Muon_pt > 20.0': ['ROOT::VecOps::abs(Muon_dxy) '
                                                                                     '< 0.02']},
                         'cut_TightID_pfIsoLoose_HWW_tthmva_HWW': {'ROOT::RVecB (Muon_pt.size(), true)': ['ROOT::VecOps::abs(Muon_eta) '
                                                                                                          '< '
                                                                                                          '2.4',
                                                                                                          'Muon_tightId',
                                                                                                          'ROOT::VecOps::abs(Muon_dz) '
                                                                                                          '< '
                                                                                                          '0.1',
                                                                                                          'Muon_pfIsoId '
                                                                                                          '>= '
                                                                                                          '2'],
                                                                   'Muon_pt <= 20.0': ['ROOT::VecOps::abs(Muon_dxy) '
                                                                                       '< 0.01',
                                                                                       'Muon_promptMVA '
                                                                                       '> 0.20'],
                                                                   'Muon_pt > 20.0': ['ROOT::VecOps::abs(Muon_dxy) '
                                                                                      '< 0.02',
                                                                                      'Muon_promptMVA '
                                                                                      '> 0.67']},
                         'cut_TightID_pfIsoLoose_HWW_PNet': {'ROOT::RVecB (Muon_pt.size(), true)': ['ROOT::VecOps::abs(Muon_eta) '
                                                                                                    '< '
                                                                                                    '2.4',
                                                                                                    'Muon_tightId',
                                                                                                    'ROOT::VecOps::abs(Muon_dz) '
                                                                                                    '< '
                                                                                                    '0.1',
                                                                                                    'Muon_pfIsoId '
                                                                                                    '>= '
                                                                                                    '2',
                                                                                                    '(Muon_pnScore_prompt '
                                                                                                    '+ '
                                                                                                    'Muon_pnScore_tau) '
                                                                                                    '> '
                                                                                                    '0.989'],
                                                             'Muon_pt <= 20.0': ['ROOT::VecOps::abs(Muon_dxy) '
                                                                                 '< 0.01'],
                                                             'Muon_pt > 20.0': ['ROOT::VecOps::abs(Muon_dxy) '
                                                                                '< 0.02']}}}}

# Recorded repaired snapshot evidence; NOT a fresh ROOT read in this inspector.
REPAIR_REVISION = "8d940abcf429f753074121a250db3717434eb2f6"
REPAIR_SOURCE = "PlotsConfigurationsRun3/ZH_4lMET/RunStability/diagnostics/hww_object_associations/repair-witnesses.json"
REPAIR_SOURCE_SHA256 = "1248b7ecac3e2b1f6ccf10ac2a5174ef9e6fe94c8d998ac43a128cce95b260eb"
REPAIRED_OPENING = {'key': [386509, 735, 1539152813],
 'source_entry': 46209,
 'final': {'Lepton_electronIdx': [1, 0],
           'Lepton_eta': [1.73095703125, 0.6126708984375],
           'Lepton_isTightElectron_cutBased_MediumID_tthMVA_HWW': [True, True],
           'Lepton_isTightElectron_cutBased_MediumID_tthMVA_Run3': [True, True],
           'Lepton_isTightElectron_mvaWinter22V2Iso_WP90': [True, True],
           'Lepton_isTightElectron_mvaWinter22V2Iso_WP90_tthMVA_HWW': [True, True],
           'Lepton_isTightElectron_mvaWinter22V2Iso_WP90_tthMVA_Run3': [True, True],
           'Lepton_isTightElectron_testrecipes': [True, True],
           'Lepton_isTightElectron_wp90iso': [True, True],
           'Lepton_isTightMuon_cut_TightID_POG': [False, False],
           'Lepton_isTightMuon_cut_TightID_pfIsoLoose_HWW_PNet': [False, False],
           'Lepton_isTightMuon_cut_TightID_pfIsoLoose_HWW_tthmva_67': [False, False],
           'Lepton_isTightMuon_cut_TightID_pfIsoLoose_HWW_tthmva_HWW': [False, False],
           'Lepton_isTightMuon_cut_TightID_pfIsoTight_HWW_tthmva_67': [False, False],
           'Lepton_isTightMuon_cut_Tight_HWW': [False, False],
           'Lepton_muonIdx': [-1, -1],
           'Lepton_pdgId': [-11, 11],
           'Lepton_phi': [-1.76171875, 1.408203125],
           'Lepton_pt': [39.51831817626953, 38.97809600830078],
           'Lepton_rochesterSF': [1.018836498260498, 0.9983659386634827],
           'isLoose': [1, 1]}}

HWW_ID = {
    "muon_c": ("bcc9d2f0-3579-11f1-a0a2-a4bf01606976", 316341),
    "egamma_c": ("ebce4a80-358e-11f1-aade-3cecef951668", 49200),
    "egamma_i": ("904011a4-359c-11f1-9867-7cc2559e8508", 44596),
    "dy_ee": ("c183f92c-3747-11f1-be55-3cecef0de5e4", 68421),
    "dy_mumu": ("d4c93ad6-37e9-11f1-98cc-3cecef0ddda8", 88692),
}
# Zero-based source/HWW entries, full key, required observed mismatch fields.
CASES = {
    "muon_c": ("muon_c", 234, 65, (379416, 147, 131724611), {"tight"}),
    "egamma_c": ("egamma_c", 20774, 991, (379729, 907, 1396820419), {"tight"}),
    "egamma_i_eta": ("egamma_i", 27025, 1936, (386509, 159, 333332716), {"eta"}),
    "egamma_i_both": ("egamma_i", 46209, 3325, (386509, 735, 1539152813), {"tight", "eta"}),
    "dy_ee_singleton": ("dy_ee", 8, 2, (1, 384532, 2060317109), set()),
    "dy_mumu_singleton": ("dy_mumu", 102, 39, (1, 260002, 1443526295), set()),
    "dy_ee_association": ("dy_ee", 1480, 632, (1, 404199, 2165694222), {"tight"}),
}
TOLERANCE = 1e-6  # Coordinates are the same raw float values, not smeared pT.
UINT64_MASK = (1 << 64) - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def table(headers, rows):
    rows = [[format(value, ".12g") if isinstance(value, float) else str(value)
             for value in row] for row in rows]
    widths = [max([len(header), *(len(row[i]) for row in rows)])
              for i, header in enumerate(headers)]
    print(" | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(" | ".join(value.ljust(w) for value, w in zip(row, widths)))


def vector(tree, name):
    branch = tree.GetBranch(name)
    require(bool(branch), f"Missing required branch: {name}")
    values = getattr(tree, name)
    if branch.GetClassName():
        return list(values)
    leaf = tree.GetLeaf(name)
    require(bool(leaf), f"Missing leaf: {name}")
    if isinstance(values, (bool, int, float, str)):
        require(leaf.GetLen() == 1, f"Unexpected scalar representation: {name}")
        return [values]
    return [values[i] for i in range(leaf.GetLen())]


def key(tree):
    return (int(tree.run), int(tree.luminosityBlock), int(tree.event) & UINT64_MASK)


def cuts(flavor, obj):
    eta, dxy, dz = abs(obj["eta"]), abs(obj["dxy"]), abs(obj["dz"])
    if flavor == "Electron":
        xy_limit, z_limit = (0.05, 0.1) if eta <= 1.479 else (0.1, 0.2)
        return {
            "abs(eta)<2.5": eta < 2.5,
            "mvaIso_WP90": bool(obj["mvaIso_WP90"]),
            "convVeto": bool(obj["convVeto"]),
            "pfRelIso03_all<0.06": obj["pfRelIso03_all"] < 0.06,
            "promptMVA>0.90": obj["promptMVA"] > 0.90,
            f"abs(dxy)<{xy_limit}": dxy < xy_limit,
            f"abs(dz)<{z_limit}": dz < z_limit,
        }
    xy_limit = 0.01 if obj["pt"] <= 20.0 else 0.02
    return {
        "abs(eta)<2.4": eta < 2.4,
        "tightId": bool(obj["tightId"]),
        "abs(dz)<0.1": dz < 0.1,
        "pfIsoId>=4": obj["pfIsoId"] >= 4,
        "promptMVA>0.67": obj["promptMVA"] > 0.67,
        f"abs(dxy)<{xy_limit}": dxy < xy_limit,
    }


def raw(tree, label, verbose=True):
    objects = {}
    for flavor, fields in NAMED_INPUTS.items():
        columns = {field: vector(tree, f"{flavor}_{field}") for field in fields}
        count = len(columns["pt"])
        require(count == int(getattr(tree, "n" + flavor)),
                f"Stored n{flavor} disagrees with raw array length")
        require(all(len(v) == count for v in columns.values()),
                f"Unequal {label} raw {flavor} vector lengths")
        objects[flavor] = [{field: columns[field][i] for field in fields}
                           for i in range(count)]
        require(all(math.isfinite(value) for obj in objects[flavor] for value in obj.values()),
                f"Nonfinite {label} raw {flavor} input")
        if not verbose:
            continue
        print(f"\n{label} raw {flavor}: {count} objects")
        if not count:
            continue
        pdg = 11 if flavor == "Electron" else 13
        table(["index", *fields, "pdgId", "named tight"],
              [[i, *obj.values(), -pdg * int(obj["charge"]), all(cuts(flavor, obj).values())]
               for i, obj in enumerate(objects[flavor])])
        print("Named-WP cuts (evaluated at raw HWW/NanoAOD pT, before correction):")
        table(["index", "cut", "decision"],
              [[i, cut, "PASS" if passed else "FAIL"]
               for i, obj in enumerate(objects[flavor]) for cut, passed in cuts(flavor, obj).items()])
    return objects


def branch_names(tree):
    return {branch.GetName() for branch in tree.GetListOfBranches()}


def printable(value):
    """Preserve bools, integer words and nested values without display truncation."""
    if isinstance(value, (bool, int, float, str)):
        return value
    return [printable(item) for item in value]


def field_values(tree, name):
    values = vector(tree, name)
    leaf = tree.GetLeaf(name)
    kind = leaf.GetTypeName() if leaf else tree.GetBranch(name).GetClassName()
    # PyROOT exposes some byte leaves as one-character strings.
    if kind in ("Char_t", "UChar_t"):
        values = [ord(v) if isinstance(v, str) else int(v) for v in values]
        if kind == "Char_t":
            values = [v - 256 if v >= 128 else v for v in values]
    return [printable(v) for v in values]


def formatted(value):
    if value is None:
        return "UNAVAILABLE"
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, list):
        return "[" + ", ".join(formatted(v) for v in value) + "]"
    return str(value)


def comparison(left, right):
    if left is None or right is None:
        return "UNAVAILABLE (not a false decision)"
    # Scalars are compared according to their type, never by truthiness.
    if isinstance(left, list) or isinstance(right, list):
        if not isinstance(left, list) or not isinstance(right, list):
            return "DIFFERENT TYPE"
        if len(left) != len(right):
            return "DIFFERENT LENGTH"
        return "EQUAL" if all(comparison(a, b) == "EQUAL" for a, b in zip(left, right)) else "DIFFERENT"
    if isinstance(left, bool) or isinstance(right, bool):
        return "EQUAL" if type(left) is type(right) and left == right else "DIFFERENT TYPE/VALUE"
    if isinstance(left, float) or isinstance(right, float):
        if not (math.isfinite(left) and math.isfinite(right)):
            return "NONFINITE (not certified equal)"
        # The two raw collections should contain copied values. Do not hide
        # representable differences with a kinematic-association tolerance.
        return "EQUAL" if left == right else "DIFFERENT, HWW-Central=" + formatted(right - left)
    return "EQUAL" if left == right else "DIFFERENT"


def dependencies(expressions):
    return sorted(set(re.findall(r"\b(?:Electron|Muon)_[A-Za-z0-9_]+", " ".join(expressions))))


def field_group(name):
    """Names choose the section only; every schema-discovered field is included."""
    field = name.lower()
    for group, tokens in (
        ("ID flags and scores", ("mva", "score", "id", "cutbased")),
        ("Isolation", ("iso",)),
        ("Impact parameters", ("dxy", "dz", "sip", "ip3d")),
        ("Conversion and tracking", ("conv", "losthit", "missinghit", "track", "hit", "err", "chi2")),
        ("Shower shape and matching", ("sieie", "hoe", "r9", "einv", "delta", "seed", "scet")),
    ):
        if any(token in field for token in tokens):
            return group
    return "Kinematics, indices and other fields"


def positions(tree, collection, flavor, index):
    return [i for i, raw_index in enumerate(vector(tree, f"{collection}_{flavor.lower()}Idx"))
            if int(raw_index) == index]


def wp_input_text(exprs, index, columns):
    return "; ".join(f"{b}={formatted(columns[b][index]) if b in columns else 'UNAVAILABLE'}"
                     for b in dependencies(exprs)) or "no raw inputs (constant expression)"


def configured_definitions(flavor, ccols, hcols, craw, hraw):
    print(f"\nExact {flavor} Full2024v15 WP definitions and indexed raw inputs:")
    print("Each condition implies the AND of its listed cuts; all implications are ANDed.")
    print("FakeObjWP/HLTsafe supplies Loose hygiene; VetoObjWP is separate. No WgStarObjWP exists in this era.")
    for group, wps in WP_DEFINITIONS[flavor].items():
        for name, conditions in wps.items():
            recomputed = group == "TightObjWP" and name == WPS[flavor]
            print(f"\n{group}/{name}: " + ("RECOMPUTED named WP" if recomputed else "DEFINITION/INPUTS ONLY; not recomputed"))
            for condition, exprs in conditions.items():
                print(f"  IF {condition}")
                for expr in exprs:
                    print(f"    REQUIRE {expr}")
                for i in range(max(len(craw), len(hraw))):
                    for label, cols, objs in [("Central", ccols, craw), ("HWW raw", hcols, hraw)]:
                        inputs = wp_input_text([condition, *exprs], i, cols) if i < len(objs) else "OBJECT UNAVAILABLE"
                        print(f"    {label} raw index {i}: {inputs}")
    print("\nEVERY individual named-WP cut (raw inputs at the pre-correction defining stage):")
    for label, objs in [("Central", craw), ("HWW raw", hraw)]:
        for i, obj in enumerate(objs):
            # Reuse cuts(), the inspector's verified two-WP implementation.
            rows = []
            for expr, passed in cuts(flavor, obj).items():
                inputs = [(name, obj[name]) for name in NAMED_INPUTS[flavor]
                          if name in expr or (name == "eta" and ("dxy" in expr or "dz" in expr))
                          or (flavor == "Muon" and name == "pt" and "dxy" in expr)]
                rows.append([expr, "; ".join(f"{name}={formatted(v)}" for name, v in inputs),
                             "PASS" if passed else "FAIL"])
            print(f"{label} {flavor} raw index {i}; named tight={all(cuts(flavor, obj).values())}")
            table(["cut/threshold", "actual raw inputs", "decision"], rows)


def comprehensive_display(ctree, htree, craw, hraw, case_name):
    cnames, hnames = branch_names(ctree), branch_names(htree)
    if case_name == "egamma_i_both":
        require(vector(htree, "VetoLepton_muonIdx") == [0, -1, -1]
                and vector(htree, "VetoLepton_electronIdx") == [-1, 0, 1], "Opening prefilter identities changed")
        require(vector(htree, "Lepton_electronIdx") == [0, 1], "Opening retained identities changed")
        require(all(all(cuts("Electron", obj).values()) for obj in hraw["Electron"]), "Opening named electron WP changed")
        require(vector(htree, "Lepton_isTightElectron_" + WPS["Electron"]) == [False, True],
                "Opening stored named tight bits changed")
        for i in range(2):
            require(abs(vector(htree, "Lepton_eta")[i] - hraw["Electron"][1-i]["eta"]) <= TOLERANCE
                    and abs(math.remainder(vector(htree, "Lepton_phi")[i] - hraw["Electron"][i]["phi"],
                                           2 * math.pi)) <= TOLERANCE, "Opening coordinate pattern changed")
        require(all(vector(htree, b) == REPAIRED_OPENING["final"][b] for b in ["Lepton_pt", "Lepton_eta"]),
                "Opening historical/repaired pT or eta equality changed")
        print("\nOPENING WITNESS — freshly read historical/raw ROOT values:")
        print("Prefilter order: Muon 0, Electron 0, Electron 1. Muon 0 is absent from retained Lepton.")
        print("Its tightId=False and |dz|>=0.1 fail the configured Loose hygiene; both raw electrons pass the named tight WP.")
        require(not hraw["Muon"][0]["tightId"] and abs(hraw["Muon"][0]["dz"]) >= 0.1,
                "Opening muon hygiene-failure inputs changed")
        print("Retained electron identities [0,1]: stored named tight [False,True], correctly attached [True,True].")
        print("Stored eta follows electron identities [1,0]; stored indices and phi follow [0,1].")
        print("This is DATA: the MC l2tight production gate was NOT applied to this recipe.")
    print(f"\nWP source snapshot: {WP_REVISION}/{WP_SOURCE}; file SHA-256={WP_SOURCE_SHA256}")
    print("A/B: Central and historical RAW Electron/Muon collections (not the retained Lepton collection).")
    print("Raw fields: bool/integer exact, finite floats exact; 17 significant digits; nested values untruncated.")
    printed, raw_differences = 0, 0
    for flavor in NAMED_INPUTS:
        available = sorted(b for b in cnames | hnames if b.startswith(flavor + "_"))
        columns = []
        for tree, names in [(ctree, cnames), (htree, hnames)]:
            cols = {b: field_values(tree, b) for b in available if b in names}
            count = int(getattr(tree, "n" + flavor))
            require(all(len(values) == count for values in cols.values()),
                    f"Non-object/unequal {flavor} branch length; cannot silently assign it to raw objects")
            columns.append(cols)
        ccols, hcols = columns
        annotations = {}
        for group, wps in WP_DEFINITIONS[flavor].items():
            for wp, conditions in wps.items():
                for b in dependencies([x for condition, cuts_ in conditions.items() for x in [condition, *cuts_]]):
                    annotations.setdefault(b, []).append(f"{group}/{wp}")
        print(f"\n{flavor} branch availability inventory: {len(ccols)} Central, {len(hcols)} HWW, {len(available)} union")
        table(["branch", "availability", "configured WP dependencies"],
              [[b, "both" if b in ccols and b in hcols else "Central-only" if b in ccols else "HWW-only",
                ", ".join(annotations.get(b, [])) or "not used by the inspected WP expressions"] for b in available])
        missing = sorted(set(annotations) - (set(ccols) & set(hcols)))
        print("Required by configured WP but unavailable: " + (", ".join(missing) or "NONE"))
        for i in range(max(len(craw[flavor]), len(hraw[flavor]))):
            print(f"\n{flavor} RAW INDEX {i} — Central exists={i < len(craw[flavor])}, HWW exists={i < len(hraw[flavor])}")
            print(f"Historical VetoLepton positions={positions(htree, 'VetoLepton', flavor, i)}; "
                  f"retained Lepton positions={positions(htree, 'Lepton', flavor, i)}")
            for group in dict.fromkeys(field_group(b.split("_", 1)[1]) for b in available):
                print(f"  {group}")
                rows = []
                for b in available:
                    if field_group(b.split("_", 1)[1]) != group:
                        continue
                    c = ccols[b][i] if b in ccols and i < len(ccols[b]) else None
                    h = hcols[b][i] if b in hcols and i < len(hcols[b]) else None
                    status = comparison(c, h)
                    raw_differences += status not in ("EQUAL", "UNAVAILABLE (not a false decision)")
                    rows.append([b, formatted(c), formatted(h), status])
                    printed += 1
                table(["field", "Central raw", "historical HWW raw", "comparison"], rows)
        configured_definitions(flavor, ccols, hcols, craw[flavor], hraw[flavor])
    print(f"\nRAW FIELD COVERAGE: {printed} object/field rows; differences among available common raw values={raw_differences}")
    print("C/D: Historical prefilter VetoLepton and retained Lepton follow below, with their OWN positions.")
    print("Additional complete stored per-lepton fields (including every decision; not presumed aligned):")
    for collection in ["VetoLepton", "Lepton"]:
        n = len(vector(htree, collection + "_pt"))
        table(["branch", "actual length", "collection length", "FULL stored values"],
              [[b, len(field_values(htree, b)), n, formatted(field_values(htree, b))]
               for b in sorted(hnames) if b.startswith(collection + "_")])
    other_decisions = {"isLoose", "isVeto", "isWgs"} | {b for b in hnames if b.startswith("hygiene")}
    for b in sorted(other_decisions):
        values = field_values(htree, b) if b in hnames else None
        print(f"{b}: actual length={len(values) if values is not None else 'UNAVAILABLE'}; values={formatted(values)}")
    print("isLoose in original Loose recipe was formed on the prefilter domain using OR of hygiene masks")
    print("with true defaults for the opposite flavor. Its stored length is evidence, not a guarantee of retained association.")
    configured = ["Lepton_isTight" + flavor + "_" + wp for flavor, groups in WP_DEFINITIONS.items()
                  for wp in groups["TightObjWP"]]
    require(len(configured) == 13, "Pinned tight-WP inventory changed")
    require(all(b in hnames for b in configured), "Missing configured tight-WP vector")
    bits = {b: field_values(htree, b) for b in configured}
    max_slots = max(len(v) for v in bits.values())
    slot_or = [any(bits[b][i] for b in configured) if all(i < len(v) for v in bits.values()) else None
               for i in range(max_slots)]
    print(f"\nAll 13 STORED tight-WP vectors: per-position OR={formatted(slot_or)}")
    print("MC production predicate: OR(electron WPs, muon WPs) at slot 0 AND the OR at slot 1.")
    if len(slot_or) >= 2 and None not in slot_or[:2]:
        print(f"Stored two-position predicate={bool(slot_or[0] and slot_or[1])}; retained nLepton={int(htree.nLepton)}")
    else:
        print("Stored two-position predicate=UNAVAILABLE (no invented out-of-range decision)")
    print("This is a stored-vector diagnostic, not a named-WP recomputation or an applied DATA production skim.")
    if case_name == "egamma_i_both":
        require(tuple(REPAIRED_OPENING["key"]) == key(htree), "Recorded repaired key changed")
        print(f"\nRECORDED REPAIRED COUNTERPART (JSON, NOT freshly read ROOT): {REPAIR_REVISION}/{REPAIR_SOURCE}")
        print(f"Evidence file SHA-256={REPAIR_SOURCE_SHA256}; source entry={REPAIRED_OPENING['source_entry']}")
        table(["field", "historical ROOT (fresh read)", "repaired snapshot (recorded JSON)"],
              [[b, formatted(field_values(htree, b)), formatted(v)] for b, v in REPAIRED_OPENING["final"].items()])
        print("Corrected pT reverses electron order: repaired identities [1,0] follow pT/eta, with phi and bits following too.")
        print("Historical pT/eta match the recorded repaired arrays, but its indices/phi/ID bits do not follow that order.")
        print("Repair restores object identity across fields; it is not merely swapping eta back.")
        print("The exact dirty historical producer operation causing the coordinate error remains unresolved.")


def display(central, hww, case_name, case, comprehensive=False):
    role, source_entry, hww_entry, wanted, expected = case
    ctree, htree = central.Get("Events"), hww.Get("Events")
    for tree, entry in [(ctree, source_entry), (htree, hww_entry)]:
        require(0 <= entry < tree.GetEntries() and tree.GetEntry(entry) > 0,
                f"Cannot read Events entry {entry}")
        require(key(tree) == wanted, f"Wrong key at entry {entry}: {key(tree)} != {wanted}")
    print(f"\n=== CASE {case_name}: key={wanted}, zero-based entries {source_entry} / {hww_entry} ===")
    for label, file, entry in [("CENTRAL", central, source_entry), ("HISTORICAL HWW part0", hww, hww_entry)]:
        print(f"{label}: {file.GetName()}\n  UUID={file.GetUUID().AsString()}, tree=Events, entry={entry}")
    craw, hraw = raw(ctree, "CENTRAL", not comprehensive), raw(htree, "HWW", not comprehensive)
    if comprehensive:
        comprehensive_display(ctree, htree, craw, hraw, case_name)
    differences = []
    for flavor in NAMED_INPUTS:
        require(len(craw[flavor]) == len(hraw[flavor]), f"Raw {flavor} counts differ")
        for i, (cobj, hobj) in enumerate(zip(craw[flavor], hraw[flavor])):
            for field in NAMED_INPUTS[flavor]:
                if cobj[field] != hobj[field]:
                    differences.append([flavor, i, field, cobj[field], hobj[field]])
    print("\nCentral versus HWW raw cut inputs: " + ("EXACTLY EQUAL" if not differences else "DIFFERENCES"))
    if differences:
        table(["flavor", "raw index", "field", "central", "HWW raw"], differences)
    core_fields = ("pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx")
    core = {}
    for collection in ["VetoLepton", "Lepton"]:
        core[collection] = {field: vector(htree, f"{collection}_{field}") for field in core_fields}
        n = len(core[collection]["pt"])
        require(all(len(v) == n for v in core[collection].values()), f"Unequal {collection} core lengths")
        print(f"\nHistorical {collection} collection ({n} slots):")
        table(["slot", *core_fields], [[i, *(core[collection][f][i] for f in core_fields)] for i in range(n)])
    bits = {flavor: vector(htree, "Lepton_isTight" + flavor + "_" + wp) for flavor, wp in WPS.items()}
    print("\nALL stored tight-decision vector lengths (no truncation or repair):")
    bit_names = sorted(b.GetName() for b in htree.GetListOfBranches() if b.GetName().startswith("Lepton_isTight"))
    table(["branch", "length", "stored values"], [[b, len(vector(htree, b)), vector(htree, b)] for b in bit_names])
    leptons = core["Lepton"]
    n = len(leptons["pt"])
    require(int(htree.nLepton) == n, "Stored nLepton disagrees with core arrays")
    observed, rows = set(), []
    for i in range(n):
        e, m = int(leptons["electronIdx"][i]), int(leptons["muonIdx"][i])
        require((e >= 0) != (m >= 0), f"Ambiguous flavor at retained slot {i}")
        flavor, index = ("Electron", e) if e >= 0 else ("Muon", m)
        require(index < len(hraw[flavor]), f"Invalid raw index at slot {i}")
        obj = hraw[flavor][index]
        require(int(leptons["pdgId"][i]) == -(11 if e >= 0 else 13) * int(obj["charge"]),
                f"Flavor/charge/index mismatch at slot {i}")
        require(i < len(bits[flavor]), f"Missing tight bit at slot {i}")
        require(all(math.isfinite(leptons[field][i]) for field in ["pt", "eta", "phi"]),
                f"Nonfinite stored kinematics at retained slot {i}")
        expected_bit, stored_bit = all(cuts(flavor, obj).values()), bool(bits[flavor][i])
        eta_delta = leptons["eta"][i] - obj["eta"]
        phi_delta = math.remainder(leptons["phi"][i] - obj["phi"], 2 * math.pi)
        failures = [f for f, bad in [("tight", expected_bit != stored_bit),
                                    ("eta", abs(eta_delta) > TOLERANCE),
                                    ("phi", abs(phi_delta) > TOLERANCE)] if bad]
        observed.update(failures)
        ratio = leptons["pt"][i] / obj["pt"] if obj["pt"] else "undefined"
        rows.append([i, flavor, index, obj["pt"], leptons["pt"][i], ratio,
                     obj["eta"], leptons["eta"][i], obj["phi"], leptons["phi"][i],
                     expected_bit, stored_bit, "MISMATCH: " + ",".join(failures) if failures else "OK"])
        if expected_bit != stored_bit:
            print(f"MISMATCH slot {i}: stored tight={stored_bit}, indexed raw tight={expected_bit}")
    print("\nRetained slot versus the RAW HWW object named by its raw index:")
    table(["slot", "flavor", "raw index", "raw pT", "stored pT", "pT ratio",
           "raw eta", "stored eta", "raw phi", "stored phi", "expected tight", "stored tight", "result"], rows)
    require(expected <= observed, f"Expected discrepancy did not reproduce: {expected} versus {observed}")
    if case_name.endswith("singleton"):
        require(n == 1, f"Expected historical singleton, found {n} retained leptons")
        print("FACT: this MC __l2tight part0 stores nLepton=1. This read does not identify its historical rejection/acceptance operation.")
    if case_name == "dy_ee_association":
        require(n >= 2 and observed, "Main MC association witness must show a real retained-object mismatch")
    if case_name == "egamma_i_eta":
        require(observed == {"eta"}, f"Expected eta-only observation, found {observed}")
    print(f"OBSERVATION REPRODUCED: {case_name}; mismatching fields={sorted(observed)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, action="append", help="Show one fixed case (repeatable); default: all")
    parser.add_argument("--all-lepton-fields", action="store_true",
                        help="Discover and compare every Electron_/Muon_ field, with exact WP definitions")
    args = parser.parse_args()
    import ROOT
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(True)
    ROOT.TFile.SetOpenTimeout(30000)
    # One ordinary TTree/GetEntry loop scans only integer identity branches.
    # It checks uniqueness of the displayed keys, not full-population deduplication.
    ROOT.gInterpreter.Declare(r'''
    #include <TTree.h>
    #include <TLeaf.h>
    #include <vector>
    #include <stdexcept>
    std::vector<std::vector<Long64_t>> root_inspection_matches(
        TTree* tree, const std::vector<ULong64_t>& keys) {
      std::vector<std::vector<Long64_t>> found(keys.size()/3);
      tree->SetBranchStatus("*", false);
      for (auto name : {"run", "luminosityBlock", "event"}) tree->SetBranchStatus(name, true);
      auto runLeaf = tree->GetLeaf("run");
      auto lumiLeaf = tree->GetLeaf("luminosityBlock");
      auto eventLeaf = tree->GetLeaf("event");
      for (Long64_t entry=0; entry<tree->GetEntries(); ++entry) {
        if (tree->GetEntry(entry)<=0) throw std::runtime_error("Identity GetEntry failed");
        const auto run = static_cast<ULong64_t>(runLeaf->GetValueLong64());
        const auto lumi = static_cast<ULong64_t>(lumiLeaf->GetValueLong64());
        const auto event = static_cast<ULong64_t>(eventLeaf->GetValueLong64());
        for (size_t i=0; i<found.size(); ++i)
          if (run==keys[3*i] && lumi==keys[3*i+1] && event==keys[3*i+2]) found[i].push_back(entry);
      }
      return found;
    }
    ''')
    manifest = Path(__file__).with_name("inputs") / "inputs.json"
    data = manifest.read_bytes()
    require(hashlib.sha256(data).hexdigest() == MANIFEST_SHA256, "Pinned manifest hash changed")
    sources = {item["role"]: item for item in json.loads(data)["files"]}
    selected = args.case or list(CASES)
    print(f"Direct ROOT inspection; ROOT {ROOT.gROOT.GetVersion()}, Python {sys.version.split()[0]}")
    print(f"Script SHA-256={hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}")
    print(f"Manifest SHA-256={MANIFEST_SHA256}; eta/wrapped-phi tolerance={TOLERANCE}")
    print("Named WP source: mkShapesRDF 69ff2dad, Full2024v15 LeptonSel_cfg.py; definitions are frozen locally, no framework imports.")
    start = time.monotonic()
    for role in dict.fromkeys(CASES[name][0] for name in selected):
        source = sources[role]
        cases = [(name, CASES[name]) for name in selected if CASES[name][0] == role]
        files = []
        try:
            for kind, pfn, uuid, entries in [
                ("central", source["pfn"], source["verified_root_uuid"], source["verified_events_entries"]),
                ("HWW", source["hww_part0_pfn"], *HWW_ID[role]),
            ]:
                file = ROOT.TFile.Open(pfn, "READ")
                require(bool(file) and not file.IsZombie(), f"Cannot open {pfn}")
                files.append(file)
                tree = file.Get("Events")
                require(bool(tree) and tree.InheritsFrom("TTree"), f"Missing Events tree: {pfn}")
                require(file.GetUUID().AsString() == uuid and tree.GetEntries() == entries,
                        f"UUID or entry count changed: {pfn}")
                for branch in ["run", "luminosityBlock", "event"]:
                    leaf = tree.GetLeaf(branch)
                    require(bool(leaf) and leaf.GetTypeName() in ["UInt_t", "ULong64_t", "Long64_t"],
                            f"Noninteger/missing identity branch {branch}")
                targets = ROOT.std.vector("ULong64_t")([word for _, c in cases for word in c[3]])
                print(f"\nChecking {role} {kind}: complete {entries:,}-entry identity-only scan for {len(cases)} fixed keys", flush=True)
                matches = ROOT.root_inspection_matches(tree, targets)
                for (_, case), found in zip(cases, matches):
                    expected_entry = case[1] if kind == "central" else case[2]
                    require(list(found) == [expected_entry], f"Missing/duplicate/wrong entry for {case[3]}: {list(found)}")
                needed = {"run", "luminosityBlock", "event", "nElectron", "nMuon"}
                needed.update(f"{flavor}_{field}" for flavor, fields in NAMED_INPUTS.items() for field in fields)
                if kind == "HWW":
                    needed.add("nLepton")
                    needed.update(f"{c}_{f}" for c in ["Lepton", "VetoLepton"]
                                  for f in ["pt", "eta", "phi", "pdgId", "electronIdx", "muonIdx"])
                    needed.update(b.GetName() for b in tree.GetListOfBranches() if b.GetName().startswith("Lepton_isTight"))
                    needed.update("Lepton_isTight" + f + "_" + wp for f, wp in WPS.items())
                if args.all_lepton_fields:
                    needed.update(b.GetName() for b in tree.GetListOfBranches()
                                  if b.GetName().startswith(("Electron_", "Muon_", "Lepton_", "VetoLepton_"))
                                  or b.GetName().startswith("hygiene")
                                  or b.GetName() in ("isLoose", "isVeto", "isWgs"))
                for branch in needed:
                    require(bool(tree.GetBranch(branch)), f"Missing required branch: {kind} {branch}")
                    tree.SetBranchStatus(branch, True)
            for name, case in cases:
                display(*files, name, case, args.all_lepton_fields)
        finally:
            for file in files:
                file.Close()
    print(f"\nPASS: all {len(selected)} fixed observations reproduced; elapsed={time.monotonic()-start:.2f}s")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        sys.exit(1)
