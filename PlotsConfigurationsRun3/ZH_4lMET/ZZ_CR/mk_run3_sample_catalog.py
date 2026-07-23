#!/usr/bin/env python3
"""Build a Run-3 HWWNano file list and a structured sample catalog.

The program has two primary modes:

1. ``crawl`` discovers files on EOS, writes the traditional text file, then
   re-reads that exact text file to build the JSON catalog.
2. ``index`` builds or rebuilds the JSON catalog from an existing text file
   without contacting EOS.

The default text-list semantics match the preceding Bash implementation:
only ``nanoLatino_*__part0.root`` files are selected, nominal paths are written
first, one blank line separates them from systematic paths, and systematic
paths are recognized by a processing suffix ending in ``do_suffix`` or
``up_suffix``.

Only the Python standard library is required. Python 3.9 or newer is supported.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import datetime as dt
import hashlib
import json
import logging
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Mapping, MutableMapping, Optional, Sequence


PROGRAM = "mk_run3_sample_catalog"
VERSION = "1.0.0"
SCHEMA_VERSION = "1.0"

DEFAULT_BASE = "/eos/cms/store/group/phys_higgs/cmshww"
DEFAULT_YEARS = (2022, 2023, 2024, 2025)
DEFAULT_FIND_REGEX_PART0 = r".*__part0[.]root$"
DEFAULT_FIND_REGEX_ALL_PARTS = r".*__part[0-9]+[.]root$"
DEFAULT_EXCLUDED_OWNER_PREFIXES = ("TO_DELETE", "crab3checkwrite_")

TRUNCATION_PATTERNS = (
    re.compile(r"result\s+is\s+truncated", re.IGNORECASE),
    re.compile(r"results\s+are\s+limited", re.IGNORECASE),
)

FILE_NAME_RE = re.compile(
    r"^nanoLatino_(?P<sample>.+)__part(?P<part>[0-9]+)[.]root$"
)
VARIATION_TOKEN_RE = re.compile(
    r"^(?P<systematic>.*?)(?P<raw_direction>do|up)_suffix$"
)
DATA_SAMPLE_RE = re.compile(
    r"^(?P<dataset>.+)_(?P<run_tag>Run(?P<run_year>20[0-9]{2})(?P<run_era>[A-Z]).*)$"
)
CAMPAIGN_YEAR_RE = re.compile(r"(?:Summer|Run)(?P<year>20[0-9]{2}|[0-9]{2})")
NANOAOD_VERSION_RE = re.compile(r"nAODv(?P<version>[0-9]+)")
CMSSW_SERIES_RE = re.compile(r"(?:^|_)(?P<series>[0-9]{3}x)(?:_|$)")
FULL_VERSION_RE = re.compile(r"(?P<full>Full20[0-9]{2}v[0-9]+)")


class CatalogError(RuntimeError):
    """Base exception for controlled failures."""


class ConfigurationError(CatalogError):
    """Raised for invalid command-line configuration."""


class EOSCommandError(CatalogError):
    """Raised when an EOS command fails after retries."""

    def __init__(
        self,
        command: Sequence[str],
        returncode: int,
        stderr: str,
        attempts: int,
    ) -> None:
        self.command = tuple(command)
        self.returncode = returncode
        self.stderr = stderr
        self.attempts = attempts
        rendered = " ".join(_shell_quote(part) for part in command)
        super().__init__(
            f"EOS command failed after {attempts} attempt(s), rc={returncode}: "
            f"{rendered}\n{stderr.strip()}"
        )


class EOSResultTruncated(CatalogError):
    """Internal signal that an EOS find result must be subdivided."""


@dataclasses.dataclass(frozen=True)
class DirectoryEntry:
    """One entry returned by ``eos ls -F``."""

    name: str
    path: str
    is_directory: bool


@dataclasses.dataclass(frozen=True)
class FindResult:
    """Result from one recursive EOS find invocation."""

    paths: tuple[str, ...]
    truncated: bool
    stderr: str


@dataclasses.dataclass(frozen=True)
class CampaignRef:
    """A discovered owner/campaign root."""

    owner: str
    campaign: str
    path: str
    year: Optional[int]


@dataclasses.dataclass(frozen=True)
class FileRecord:
    """Normalized interpretation of one HWWNano file path."""

    path: str
    logical_path: Optional[str]
    owner: str
    tree_base: str
    campaign: str
    campaign_root: str
    campaign_year: Optional[int]
    campaign_kind: str
    era: Optional[str]
    cmssw_series: Optional[str]
    nanoaod_version: Optional[str]
    full_version: Optional[str]
    relative_directories: tuple[str, ...]
    processing_path: str
    processing_component: Optional[str]
    processing_steps: tuple[str, ...]
    processing_family: str
    variation_kind: str
    systematic: Optional[str]
    direction: Optional[str]
    raw_direction: Optional[str]
    sample: str
    sample_kind: str
    dataset: Optional[str]
    run_tag: Optional[str]
    run_year: Optional[int]
    run_era: Optional[str]
    part: int
    filename: str
    is_old: bool

    def file_payload(self) -> dict[str, Any]:
        """Return the compact path object stored under a grouped sample."""

        payload: dict[str, Any] = {
            "part": self.part,
            "path": self.path,
        }
        if self.logical_path is not None:
            payload["logical_path"] = self.logical_path
        return payload


@dataclasses.dataclass(frozen=True)
class ParseFailure:
    """A path that could not be normalized into the expected schema."""

    path: str
    reason: str


@dataclasses.dataclass(frozen=True)
class CrawlResult:
    """Complete crawler result before text serialization."""

    paths: tuple[str, ...]
    campaigns: tuple[CampaignRef, ...]
    recovered_events: tuple[dict[str, Any], ...]


class EventRecorder:
    """Thread-safe record of retries, splits, and recoverable events."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def add(self, event: Mapping[str, Any]) -> None:
        with self._lock:
            self._events.append(dict(event))

    def snapshot(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            return tuple(
                sorted(
                    (dict(item) for item in self._events),
                    key=lambda item: (
                        str(item.get("type", "")),
                        str(item.get("path", "")),
                        int(item.get("attempt", 0)),
                    ),
                )
            )


class EOSClient:
    """Small, retrying wrapper around the EOS command-line client."""

    def __init__(
        self,
        *,
        eos_bin: str,
        retries: int,
        initial_backoff: float,
        timeout: float,
        recorder: EventRecorder,
        logger: logging.Logger,
    ) -> None:
        self.eos_bin = eos_bin
        self.retries = retries
        self.initial_backoff = initial_backoff
        self.timeout = timeout
        self.recorder = recorder
        self.logger = logger

    def list_directory(self, path: str) -> tuple[DirectoryEntry, ...]:
        """Return a shallow directory listing using ``eos ls -F``."""

        completed = self._run_with_retries(("ls", "-F", path), operation="ls")
        entries: list[DirectoryEntry] = []
        for raw_line in completed.stdout.splitlines():
            line = raw_line.rstrip("\r").strip()
            if not line:
                continue
            is_directory = line.endswith("/")
            stripped = line[:-1] if is_directory else line
            if stripped.startswith("/"):
                full_path = posixpath.normpath(stripped)
                name = PurePosixPath(full_path).name
            else:
                name = stripped
                full_path = posixpath.join(path.rstrip("/"), name)
            entries.append(
                DirectoryEntry(name=name, path=full_path, is_directory=is_directory)
            )
        return tuple(sorted(entries, key=lambda item: (not item.is_directory, item.name)))

    def find_files(self, root: str, name_regex: str) -> FindResult:
        """Recursively find files and identify EOS result-limit truncation."""

        command = ("find", "-f", "--name", name_regex, root)
        backoff = self.initial_backoff
        last_rc = 1
        last_stderr = ""

        for attempt in range(1, self.retries + 2):
            completed = self._run_once(command)
            last_rc = completed.returncode
            last_stderr = completed.stderr
            truncated = _contains_truncation(completed.stderr)

            if truncated:
                self.recorder.add(
                    {
                        "type": "eos_find_truncated",
                        "path": root,
                        "attempt": attempt,
                        "returncode": completed.returncode,
                    }
                )
                # Partial stdout is intentionally discarded.
                return FindResult(paths=(), truncated=True, stderr=completed.stderr)

            if completed.returncode == 0:
                paths = tuple(
                    sorted(
                        {
                            line.strip()
                            for line in completed.stdout.splitlines()
                            if line.strip()
                        }
                    )
                )
                return FindResult(paths=paths, truncated=False, stderr=completed.stderr)

            if attempt <= self.retries:
                self.recorder.add(
                    {
                        "type": "eos_retry",
                        "operation": "find",
                        "path": root,
                        "attempt": attempt,
                        "returncode": completed.returncode,
                        "stderr": completed.stderr.strip(),
                    }
                )
                self.logger.warning(
                    "EOS find failed for %s (attempt %d/%d, rc=%d); retrying",
                    root,
                    attempt,
                    self.retries + 1,
                    completed.returncode,
                )
                if backoff > 0:
                    time.sleep(backoff)
                backoff *= 2

        raise EOSCommandError(
            (self.eos_bin, *command),
            last_rc,
            last_stderr,
            self.retries + 1,
        )

    def _run_with_retries(
        self,
        command: Sequence[str],
        *,
        operation: str,
    ) -> subprocess.CompletedProcess[str]:
        backoff = self.initial_backoff
        last: Optional[subprocess.CompletedProcess[str]] = None

        for attempt in range(1, self.retries + 2):
            completed = self._run_once(command)
            last = completed
            if completed.returncode == 0:
                return completed

            if attempt <= self.retries:
                self.recorder.add(
                    {
                        "type": "eos_retry",
                        "operation": operation,
                        "path": command[-1] if command else "",
                        "attempt": attempt,
                        "returncode": completed.returncode,
                        "stderr": completed.stderr.strip(),
                    }
                )
                self.logger.warning(
                    "EOS %s failed for %s (attempt %d/%d, rc=%d); retrying",
                    operation,
                    command[-1] if command else "",
                    attempt,
                    self.retries + 1,
                    completed.returncode,
                )
                if backoff > 0:
                    time.sleep(backoff)
                backoff *= 2

        assert last is not None
        raise EOSCommandError(
            (self.eos_bin, *command),
            last.returncode,
            last.stderr,
            self.retries + 1,
        )

    def _run_once(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        argv = [self.eos_bin, *command]
        try:
            return subprocess.run(
                argv,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            stderr = (exc.stderr or "") + f"\nCommand timed out after {self.timeout}s"
            return subprocess.CompletedProcess(
                argv,
                124,
                stdout=exc.stdout or "",
                stderr=stderr,
            )
        except OSError as exc:
            return subprocess.CompletedProcess(
                argv,
                127,
                stdout="",
                stderr=str(exc),
            )


class EOSCrawler:
    """Discover HWWNano campaigns and crawl them concurrently."""

    def __init__(
        self,
        *,
        client: EOSClient,
        base: str,
        years: set[int],
        workers: int,
        find_name_regex: str,
        excluded_owner_prefixes: Sequence[str],
        include_owner_patterns: Sequence[re.Pattern[str]],
        campaign_pattern: Optional[re.Pattern[str]],
        exclude_old: bool,
        max_split_depth: int,
        logger: logging.Logger,
    ) -> None:
        self.client = client
        self.base = base.rstrip("/")
        self.years = years
        self.workers = workers
        self.find_name_regex = find_name_regex
        self.python_file_regex = re.compile(find_name_regex)
        self.excluded_owner_prefixes = tuple(excluded_owner_prefixes)
        self.include_owner_patterns = tuple(include_owner_patterns)
        self.campaign_pattern = campaign_pattern
        self.exclude_old = exclude_old
        self.max_split_depth = max_split_depth
        self.logger = logger

    def crawl(self) -> CrawlResult:
        campaigns = self.discover_campaigns()
        if not campaigns:
            raise CatalogError(
                f"No HWWNano campaigns for years {sorted(self.years)} were found under "
                f"{self.base}"
            )

        self.logger.info(
            "Crawling %d campaign(s) with %d worker(s)",
            len(campaigns),
            self.workers,
        )

        all_paths: set[str] = set()
        failures: list[tuple[CampaignRef, BaseException]] = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.workers,
            thread_name_prefix="eos-campaign",
        ) as executor:
            futures = {
                executor.submit(self._crawl_campaign, campaign): campaign
                for campaign in campaigns
            }
            for future in concurrent.futures.as_completed(futures):
                campaign = futures[future]
                try:
                    paths = future.result()
                except BaseException as exc:  # preserve every campaign failure
                    failures.append((campaign, exc))
                    self.logger.error("Campaign failed: %s: %s", campaign.path, exc)
                    continue
                all_paths.update(paths)
                self.logger.info(
                    "Completed %s/%s: %d file(s)",
                    campaign.owner,
                    campaign.campaign,
                    len(paths),
                )

        if failures:
            details = "\n\n".join(
                f"[{campaign.path}]\n{exception}" for campaign, exception in failures
            )
            raise CatalogError(
                f"{len(failures)} campaign(s) could not be crawled completely. "
                f"No output should be trusted.\n\n{details}"
            )

        return CrawlResult(
            paths=tuple(sorted(all_paths)),
            campaigns=campaigns,
            recovered_events=self.client.recorder.snapshot(),
        )

    def discover_campaigns(self) -> tuple[CampaignRef, ...]:
        self.logger.info("Discovering owners under %s", self.base)
        root_entries = self.client.list_directory(self.base)
        owners = [
            entry.name
            for entry in root_entries
            if entry.is_directory and self._owner_is_selected(entry.name)
        ]

        self.logger.info(
            "Inspecting %d owner director%s",
            len(owners),
            "y" if len(owners) == 1 else "ies",
        )

        campaigns: list[CampaignRef] = []
        failures: list[tuple[str, BaseException]] = []
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.workers,
            thread_name_prefix="eos-owner",
        ) as executor:
            futures = {
                executor.submit(self._discover_owner, owner): owner for owner in owners
            }
            for future in concurrent.futures.as_completed(futures):
                owner = futures[future]
                try:
                    campaigns.extend(future.result())
                except BaseException as exc:
                    failures.append((owner, exc))

        if failures:
            details = "\n\n".join(
                f"[{owner}]\n{exception}" for owner, exception in failures
            )
            raise CatalogError(
                f"{len(failures)} owner director(s) could not be inspected.\n\n{details}"
            )

        return tuple(sorted(campaigns, key=lambda item: (item.owner, item.campaign)))

    def _discover_owner(self, owner: str) -> tuple[CampaignRef, ...]:
        owner_root = posixpath.join(self.base, owner)
        entries = self.client.list_directory(owner_root)
        hwwnano = next(
            (
                entry
                for entry in entries
                if entry.is_directory and entry.name == "HWWNano"
            ),
            None,
        )
        if hwwnano is None:
            return ()

        campaign_entries = self.client.list_directory(hwwnano.path)
        campaigns: list[CampaignRef] = []
        for entry in campaign_entries:
            if not entry.is_directory:
                continue
            campaign = entry.name
            year = infer_campaign_year(campaign)
            if year not in self.years:
                continue
            if self.exclude_old and "_OLD" in campaign:
                continue
            if self.campaign_pattern and not self.campaign_pattern.search(campaign):
                continue
            campaigns.append(
                CampaignRef(
                    owner=owner,
                    campaign=campaign,
                    path=entry.path,
                    year=year,
                )
            )
        return tuple(campaigns)

    def _crawl_campaign(self, campaign: CampaignRef) -> tuple[str, ...]:
        return tuple(sorted(set(self._crawl_tree(campaign.path, depth=0))))

    def _crawl_tree(self, root: str, *, depth: int) -> list[str]:
        result = self.client.find_files(root, self.find_name_regex)
        if not result.truncated:
            return list(result.paths)

        if depth >= self.max_split_depth:
            raise CatalogError(
                f"EOS result remained truncated at split depth {depth} for {root}. "
                f"Increase --max-split-depth only after inspecting this subtree."
            )

        self.logger.warning("EOS result limit reached; splitting subtree: %s", root)
        self.client.recorder.add(
            {
                "type": "subtree_split",
                "path": root,
                "depth": depth,
            }
        )

        entries = self.client.list_directory(root)
        direct_files = [
            entry.path
            for entry in entries
            if not entry.is_directory and self.python_file_regex.fullmatch(entry.name)
        ]
        subdirectories = [entry.path for entry in entries if entry.is_directory]

        if not subdirectories:
            raise CatalogError(
                f"EOS truncated {root}, but a shallow listing exposed no child "
                "directories to split. The namespace cannot be crawled completely "
                "with the current account limits."
            )

        paths = list(direct_files)
        for child in subdirectories:
            paths.extend(self._crawl_tree(child, depth=depth + 1))
        return paths

    def _owner_is_selected(self, owner: str) -> bool:
        if owner.startswith(self.excluded_owner_prefixes):
            return False
        if not self.include_owner_patterns:
            return True
        return any(pattern.search(owner) for pattern in self.include_owner_patterns)


class CatalogBuilder:
    """Build a hierarchical, deterministic JSON document from file records."""

    def __init__(
        self,
        *,
        base: str,
        source_list: Path,
        source_sha256: str,
        input_line_count: int,
        duplicate_input_count: int,
        records: Sequence[FileRecord],
        parse_failures: Sequence[ParseFailure],
        crawl_metadata: Optional[Mapping[str, Any]],
        include_replica_details: bool,
        generated_at: Optional[str] = None,
    ) -> None:
        self.base = base.rstrip("/")
        self.source_list = source_list
        self.source_sha256 = source_sha256
        self.input_line_count = input_line_count
        self.duplicate_input_count = duplicate_input_count
        self.records = tuple(records)
        self.parse_failures = tuple(parse_failures)
        self.crawl_metadata = dict(crawl_metadata or {})
        self.include_replica_details = include_replica_details
        self.generated_at = generated_at or _utc_now_iso()

    def build(self) -> dict[str, Any]:
        owners: dict[str, Any] = {}
        sample_locations: dict[str, list[dict[str, Any]]] = defaultdict(list)
        replica_signatures: dict[tuple[Any, ...], list[FileRecord]] = defaultdict(list)

        by_owner: Counter[str] = Counter()
        by_year: Counter[str] = Counter()
        by_campaign_kind: Counter[str] = Counter()
        by_sample_kind: Counter[str] = Counter()
        by_systematic: Counter[str] = Counter()
        by_direction: Counter[str] = Counter()
        campaigns_seen: set[tuple[str, str]] = set()
        processing_families_seen: set[tuple[str, str, str]] = set()
        samples_seen: set[str] = set()
        nominal_count = 0
        systematic_count = 0
        old_count = 0

        for record in sorted(self.records, key=lambda item: item.path):
            by_owner[record.owner] += 1
            by_year[str(record.campaign_year) if record.campaign_year else "unknown"] += 1
            by_campaign_kind[record.campaign_kind] += 1
            by_sample_kind[record.sample_kind] += 1
            samples_seen.add(record.sample)
            campaigns_seen.add((record.owner, record.campaign))
            processing_families_seen.add(
                (record.owner, record.campaign, record.processing_family)
            )
            if record.is_old:
                old_count += 1

            if record.variation_kind == "systematic":
                systematic_count += 1
                by_systematic[record.systematic or "unknown"] += 1
                by_direction[record.direction or "unknown"] += 1
            else:
                nominal_count += 1

            owner_node = owners.setdefault(
                record.owner,
                {
                    "tree_base": record.tree_base,
                    "counts": {"files": 0, "campaigns": 0},
                    "campaigns": {},
                },
            )
            owner_node["counts"]["files"] += 1

            campaigns = owner_node["campaigns"]
            campaign_node = campaigns.setdefault(
                record.campaign,
                {
                    "campaign_root": record.campaign_root,
                    "metadata": {
                        "year": record.campaign_year,
                        "kind": record.campaign_kind,
                        "era": record.era,
                        "cmssw_series": record.cmssw_series,
                        "nanoaod_version": record.nanoaod_version,
                        "full_version": record.full_version,
                        "is_old": "_OLD" in record.campaign,
                    },
                    "counts": {
                        "files": 0,
                        "nominal": 0,
                        "systematic": 0,
                        "processing_families": 0,
                        "samples": 0,
                    },
                    "processing_families": {},
                },
            )
            campaign_node["counts"]["files"] += 1
            campaign_node["counts"][record.variation_kind] += 1

            family_node = campaign_node["processing_families"].setdefault(
                record.processing_family,
                {
                    "processing_family": record.processing_family,
                    "processing_steps": list(record.processing_steps),
                    "observed_processing_paths": [],
                    "counts": {
                        "files": 0,
                        "nominal": 0,
                        "systematic": 0,
                        "samples": 0,
                    },
                    "samples": {},
                },
            )
            family_node["counts"]["files"] += 1
            family_node["counts"][record.variation_kind] += 1
            if record.processing_path not in family_node["observed_processing_paths"]:
                family_node["observed_processing_paths"].append(record.processing_path)

            sample_node = family_node["samples"].setdefault(
                record.sample,
                {
                    "sample_name": record.sample,
                    "sample_kind": record.sample_kind,
                    "data_identity": (
                        {
                            "dataset": record.dataset,
                            "run_tag": record.run_tag,
                            "run_year": record.run_year,
                            "run_era": record.run_era,
                        }
                        if record.sample_kind == "data"
                        else None
                    ),
                    "counts": {
                        "files": 0,
                        "nominal": 0,
                        "systematic": 0,
                    },
                    "nominal": [],
                    "systematics": {},
                },
            )
            sample_node["counts"]["files"] += 1
            sample_node["counts"][record.variation_kind] += 1

            if record.variation_kind == "nominal":
                sample_node["nominal"].append(record.file_payload())
            else:
                systematic_node = sample_node["systematics"].setdefault(
                    record.systematic or "unknown",
                    {"up": [], "down": [], "unknown": []},
                )
                systematic_node[record.direction or "unknown"].append(
                    record.file_payload()
                )

            replica_signatures[_replica_signature(record)].append(record)

        self._finalize_hierarchy(owners, sample_locations)
        replica_groups = self._build_replica_groups(replica_signatures)

        summary = {
            "input_lines_nonempty": self.input_line_count,
            "duplicate_input_paths_removed": self.duplicate_input_count,
            "parsed_files": len(self.records),
            "unparsed_paths": len(self.parse_failures),
            "nominal_files": nominal_count,
            "systematic_files": systematic_count,
            "old_paths": old_count,
            "owners": len(owners),
            "campaigns": len(campaigns_seen),
            "processing_families": len(processing_families_seen),
            "unique_sample_names": len(samples_seen),
            "cross_owner_replica_groups": len(replica_groups),
            "by_owner": _counter_to_sorted_dict(by_owner),
            "by_year": _counter_to_sorted_dict(by_year),
            "by_campaign_kind": _counter_to_sorted_dict(by_campaign_kind),
            "by_sample_kind": _counter_to_sorted_dict(by_sample_kind),
            "by_systematic": _counter_to_sorted_dict(by_systematic),
            "by_direction": _counter_to_sorted_dict(by_direction),
        }

        document: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "generator": {
                "program": PROGRAM,
                "version": VERSION,
                "generated_at_utc": self.generated_at,
            },
            "source": {
                "file_list": str(self.source_list),
                "file_list_sha256": self.source_sha256,
                "base": self.base,
                **self.crawl_metadata,
            },
            "schema_notes": {
                "owner": "Directory immediately below the cmshww base path.",
                "campaign": (
                    "Production/reconstruction directory immediately below HWWNano, "
                    "for example Summer24_150x_nAODv15_Full2024v15."
                ),
                "processing_family": (
                    "Processing path with a terminal systematic token such as "
                    "jerdo_suffix or jes...up_suffix removed. Nominal and shifted "
                    "files therefore meet under one family when the naming convention "
                    "is consistent."
                ),
                "sample": (
                    "Token between nanoLatino_ and __partN.root. A token containing "
                    "_RunYYYY<era> is classified as data; other tokens are classified "
                    "as MC."
                ),
                "systematic_direction": (
                    "EOS/HWWNano raw suffix 'up_suffix' maps to 'up'; 'do_suffix' "
                    "maps to 'down'."
                ),
                "replica_group": (
                    "Same campaign, normalized processing family, sample, part, and "
                    "variation found under more than one owner. This is a storage "
                    "replica/copy signal, not proof of byte-identical content."
                ),
            },
            "summary": summary,
            "sample_index": dict(sorted(sample_locations.items())),
            "owners": dict(sorted(owners.items())),
            "quality": {
                "parse_failures": [dataclasses.asdict(item) for item in self.parse_failures],
                "cross_owner_replica_groups": replica_groups,
            },
        }
        return document

    def _finalize_hierarchy(
        self,
        owners: MutableMapping[str, Any],
        sample_locations: MutableMapping[str, list[dict[str, Any]]],
    ) -> None:
        for owner_name, owner_node in owners.items():
            owner_node["counts"]["campaigns"] = len(owner_node["campaigns"])
            owner_node["campaigns"] = dict(sorted(owner_node["campaigns"].items()))

            for campaign_name, campaign_node in owner_node["campaigns"].items():
                families = campaign_node["processing_families"]
                campaign_sample_names: set[str] = set()
                campaign_node["counts"]["processing_families"] = len(families)
                campaign_node["processing_families"] = dict(sorted(families.items()))

                for family_name, family_node in campaign_node[
                    "processing_families"
                ].items():
                    family_node["observed_processing_paths"] = sorted(
                        family_node["observed_processing_paths"]
                    )
                    samples = family_node["samples"]
                    family_node["counts"]["samples"] = len(samples)
                    family_node["samples"] = dict(sorted(samples.items()))

                    for sample_name, sample_node in family_node["samples"].items():
                        campaign_sample_names.add(sample_name)
                        sample_node["nominal"] = sorted(
                            sample_node["nominal"],
                            key=lambda item: (item["part"], item["path"]),
                        )
                        sample_node["systematics"] = self._finalize_systematics(
                            sample_node["systematics"]
                        )
                        sample_locations[sample_name].append(
                            {
                                "owner": owner_name,
                                "campaign": campaign_name,
                                "year": campaign_node["metadata"]["year"],
                                "campaign_kind": campaign_node["metadata"]["kind"],
                                "processing_family": family_name,
                                "sample_kind": sample_node["sample_kind"],
                                "nominal_files": sample_node["counts"]["nominal"],
                                "systematic_files": sample_node["counts"]["systematic"],
                                "systematics": sorted(sample_node["systematics"]),
                            }
                        )

                campaign_node["counts"]["samples"] = len(campaign_sample_names)

        for sample_name in list(sample_locations):
            sample_locations[sample_name] = sorted(
                sample_locations[sample_name],
                key=lambda item: (
                    str(item["year"]),
                    item["owner"],
                    item["campaign"],
                    item["processing_family"],
                ),
            )

    @staticmethod
    def _finalize_systematics(systematics: Mapping[str, Any]) -> dict[str, Any]:
        finalized: dict[str, Any] = {}
        for systematic, directions in sorted(systematics.items()):
            cleaned: dict[str, Any] = {}
            for direction in ("up", "down", "unknown"):
                files = sorted(
                    directions.get(direction, []),
                    key=lambda item: (item["part"], item["path"]),
                )
                if files:
                    cleaned[direction] = files
            finalized[systematic] = cleaned
        return finalized

    def _build_replica_groups(
        self,
        signatures: Mapping[tuple[Any, ...], Sequence[FileRecord]],
    ) -> list[dict[str, Any]]:
        groups: list[dict[str, Any]] = []
        for signature, records in signatures.items():
            owners = sorted({record.owner for record in records})
            if len(owners) < 2:
                continue
            campaign, processing_family, sample, variation, systematic, direction, part = (
                signature
            )
            group: dict[str, Any] = {
                "campaign": campaign,
                "processing_family": processing_family,
                "sample": sample,
                "variation_kind": variation,
                "systematic": systematic,
                "direction": direction,
                "part": part,
                "owners": owners,
                "copy_count": len(records),
            }
            if self.include_replica_details:
                group["copies"] = [
                    {
                        "owner": record.owner,
                        "path": record.path,
                        "logical_path": record.logical_path,
                    }
                    for record in sorted(records, key=lambda item: (item.owner, item.path))
                ]
            groups.append(group)
        return sorted(
            groups,
            key=lambda item: (
                item["campaign"],
                item["processing_family"],
                item["sample"],
                item["variation_kind"],
                str(item["systematic"]),
                str(item["direction"]),
                item["part"],
            ),
        )


