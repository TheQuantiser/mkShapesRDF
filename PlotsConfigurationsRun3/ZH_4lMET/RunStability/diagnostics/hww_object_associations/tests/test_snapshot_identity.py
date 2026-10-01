"""Synthetic high-bit identity checks of the real Cache/Snapshot callback.

The signed case explicitly encodes unsigned event IDs in two's complement:
u <= 2**63-1 maps to u, otherwise to u-2**64. Reinterpret signed output as
uint64 to invert this mapping. The native unsigned case is a strict expected
failure: the current callback loses uint64 typing through Python lists. This
separate serialization limitation is not part of the association repair.
This fixture does not alter production code.
"""

import numpy as np
import pytest
import uproot


@pytest.mark.parametrize(
    "signed_bridge",
    [
        pytest.param(
            False,
            marks=pytest.mark.xfail(
                strict=True,
                raises=RuntimeError,
                reason="Snapshot converts uint64 event IDs to untyped Python lists; "
                "awkward reconstruction fails at 2**63 (mRDF.py:546)",
            ),
        ),
        True,
    ],
)
def test_snapshot_preserves_full_event_identity(tmp_path, signed_bridge):
    import ROOT
    from mkShapesRDF.processor.framework.mRDF import mRDF
    from mkShapesRDF.processor.modules.Snapshot import Snapshot

    if ROOT.IsImplicitMTEnabled():
        raise RuntimeError("The configured Snapshot callback requires serial Range")
    events = np.array([0, 2**63 - 1, 2**63, 2**63 + 1, 2**64 - 1], dtype=np.uint64)
    runs = np.array([1, 2, 3, 4, 5], dtype=np.uint32)
    lumis = np.array([10, 20, 30, 40, 50], dtype=np.uint32)
    source = tmp_path / "unsigned-input.root"
    output = tmp_path / "snapshot.root"
    with uproot.recreate(source) as root:
        root.mktree(
            "Events", {"run": "uint32", "luminosityBlock": "uint32", "event": "uint64"}
        )
        root["Events"].extend({"run": runs, "luminosityBlock": lumis, "event": events})
    frame = mRDF().readRDF("Events", str(source))
    if signed_bridge:
        # Avoid an out-of-range unsigned-to-signed cast in the fixture itself.
        frame = frame.Redefine(
            "event",
            "event <= 9223372036854775807ULL ? static_cast<Long64_t>(event) "
            ": -static_cast<Long64_t>(18446744073709551615ULL-event)-1",
        )
    values = []
    frame = Snapshot(
        str(output),
        ["run", "luminosityBlock", "event"],
        str(tmp_path),
        output.name,
        includeVariations=False,
        splitVariations=False,
        storeNominals=True,
    ).runModule(frame, values)
    snapshots = [value for value in values if value[0] == "snapshot"]
    assert len(snapshots) == 1
    callback, columns = snapshots[0][1]
    cache = frame.df.Cache(columns)
    assert cache.Count().GetValue() == len(events)
    callback(cache)
    with uproot.open(output) as root:
        assert root["Events"].num_entries == len(events)
        observed = root["Events"].arrays(
            ["run", "luminosityBlock", "event"], library="np"
        )
    np.testing.assert_array_equal(observed["run"], runs)
    np.testing.assert_array_equal(observed["luminosityBlock"], lumis)
    assert observed["event"].dtype.kind in "iu", "Identity must never become float"
    if signed_bridge:
        assert observed["event"].dtype == np.dtype("int64")
        np.testing.assert_array_equal(observed["event"], events.view(np.int64))
    decoded = observed["event"].astype(np.uint64, copy=False)
    np.testing.assert_array_equal(decoded, events)
