from common.eras import load_selected_era
from common.presentation import build_structure

_, _, _full_cfg = load_selected_era()
structure = build_structure(samples, _full_cfg)