def infer_campaign_year(campaign: str) -> Optional[int]:
    """Infer a four-digit year from a Run/Summer campaign name."""

    match = CAMPAIGN_YEAR_RE.search(campaign)
    if not match:
        return None
    raw = match.group("year")
    if len(raw) == 2:
        return 2000 + int(raw)
    return int(raw)


def infer_campaign_kind(campaign: str) -> str:
    if campaign.startswith("Summer"):
        return "mc"
    if campaign.startswith("Run"):
        return "data"
    return "unknown"


def infer_era(campaign: str, year: Optional[int]) -> Optional[str]:
    if year == 2022:
        return "postEE" if "EE" in campaign else "preEE"
    if year == 2023:
        return "postBPix" if "BPix" in campaign else "preBPix"
    return None


def parse_file_record(path: str, *, base: str) -> FileRecord:
    """Normalize one expected HWWNano path or raise ``ValueError``."""

    normalized = posixpath.normpath(path.strip())
    normalized_base = posixpath.normpath(base.rstrip("/"))
    prefix = normalized_base + "/"
    if not normalized.startswith(prefix):
        raise ValueError(f"path is not below configured base {normalized_base}")

    relative = normalized[len(prefix) :]
    parts = PurePosixPath(relative).parts
    if len(parts) < 5:
        raise ValueError(
            "expected <owner>/HWWNano/<campaign>/<processing...>/<filename>"
        )

    owner, area, campaign = parts[0], parts[1], parts[2]
    if area != "HWWNano":
        raise ValueError(f"expected HWWNano path component, found {area!r}")

    relative_directories = tuple(parts[3:-1])
    filename = parts[-1]
    if not relative_directories:
        raise ValueError("file has no processing directory below campaign")

    file_match = FILE_NAME_RE.fullmatch(filename)
    if not file_match:
        raise ValueError(
            "filename does not match nanoLatino_<sample>__partN.root"
        )

    sample = file_match.group("sample")
    part = int(file_match.group("part"))
    campaign_year = infer_campaign_year(campaign)
    campaign_kind = infer_campaign_kind(campaign)

    variation = _parse_variation(relative_directories)
    processing_component = _select_processing_component(relative_directories)
    processing_steps = _processing_steps(processing_component, variation)
    processing_family = _normalize_processing_family(
        relative_directories,
        variation,
    )

    data_match = DATA_SAMPLE_RE.fullmatch(sample)
    if data_match:
        sample_kind = "data"
        dataset = data_match.group("dataset")
        run_tag = data_match.group("run_tag")
        run_year = int(data_match.group("run_year"))
        run_era = data_match.group("run_era")
    else:
        sample_kind = "mc"
        dataset = None
        run_tag = None
        run_year = None
        run_era = None

    cmssw_match = CMSSW_SERIES_RE.search(campaign)
    nanoaod_match = NANOAOD_VERSION_RE.search(campaign)
    full_match = FULL_VERSION_RE.search(campaign)

    tree_base = posixpath.join(normalized_base, owner, "HWWNano")
    campaign_root = posixpath.join(tree_base, campaign)
    processing_path = "/".join(relative_directories)

    return FileRecord(
        path=normalized,
        logical_path=_to_logical_path(normalized),
        owner=owner,
        tree_base=tree_base,
        campaign=campaign,
        campaign_root=campaign_root,
        campaign_year=campaign_year,
        campaign_kind=campaign_kind,
        era=infer_era(campaign, campaign_year),
        cmssw_series=cmssw_match.group("series") if cmssw_match else None,
        nanoaod_version=(
            f"v{nanoaod_match.group('version')}" if nanoaod_match else None
        ),
        full_version=full_match.group("full") if full_match else None,
        relative_directories=relative_directories,
        processing_path=processing_path,
        processing_component=processing_component,
        processing_steps=processing_steps,
        processing_family=processing_family,
        variation_kind="systematic" if variation is not None else "nominal",
        systematic=variation[2] if variation is not None else None,
        direction=variation[3] if variation is not None else None,
        raw_direction=variation[4] if variation is not None else None,
        sample=sample,
        sample_kind=sample_kind,
        dataset=dataset,
        run_tag=run_tag,
        run_year=run_year,
        run_era=run_era,
        part=part,
        filename=filename,
        is_old=any("_OLD" in component for component in parts),
    )


