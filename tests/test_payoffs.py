from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from structured_products.enums import CouponRule, SameDayPriority
from structured_products.payoffs import evaluate_path, evaluate_paths
from structured_products.products import (
    AutocallFeature,
    CouponFeature,
    KnockInFeature,
    RedemptionFeature,
    StructuredNote,
)


def snowball(*, priority: SameDayPriority = SameDayPriority.KNOCK_OUT_FIRST) -> StructuredNote:
    return StructuredNote(
        reference_spots=(100.0,),
        notional=100.0,
        maturity_days=4,
        day_count=4,
        knock_in=KnockInFeature(0.8),
        autocall=AutocallFeature((2, 4), (1.0, 1.0), (0.2, 0.2)),
        coupon=CouponFeature(
            CouponRule.CONTINGENT_AT_REDEMPTION, maturity_rate=0.2
        ),
        redemption=RedemptionFeature(),
        same_day_priority=priority,
    )


def path(values: list[float]) -> np.ndarray:
    return np.asarray(values, dtype=float)[:, None]


def test_knock_out_first_observation() -> None:
    result = evaluate_path(path([100, 100, 110, 90, 90]), snowball())
    assert result.knocked_out
    assert result.redemption_day == 2
    assert sum(item.amount for item in result.cashflows) == pytest.approx(110.0)


def test_knock_in_followed_by_knock_out() -> None:
    result = evaluate_path(path([100, 80, 105, 90, 90]), snowball())
    assert result.knocked_in and result.knocked_out
    assert result.redemption_day == 2


def test_knock_in_no_knock_out_and_final_loss() -> None:
    result = evaluate_path(path([100, 80, 90, 75, 70]), snowball())
    assert not result.knocked_out
    assert result.knocked_in
    assert sum(item.amount for item in result.cashflows) == pytest.approx(70.0)


def test_knock_in_recovery_returns_principal_without_coupon() -> None:
    product = snowball()
    assert product.autocall is not None
    product = replace(
        product,
        autocall=replace(product.autocall, barrier_ratios=(1.2, 1.2)),
    )
    result = evaluate_path(path([100, 80, 90, 95, 100]), product)
    assert sum(item.amount for item in result.cashflows) == pytest.approx(100.0)


def test_no_knock_in_or_knock_out_pays_maturity_coupon() -> None:
    product = snowball()
    assert product.autocall is not None
    product = replace(
        product,
        autocall=replace(product.autocall, barrier_ratios=(1.2, 1.2)),
    )
    result = evaluate_path(path([100, 90, 90, 90, 90]), product)
    assert sum(item.amount for item in result.cashflows) == pytest.approx(120.0)


def test_exact_barrier_touches_are_inclusive() -> None:
    ki = evaluate_path(path([100, 80, 90, 90, 90]), snowball())
    ko = evaluate_path(path([100, 90, 100, 90, 90]), snowball())
    assert ki.knocked_in
    assert ko.knocked_out


def test_same_day_knock_out_priority_is_explicit() -> None:
    base = snowball()
    assert base.knock_in is not None
    overlap = replace(
        base,
        knock_in=replace(
            base.knock_in, barrier_ratio=1.1, monitoring_start_day=2
        ),
    )
    ko_first = evaluate_path(path([100, 100, 100, 100, 100]), overlap)
    ki_first = evaluate_path(
        path([100, 100, 100, 100, 100]),
        replace(overlap, same_day_priority=SameDayPriority.KNOCK_IN_FIRST),
    )
    assert not ko_first.knocked_in
    assert ki_first.knocked_in


def test_periodic_fcn_coupon_and_discount_entry_state() -> None:
    product = StructuredNote(
        reference_spots=(100.0,),
        notional=100.0,
        maturity_days=4,
        day_count=4,
        knock_in=KnockInFeature(0.8, initially_knocked_in=True),
        coupon=CouponFeature(
            CouponRule.FIXED_PERIODIC,
            payment_days=(2, 4),
            rate_schedule=(0.2, 0.2),
            survives_knock_in=True,
        ),
        redemption=RedemptionFeature(),
    )
    result = evaluate_path(path([100, 100, 100, 90, 90]), product)
    assert result.knocked_in
    assert result.coupon_cashflow == pytest.approx(20.0)
    assert sum(item.amount for item in result.cashflows) == pytest.approx(110.0)


def test_vectorized_and_scalar_payoffs_agree() -> None:
    product = snowball()
    paths = np.stack(
        [
            path([100, 100, 110, 90, 90]),
            path([100, 80, 90, 75, 70]),
            path([100, 90, 90, 90, 90]),
        ]
    )
    vector = evaluate_paths(paths, product)
    scalar = np.asarray(
        [
            evaluate_path(item, product).present_value(0.0, product.day_count)
            for item in paths
        ]
    )
    assert vector.present_values == pytest.approx(scalar)
