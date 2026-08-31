from __future__ import annotations

from math import exp

import pytest

from structured_products.builders import (
    make_classic_snowball,
    make_worst_of_snowball,
)
from structured_products.config import MCConfig
from structured_products.engines.mc import price_mc
from structured_products.market import MarketData


def single_market(volatility: float = 0.2) -> MarketData:
    return MarketData(
        spots=(100.0,),
        rate=0.03,
        dividend_yields=(0.0,),
        volatilities=(volatility,),
    )


def test_fixed_seed_is_reproducible_and_batch_invariant() -> None:
    product = make_classic_snowball(maturity_days=63)
    first = price_mc(product, single_market(), MCConfig(n_paths=2_000, batch_size=128))
    second = price_mc(product, single_market(), MCConfig(n_paths=2_000, batch_size=777))
    assert first.present_value == second.present_value
    assert first.standard_error == second.standard_error


def test_zero_volatility_is_deterministic() -> None:
    product = make_classic_snowball(
        maturity_days=21,
        observation_days=(21,),
        coupon_rate=0.12,
    )
    result = price_mc(product, single_market(0.0), MCConfig(n_paths=100))
    expected = 1_000.0 * (1.0 + 0.12 * 21 / 252) * exp(-0.03 * 21 / 252)
    assert result.present_value == pytest.approx(expected)
    assert result.standard_error == pytest.approx(0.0, abs=1.0e-12)


def test_standard_error_decreases_with_more_paths() -> None:
    product = make_classic_snowball(maturity_days=63)
    small = price_mc(product, single_market(), MCConfig(n_paths=1_000))
    large = price_mc(product, single_market(), MCConfig(n_paths=8_000))
    assert large.standard_error < small.standard_error


def test_knock_in_is_not_recorded_after_knock_out() -> None:
    product = make_classic_snowball(
        maturity_days=2,
        day_count=252,
        observation_days=(1,),
        knock_out_ratio=0.5,
        knock_in_ratio=2.0,
    )
    result = price_mc(product, single_market(0.0), MCConfig(n_paths=100))
    assert result.knock_out_probability == 1.0
    assert result.knock_in_probability == 0.0


def test_worst_of_uses_correlated_multi_asset_market() -> None:
    product = make_worst_of_snowball(
        reference_spots=(100.0, 100.0),
        maturity_days=21,
        observation_days=(21,),
    )
    market = MarketData(
        spots=(100.0, 80.0),
        rate=0.0,
        dividend_yields=(0.0, 0.0),
        volatilities=(0.0, 0.0),
        correlation=((1.0, 0.5), (0.5, 1.0)),
    )
    result = price_mc(product, market, MCConfig(n_paths=100))
    assert result.knock_out_probability == 0.0
    assert result.knock_in_probability == 0.0
    assert result.present_value == pytest.approx(1_000.0 * (1 + 0.20 * 21 / 252))