def _parse_variation(
    relative_directories: Sequence[str],
) -> Optional[tuple[int, Optional[int], str, str, str]]:
    """Return index, token index, systematic, direction, raw direction."""

    for directory_index in range(len(relative_directories) - 1, -1, -1):
        component = relative_directories[directory_index]
        tokens = component.split("__")
        for token_index in range(len(tokens) - 1, -1, -1):
            token = tokens[token_index]
            match = VARIATION_TOKEN_RE.fullmatch(token)
            if not match:
                continue
            systematic = match.group("systematic").strip("_") or "unknown"
            raw_direction = match.group("raw_direction")
            direction = "down" if raw_direction == "do" else "up"
            return (
                directory_index,
                token_index,
                systematic,
                direction,
                raw_direction,
            )
    return None


def _select_processing_component(relative_directories: Sequence[str]) -> Optional[str]:
    for component in relative_directories:
        if "__" in component:
            return component
        if component.startswith(("MC", "DATA")):
            return component
        if VARIATION_TOKEN_RE.fullmatch(component):
            return component
    return relative_directories[-1] if relative_directories else None


def _processing_steps(
    processing_component: Optional[str],
    variation: Optional[tuple[int, Optional[int], str, str, str]],
) -> tuple[str, ...]:
    if processing_component is None:
        return ()
    tokens = processing_component.split("__")
    if tokens and VARIATION_TOKEN_RE.fullmatch(tokens[-1]):
        tokens = tokens[:-1]
    return tuple(token for token in tokens if token)


