"""Deterministic runtime-package construction and safe worker extraction."""

import argparse
import gzip
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "artifacts",
    "codex_analysis",
    "condor",
    "configs",
    "jobs",
    "logs",
    "myenv",
    "rootFiles",
}
EXCLUDED_FILE_SUFFIXES = {".pyc", ".pyo", ".log", ".out", ".err", ".pkl"}
EXCLUDED_ARCHIVE_SUFFIXES = {".tgz", ".tar", ".zip"}
SOURCE_LIKE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".py",
    ".sh",
}


class RuntimePackageError(RuntimeError):
    """A runtime archive cannot be built or safely extracted."""


@dataclass(frozen=True)
class PackageLayout:
    archive: str
    manifest: str
    archive_sha256: str
    members: tuple
    config_archive_root: str
    relocations: tuple
    required_members: tuple


def _is_within(path, root):
    try:
        return os.path.commonpath((str(path), str(root))) == str(root)
    except ValueError:
        return False


def _git_tracked_files(path):
    """Return tracked absolute paths without reading or hashing their content."""
    path = Path(path).resolve()
    git_root = None
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            git_root = candidate
            break
    if git_root is None:
        return set()
    try:
        result = subprocess.run(
            ["git", "-C", str(git_root), "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return set()
    return {
        (git_root / item.decode("utf-8", errors="surrogateescape")).resolve()
        for item in result.stdout.split(b"\0")
        if item
    }


def _credential_like_name(path):
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name == ".netrc" or name.startswith("x509up_"):
        return True
    if suffix in {".key", ".pem", ".p12", ".pfx"}:
        return True
    if any(token in name for token in ("credential", "secret", "bearer", "token")):
        return True
    # Physics/source helpers such as proxyW.cc are not credentials.
    if "proxy" in name and suffix not in SOURCE_LIKE_SUFFIXES:
        return True
    return False


def _excluded(path, relative, role, tracked_files, destination):
    if path == destination:
        return True
    if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative.parts[:-1]):
        return True
    if path.name == "start.sh" or _credential_like_name(path):
        return True
    suffix = path.suffix.lower()
    if suffix in EXCLUDED_FILE_SUFFIXES or suffix in EXCLUDED_ARCHIVE_SUFFIXES:
        return True
    if path.name.endswith(".tar.gz"):
        return True
    # Untracked ROOT files are normally generated outputs.  Tracked calibration
    # ROOT data remain package inputs; a non-Git external resource can be added
    # explicitly with condorRuntimeIncludes/--runtime-include.
    if (
        suffix == ".root"
        and path.resolve() not in tracked_files
        and role != "include-file"
    ):
        return True
    return False


def _iter_source_files(root, archive_root, role, destination, framework_minimal=False):
    root = Path(root).resolve()
    destination = Path(destination).resolve()
    tracked_files = _git_tracked_files(root)
    if root.is_file():
        candidates = [root]
        source_base = root.parent
        role = "include-file"
    else:
        candidates = sorted(root.rglob("*"), key=lambda item: item.as_posix())
        source_base = root

    for path in candidates:
        relative = path.relative_to(source_base)
        if path.is_dir() and not path.is_symlink():
            continue
        if framework_minimal and relative.parts:
            top = relative.parts[0]
            if top != "mkShapesRDF" and relative.parts[:2] != ("utils", "bin"):
                continue
        if _excluded(path, relative, role, tracked_files, destination):
            continue
        source = path
        if path.is_symlink():
            source = path.resolve(strict=True)
            if not source.is_file() or not _is_within(source, root):
                raise RuntimePackageError(
                    f"Runtime input symlink must resolve to a regular file below {root}: {path}"
                )
        elif not path.is_file():
            raise RuntimePackageError(f"Unsupported runtime input type: {path}")
        arcname = PurePosixPath(archive_root) / PurePosixPath(relative.as_posix())
        yield source, arcname.as_posix(), role


def _write_deterministic_archive(entries, destination):
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    if temporary.exists():
        temporary.unlink()
    try:
        with temporary.open("wb") as raw:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0
            ) as compressed:
                with tarfile.open(
                    fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT
                ) as archive:
                    for source, arcname, _role in entries:
                        source_stat = source.stat()
                        info = tarfile.TarInfo(arcname)
                        info.size = source_stat.st_size
                        info.mode = 0o755 if source_stat.st_mode & 0o111 else 0o644
                        info.uid = 0
                        info.gid = 0
                        info.uname = ""
                        info.gname = ""
                        info.mtime = 0
                        info.type = tarfile.REGTYPE
                        with source.open("rb") as stream:
                            archive.addfile(info, stream)
        os.replace(temporary, destination)
        os.chmod(destination, 0o644)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def build_runtime_archive(
    framework_root,
    config_root,
    destination,
    additional_includes=None,
):
    """Build a deterministic archive from framework, selected config, and opt-ins."""
    framework_root = Path(framework_root).resolve()
    config_root = Path(config_root).resolve()
    destination = Path(destination).resolve()
    if not framework_root.is_dir():
        raise RuntimePackageError(
            f"Framework root is not a directory: {framework_root}"
        )
    if not config_root.is_dir():
        raise RuntimePackageError(
            f"Configuration root is not a directory: {config_root}"
        )

    has_framework_package = (framework_root / "mkShapesRDF" / "__init__.py").is_file()
    if config_root == framework_root:
        config_archive_root = "."
    elif _is_within(config_root, framework_root):
        config_archive_root = config_root.relative_to(framework_root).as_posix()
    else:
        config_archive_root = "configuration"

    entries = list(
        _iter_source_files(
            framework_root,
            ".",
            "framework",
            destination,
            framework_minimal=has_framework_package,
        )
    )
    if config_root != framework_root:
        entries.extend(
            _iter_source_files(
                config_root, config_archive_root, "configuration", destination
            )
        )

    relocations = [(str(framework_root), "."), (str(config_root), config_archive_root)]
    for index, include in enumerate(additional_includes or []):
        include_path = Path(include).expanduser()
        if not include_path.is_absolute():
            include_path = config_root / include_path
        include_path = include_path.resolve(strict=True)
        safe_name = (
            "".join(
                char if char.isalnum() or char in "._-" else "_"
                for char in include_path.name
            )
            or f"include_{index}"
        )
        archive_root = f"runtime_includes/{index:03d}_{safe_name}"
        if include_path.is_file():
            entries.append((include_path, archive_root, "include-file"))
        else:
            entries.extend(
                _iter_source_files(
                    include_path,
                    archive_root,
                    "include",
                    destination,
                )
            )
        relocations.append((str(include_path), archive_root))

    by_name = {}
    for source, arcname, role in entries:
        normalized = PurePosixPath(arcname).as_posix()
        while normalized.startswith("./"):
            normalized = normalized[2:]
        if not normalized or PurePosixPath(normalized).is_absolute():
            raise RuntimePackageError(f"Invalid archive member name: {arcname!r}")
        if normalized in by_name:
            if by_name[normalized][0] == source:
                continue
            raise RuntimePackageError(f"Duplicate runtime archive member: {normalized}")
        by_name[normalized] = (source, normalized, role)
    ordered = [by_name[name] for name in sorted(by_name)]
    if not ordered:
        raise RuntimePackageError("Runtime archive would be empty")

    required = []
    if has_framework_package:
        required.extend(
            [
                "mkShapesRDF/__init__.py",
                "mkShapesRDF/lib/remote_io.py",
                "mkShapesRDF/shapeAnalysis/runner.py",
            ]
        )
    config_member = (
        "configuration.py"
        if config_archive_root in ("", ".")
        else f"{config_archive_root}/configuration.py"
    )
    if (config_root / "configuration.py").is_file():
        required.append(config_member)

    _write_deterministic_archive(ordered, destination)
    archive_sha256 = hashlib.sha256(destination.read_bytes()).hexdigest()
    manifest_path = destination.with_name(destination.name + ".manifest.json")
    manifest = {
        "schema_version": 1,
        "archive_name": destination.name,
        "archive_sha256": archive_sha256,
        "archive_size": destination.stat().st_size,
        "config_archive_root": config_archive_root,
        "required_members": required,
        "members": [
            {
                "name": arcname,
                "size": source.stat().st_size,
                "mode": "0755" if source.stat().st_mode & 0o111 else "0644",
                "role": role,
            }
            for source, arcname, role in ordered
        ],
        "excluded_categories": sorted(EXCLUDED_DIRECTORY_NAMES),
        "credentials_in_archive": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return PackageLayout(
        archive=str(destination),
        manifest=str(manifest_path),
        archive_sha256=archive_sha256,
        members=tuple(item[1] for item in ordered),
        config_archive_root=config_archive_root,
        relocations=tuple(relocations),
        required_members=tuple(required),
    )


def safe_extract_runtime_archive(archive_path, destination, required_members=None):
    """Extract regular files only after validating the entire archive manifest."""
    archive_path = Path(archive_path).resolve()
    destination = Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise RuntimePackageError(f"Extraction directory is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:*") as archive:
        members = archive.getmembers()
        seen = set()
        validated = []
        for member in members:
            name = member.name
            pure = PurePosixPath(name)
            if (
                not name
                or pure.is_absolute()
                or ".." in pure.parts
                or "\\" in name
                or name in seen
            ):
                raise RuntimePackageError(f"Unsafe runtime archive member: {name!r}")
            if not member.isfile() and not member.isdir():
                raise RuntimePackageError(
                    f"Unsupported runtime archive member type: {name!r}"
                )
            if member.mode & (stat.S_ISUID | stat.S_ISGID):
                raise RuntimePackageError(
                    f"Unsafe special mode on archive member: {name!r}"
                )
            target = (destination / Path(*pure.parts)).resolve()
            if not _is_within(target, destination):
                raise RuntimePackageError(
                    f"Archive member escapes extraction root: {name!r}"
                )
            seen.add(name)
            validated.append((member, target))
        missing = sorted(set(required_members or []) - seen)
        if missing:
            raise RuntimePackageError(
                "Runtime archive is missing required members: " + ", ".join(missing)
            )
        for member, target in validated:
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimePackageError(f"Cannot read archive member: {member.name}")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            os.chmod(target, 0o755 if member.mode & 0o111 else 0o644)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    extract = subparsers.add_parser("extract")
    extract.add_argument("archive")
    extract.add_argument("destination")
    extract.add_argument("--require", action="append", default=[])
    args = parser.parse_args(argv)
    if args.command == "extract":
        safe_extract_runtime_archive(args.archive, args.destination, args.require)


if __name__ == "__main__":
    main()
