import pytest

from inspect_plan import inspect
from study_config import SUPPORTED_ERAS


@pytest.mark.parametrize("year", SUPPORTED_ERAS)
def test_full_profile_is_complete_and_major_is_a_strict_pilot_subset(year):
    full = inspect(year, "full")
    major = inspect(year, "major")
    assert "DATA" in full["samples"] and "DATA" in major["samples"]
    assert set(major["samples"]) < set(full["samples"])
    assert full["sample_count"] in (53, 55)
    assert full["nonprompt_fake_background_included"] is False

