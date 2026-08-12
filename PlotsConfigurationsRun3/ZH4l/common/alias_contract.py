"""Fail-closed ownership and collision policy for public ZH4l aliases."""

from .corrections import PUBLIC_CORRECTION_ALIASES
from .objects import PUBLIC_OBJECT_ALIASES
from .observables import PUBLIC_OBSERVABLE_ALIASES


COMMON_PUBLIC_ALIASES = frozenset(
    PUBLIC_OBJECT_ALIASES | PUBLIC_CORRECTION_ALIASES | PUBLIC_OBSERVABLE_ALIASES
)

# These well-known framework names have different domains or meanings and may
# never be repurposed by this family.
FORBIDDEN_NATIVE_COLLISIONS = frozenset(
    {"mll", "TriggerSFWeight_2l", "TriggerSFWeight_4l"}
)

# The common implementation deliberately supplies the standard physical loose
# 20-GeV veto semantics.  This is an identical-semantic reuse, not an overload.
INTENTIONAL_IDENTICAL_REUSE = frozenset({"bVeto"})


def classify_alias(name):
    if name.startswith("ZH4l_"):
        return "family-private"
    if name in FORBIDDEN_NATIVE_COLLISIONS:
        return "collision/error"
    if name in INTENTIONAL_IDENTICAL_REUSE:
        return "intentional-identical-reuse"
    if name in COMMON_PUBLIC_ALIASES:
        return "safe"
    return "study-local"
