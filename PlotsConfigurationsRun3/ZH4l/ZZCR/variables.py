"""Explicit compact observable set for nominal ZZCR/SR production."""

from common.observables import select_observables

variables = select_observables(
    "mZ", "mX", "m4l", "ptZ", "ptX", "pt4l", "PuppiMET_pt", "minMll4l", "nLepton10"
)
