"""Processed Run-3 source adapters and nominal candidate presets.

Production ordering is reconstructed only through the established retained
VetoLepton alignment kernels. No momentum calibration is applied again.
"""

from dataclasses import replace
from .naming import public_name
from pathlib import Path
import json

from mkShapesRDF.processor.data.LeptonSel_cfg import ElectronWP, MuonWP


def lepton_source(
    analysis,
    era_cfg,
    *,
    name="leptons",
    electron_wps=None,
    muon_wps=None,
    available_branches=None,
):
    lep = era_cfg["lepton_ids"]
    electron_wps = tuple(electron_wps or (lep["electron_wp"],))
    muon_wps = tuple(muon_wps or (lep["muon_wp"],))
    fields = {key: f"Lepton_{key}" for key in ("pt", "eta", "phi")}
    fields.update(
        pdg_id="Lepton_pdgId",
        electron_index="Lepton_electronIdx",
        muon_index="Lepton_muonIdx",
    )
    for kind, working_points, catalog in (
        ("Electron", electron_wps, ElectronWP),
        ("Muon", muon_wps, MuonWP),
    ):
        for wp in working_points:
            if wp not in catalog[era_cfg["l2tight_era"]]["TightObjWP"]:
                raise ValueError(f"Unsupported {kind} WP {wp}")
            flag = f"Lepton_isTight{kind}_{wp}"
            if available_branches is not None and flag not in available_branches:
                raise ValueError(f"Requested WP branch is absent: {flag}")
            fields[f"{kind.lower()}_{wp}"] = flag
            fields[f"{kind.lower()}_sf_{wp}"] = f"Lepton_tight{kind}_{wp}_TotSF"
    source = analysis.source(
        name,
        "lepton",
        fields,
        lineage=f"{era_cfg['l2tight_era']}:LeptonScaleSmearing:retained-final-Lepton",
        identity="Lepton",
    )
    # DATA do not carry MC SF branches. The same named source fields have
    # explicit unit representations selected using sample metadata.
    converted = []
    for field, column in source.fields:
        if field.startswith(("electron_sf_", "muon_sf_")):
            column = replace(
                column, data_expression="ROOT::RVecF(Lepton_pt.size(),1.f)"
            )
            analysis.columns[column.name] = column
        converted.append((field, column))
    return replace(source, fields=tuple(converted))


def nominal_pairs(
    analysis,
    era_cfg,
    *,
    name="",
    z_wps=None,
    x_wps=None,
    with_x=True,
    available_branches=None,
):
    prefix = public_name(name) + "_" if name else ""
    lep = era_cfg["lepton_ids"]
    z_wps = tuple(z_wps or (lep["electron_wp"], lep["muon_wp"]))
    x_wps = tuple(x_wps or z_wps)
    source = lepton_source(
        analysis,
        era_cfg,
        name=f"{prefix}leptons",
        electron_wps=tuple(dict.fromkeys((z_wps[0], x_wps[0]))),
        muon_wps=tuple(dict.fromkeys((z_wps[1], x_wps[1]))),
        available_branches=available_branches,
    )
    z_pool = analysis.view(
        f"{prefix}z_pool", source, electron_wp=z_wps[0], muon_wp=z_wps[1]
    )
    z = analysis.pair(
        f"{prefix}z", z_pool, min_pt=lep["z0_pt_mins"], min_pass=int(lep["z0_min_pass"])
    )
    if not with_x:
        return z, None
    x_pool = analysis.view(
        f"{prefix}x_pool", source, electron_wp=x_wps[0], muon_wp=x_wps[1]
    )
    x = analysis.pair(
        f"{prefix}x",
        x_pool,
        policy="highest_pt",
        min_pt=lep["x_pt_mins"],
        min_pass=int(lep["x_min_pass"]),
        flavor="any",
        exclude=z,
    )
    return z, x


def trigger_sf(analysis, name, z, era_cfg, *, x=None):
    """Canonical selected two/four-lepton trigger union, in production kinematics."""
    source = z.view.source
    expected = {
        "pt": "Lepton_pt",
        "eta": "Lepton_eta",
        "phi": "Lepton_phi",
        "pdg_id": "Lepton_pdgId",
    }
    if not source.lineage.endswith(":LeptonScaleSmearing:retained-final-Lepton") or any(
        source[field].expression != expr for field, expr in expected.items()
    ):
        raise ValueError(
            "The retained trigger provider requires the processed Lepton source; other representations need their own provider"
        )
    if x is not None and x.view.source != source:
        raise ValueError("A trigger union requires one retained lepton source")
    common = Path(__file__).resolve().parent
    pt = analysis.column(
        f"zh4l_internal_{source.name}_production_pt",
        "FourLepton::productionAlignedPt(Lepton_eta,Lepton_phi,Lepton_pdgId,VetoLepton_pt,VetoLepton_eta,VetoLepton_phi,VetoLepton_pdgId)",
        declarations=(f'#include "{common / "macros/objects.cc"}"',),
    )
    pdg = analysis.column(
        f"zh4l_internal_{source.name}_production_pdg_id",
        "FourLepton::productionAlignedPdgId(Lepton_eta,Lepton_phi,VetoLepton_eta,VetoLepton_phi,VetoLepton_pdgId)",
    )
    args = (pt, source["eta"], source["phi"], pdg, z.indices) + (
        (x.indices,) if x else ()
    )
    result = analysis.column(
        f"zh4l_internal_{name}_result",
        f"SelectedTrigger::selected{'Four' if x else 'Pair'}Result({','.join(map(str, args))},PV_npvsGood,static_cast<int>(run_period))",
        dependencies=args,
        data_expression="ROOT::RVecF{1.f,1.f,1.f,1.f,1.f,1.f,1.f,1.f}",
        setup=(
            f"from common.selected_trigger_adapter import declare_canonical_trigger; declare_canonical_trigger({era_cfg['l2tight_era']!r})",
        ),
        declarations=(f'#include "{common / "macros/trigger.cc"}"',),
    )
    target = analysis.union(f"{name}_members", z, x) if x else z.view
    return analysis.correction(
        name,
        target,
        "trigger_union",
        f"{result}[7] > 0.5f ? {result}[4] : std::numeric_limits<float>::quiet_NaN()",
        dependencies=(result,),
        valid=f"{result}[7] > 0.5f",
        calibration=f"canonical TrigMaker:{era_cfg['l2tight_era']}:selected-{'four' if x else 'pair'}",
        declarations=("#include <limits>",),
    )