def _normalize_processing_family(
    relative_directories: Sequence[str],
    variation: Optional[tuple[int, Optional[int], str, str, str]],
) -> str:
    components = list(relative_directories)
    if variation is not None:
        directory_index, token_index, _systematic, _direction, _raw = variation
        tokens = components[directory_index].split("__")
        if token_index is not None:
            del tokens[token_index]
        replacement = "__".join(token for token in tokens if token)
        if replacement:
            components[directory_index] = replacement
        else:
            del components[directory_index]
    normalized = "/".join(component for component in components if component)
    return normalized or "<campaign-root>"


def _to_logical_path(path: str) -> Optional[str]:
    prefix = "/eos/cms"
    if path == prefix:
        return "/"
    if path.startswith(prefix + "/"):
        return path[len(prefix) :]
    return None


def _replica_signature(record: FileRecord) -> tuple[Any, ...]:
    return (
        record.campaign,
        record.processing_family,
        record.sample,
        record.variation_kind,
        record.systematic,
        record.direction,
        record.part,
    )


def read_file_list(path: Path) -> tuple[list[str], int, int]:
    """Read nonempty paths, returning unique sorted paths and input statistics."""

    lines = path.read_text(encoding="utf-8").splitlines()
    nonempty = [line.strip() for line in lines if line.strip()]
    unique = sorted(set(nonempty))
    return unique, len(nonempty), len(nonempty) - len(unique)


