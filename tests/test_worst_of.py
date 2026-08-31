from __future__ import annotations

import numpy as np

from structured_products import (
    MCConfig,
    MarketData,
    make_classic_snowball,
    make_worst_of_snowball,
    price,
)
from structured_products.payoffs import evaluate_path


def test_one_asset_worst_of_reduces_exactly_to_single_asset() -> None:
    single = make_classic_snowball(
        maturity_days=42,
        knock_in_ratio=0.8,
        knock_out_ratio=1.0,
        coupon_rate=0.18,
    )
    worst = make_worst_of_snowball(
        reference_spots=(100.0,),
        maturity_days=42,
        knock_in_ratio=0.8,
        knock_out_ratio=1.0,
        coupon_rate=0.18,
    )
    market = MarketData(
        spots=(100.0,),
        rate=0.03,
        dividend_yields=(0.0,),
        volatilities=(0.2,),
    )
    config = MCConfig(n_paths=2_000, seed=7)
    assert price(single, market, "mc", config).present_value == price(
        worst, market, "mc", config
    ).present_value


def test_identical_underlying_paths_reduce_to_single_performance() -> None:
    single = make_classic_snowball(
        maturity_days=2,
        observation_days=(2,),
        knock_in_ratio=0.8,
        knock_out_ratio=1.0,
        coupon_rate=0.18,
    )
    worst = make_worst_of_snowball(
        reference_spots=(100.0, 100.0),
        maturity_days=2,
        observation_days=(2,),
        knock_in_ratio=0.8,
        knock_out_ratio=1.0,
        coupon_rate=0.18,
    )
    one = np.asarray([[100.0], [90.0], [105.0]])
    two = np.repeat(one, 2, axis=1)
    single_result = evaluate_path(one, single)
    worst_result = evaluate_path(two, worst)
    assert worst_result.cashflows == single_result.cashflows
    assert worst_result.knocked_in == single_result.knocked_in
