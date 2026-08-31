from __future__ import annotations

import pytest

from structured_products import (
    MCConfig,
    PDEConfig,
    MarketData,
    PricingMethod,
    make_classic_snowball,
    make_standard_fcn,
    make_stepdown_snowball,
    make_worst_of_snowball,
    price,
)


def market(volatility: float = 0.2) -> MarketData:
    return MarketData(
        spots=(100.0,),
        rate=0.03,
        dividend_yields=(0.0,),
        volatilities=(volatility,),
    )


def test_zero_volatility_pde_matches_mc() -> None:
    product = make_classic_snowball(
        maturity_days=21, observation_days=(21,), coupon_rate=0.12
    )
    pde = price(product, market(0.0), PricingMethod.PDE, PDEConfig(spot_grid_points=201))
    mc = price(product, market(0.0), PricingMethod.MC, MCConfig(n_paths=100))
    assert pde.present_value == pytest.approx(mc.present_value)


@pytest.mark.parametrize(
    "product",
    [
        make_classic_snowball(maturity_days=42),
        make_stepdown_snowball(maturity_days=42),
        make_standard_fcn(maturity_days=63, payment_days=(21, 42, 63)),
    ],
)
def test_generic_single_asset_products_run_with_pde(product) -> None:
    result = price(product, market(), "pde", PDEConfig(spot_grid_points=201))
    assert result.present_value > 0
    assert result.standard_error is None


def test_grid_refinement_is_stable() -> None:
    product = make_classic_snowball(maturity_days=63)
    coarse = price(product, market(), "pde", PDEConfig(spot_grid_points=201))
    fine = price(product, market(), "pde", PDEConfig(spot_grid_points=401))
    assert abs(coarse.present_value - fine.present_value) < 5.0


def test_worst_of_pde_is_explicitly_rejected() -> None:
    product = make_worst_of_snowball(reference_spots=(100.0, 100.0))
    multi_market = MarketData(
        spots=(100.0, 100.0),
        rate=0.03,
        dividend_yields=(0.0, 0.0),
        volatilities=(0.2, 0.2),
        correlation=((1.0, 0.5), (0.5, 1.0)),
    )
    with pytest.raises(ValueError, match="single-asset"):
        price(product, multi_market, "pde", PDEConfig())


def test_invalid_method_and_wrong_engine_config_fail() -> None:
    product = make_classic_snowball(maturity_days=21)
    with pytest.raises(ValueError, match="unsupported"):
        price(product, market(), "tree")
    with pytest.raises(TypeError, match="MCConfig"):
        price(product, market(), "mc", PDEConfig())
