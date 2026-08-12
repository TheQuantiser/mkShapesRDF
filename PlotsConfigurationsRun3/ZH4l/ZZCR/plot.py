"""Visual process groups derived from the common catalogue."""

from common.eras import load_selected_era
from common.presentation import build_plot

_, _era_cfg, _full_cfg = load_selected_era()
groupPlot, plot, legend = build_plot(samples, _full_cfg, _era_cfg["lumi_fb"])
