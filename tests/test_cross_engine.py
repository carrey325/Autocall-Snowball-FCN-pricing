from __future__ import annotations

from structured_products import MCConfig, PDEConfig, MarketData, make_classic_snowball, price


def test_mc_and_pde_agree_within_mc_error_and_discretization() -> None:
    product = make_classic_snowball(maturity_days=63)
    market = MarketData(
        spots=(100.0,),
        rate=0.03,
        dividend_yields=(0.0,),
        volatilities=(0.2,),
    )
    mc = price(product, market, "mc", MCConfig(n_paths=20_000))
    pde = price(product, market, "pde", PDEConfig(spot_grid_points=401))
    tolerance = max(4.0 * float(mc.standard_error), 0.002 * product.notional)
    assert abs(mc.present_value - pde.present_value) <= tolerance
