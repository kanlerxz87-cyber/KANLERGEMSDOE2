from __future__ import annotations

import numpy as np

from gems32.htcads import (
    SUBSURF_FEATURE_NAMES,
    _advective_upgradient_plume,
    _fixed_axis_strike_alignment,
)


def test_feature_28_is_named_and_computed_as_fixed_axis_alignment() -> None:
    assert len(SUBSURF_FEATURE_NAMES) == 36
    assert SUBSURF_FEATURE_NAMES[28] == "strike_alignment_fixed_62deg"
    assert "slip_tendency" not in SUBSURF_FEATURE_NAMES[28]

    reference = np.deg2rad(62.0)
    strikes = np.asarray([reference, reference + np.pi / 2.0, reference + np.pi])
    values = _fixed_axis_strike_alignment(strikes)
    assert values.dtype == np.float32
    np.testing.assert_allclose(values, [1.0, 0.0, 1.0], atol=1e-6)


def test_feature_28_does_not_claim_stress_tendency_inputs() -> None:
    # The semantics are deliberately geometric: an axial strike alignment to a
    # fixed reference. No stress/friction/slip inputs are accepted by the helper.
    assert _fixed_axis_strike_alignment.__code__.co_argcount == 1


def test_thermal_path_docstring_identifies_elevation_as_proxy() -> None:
    doc = _advective_upgradient_plume.__doc__ or ""
    assert "terrain-elevation-gradient proxy" in doc
    assert "measured groundwater hydraulic head" in doc
    assert "must not be described as a measured" in doc
