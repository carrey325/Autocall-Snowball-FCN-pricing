from __future__ import annotations

import pytest

from structured_products import (
    GreekConfig,
    MCConfig,
    MarketData,
    calculate_greeks,
    make_classic_snowball,
    make_worst_of_snowball,
)
from structured_products.analytics.greeks import _roll_product


def test_spot_greeks_do_not_move_contractual_reference_levels() -> None:
    product = make_classic_snowball(maturity_days=42)
    references = product.reference_spots
    market = MarketData(
        spots=(100.0,),
        rate=0.03,
        dividend_yields=(0.0,),
        volatilities=(0.2,),
    )
    result = calculate_greeks(
        product, market, "mc", MCConfig(n_paths=2_000), GreekConfig(theta_days=1)
    )
    assert product.reference_spots == references
    assert len(result.delta) == len(result.gamma) == len(result.vega) == 1
    assert result.base_price > 0


def test_theta_roll_shifts_all_schedules() -> None:
    product = make_classic_snowball(
        maturity_days=42, observation_days=(21, 42)
    )
    rolled = _roll_product(product, 1)
    assert rolled.maturity_days == 41
    assert rolled.reference_spots == product.reference_spots
    assert rolled.autocall is not None
    assert rolled.autocall.observation_days == (20, 41)


def test_multi_asset_greeks_include_correlation_sensitivity() -> None:
    product = make_worst_of_snowball(
        reference_spots=(100.0, 100.0), maturity_days=21, observation_days=(21,)
    )
    market = MarketData(
        spots=(100.0, 100.0),
        rate=0.03,
        dividend_yields=(0.0, 0.0),
        volatilities=(0.2, 0.25),
        correlation=((1.0, 0.4), (0.4, 1.0)),
    )
    result = calculate_greeks(product, market, "mc", MCConfig(n_paths=1_000))
    assert len(result.delta) == len(result.gamma) == len(result.vega) == 2
    assert result.correlation_sensitivity is not None


def test_mc_greeks_are_reproducible() -> None:
    product = make_classic_snowball(maturity_days=21, observation_days=(21,))
    market = MarketData(
        spots=(100.0,),
        rate=0.03,
        dividend_yields=(0.0,),
        volatilities=(0.2,),
    )
    first = calculate_greeks(product, market, "mc", MCConfig(n_paths=1_000))
    second = calculate_greeks(product, market, "mc", MCConfig(n_paths=1_000))
    assert first == second