def cleanjet_source(analysis, era_cfg, *, name="jets"):
    """Every field is in CleanJet order, including mapped native Jet fields."""
    fields = {key: f"CleanJet_{key}" for key in ("pt", "eta", "phi")}
    fields["jet_index"] = "CleanJet_jetIdx"
    fields.update(
        tag=f"ZH4lViews::take(Jet_{era_cfg['btag']['algo']},CleanJet_jetIdx)",
        flavor="ZH4lViews::take(Jet_hadronFlavour,CleanJet_jetIdx)",
    )
    source = analysis.source(
        name,
        "jet",
        fields,
        lineage="retained CleanJet with CleanJet_jetIdx -> Jet",
        identity="CleanJet",
    )
    converted = []
    for field, column in source.fields:
        if field in {"tag", "flavor"}:
            column = replace(
                column,
                declarations=(
                    f'#include "{Path(__file__).resolve().parent / "macros/views.h"}"',
                ),
            )
        if field == "flavor":
            column = replace(
                column, data_expression="ROOT::RVecI(CleanJet_pt.size(),0)"
            )
        analysis.columns[column.name] = column
        converted.append((field, column))
    return replace(source, fields=tuple(converted))


def b_veto(analysis, name, jets, era_cfg, *, min_pt=20.0, max_eta=2.5):
    """Loose fixed-WP veto and correction on the same accepted jet subset.

    The retained provider supports the configured loose WP and acceptance
    inside pT>20, |eta|<2.5. A tighter subset is explicit; other domains require
    a separate scientifically supported provider.
    """
    from .eras import (
        resolve_btag_efficiency_map,
        resolve_btag_sf_payload,
        resolve_btag_working_point,
    )

    if jets.source.kind != "jet" or min_pt < 20 or not 0 < max_eta <= 2.5:
        raise ValueError(
            "The fixed-WP provider requires a jet view within pT>20 and |eta|<2.5"
        )
    config = era_cfg["btag"]
    wp = resolve_btag_working_point(
        config["correction_file"], config["correction_prefix"], "L"
    )
    if abs(wp - float(config["veto_wp"])) > 5.0e-5:
        raise ValueError("Configured and POG b-tag working points disagree")
    pt = analysis.take(f"{name}_input_pt", jets, "pt")
    eta = analysis.take(f"{name}_input_eta", jets, "eta")
    idx = analysis._helper(
        f"{name}_index",
        f"ZH4lViews::take({jets.indices},ZH4lViews::indices({pt},({pt}>{float(min_pt)}) && (abs({eta})<{float(max_eta)}),false))",
        (jets.indices, pt, eta),
    )
    selected = analysis.subset(f"{name}_jets", jets, idx)
    pt = analysis.take(f"{name}_pt", selected, "pt")
    eta = analysis.take(f"{name}_eta", selected, "eta")
    # Adapt aligned selected fields to the established kernel's index argument.
    # Original CleanJet -> Jet identity remains available through jet_index.
    native_idx = analysis._helper(
        f"zh4l_internal_{name}_local_index",
        f"ZH4lViews::indices({pt},ROOT::RVecB({pt}.size(),true),false)",
        (pt,),
    )
    tag = analysis.take(f"{name}_tag", selected, "tag")
    flavor = analysis.take(f"{name}_flavor", selected, "flavor")
    include = (f'#include "{Path(__file__).resolve().parent / "macros/btag.cc"}"',)
    decision = analysis.column(
        f"event_pass_{name}",
        f"FixedWPBTag::veto({pt},{eta},{native_idx},{tag},{wp},20.f)",
        dependencies=(pt, eta, native_idx, tag),
        declarations=include,
    )
    efficiency = resolve_btag_efficiency_map(config["efficiency_map"])
    payload = resolve_btag_sf_payload(config["correction_file"])
    values = []
    for group in (0, 1):
        values.append(
            f"FixedWPBTag::eventSF({pt},{eta},{native_idx},{flavor},{tag},{json.dumps(efficiency)},{json.dumps(payload)},{json.dumps(config['correction_prefix'])},\"central\",{group},{wp})"
        )
    correction = analysis.correction(
        f"sf_{name}",
        selected,
        "btag_veto",
        " * ".join(values),
        dependencies=(pt, eta, native_idx, flavor, tag, decision),
        valid=str(decision),
        calibration=f"{payload}:{efficiency}:L:{min_pt}:{max_eta}",
        declarations=include,
    )
    return decision, correction