def parse_file_list(
    paths: Iterable[str],
    *,
    base: str,
    strict: bool,
) -> tuple[list[FileRecord], list[ParseFailure]]:
    records: list[FileRecord] = []
    failures: list[ParseFailure] = []
    for path in paths:
        try:
            records.append(parse_file_record(path, base=base))
        except ValueError as exc:
            failure = ParseFailure(path=path, reason=str(exc))
            failures.append(failure)
            if strict:
                raise CatalogError(f"Could not parse {path}: {exc}") from exc
    return records, failures


def build_catalog_from_list(
    *,
    file_list: Path,
    json_output: Path,
    base: str,
    strict: bool,
    crawl_metadata: Optional[Mapping[str, Any]],
    include_replica_details: bool,
    generated_at: Optional[str] = None,
) -> dict[str, Any]:
    """Re-read a text list and atomically produce its JSON catalog."""

    paths, input_count, duplicate_count = read_file_list(file_list)
    records, failures = parse_file_list(paths, base=base, strict=strict)
    builder = CatalogBuilder(
        base=base,
        source_list=file_list,
        source_sha256=sha256_file(file_list),
        input_line_count=input_count,
        duplicate_input_count=duplicate_count,
        records=records,
        parse_failures=failures,
        crawl_metadata=crawl_metadata,
        include_replica_details=include_replica_details,
        generated_at=generated_at,
    )
    catalog = builder.build()
    atomic_write_json(json_output, catalog)
    return catalog


