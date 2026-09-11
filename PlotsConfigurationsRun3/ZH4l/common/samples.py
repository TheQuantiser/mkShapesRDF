"""Callable boundary around the canonical family catalogue and discovery."""

from pathlib import Path
from collections.abc import Mapping

from . import eras


def pinned_file_list(mapping, source):
    """Validate an explicit source-file override; None requests discovery."""
    if mapping is None:
        return None
    if not isinstance(mapping, Mapping) or source not in mapping:
        raise ValueError(f"PINNED_FILES requires a file list for {source}")
    files = mapping[source]
    if (
        not isinstance(files, (list, tuple))
        or not files
        or not all(isinstance(path, str) and path for path in files)
    ):
        raise ValueError(f"Invalid pinned file list for {source}")
    return list(files)


def materialize_catalog(
    correction_weight,
    *,
    remote_io=None,
    sample_profile="full",
    sample_filter=None,
    pinned_files=None,
):
    """Return the native samples and catalogue helpers for shared-global leaves.

    Importing this module does no discovery. ``pinned_files`` maps exact
    physical source names to explicit URIs and bypasses listing for those
    sources. A supplied mapping is complete: missing sources fail closed.
    """
    namespace = {
        name: value for name, value in vars(eras).items() if not name.startswith("_")
    }
    namespace.update(
        CORRECTION_WEIGHT=correction_weight,
        remoteIO=remote_io or {},
        SAMPLE_PROFILE=sample_profile,
        SAMPLE_FILTER=sample_filter,
        PINNED_FILES=pinned_files,
    )
    path = Path(__file__).with_name("catalog.py")
    namespace["__file__"] = str(path)
    exec(compile(path.read_text(), str(path), "exec"), namespace, namespace)
    return {
        name: value for name, value in namespace.items() if not name.startswith("__")
    }
