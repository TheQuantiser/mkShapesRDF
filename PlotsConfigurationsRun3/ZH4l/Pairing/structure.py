"""Minimal process structure; the study does not build datacards."""

structure = {}
for _sample in PAIRING_ERA["inventory"]["ZH"]:
    structure[_sample] = {"isSignal": 1, "isData": 0}
for _sample in PAIRING_ERA["inventory"]["ZZ"]:
    structure[_sample] = {"isSignal": 0, "isData": 0}
