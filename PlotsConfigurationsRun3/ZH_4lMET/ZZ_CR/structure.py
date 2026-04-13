structure = {}
_samples_dict = globals().get("samples", {})

for sample_name in _samples_dict:
    structure[sample_name] = {
        "isSignal": 0,
        "isData": 1 if sample_name == "DATA" else 0,
    }
