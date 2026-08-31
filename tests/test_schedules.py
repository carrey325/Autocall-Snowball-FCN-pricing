from __future__ import annotations

import pytest

from structured_products.schedules import (
    linear_schedule,
    monthly_observation_days,
    validate_days,
)


def test_monthly_days_are_sorted_and_inside_maturity() -> None:
    days = monthly_observation_days(252)
    assert len(days) == 12
    assert days[-1] == 252
    assert tuple(sorted(days)) == days


def test_validate_days_rejects_duplicates_and_out_of_range() -> None:
    with pytest.raises(ValueError):
        validate_days((21, 21), 252, name="test")
    with pytest.raises(ValueError):
        validate_days((21, 253), 252, name="test")


def test_linear_schedule_includes_endpoints() -> None:
    assert linear_schedule(1.03, 0.95, 3) == pytest.approx((1.03, 0.99, 0.95))
