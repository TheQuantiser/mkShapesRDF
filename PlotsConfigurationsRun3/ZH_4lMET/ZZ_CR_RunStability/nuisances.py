"""Verified Run-III nuisance model for the disjoint analysis passes."""

import os
import re

if "load_selected_year" not in globals() or "resolve_overlap_model" not in globals():
    from year_config import load_selected_year, resolve_overlap_model
if "analysis_pass" not in globals():
    from selection_config import analysis_pass

_samples_dict = globals().get("samples", {})
mc = [sample for sample in _samples_dict if sample != "DATA"]
YEAR, _selected_year, _full_config = load_selected_year()
_resolved_overlap = resolve_overlap_model(_selected_year, _full_config)
_logical_theory_groups = {
    process: cfg["theory_group"]
    for process, cfg in _resolved_overlap["processes"].items()
}
_PASS = analysis_pass(globals().get("ANALYSIS_PASS") or os.environ.get("ANALYSIS_PASS"))

nuisances = {}


def _ratio(varied, nominal):
    return f"(({nominal}) == 0.f ? 1.f : ({varied})/({nominal}))"


def _shape_weight(name, nuisance_name, up, down, applicable=None):
    selected = list(mc if applicable is None else applicable)
    if not selected:
        return
    nuisances[name] = {
        "name": nuisance_name,
        "kind": "weight",
        "type": "shape",
        # mkShapesRDF's public contract is [up, down].
        "samples": {sample: [up, down] for sample in selected},
    }


# The local HWW reference provides a single era-specific luminosity component;
# retaining the era in the name makes the correlation decision explicit.
_lumi_cfg = _selected_year["lumi_nuisance"]
nuisances[_lumi_cfg["name"]] = {
    "name": _lumi_cfg["name"],
    "type": "lnN",
    "samples": {sample: _lumi_cfg["value"] for sample in mc},
}

# Keep the canonical Run-III CP5 underlying-event normalization used by the
# five corresponding external WW control-region configurations.  It applies
# to every simulated process and, by construction, never targets DATA.
nuisances["UE_CP5"] = {
    "name": "UEPS",
    "type": "lnN",
    "samples": {sample: "1.015" for sample in mc},
}

_pair = _PASS["selected_lepton_sf"]
_trigger = _PASS["trigger_sf"]
for _key, _nuisance_name, _nominal, _up, _down in (
    ("pileup", f"CMS_pileup_{YEAR}", "puWeight", "puWeightUp", "puWeightDown"),
    (
        "electron_efficiency",
        f"CMS_eff_e_{YEAR}",
        f"SelectedLeptonSF_{_pair}",
        f"SelectedElectronSF_{_pair}_Up",
        f"SelectedElectronSF_{_pair}_Down",
    ),
    (
        "muon_efficiency",
        f"CMS_eff_m_{YEAR}",
        f"SelectedLeptonSF_{_pair}",
        f"SelectedMuonSF_{_pair}_Up",
        f"SelectedMuonSF_{_pair}_Down",
    ),
    (
        "event_trigger",
        f"CMS_eff_hwwtrigger_{YEAR}",
        f"TriggerSF_{_trigger}",
        f"TriggerSF_{_trigger}_Up",
        f"TriggerSF_{_trigger}_Down",
    ),
):
    _shape_weight(
        _key,
        _nuisance_name,
        _ratio(_up, _nominal),
        _ratio(_down, _nominal),
    )

if _PASS["btag_sf"]:
    for _flavor in ("bc", "light"):
        for _correlation in ("correlated", "uncorrelated"):
            _public_name = (
                f"CMS_btagSF{_flavor}_correlated"
                if _correlation == "correlated"
                else f"CMS_btagSF{_flavor}_{YEAR}"
            )
            _shape_weight(
                f"btagSF{_flavor}_{_correlation}",
                _public_name,
                _ratio(
                    f"btagSF{_flavor}_up_{_correlation}",
                    f"btagSF{_flavor}",
                ),
                _ratio(
                    f"btagSF{_flavor}_down_{_correlation}",
                    f"btagSF{_flavor}",
                ),
            )


def _friend_directory(suffix):
    resolver = globals().get("makeMCFriendDirectory")
    if resolver is None:
        raise RuntimeError("samples.py did not expose makeMCFriendDirectory")
    path = resolver(suffix)
    if path.startswith("root://") and not re.match(
        r"^root://[^/]+//store/",
        path,
    ):
        raise RuntimeError(
            "Malformed XRootD systematic-friend directory; expected "
            f"root://host//store/... and received {path!r}"
        )
    return path


def _suffix(name, public_name, up, down):
    nuisances[name] = {
        "name": public_name,
        "skipCMS": 1,
        "kind": "suffix",
        "type": "shape",
        "mapUp": up,
        "mapDown": down,
        "folderUp": _friend_directory(up + "_suffix"),
        "folderDown": _friend_directory(down + "_suffix"),
        "samples": {sample: ["1", "1"] for sample in mc},
        "AsLnN": "0",
    }


_suffix("JER", f"CMS_res_j_{YEAR}", "jerup", "jerdo")
_suffix("MET_unclustered", f"CMS_scale_met_{YEAR}", "unclustEnup", "unclustEndo")
_suffix("lepton_scale", f"CMS_lepscale_{YEAR}", "leptonScaleup", "leptonScaledo")
_suffix(
    "lepton_resolution",
    f"CMS_lepres_{YEAR}",
    "leptonResolutionup",
    "leptonResolutiondo",
)