def write_traditional_file_list(path: Path, paths: Iterable[str], *, base: str) -> None:
    """Write sorted nominal paths, one blank line, then sorted systematics."""

    nominal: list[str] = []
    systematic: list[str] = []
    for item in sorted(set(paths)):
        try:
            record = parse_file_record(item, base=base)
            is_systematic = record.variation_kind == "systematic"
        except ValueError:
            is_systematic = bool(re.search(r"(?:do|up)_suffix", item))
        (systematic if is_systematic else nominal).append(item)

    content = "\n".join(nominal) + "\n\n" + "\n".join(systematic) + "\n"
    atomic_write_text(path, content)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_write_json(path: Path, document: Mapping[str, Any]) -> None:
    content = json.dumps(
        document,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"
    atomic_write_text(path, content)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contains_truncation(stderr: str) -> bool:
    return any(pattern.search(stderr) for pattern in TRUNCATION_PATTERNS)


def _counter_to_sorted_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _default_output_names() -> tuple[Path, Path, Path]:
    stamp = dt.datetime.now().strftime("%Y_%m_%d")
    text = Path(f"{stamp}_cmshww_HWWNano_file_list_22to25.txt")
    json_path = text.with_suffix(".json")
    errors = text.with_suffix(".errors.log")
    return text, json_path, errors


def _shell_quote(value: str) -> str:
    if not value:
        return "''"
    if re.fullmatch(r"[A-Za-z0-9_./:=+,-]+", value):
        return value
    return "'" + value.replace("'", "'\\''") + "'"


def _compile_regex(value: Optional[str], label: str) -> Optional[re.Pattern[str]]:
    if value is None:
        return None
    try:
        return re.compile(value)
    except re.error as exc:
        raise ConfigurationError(f"Invalid {label} regular expression {value!r}: {exc}")


def _validate_find_regex(regex: str) -> None:
    if regex[:1] in {"*", "+", "?", "{"}:
        raise ConfigurationError(
            f"EOS --name uses egrep/ERE syntax; the expression cannot begin with "
            f"a repetition operator: {regex!r}"
        )
    try:
        compiled = re.compile(regex)
    except re.error as exc:
        raise ConfigurationError(f"Invalid file-name regular expression {regex!r}: {exc}")
    representative_names = (
        "nanoLatino_ZZ__part0.root",
        "nanoLatino_ZZ__part1.root",
        "nanoLatino_ZZ__part17.root",
    )
    if not any(compiled.fullmatch(name) for name in representative_names):
        raise ConfigurationError(
            "File-name expression does not match a representative Latino ROOT file "
            f"name: {regex!r}"
        )
    if compiled.fullmatch("nanoLatino_ZZ__part0Xroot"):
        raise ConfigurationError(
            f"File-name expression does not require a literal .root suffix: {regex!r}"
        )


def _configure_logging(verbose: int) -> logging.Logger:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger(PROGRAM)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=(
            "Crawl Run-3 HWWNano storage and produce both a traditional text "
            "file list and a structured JSON sample catalog."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    crawl = subparsers.add_parser(
        "crawl",
        help="crawl EOS, write the text list, then index that list as JSON",
    )
    crawl.add_argument("--base", default=DEFAULT_BASE)
    crawl.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(DEFAULT_YEARS),
        metavar="YEAR",
    )
    crawl.add_argument("--workers", type=int, default=8)
    crawl.add_argument("--retries", type=int, default=4)
    crawl.add_argument("--backoff", type=float, default=0.5)
    crawl.add_argument("--timeout", type=float, default=300.0)
    crawl.add_argument("--max-split-depth", type=int, default=12)
    crawl.add_argument("--eos-bin", default=os.environ.get("EOS_BIN", "eos"))
    crawl.add_argument("--list-out", type=Path)
    crawl.add_argument("--json-out", type=Path)
    crawl.add_argument("--errors-out", type=Path)
    part_group = crawl.add_mutually_exclusive_group()
    part_group.add_argument(
        "--part",
        type=int,
        default=0,
        help="select one part number (default: 0, preserving the old script)",
    )
    part_group.add_argument(
        "--all-parts",
        action="store_true",
        help="select every nanoLatino __partN.root file",
    )
    crawl.add_argument(
        "--find-name-regex",
        help="advanced override for the EOS egrep-style --name expression",
    )
    crawl.add_argument(
        "--owner-regex",
        action="append",
        default=[],
        help="include owners matching this regex; repeatable",
    )
    crawl.add_argument(
        "--campaign-regex",
        help="additional campaign-name filter",
    )
    crawl.add_argument(
        "--exclude-owner-prefix",
        action="append",
        default=list(DEFAULT_EXCLUDED_OWNER_PREFIXES),
        help="owner prefix to skip; repeatable",
    )
    crawl.add_argument("--exclude-old", action="store_true")
    crawl.add_argument(
        "--strict-json",
        action="store_true",
        default=True,
        help="fail if a path cannot be parsed (default)",
    )
    crawl.add_argument(
        "--no-strict-json",
        dest="strict_json",
        action="store_false",
        help="retain unparsed paths in quality.parse_failures",
    )
    crawl.add_argument(
        "--compact-replicas",
        action="store_true",
        help="omit individual copy paths from cross-owner replica groups",
    )
    crawl.add_argument("-v", "--verbose", action="count", default=1)
    crawl.set_defaults(func=run_crawl)

    index = subparsers.add_parser(
        "index",
        help="build JSON from an already-produced text file list",
    )
    index.add_argument("file_list", type=Path)
    index.add_argument("--json-out", type=Path)
    index.add_argument("--base", default=DEFAULT_BASE)
    index.add_argument("--strict", action="store_true", default=True)
    index.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="record malformed paths instead of failing",
    )
    index.add_argument(
        "--compact-replicas",
        action="store_true",
        help="omit individual copy paths from cross-owner replica groups",
    )
    index.add_argument("-v", "--verbose", action="count", default=1)
    index.set_defaults(func=run_index)

    explain = subparsers.add_parser(
        "explain-schema",
        help="print a concise explanation of the JSON grouping model",
    )
    explain.set_defaults(func=run_explain_schema, verbose=0)
    return parser


