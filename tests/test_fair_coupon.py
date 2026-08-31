from __future__ import annotations

import pytest

from structured_products import (
    MCConfig,
    PDEConfig,
    MarketData,
    make_classic_snowball,
    price,
    solve_fair_coupon,
)


MARKET = MarketData(
    spots=(100.0,),
    rate=0.03,
    dividend_yields=(0.0,),
    volatilities=(0.2,),
)


def test_pde_fair_coupon_reprices_to_target() -> None:
    source = make_classic_snowball(maturity_days=63, coupon_rate=0.14)
    config = PDEConfig(spot_grid_points=201)
    target = price(source, MARKET, "pde", config).present_value
    candidate = make_classic_snowball(maturity_days=63, coupon_rate=0.05)
    result = solve_fair_coupon(candidate, MARKET, target, "pde", config, 0.01, 0.40)
    assert result.coupon_rate == pytest.approx(0.14, abs=1.0e-7)
    assert abs(result.residual) < 1.0e-6


def test_mc_fair_coupon_is_reproducible() -> None:
    product = make_classic_snowball(maturity_days=42, coupon_rate=0.10)
    config = MCConfig(n_paths=2_000)
    target = product.notional
    first = solve_fair_coupon(product, MARKET, target, "mc", config, 0.0, 0.5)
    second = solve_fair_coupon(product, MARKET, target, "mc", config, 0.0, 0.5)
    assert first == second


def test_non_bracketing_coupon_interval_fails() -> None:
    product = make_classic_snowball(maturity_days=42)
    with pytest.raises(ValueError, match="does not bracket"):
        solve_fair_coupon(
            product,
            MARKET,
            10_000.0,
            "pde",
            PDEConfig(spot_grid_points=201),
            0.01,
            0.02,
        )
