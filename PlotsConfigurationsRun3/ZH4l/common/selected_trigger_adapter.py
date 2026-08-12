"""Declaration-only bridge to the canonical mkShapesRDF TrigMaker.

The analysis calculator itself is C++ and lives in
``macros/trigger.cc``.  This module deliberately asks the
canonical producer to declare its payload readers and exact event formulae on
a no-op dataframe.  No run period is generated and no framework file is
modified.
"""

import threading


_LOCK = threading.Lock()
_DECLARED_ERA = None


class _DeclarationOnlyDataFrame:
    def Define(self, *_args, **_kwargs):
        return self

    def Redefine(self, *_args, **_kwargs):
        return self

    def DropColumns(self, *_args, **_kwargs):
        return self


def declare_canonical_trigger(era):
    """Declare one canonical TrigMaker era in the active ROOT interpreter."""
    global _DECLARED_ERA
    with _LOCK:
        if _DECLARED_ERA == era:
            return
        if _DECLARED_ERA is not None:
            raise RuntimeError(
                "Canonical TrigMaker C++ names are process-global: attempted "
                f"to load {era!r} after {_DECLARED_ERA!r}"
            )

        from mkShapesRDF.processor.modules.TrigMaker import TrigMaker

        producer = TrigMaker(
            era=era,
            isData=False,
            keepRunP=True,
            seeded=False,
            computeSF=True,
        )
        producer.runModule(_DeclarationOnlyDataFrame(), {})
        _DECLARED_ERA = era


def declared_era():
    return _DECLARED_ERA