def run_crawl(args: argparse.Namespace) -> int:
    logger = _configure_logging(args.verbose)
    _validate_common_numeric_args(args)

    default_list, default_json, default_errors = _default_output_names()
    list_output = args.list_out or default_list
    json_output = args.json_out or (
        list_output.with_suffix(".json") if args.list_out else default_json
    )
    errors_output = args.errors_out or (
        list_output.with_suffix(".errors.log") if args.list_out else default_errors
    )

    if args.find_name_regex:
        find_regex = args.find_name_regex
    elif args.all_parts:
        find_regex = DEFAULT_FIND_REGEX_ALL_PARTS
    else:
        if args.part < 0:
            raise ConfigurationError("--part must be non-negative")
        find_regex = rf".*__part{args.part}[.]root$"
    _validate_find_regex(find_regex)

    eos_path = shutil.which(args.eos_bin)
    if eos_path is None and not Path(args.eos_bin).is_file():
        raise ConfigurationError(f"EOS executable not found: {args.eos_bin}")

    owner_patterns = [
        _compile_regex(value, "owner") for value in args.owner_regex
    ]
    campaign_pattern = _compile_regex(args.campaign_regex, "campaign")
    recorder = EventRecorder()
    client = EOSClient(
        eos_bin=args.eos_bin,
        retries=args.retries,
        initial_backoff=args.backoff,
        timeout=args.timeout,
        recorder=recorder,
        logger=logger,
    )
    crawler = EOSCrawler(
        client=client,
        base=args.base,
        years=set(args.years),
        workers=args.workers,
        find_name_regex=find_regex,
        excluded_owner_prefixes=args.exclude_owner_prefix,
        include_owner_patterns=[pattern for pattern in owner_patterns if pattern],
        campaign_pattern=campaign_pattern,
        exclude_old=args.exclude_old,
        max_split_depth=args.max_split_depth,
        logger=logger,
    )

    started = time.monotonic()
    result = crawler.crawl()
    elapsed = time.monotonic() - started

    write_traditional_file_list(list_output, result.paths, base=args.base)

    crawl_metadata = {
        "mode": "eos_crawl",
        "years": sorted(set(args.years)),
        "find_name_regex": find_regex,
        "workers": args.workers,
        "campaigns_crawled": len(result.campaigns),
        "campaign_roots": [campaign.path for campaign in result.campaigns],
        "recovered_events": list(result.recovered_events),
        "elapsed_seconds": round(elapsed, 3),
    }
    catalog = build_catalog_from_list(
        file_list=list_output,
        json_output=json_output,
        base=args.base,
        strict=args.strict_json,
        crawl_metadata=crawl_metadata,
        include_replica_details=not args.compact_replicas,
    )

    if result.recovered_events:
        atomic_write_text(
            errors_output,
            "\n".join(json.dumps(item, sort_keys=True) for item in result.recovered_events)
            + "\n",
        )
    else:
        errors_output.unlink(missing_ok=True)

    summary = catalog["summary"]
    print(f"Wrote file list: {list_output}")
    print(f"Wrote JSON catalog: {json_output}")
    print(f"Campaigns: {summary['campaigns']}")
    print(
        f"Files: {summary['parsed_files']} "
        f"(nominal={summary['nominal_files']}, "
        f"systematic={summary['systematic_files']})"
    )
    print(
        f"Owners: {summary['owners']}  "
        f"Samples: {summary['unique_sample_names']}  "
        f"Replica groups: {summary['cross_owner_replica_groups']}"
    )
    if result.recovered_events:
        print(f"Recovered EOS events: {errors_output}")
    return 0


