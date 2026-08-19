import copy

import pytest

import make_sample_catalog as catalog


def test_eos_command_error_preserves_context_across_copy():
    error = catalog.EOSCommandError(("eos", "ls", "/store/test"), 54, "missing", 3)
    cloned = copy.copy(error)

    assert cloned.command == error.command
    assert cloned.returncode == 54
    assert cloned.stderr == "missing"
    assert cloned.attempts == 3
    assert str(cloned) == str(error)


def test_default_part_policy_prefers_zero_and_falls_back_to_one():
    paths = [
        "/eos/cms/store/a/nominal/nanoLatino_A__part1.root",
        "/eos/cms/store/a/nominal/nanoLatino_A__part0.root",
        "/eos/cms/store/a/nominal/nanoLatino_B__part1.root",
        "/eos/cms/store/a/systematic/nanoLatino_A__part1.root",
    ]

    assert catalog.select_representative_paths(paths) == (
        "/eos/cms/store/a/nominal/nanoLatino_A__part0.root",
        "/eos/cms/store/a/nominal/nanoLatino_B__part1.root",
        "/eos/cms/store/a/systematic/nanoLatino_A__part1.root",
    )


def test_default_part_policy_rejects_paths_outside_discovery_contract():
    with pytest.raises(catalog.CatalogError, match="outside parts 0/1"):
        catalog.select_representative_paths(
            ["/eos/cms/store/a/nanoLatino_A__part2.root"]
        )


def test_crawl_parser_uses_fallback_only_when_part_is_unspecified():
    parser = catalog.make_parser()

    default = parser.parse_args(["crawl"])
    exact = parser.parse_args(["crawl", "--part", "0"])

    assert default.part is None
    assert default.all_parts is False
    assert exact.part == 0
    assert exact.all_parts is False


@pytest.mark.parametrize(
    "arguments",
    (
        ["crawl", "--part", "1", "--find-name-regex", ".*__part0[.]root$"],
        ["crawl", "--all-parts", "--find-name-regex", ".*__part0[.]root$"],
    ),
)
def test_crawl_parser_rejects_conflicting_part_selection(arguments):
    with pytest.raises(SystemExit):
        catalog.make_parser().parse_args(arguments)


def test_advanced_regex_rejects_python_only_constructs():
    with pytest.raises(catalog.ConfigurationError, match="portable Python/ERE"):
        catalog._validate_find_regex(r".*__part\d[.]root$")

    catalog._validate_find_regex(r".*__part[0-9]+[.]root$")
