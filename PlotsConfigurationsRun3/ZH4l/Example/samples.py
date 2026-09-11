"""One exact file per process; imports and compilation never list a campaign."""

from common.samples import materialize_catalog

sample_names = ("ZZ", "ZH_Zto2L_Hto2Wto2L2Nu_M125")
input_directory = (
    "root://eoscms.cern.ch//store/group/phys_higgs/cmshww/amassiro/HWWNano/"
    "Summer24_150x_nAODv15_Full2024v15/"
    "MCl2loose2024v15__MCCorr2024v15__JERFrom23BPix__l2tight"
)
selected_samples = os.environ.get("SAMPLE_FILTER", ",".join(sample_names))
if not selected_samples or not set(selected_samples.split(",")) <= set(sample_names):
    raise ValueError(f"Example SAMPLE_FILTER must select from {sample_names}")
pinned_files = {
    name: [f"{input_directory}/nanoLatino_{name}__part0.root"] for name in sample_names
}
# Native weight includes XSWeight, METFilter_Common, puWeight, luminosity and
# catalogue component normalization. Selected-object SFs are added in analysis.py.
samples = materialize_catalog(
    "puWeight",
    remote_io=remoteIO,
    sample_filter=selected_samples,
    pinned_files=pinned_files,
)["samples"]
