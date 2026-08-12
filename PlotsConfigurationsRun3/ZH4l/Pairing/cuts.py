"""Pairing-independent reconstructed-object denominators."""

# Quartet topology is deliberately a histogram axis, not a cut category.  This
# keeps all five mutually exclusive topologies in one graph without multiplying
# every histogram action by five.
preselections = "nLepton >= 4"

cuts = {
    "PAIRING_OBJECT_BASE": "PairingObjectBase",
    "PAIRING_PHYS_BASE": "PairingPhysBase",
}
