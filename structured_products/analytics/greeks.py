"""Common-random-number bump-and-revalue Greeks."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from ..config import GreekConfig, MCConfig, PDEConfig
from ..enums import PricingMethod
from ..market import MarketData
from ..pricing import price
from ..products import StructuredNote
from ..results import GreeksResult


def _roll_product(
    product: StructuredNote, shift_days: int
) -> StructuredNote:
    if shift_days <= 0 or shift_days >= product.maturity_days:
        raise ValueError("theta shift must be inside the remaining maturity")
    autocall = product.autocall
    if autocall:
        keep = [
            day > shift_days for day in autocall.observation_days
        ]
        autocall = replace(
            autocall,
            observation_days=tuple(
                day - shift_days
                for day, include in zip(autocall.observation_days, keep)
                if include
            ),
            barrier_ratios=tuple(
                value
                for value, include in zip(autocall.barrier_ratios, keep)
                if include
            ),
            coupon_rates=tuple(
                value
                for value, include in zip(autocall.coupon_rates, keep)
                if include
            ),
        )
        if not autocall.observation_days:
            autocall = None

    coupon = product.coupon
    if coupon.payment_days:
        keep_coupon = [day > shift_days for day in coupon.payment_days]
        coupon = replace(
            coupon,
            payment_days=tuple(
                day - shift_days
                for day, include in zip(coupon.payment_days, keep_coupon)
                if include
            ),
            rate_schedule=tuple(
                rate
                for rate, include in zip(coupon.rate_schedule, keep_coupon)
                if include
            ),
        )
    knock_in = product.knock_in
    if knock_in:
        knock_in = replace(
            knock_in,
            monitoring_start_day=max(1, knock_in.monitoring_start_day - shift_days),
        )
    return replace(
        product,
        maturity_days=product.maturity_days - shift_days,
        autocall=autocall,
        coupon=coupon,
        knock_in=knock_in,
    )


def _bump_correlation(
    market: MarketData, bump: float
) -> MarketData:
    matrix = np.asarray(market.correlation, dtype=float).copy()
    mask = ~np.eye(len(matrix), dtype=bool)
    matrix[mask] += bump
    return replace(market, correlation=tuple(tuple(row) for row in matrix))


def calculate_greeks(
    product: StructuredNote,
    market: MarketData,
    method: PricingMethod | str,
    engine_config: MCConfig | PDEConfig,
    greek_config: GreekConfig | None = None,
) -> GreeksResult:
    selected = method if isinstance(method, PricingMethod) else PricingMethod(method.lower())
    config = greek_config or GreekConfig()
    market.validate_for(product)

    def value(candidate_product: StructuredNote, candidate_market: MarketData) -> float:
        return price(
            candidate_product, candidate_market, selected, engine_config
        ).present_value

    base = value(product, market)
    deltas: list[float] = []
    gammas: list[float] = []
    vegas: list[float] = []

    for index, spot in enumerate(market.spots):
        bump = spot * config.relative_spot_bump
        up_spots = list(market.spots)
        down_spots = list(market.spots)
        up_spots[index] += bump
        down_spots[index] -= bump
        up = value(product, replace(market, spots=tuple(up_spots)))
        down = value(product, replace(market, spots=tuple(down_spots)))
        deltas.append((up - down) / (2.0 * bump))
        gammas.append((up - 2.0 * base + down) / bump**2)

        volatility = market.volatilities[index]
        if volatility <= config.volatility_bump:
            raise ValueError("volatility bump requires base volatility above the bump")
        up_vols = list(market.volatilities)
        down_vols = list(market.volatilities)
        up_vols[index] += config.volatility_bump
        down_vols[index] -= config.volatility_bump
        up_vega = value(product, replace(market, volatilities=tuple(up_vols)))
        down_vega = value(product, replace(market, volatilities=tuple(down_vols)))
        vegas.append((up_vega - down_vega) / (2.0 * config.volatility_bump))

    up_rate = value(product, replace(market, rate=market.rate + config.rate_bump))
    down_rate = value(product, replace(market, rate=market.rate - config.rate_bump))
    rho = (up_rate - down_rate) / (2.0 * config.rate_bump)

    rolled = _roll_product(product, config.theta_days)
    theta = value(rolled, market) - base

    correlation_sensitivity: float | None = None
    if product.n_assets > 1:
        try:
            up_correlation = _bump_correlation(market, config.correlation_bump)
            down_correlation = _bump_correlation(market, -config.correlation_bump)
        except ValueError as exc:
            raise ValueError(
                "correlation bump does not preserve a positive-semidefinite matrix"
            ) from exc
        correlation_sensitivity = (
            value(product, up_correlation) - value(product, down_correlation)
        ) / (2.0 * config.correlation_bump)

    return GreeksResult(
        method=selected.value,
        base_price=base,
        delta=tuple(deltas),
        gamma=tuple(gammas),
        vega=tuple(vegas),
        theta=theta,
        rho=rho,
        correlation_sensitivity=correlation_sensitivity,
        bumps={
            "relative_spot": config.relative_spot_bump,
            "volatility": config.volatility_bump,
            "rate": config.rate_bump,
            "theta_days": float(config.theta_days),
            "correlation": config.correlation_bump,
        },
    )
