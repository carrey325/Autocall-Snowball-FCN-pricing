from __future__ import annotations

import pytest

from structured_products.builders import (
    make_butterfly_snowball,
    make_stepdown_snowball,
    make_worst_of_snowball,
)
from structured_products.market import MarketData


def test_schedule_variants_are_data_not_product_classes() -> None:
    butterfly = make_butterfly_snowball()
    stepdown = make_stepdown_snowball()
    assert type(butterfly) is type(stepdown)
    assert butterfly.autocall is not None
    assert stepdown.autocall is not None
    assert butterfly.autocall.coupon_rates[0] > butterfly.autocall.coupon_rates[-1]
    assert stepdown.autocall.barrier_ratios[0] > stepdown.autocall.barrier_ratios[-1]


def test_worst_of_requires_matching_market_dimensions() -> None:
    product = make_worst_of_snowball(reference_spots=(100.0, 90.0))
    market = MarketData(
        spots=(100.0,),
        rate=0.03,
        dividend_yields=(0.0,),
        volatilities=(0.2,),
    )
    with pytest.raises(ValueError, match="dimensions"):
        market.validate_for(product)


def test_invalid_correlation_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive semidefinite"):
        MarketData(
            spots=(100.0, 100.0, 100.0),
            rate=0.03,
            dividend_yields=(0.0, 0.0, 0.0),
            volatilities=(0.2, 0.2, 0.2),
            correlation=((1.0, 0.9, 0.9), (0.9, 1.0, -0.9), (0.9, -0.9, 1.0)),
        )
