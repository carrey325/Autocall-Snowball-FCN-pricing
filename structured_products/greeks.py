"""Bump-and-revalue Greeks for the new autocall Monte Carlo engine."""

from __future__ import annotations

from dataclasses import replace

from .autocall_engine_mc import generate_normal_shocks, price_autocall_mc
from .market import EngineConfig, MarketData
from .products import AutocallProduct


def _shorten_product(
    product: AutocallProduct,
    day_counter: int,
    shift_days: int,
) -> AutocallProduct:
    total_days = product.maturity_days(day_counter)
    if shift_days >= total_days:
        raise ValueError("time shift is too large for the remaining maturity")
    remaining_days = total_days - shift_days
    keep = [day <= remaining_days for day in product.knock_out_observation_days]
    return replace(
        product,
        maturity=remaining_days / day_counter,
        knock_out_observation_days=tuple(
            day for day, flag in zip(product.knock_out_observation_days, keep) if flag
        ),
        knock_out_barrier_schedule=tuple(
            value for value, flag in zip(product.knock_out_barrier_schedule, keep) if flag
        ),
        knock_out_coupon_schedule=tuple(
            value for value, flag in zip(product.knock_out_coupon_schedule, keep) if flag
        ),
    )


def mc_greeks(
    product: AutocallProduct,
    market: MarketData,
    engine_config: EngineConfig,
    *,
    spot_bump_ratio: float = 0.01,
    vol_bump: float = 0.01,
    theta_shift_days: int = 1,
) -> dict[str, float]:
    shocks = generate_normal_shocks(product, engine_config)
    base = price_autocall_mc(product, market, engine_config, shocks=shocks)

    spot_bump = product.s0 * spot_bump_ratio
    up_product = product.with_updates(s0=product.s0 + spot_bump)
    down_product = product.with_updates(s0=product.s0 - spot_bump)
    up = price_autocall_mc(up_product, market, engine_config, shocks=shocks)
    down = price_autocall_mc(down_product, market, engine_config, shocks=shocks)

    higher_vol = replace(market, volatility=market.volatility + vol_bump)
    lower_vol = replace(market, volatility=max(1.0e-6, market.volatility - vol_bump))
    vega_up = price_autocall_mc(product, higher_vol, engine_config, shocks=shocks)
    vega_down = price_autocall_mc(product, lower_vol, engine_config, shocks=shocks)

    shorter_product = _shorten_product(product, engine_config.day_counter, theta_shift_days)
    shorter_steps = engine_config.total_mc_steps(shorter_product.maturity)
    theta_price = price_autocall_mc(
        shorter_product,
        market,
        engine_config,
        shocks=shocks[:, :shorter_steps],
    )
    theta_dt = theta_shift_days / engine_config.day_counter

    return {
        "price": float(base),
        "delta": float((up - down) / (2.0 * spot_bump)),
        "gamma": float((up - 2.0 * base + down) / (spot_bump**2)),
        "vega": float((vega_up - vega_down) / (2.0 * vol_bump)),
        "theta": float((theta_price - base) / theta_dt),
    }
