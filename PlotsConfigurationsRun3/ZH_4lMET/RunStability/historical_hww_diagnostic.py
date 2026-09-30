"""Opt-in, one-file historical HWW RunStability replay for paired NanoAOD keys.

The compiled 2024 pickle is trusted local executable state.  This script does
not change that pickle or the nominal RunStability configuration.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import zlib


PICKLE_SHA256 = "6f7fb49e310297baa0e2b0624d58a46d2e88c28f96481991bfc95e7dea2e86ef"
HISTORICAL_PREFIX = "runtime/PlotsConfigurationsRun3/ZH_4lMET/ZZ_CR_RunStability"
HELPER_HASHES = {
    "macros/four_lepton_helpers.cc": "ce5d3e32a4b1ec0f90f2f9f839981501d9dccad417941ca51778a9916c61c762",
    "macros/selected_trigger_wrappers.cc": "0b6558b380bd6ba8a79ced32cf224ff09bc50ff9900c701c65faaa8861b3100e",
    "macros/fixed_wp_btag_sf.cc": "9633b720b09c35a5f596b7ca0fe9c171eaffd5619a5f44d6b8e305eb16759359",
    "selected_trigger_adapter.py": "eb187fac7d384e227f63d8da3bd086ed92041bcea3bf80f596846c9c6492cee0",
}
TARGET_CATEGORIES = {
    "dy_ee": ("DY_HLT_ELE30_ZEE", "DY_HLT_ELE23_ELE12_ZEE"),
    "dy_mumu": ("DY_HLT_ISOMU24_ZMM", "DY_HLT_MU17_MU8_ZMM"),
    "muon_c": ("DY_HLT_ISOMU24_ZMM", "DY_HLT_MU17_MU8_ZMM"),
    "muon_i": ("DY_HLT_ISOMU24_ZMM", "DY_HLT_MU17_MU8_ZMM"),
    "egamma_c": ("DY_HLT_ELE30_ZEE", "DY_HLT_ELE23_ELE12_ZEE"),
    "egamma_i": ("DY_HLT_ELE30_ZEE", "DY_HLT_ELE23_ELE12_ZEE"),
}
KEY_FIELDS = ("run", "luminosityBlock", "event")
ROW_FIELDS = ("rdfentry_",) + KEY_FIELDS
GATE_EXPRESSIONS = {
    "trigger_or": "Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || Trigger_sngEl || Trigger_dblEl",
    "two_leptons": "nLepton >= 2",
    "leading_two_tight": "L2TightLeading2",
    "no_horn_jet": "nJetInHorn == 0",
    "nonzero_weight": "abs(weight) > 0.0",
    "valid_z0": "hasValidZ0",
    "z0_mass_gt30": "Z0_mass > 30.",
    "z0_l1_pt_gt10": "Alt(Lepton_pt, Alt(Z0_idx, 0, -1), -999.f) > 10",
    "z0_l2_pt_gt10": "Alt(Lepton_pt, Alt(Z0_idx, 1, -1), -999.f) > 10",
    "z0_mass_gt60": "Z0_mass > 60.",
    "z0_mass_lt120": "Z0_mass < 120.",
    "ordered_pt35": "Passes2lOrderedPt",
}
DETAIL_FIELDS = (
    "nLepton",
    "L2TightLeading2",
    "L2TightGateIndex0",
    "L2TightGateIndex1",
    "nJetInHorn",
    "hasValidZ0",
    "Z0_mass",
    "Z0_pt",
    "Z0_isEE",
    "Z0_isMM",
    "Passes2lOrderedPt",
    "Trigger_ElMu",
    "Trigger_sngMu",
    "Trigger_dblMu",
    "Trigger_sngEl",
    "Trigger_dblEl",
    "streamPriority_MuonEG",
    "streamPriority_Muon",
    "streamPriority_EGamma",
    "dataStreamPriority",
    "HLT_IsoMu24",
    "HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8",
    "HLT_Ele30_WPTight_Gsf",
    "HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL",
    "METFilter_DATA",
    "METFilter_Common",
    "XSWeight",
    "baseW",
    "genWeight",
    "puWeight",
    "SelectedLeptonSF_Z",
    "TriggerSF_Z",
)
SELECTED_WP_FIELDS = (
    "Lepton_isTightElectron_mvaWinter22V2Iso_WP90_tthMVA_Run3",
    "Lepton_isTightMuon_cut_TightID_pfIsoTight_HWW_tthmva_67",
)
ELECTRON_TIGHT = SELECTED_WP_FIELDS[0]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unique_keys(rows, label):
    """Keep the full unsigned 32/32/64 identity, rejecting ambiguous joins."""
    seen = {}
    for row in rows:
        key = tuple(int(row[name]) for name in KEY_FIELDS)
        if not (0 <= key[0] < 2**32 and 0 <= key[1] < 2**32 and 0 <= key[2] < 2**64):
            raise ValueError(f"{label} contains an out-of-range event key: {key}")
        if key in seen:
            raise ValueError(f"{label} contains duplicate event key {key}")
        seen[key] = row
    return seen


def load_compiled(path):
    if sha256(path) != PICKLE_SHA256:
        raise ValueError("Historical compiled pickle SHA256 mismatch")
    import cloudpickle

    config = cloudpickle.loads(zlib.decompress(Path(path).read_bytes()))
    if config.get("YEAR") != "2024" or config.get("runnerFile") != "zz_cr_runner.py":
        raise ValueError("Historical pickle has an unexpected era or runner")
    if config.get("nuisances"):
        raise ValueError("Historical diagnostic expects no nuisances")
    return config


def relocate_aliases(aliases, leaf):
    """Redirect only deleted runtime paths to byte-identical retained helpers."""
    helper_root = leaf.parent / "ZZ_CR"
    for relative, expected in HELPER_HASHES.items():
        if sha256(helper_root / relative) != expected:
            raise ValueError(f"Historical helper bytes changed: {relative}")
    result = deepcopy(aliases)
    result.pop("__run_stability_contract__", None)  # TH2 is outside this TH1 diagnostic
    old_include = HISTORICAL_PREFIX.replace("runtime/", "runtime//")
    for definition in result.values():
        for field in ("linesToAdd", "linesToProcess"):
            if field not in definition:
                continue
            relocated = []
            for line in definition[field]:
                line = line.replace(old_include, str(helper_root))
                line = line.replace(HISTORICAL_PREFIX, str(helper_root))
                if "ZZ_CR_RunStability" in line:
                    raise ValueError("Unresolved historical runtime include")
                relocated.append(line)
            definition[field] = relocated
    return result


def selected_sample(config, pair):
    name = pair["sample"] if pair["role"].startswith("dy_") else "DATA"
    source = config["samples"][name]
    matches = [
        component for component in source["name"] if pair["hww_pfn"] in component[1]
    ]
    if len(matches) != 1:
        raise ValueError("HWW part0 is not uniquely listed in the compiled sample")
    component = matches[0]
    if not pair["hww_pfn"].endswith("__part0.root"):
        raise ValueError("Expected one historical part0 input")
    narrowed = deepcopy(source)
    narrowed["name"] = [(component[0], [pair["hww_pfn"]], *component[2:])]
    narrowed["FilesPerJob"] = 1
    return name, {name: narrowed}


def selected_cuts(config, categories):
    source = config["cuts"]
    parent = source["cuts"]["DY"]
    short_names = [name.removeprefix("DY_") for name in categories]
    if any(name not in parent["categories"] for name in short_names):
        raise ValueError("Requested category is absent from the historical pickle")
    chosen = deepcopy(parent)
    chosen["categories"] = {name: parent["categories"][name] for name in short_names}
    return {"preselections": source["preselections"], "cuts": {"DY": chosen}}


def central_prefix(pair, stop):
    import uproot

    with uproot.open(pair["central_pfn"], timeout=60) as source:
        tree = source["Events"]
        if int(tree.num_entries) != pair["central_events_entries"]:
            raise ValueError("Central Events count changed from the verified pair")
        if stop > tree.num_entries:
            raise ValueError("Requested prefix exceeds central Events entries")
        arrays = tree.arrays(
            list(KEY_FIELDS), entry_start=0, entry_stop=stop, library="np"
        )
    for name in KEY_FIELDS:
        dtype = arrays[name].dtype
        if dtype.kind != "u" or dtype.itemsize != (8 if name == "event" else 4):
            raise ValueError(f"Unexpected central identity type for {name}: {dtype}")
    rows = [
        {
            "central_source_entry": i,
            **{name: int(arrays[name][i]) for name in KEY_FIELDS},
        }
        for i in range(stop)
    ]
    return unique_keys(rows, "central prefix")


def declare_key_filter(ROOT, keys, identity):
    namespace = "hww_pair_" + hashlib.sha256(identity.encode()).hexdigest()[:16]
    ROOT.gInterpreter.Declare(
        "#include <cstdint>\n#include <unordered_set>\n"
        f"namespace {namespace} {{\n"
        "struct Key { unsigned int run, lumi; unsigned long long event;\n"
        " bool operator==(Key const& o) const {return run==o.run && lumi==o.lumi && event==o.event;} };\n"
        "struct Hash { size_t operator()(Key const& k) const {\n"
        " auto h=std::hash<unsigned long long>{}(k.event);\n"
        " h ^= std::hash<unsigned int>{}(k.run)+0x9e3779b9+(h<<6)+(h>>2);\n"
        " h ^= std::hash<unsigned int>{}(k.lumi)+0x9e3779b9+(h<<6)+(h>>2); return h;} };\n"
        "std::unordered_set<Key,Hash> keys;\n"
        "void add(unsigned int r,unsigned int l,unsigned long long e) {keys.insert({r,l,e});}\n"
        "bool contains(unsigned int r,unsigned int l,unsigned long long e) {return keys.count({r,l,e})!=0;}\n"
        "}\n"
    )
    store = getattr(ROOT, namespace)
    for run, lumi, event in keys:
        store.add(run, lumi, event)
    if int(store.keys.size()) != len(keys):
        raise ValueError("C++ typed event-key set lost entries")
    return f"{namespace}::contains(run, luminosityBlock, event)"


def take_columns(df, names):
    return {name: df.Take[df.GetColumnType(name)](name) for name in names}


def materialize_rows(actions):
    columns = {name: list(result.GetValue()) for name, result in actions.items()}
    lengths = {len(values) for values in columns.values()}
    if len(lengths) != 1:
        raise ValueError("RDataFrame Take columns have inconsistent lengths")
    return [
        {
            name: (
                float(value)
                if name
                in (
                    "weight",
                    "Z0_mass_0",
                    "Z0_mass",
                    "Z0_pt",
                    "XSWeight",
                    "baseW",
                    "genWeight",
                    "puWeight",
                    "SelectedLeptonSF_Z",
                    "TriggerSF_Z",
                )
                or name.startswith(("diag_pair_pt", "diag_pair_eta"))
                else signed_event_to_uint64(value) if name == "event" else int(value)
            )
            for name, value in ((name, values[i]) for name, values in columns.items())
        }
        for i in range(next(iter(lengths)))
    ]


def signed_event_to_uint64(value):
    number = int(value)
    if not -(2**63) <= number < 2**64:
        raise ValueError("HWW event identity is outside signed/unsigned 64-bit range")
    return number & (2**64 - 1)


def aligned_electron_tight(df, ROOT):
    """Recompute the compiled pair WP on HWW raw electrons, then retain-index it."""
    from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP

    cuts = ElectronWP["Full2024v15"]["TightObjWP"]["mvaWinter22V2Iso_WP90_tthMVA_Run3"][
        "cuts"
    ]
    ROOT.gInterpreter.Declare(
        "#include <ROOT/RVec.hxx>\n#include <stdexcept>\n"
        "namespace hww_electron_counterfactual {\n"
        "template <class Indices, class Bits>\n"
        "Bits align(Indices const& indices, Bits const& raw) {\n"
        " Bits result; result.reserve(indices.size());\n"
        " for (int i : indices) {\n"
        "  if (i < -1 || i >= static_cast<int>(raw.size())) "
        'throw std::out_of_range("Electron index outside raw collection");\n'
        "  result.push_back(i < 0 ? false : raw[i]);\n"
        " } return result; } }\n"
    )
    df = df.Define("diag_electron_tight_raw", "ROOT::RVecB(Electron_pt.size(), true)")
    for guard, ingredients in cuts.items():
        expression = " && ".join(f"({ingredient})" for ingredient in ingredients)
        df = df.Redefine(
            "diag_electron_tight_raw",
            f"diag_electron_tight_raw && (!({guard}) || ({expression}))",
        )
    df = df.Define(
        "diag_electron_tight_aligned",
        "hww_electron_counterfactual::align(Lepton_electronIdx, diag_electron_tight_raw)",
    )
    return df.Redefine(ELECTRON_TIGHT, "diag_electron_tight_aligned")


def replay(config, pair, central, categories, leaf, output_root, counterfactual=None):
    import ROOT
    from run_stability_runner import RunAnalysis

    if ROOT.IsImplicitMTEnabled():
        raise RuntimeError(
            "Historical row alignment requires single-threaded RDataFrame"
        )
    ROOT.gInterpreter.AddIncludePath(str(leaf.parents[2] / "mkShapesRDF" / "include"))
    ROOT.gInterpreter.Declare('#include "headers.hh"')
    name, samples = selected_sample(config, pair)
    runner = DiagnosticRunAnalysis(
        RunAnalysis,
        categories,
        RunAnalysis.splitSamples(samples),
        relocate_aliases(config["aliases"], leaf),
        {"Z0_mass": deepcopy(config["variables"]["Z0_mass"])},
        selected_cuts(config, categories),
        {},
        config["lumi"],
        outputFileMap=str(output_root),
        remote_io_settings=config["remoteIO"],
    )
    only_df = runner.dfs[name][0]["df"]
    hww_types = {field: str(only_df.GetColumnType(field)) for field in KEY_FIELDS}
    allowed = {
        "Long64_t",
        "long long",
        "int64_t",
        "UInt_t",
        "unsigned int",
        "ULong64_t",
        "unsigned long long",
        "uint64_t",
    }
    if any(kind not in allowed for kind in hww_types.values()):
        raise ValueError(f"Unexpected HWW identity types: {hww_types}")
    expression = declare_key_filter(
        ROOT, central, pair["central_lfn"] + str(len(central))
    )
    expression = (
        "run >= 0 && run < 4294967296LL && luminosityBlock >= 0 && "
        "luminosityBlock < 4294967296LL && "
        + expression.replace(
            "(run, luminosityBlock, event)",
            "(static_cast<unsigned int>(run), static_cast<unsigned int>(luminosityBlock), static_cast<unsigned long long>(event))",
        )
    )
    matched = only_df.Filter(expression, "central-prefix-key")
    runner.raw_actions = take_columns(matched, ROW_FIELDS)
    if counterfactual in ("aligned_electron_tight", "aligned_electron_tight_no_gate"):
        matched = aligned_electron_tight(matched, ROOT)
    runner.dfs[name][0]["df"] = matched
    runner.run()
    graph_runs = int(only_df.GetNRuns())
    raw = materialize_rows(runner.raw_actions)
    pre = materialize_rows(runner.pre_actions)
    selected = {
        category: materialize_rows(actions)
        for category, actions in runner.selected_actions.items()
    }
    full = materialize_rows(runner.full_actions)
    return raw, full, pre, selected, hww_types, runner.unavailable_fields, graph_runs


def DiagnosticRunAnalysis(base, categories, *args, **kwargs):
    """Attach lazy row actions before the historical runner triggers its graph."""

    class _Diagnostic(base):
        def __init__(self):
            self.diagnostic_categories = categories
            self.pre_actions = None
            self.full_actions = None
            self.unavailable_fields = []
            self.selected_actions = {}
            super().__init__(*args, **kwargs)

        def loadAliases(self, afterNuis=False):
            super().loadAliases(afterNuis)
            if not afterNuis:
                return
            metadata = next(iter(next(iter(self.dfs.values())).values()))
            df = metadata["df"]
            available = {str(name) for name in df.GetColumnNames()}
            required = {"Lepton_pt", "Lepton_eta", "Lepton_pdgId", "Z0_idx"}
            if not required <= available:
                raise ValueError(
                    f"Missing selected-pair inputs: {sorted(required - available)}"
                )
            details = [name for name in DETAIL_FIELDS if name in available]
            self.unavailable_fields = sorted(set(DETAIL_FIELDS) - available)
            for gate, expression in GATE_EXPRESSIONS.items():
                df = df.Define("diag_gate_" + gate, expression)
            pair_columns = []
            for index in (0, 1):
                selected_index = f"Alt(Z0_idx, {index}, -1)"
                for label, expression in (
                    ("index", selected_index),
                    ("pt", f"Alt(Lepton_pt, {selected_index}, -999.f)"),
                    ("eta", f"Alt(Lepton_eta, {selected_index}, -999.f)"),
                    ("pdg_id", f"Alt(Lepton_pdgId, {selected_index}, 0)"),
                ):
                    column = f"diag_pair_{label}{index}"
                    df = df.Define(column, expression)
                    pair_columns.append(column)
                for wp in SELECTED_WP_FIELDS:
                    if wp not in available:
                        self.unavailable_fields.append(wp)
                        continue
                    column = f"diag_pair_{wp}_{index}"
                    df = df.Define(column, f"Alt({wp}, {selected_index}, 0)")
                    pair_columns.append(column)
            metadata["df"] = df
            self.full_actions = take_columns(
                df,
                ROW_FIELDS
                + ("weight",)
                + tuple(details)
                + tuple("diag_gate_" + gate for gate in GATE_EXPRESSIONS)
                + tuple(pair_columns),
            )

        def create_cuts_vars(self):
            df = next(iter(next(iter(self.dfs.values())).values()))["df"]
            self.pre_actions = take_columns(df, ROW_FIELDS + ("weight",))
            for category in self.diagnostic_categories:
                selected_df = df.Filter(self.cuts[category]["expr"], category)
                self.selected_actions[category] = take_columns(
                    selected_df, ROW_FIELDS + ("weight", "Z0_mass_0")
                )
            super().create_cuts_vars()

    return _Diagnostic()


def ledger(raw, full, pre, selected, central, categories, counterfactual=None):
    raw_map = unique_keys(raw, "matched HWW")
    full_map = unique_keys(full, "full historical alias stage")
    pre_map = unique_keys(pre, "historical preselection")
    selected_maps = {name: unique_keys(rows, name) for name, rows in selected.items()}
    if (
        not set(raw_map) <= set(central)
        or set(full_map) != set(raw_map)
        or not set(pre_map) <= set(raw_map)
    ):
        raise ValueError(
            "Historical row stage is outside the paired central-prefix cohort"
        )
    if any(not set(rows) <= set(pre_map) for rows in selected_maps.values()):
        raise ValueError("Historical category is outside preselection")
    rows = []
    for key, hww in raw_map.items():
        row = {field: int(hww[field]) for field in KEY_FIELDS}
        row["central_source_entry"] = central[key]["central_source_entry"]
        row["hww_part_entry"] = hww["rdfentry_"]
        row["historical_preselection"] = key in pre_map
        row["historical_weight"] = pre_map[key]["weight"] if key in pre_map else None
        full_row = full_map[key]
        gates = {gate: bool(full_row["diag_gate_" + gate]) for gate in GATE_EXPRESSIONS}
        row["historical_independent_gates"] = gates
        row["historical_preselection_from_gates"] = all(
            gates[gate]
            for gate in (
                "trigger_or",
                "two_leptons",
                *(
                    ()
                    if counterfactual
                    in ("no_leading_two_gate", "aligned_electron_tight_no_gate")
                    else ("leading_two_tight",)
                ),
                "no_horn_jet",
                "nonzero_weight",
            )
        )
        if row["historical_preselection_from_gates"] != row["historical_preselection"]:
            raise ValueError(
                f"Historical preselection gate decision disagrees for {key}"
            )
        row["historical_dy_parent_from_gates"] = all(
            gates[gate]
            for gate in (
                "trigger_or",
                "two_leptons",
                "valid_z0",
                "z0_mass_gt30",
                "z0_l1_pt_gt10",
                "z0_l2_pt_gt10",
                "z0_mass_gt60",
                "z0_mass_lt120",
                "ordered_pt35",
            )
        )
        row["historical_alias_values"] = {
            name: value
            for name, value in full_row.items()
            if name not in ROW_FIELDS and not name.startswith("diag_gate_")
        }
        row["historical_categories"] = {
            name: key in selected_maps[name] for name in categories
        }
        row["historical_z0_mass"] = next(
            (
                selected_maps[name][key]["Z0_mass_0"]
                for name in categories
                if key in selected_maps[name]
            ),
            None,
        )
        rows.append(row)
    rows.sort(key=lambda row: row["central_source_entry"])
    return rows, {
        "central_prefix": len(central),
        "hww_matched": len(raw_map),
        "historical_full_alias": len(full_map),
        "historical_preselection": len(pre_map),
        "historical_categories": {
            name: len(selected_maps[name]) for name in categories
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pair-evidence", type=Path, required=True)
    parser.add_argument("--role", choices=TARGET_CATEGORIES, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--include-all", action="store_true", help="also book DY_ALL")
    parser.add_argument(
        "--counterfactual",
        choices=(
            "aligned_electron_tight",
            "no_leading_two_gate",
            "aligned_electron_tight_no_gate",
        ),
        help="opt-in historical selection counterfactual; baseline is unchanged",
    )
    args = parser.parse_args(argv)
    if args.output_dir.exists():
        parser.error(
            "Output directory already exists; choose a fresh task-owned identity"
        )
    manifest = json.loads(args.manifest.read_text())
    evidence = json.loads(args.pair_evidence.read_text())
    pairs = [pair for pair in evidence["pairs"] if pair["role"] == args.role]
    files = [item for item in manifest["files"] if item["role"] == args.role]
    if len(pairs) != 1 or len(files) != 1:
        raise ValueError("Role is not unique in paired evidence and frozen manifest")
    pair, entry = pairs[0], files[0]
    if pair["central_lfn"] != entry["lfn"] or pair["hww_pfn"] != entry["hww_part0_pfn"]:
        raise ValueError(
            "Frozen central manifest and historical parent evidence disagree"
        )
    if pair["source_id"] != entry["source_id"]:
        raise ValueError("Frozen source ID and parent evidence disagree")
    stop = entry["entry_stop"]
    if entry["entry_start"] != 0 or stop != (
        80000 if args.role.startswith("dy_") else 200000
    ):
        raise ValueError("Diagnostic requires exact central entry prefix")
    pickle_path = Path(evidence["hww_exact_compiled_pickle_path"])
    if evidence["hww_exact_compiled_pickle_sha256"] != PICKLE_SHA256:
        raise ValueError("Parent evidence refers to a different historical pickle")
    config = load_compiled(pickle_path)
    if args.counterfactual in ("no_leading_two_gate", "aligned_electron_tight_no_gate"):
        original = config["cuts"]["preselections"]
        if original.count(" && L2TightLeading2") != 1:
            raise ValueError("Historical leading-two clause changed")
        config["cuts"]["preselections"] = original.replace(" && L2TightLeading2", "", 1)
    leaf = Path(__file__).resolve().parent
    categories = TARGET_CATEGORIES[args.role] + (
        ("DY_ALL",) if args.include_all else ()
    )
    central = central_prefix(pair, stop)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    root_path = args.output_dir / "historical_histograms.root"
    raw, full, pre, selected, hww_types, unavailable, graph_runs = replay(
        config, pair, central, categories, leaf, root_path, args.counterfactual
    )
    rows, cutflow = ledger(
        raw, full, pre, selected, central, categories, args.counterfactual
    )
    rows_path = args.output_dir / "historical_rows.jsonl"
    with rows_path.open("x") as output:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")
    receipt = {
        "kind": "historical_hww_paired_prefix_diagnostic",
        "counterfactual": args.counterfactual,
        "role": args.role,
        "central_lfn": pair["central_lfn"],
        "hww_pfn": pair["hww_pfn"],
        "source_id": pair["source_id"],
        "central_entry_stop": stop,
        "compiled_pickle": str(pickle_path),
        "compiled_pickle_sha256": PICKLE_SHA256,
        "historical_lumi_fb": config["lumi"],
        "categories": categories,
        "observable": "Z0_mass",
        "cutflow": cutflow,
        "rdf_graph_runs": graph_runs,
        "manifest_sha256": sha256(args.manifest),
        "parent_pair_evidence_sha256": sha256(args.pair_evidence),
        "diagnostic_runner_sha256": sha256(__file__),
        "hww_runtime_helper_sha256": HELPER_HASHES,
        "hww_identity_branch_types": hww_types,
        "unavailable_hww_detail_fields": sorted(set(unavailable)),
        "event_identity_bridge": "HWW signed Int64_t event to central uint64 via value & (2**64-1), with signed range and full-width typed-key checks",
        "method": "Historical compiled aliases/cuts/weights; one HWW part0, central typed-key prefix filter; lazy category histograms and row actions in one RDF graph traversal",
        "limits": [
            "Retained HWW part0 is an upstream skim; absent central-prefix events are not evaluated by historical shape selection.",
            "Only the chosen category histograms and Z0_mass are booked; historical DATA auxiliary run TH2 is omitted.",
        ],
        "histogram_file": str(root_path),
        "histogram_sha256": sha256(root_path),
        "rows_file": str(rows_path),
        "rows_sha256": sha256(rows_path),
    }
    (args.output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(args.output_dir / "receipt.json")


if __name__ == "__main__":
    main()