for _jes_source in (
    "Absolute",
    f"Absolute_{YEAR}",
    "FlavorQCD",
    "BBEC1",
    "EC2",
    "HF",
    f"BBEC1_{YEAR}",
    f"EC2_{YEAR}",
    "RelativeBal",
    f"RelativeSample_{YEAR}",
    f"HF_{YEAR}",
):
    _suffix(
        f"JES_{_jes_source}",
        f"CMS_scale_j_{_jes_source}",
        f"jesRegroed_{_jes_source}up",
        f"jesRegroed_{_jes_source}do",
    )


_branches_by_sample = globals().get("AVAILABLE_BRANCHES_BY_SAMPLE", {})
_lengths_by_sample = globals().get("THEORY_VECTOR_LENGTHS_BY_SAMPLE", {})


def _has_vector(sample, branch, count_branch, minimum):
    branches = _branches_by_sample.get(sample, set())
    length = _lengths_by_sample.get(sample, {}).get(count_branch, {})
    return (
        branch in branches
        and count_branch in branches
        and length.get("min", -1) >= minimum
    )


_ps_samples = [
    sample for sample in mc if _has_vector(sample, "PSWeight", "nPSWeight", 4)
]
_shape_weight("PS_ISR", "ps_isr", "PSWeight[2]", "PSWeight[0]", _ps_samples)
_shape_weight("PS_FSR", "ps_fsr", "PSWeight[3]", "PSWeight[1]", _ps_samples)


def _theory_group(sample):
    if sample in _logical_theory_groups:
        return _logical_theory_groups[sample]
    if sample.startswith("GluGlutoContintoWW"):
        return "ggWW"
    if sample.startswith("GluGluZH"):
        return "ggZH"
    if sample.startswith("ZH_"):
        return "ZH"
    if sample.startswith("GluGluH"):
        return "ggH"
    if sample.startswith("VBFH"):
        return "VBFH"
    if sample.startswith(("HWplus", "HWminus")):
        return "WH"
    if sample.startswith("ttH"):
        return "ttH"
    if sample.startswith(("DY", "DYG")):
        return "DY"
    if sample.startswith(("TT", "ST_", "TW", "TbarW", "TZ")):
        return "top"
    if sample.startswith(("WW", "WZ", "ZZ", "WpWm", "WWW", "WZZ", "ZZZ")):
        return "VV"
    if sample.startswith("WG"):
        return "Vgamma"
    return re.sub(r"[^A-Za-z0-9]+", "_", sample).strip("_")


_scale_samples = [
    sample
    for sample in mc
    if _has_vector(sample, "LHEScaleWeight", "nLHEScaleWeight", 8)
]
_pdf_samples = [
    sample for sample in mc if _has_vector(sample, "LHEPdfWeight", "nLHEPdfWeight", 103)
]

_scale_variations = [
    "Alt(LHEScaleWeight,0,1.f)",
    "Alt(LHEScaleWeight,1,1.f)",
    "Alt(LHEScaleWeight,3,1.f)",
    "Alt(LHEScaleWeight,nLHEScaleWeight-4,1.f)",
    "Alt(LHEScaleWeight,nLHEScaleWeight-2,1.f)",
    "Alt(LHEScaleWeight,nLHEScaleWeight-1,1.f)",
]
_pdf_variations = [f"Alt(LHEPdfWeight,{index},1.f)" for index in range(1, 103)]

for _group in sorted({_theory_group(sample) for sample in _scale_samples}):
    _group_samples = [
        sample for sample in _scale_samples if _theory_group(sample) == _group
    ]
    nuisances[f"QCDscale_{_group}"] = {
        "name": f"QCDscale_{_group}",
        "kind": "weight_envelope",
        "type": "shape",
        "samples": {sample: list(_scale_variations) for sample in _group_samples},
    }

for _group in sorted({_theory_group(sample) for sample in _pdf_samples}):
    _group_samples = [
        sample for sample in _pdf_samples if _theory_group(sample) == _group
    ]
    nuisances[f"pdf_{_group}"] = {
        "name": f"CMS_pdf_{_group}",
        "skipCMS": 1,
        "kind": "weight_rms",
        "type": "shape",
        "samples": {sample: list(_pdf_variations) for sample in _group_samples},
    }

_ggww_samples = [sample for sample in mc if _theory_group(sample) == "ggWW"]
if _ggww_samples:
    nuisances["QCDscale_ggWW_norm"] = {
        "name": "QCDscale_ggWW_norm",
        "type": "lnN",
        "samples": {sample: "1.15" for sample in _ggww_samples},
    }

nuisances["stat"] = {
    "type": "auto",
    "maxPoiss": "10",
    "includeSignal": "0",
    "samples": {},
}

# DATA contributes nominal observed counts only.  No correction, suffix,
# theory, or finite-MC nuisance may ever target it.
for _nuisance_key, _nuisance_cfg in nuisances.items():
    _targets = set((_nuisance_cfg.get("samples") or {}).keys())
    if "DATA" in _targets:
        raise RuntimeError(f"Nuisance {_nuisance_key!r} illegally targets DATA")
    _unknown_targets = sorted(_targets - set(mc))
    if _unknown_targets:
        raise RuntimeError(
            f"Nuisance {_nuisance_key!r} targets unknown MC processes: "
            f"{_unknown_targets}"
        )
