"""Edit this file to change objects, selections, correction recipes or outputs."""

from common.definitions import Analysis
from common.outputs import branches
from common.presets import nominal_pairs, cleanjet_source, b_veto, trigger_sf
from common.selections import all_of, ordered_pt, window
from common.presentation import build_plot, build_structure

analysis = Analysis()

# Z uses the era's prompt-lepton MVA WPs; X uses retained WPs without that MVA.
# The two pairs share physical Lepton indices but retain separate SF domains.
z, x = nominal_pairs(
    analysis,
    ERA_CONFIG,
    x_wps=("mvaWinter22V2Iso_WP90", "cut_Tight_HWW"),
)
zx = analysis.combine("zx", z, x)
zx_lepton_pt = analysis.take("zx_lepton_pt", zx, "pt")
zx_lepton_pdg_id = analysis.take("zx_lepton_pdg_id", zx, "pdg_id")
zx_min_pair_mass = analysis.column(
    "zx_min_pair_mass",
    f"FourLepton::minimumSelectedPairMass(Lepton_pt,Lepton_eta,Lepton_phi,Lepton_pdgId,{z.indices},{x.indices})",
    dependencies=(z.indices, x.indices),
)
x_is_same_flavor = analysis.column(
    "x_is_same_flavor",
    f"FourLepton::pairFlavor(Lepton_pdgId,{x.indices}) != 0",
    dependencies=(x.indices,),
)
met_pt = analysis.column("met_pt", "PuppiMET_pt")

jets = analysis.view("jets", cleanjet_source(analysis, ERA_CONFIG), order="pt")
event_pass_b_veto, sf_b_veto = b_veto(analysis, "b_veto", jets, ERA_CONFIG)
accepted_jets = sf_b_veto.target
accepted_jet_index = analysis.take("accepted_jet_index", accepted_jets, "jet_index")
accepted_jet_pt = analysis.take("accepted_jet_pt", accepted_jets, "pt")
accepted_jet_tag = analysis.take("accepted_jet_tag", accepted_jets, "tag")

sf_lepton_z = analysis.lepton_sf("sf_lepton_z", z)
sf_lepton_x = analysis.lepton_sf("sf_lepton_x", x)
sf_trigger_zx = trigger_sf(analysis, "sf_trigger_zx", z, ERA_CONFIG, x=x)
weight_base = analysis.weight("weight_base")
weight_raw = analysis.weight("weight_raw", base="1.0")
weight_lepton = analysis.weight(
    "weight_lepton", sf_lepton_z, sf_lepton_x, base=weight_base
)
weight_lepton_trigger = analysis.weight(
    "weight_lepton_trigger", sf_trigger_zx, base=weight_lepton
)
weight_nominal = analysis.weight(
    "weight_nominal", sf_b_veto, base=weight_lepton_trigger
)

z_pass_mass_window = window(analysis, "z_pass_mass_window", z.mass, 76.1876, 106.1876)
zx_pass_ordered_pt = ordered_pt(
    analysis, "zx_pass_ordered_pt", zx, (25.0, 15.0, 10.0, 10.0)
)
zx_pass_quality = analysis.column(
    "zx_pass_quality",
    f"{x.mass}>4. && {zx.mass}>0. && {zx_min_pair_mass}>12. && Sum(Lepton_pt>=10.f)==4",
    dependencies=(x.mass, zx.mass, zx_min_pair_mass),
)
four_lepton = analysis.region(
    "four_lepton",
    all_of(
        analysis,
        "zx_pass_baseline",
        zx.valid,
        z_pass_mass_window,
        zx_pass_ordered_pt,
        zx_pass_quality,
    ),
    weight=weight_lepton_trigger,
)
veto = analysis.region(
    "b_veto", event_pass_b_veto, parent=four_lepton, weight=weight_nominal
)
zz_control = analysis.region(
    "zz_control",
    f"{x_is_same_flavor} && {x.mass}>75. && {x.mass}<105. && {met_pt}<35.",
    dependencies=(x_is_same_flavor, x.mass, met_pt),
    parent=veto,
)
x_same_flavor = analysis.region(
    "x_same_flavor",
    f"{x_is_same_flavor} && {x.mass}>10. && {x.mass}<65. && {met_pt}>35. && {zx.mass}>140.",
    dependencies=(x_is_same_flavor, x.mass, met_pt, zx.mass),
    parent=veto,
)
x_different_flavor = analysis.region(
    "x_different_flavor",
    f"!{x_is_same_flavor} && {x.mass}>10. && {x.mass}<70. && {met_pt}>20.",
    dependencies=(x_is_same_flavor, x.mass, met_pt),
    parent=veto,
)
veto_regions = [veto, zz_control, x_same_flavor, x_different_flavor]
regions = [four_lepton, *veto_regions]

# One booking inherits the appropriate total weight for each region.
for column, edges, title in (
    (z.mass, (60, 75, 80, 85, 90, 95, 100, 105, 120), "m(Z) [GeV]"),
    (x.mass, (0, 10, 20, 35, 50, 65, 75, 85, 95, 105, 120), "m(X) [GeV]"),
    (zx.mass, (60, 100, 140, 180, 220, 300, 400, 600), "m(4l) [GeV]"),
    (met_pt, (0, 20, 35, 50, 80, 120, 200), "Missing pT [GeV]"),
    (zx_lepton_pt, (0, 10, 15, 25, 40, 60, 100, 200), "Selected lepton pT [GeV]"),
):
    analysis.histogram(str(column), column, edges, regions=regions, title=title, fold=3)

# Same population and observable; change only the declared weight recipe.
for recipe in (weight_raw, weight_base, weight_lepton, weight_lepton_trigger):
    analysis.histogram(
        f"x_mass_{recipe.name}",
        x.mass,
        (0, 10, 20, 35, 50, 65, 75, 85, 95, 105, 120),
        regions=[veto],
        weight=recipe,
        title="m(X) [GeV]",
        fold=3,
    )

fields = branches(
    "identity",
    "source",
    z,
    x,
    zx,
    zx_lepton_pt,
    zx_lepton_pdg_id,
    zx_min_pair_mass,
    met_pt,
    accepted_jets,
    accepted_jet_index,
    accepted_jet_pt,
    accepted_jet_tag,
    event_pass_b_veto,
    sf_lepton_z,
    sf_lepton_x,
    sf_trigger_zx,
    sf_b_veto,
    weight_base,
    weight_raw,
    weight_lepton,
    weight_lepton_trigger,
    weight_nominal,
    *(region.selection for region in regions),
)
# The broad tree exports validity for the unapplied b-veto correction. Its
# chosen weight excludes that correction; veto-region trees use the full recipe.
analysis.tree(
    "baseline_events", fields, regions=[four_lepton], weight=weight_lepton_trigger
)
analysis.tree("selected_events", fields, regions=veto_regions, weight=weight_nominal)
preselection = analysis.column(
    "event_pass_preselection",
    "METFilter_Common && (Trigger_ElMu || Trigger_sngMu || Trigger_dblMu || Trigger_sngEl || Trigger_dblEl)"
    " && nLepton>=4 && Sum(CleanJet_pt>30 && CleanJet_pt<50 && abs(CleanJet_eta)>2.5 && abs(CleanJet_eta)<3.0)==0",
)
globals().update(analysis.compile(mode=ZH4L_OUTPUT_MODE, preselections=preselection))
groupPlot, plot, legend = build_plot(samples, FULL_CONFIG, lumi)
legend["lumi"] = "MC subset (example)"
structure = build_structure(samples, FULL_CONFIG)