def run_index(args: argparse.Namespace) -> int:
    logger = _configure_logging(args.verbose)
    del logger
    if not args.file_list.is_file():
        raise ConfigurationError(f"File list does not exist: {args.file_list}")
    json_output = args.json_out or args.file_list.with_suffix(".json")
    catalog = build_catalog_from_list(
        file_list=args.file_list,
        json_output=json_output,
        base=args.base,
        strict=args.strict,
        crawl_metadata={"mode": "existing_file_list"},
        include_replica_details=not args.compact_replicas,
    )
    summary = catalog["summary"]
    print(f"Read file list: {args.file_list}")
    print(f"Wrote JSON catalog: {json_output}")
    print(
        f"Files: {summary['parsed_files']} "
        f"(nominal={summary['nominal_files']}, "
        f"systematic={summary['systematic_files']}, "
        f"unparsed={summary['unparsed_paths']})"
    )
    return 0


def run_explain_schema(_args: argparse.Namespace) -> int:
    print(
        "owner -> campaign -> processing_family -> sample -> nominal/systematics\n\n"
        "The processing family removes a terminal HWWNano systematic token "
        "such as jerdo_suffix or jesAbsoluteup_suffix. This groups nominal and "
        "shifted files together while preserving each observed processing path. "
        "Data samples are recognized from <dataset>_RunYYYY<era>... names. "
        "Cross-owner replica groups identify the same normalized file identity "
        "stored under multiple cmshww owners."
    )
    return 0


def _validate_common_numeric_args(args: argparse.Namespace) -> None:
    if args.workers < 1:
        raise ConfigurationError("--workers must be at least 1")
    if args.retries < 0:
        raise ConfigurationError("--retries must be non-negative")
    if args.backoff < 0:
        raise ConfigurationError("--backoff must be non-negative")
    if args.timeout <= 0:
        raise ConfigurationError("--timeout must be positive")
    if args.max_split_depth < 1:
        raise ConfigurationError("--max-split-depth must be at least 1")
    if not args.years:
        raise ConfigurationError("At least one --years value is required")


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    # Preserve convenient no-subcommand behavior: plain execution means crawl.
    known_commands = {"crawl", "index", "explain-schema"}
    global_options = {"-h", "--help", "--version"}
    if not arguments:
        arguments.insert(0, "crawl")
    elif arguments[0] not in known_commands and arguments[0] not in global_options:
        arguments.insert(0, "crawl")

    parser = make_parser()
    args = parser.parse_args(arguments)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except CatalogError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
