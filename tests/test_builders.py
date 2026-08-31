from __future__ import annotations

import pytest

from structured_products import (
    MCConfig,
    PDEConfig,
    MarketData,
    make_butterfly_snowball,
    make_classic_snowball,
    make_discount_entry_fcn,
    make_dividend_snowball,
    make_standard_fcn,
    make_stepdown_snowball,
    make_wide_snowball,
    make_worst_of_fcn,
    make_worst_of_snowball,
    price,
)


SINGLE_MARKET = MarketData(
    spots=(100.0,),
    rate=0.03,
    dividend_yields=(0.0,),
    volatilities=(0.2,),
)
MULTI_MARKET = MarketData(
    spots=(100.0, 100.0),
    rate=0.03,
    dividend_yields=(0.0, 0.0),
    volatilities=(0.2, 0.25),
    correlation=((1.0, 0.4), (0.4, 1.0)),
)


@pytest.mark.parametrize(
    "product",
    [
        make_classic_snowball(maturity_days=21, observation_days=(21,)),
        make_wide_snowball(maturity_days=21, observation_days=(21,)),
        make_butterfly_snowball(maturity_days=21, observation_days=(21,)),
        make_dividend_snowball(maturity_days=21, observation_days=(21,)),
        make_stepdown_snowball(maturity_days=21, observation_days=(21,)),
        make_standard_fcn(maturity_days=21, payment_days=(21,)),
        make_discount_entry_fcn(maturity_days=21, payment_days=(21,)),
    ],
)
def test_all_single_asset_builders_share_mc_and_pde(product) -> None:
    mc = price(product, SINGLE_MARKET, "mc", MCConfig(n_paths=200))
    pde = price(product, SINGLE_MARKET, "pde", PDEConfig(spot_grid_points=201))
    assert mc.present_value > 0
    assert pde.present_value > 0


@pytest.mark.parametrize(
    "product",
    [
        make_worst_of_snowball(
            reference_spots=(100.0, 100.0), maturity_days=21, observation_days=(21,)
        ),
        make_worst_of_fcn(
            reference_spots=(100.0, 100.0), maturity_days=21, payment_days=(21,)
        ),
    ],
)
def test_worst_of_builders_share_mc_engine(product) -> None:
    assert price(product, MULTI_MARKET, "mc", MCConfig(n_paths=200)).present_value > 0
