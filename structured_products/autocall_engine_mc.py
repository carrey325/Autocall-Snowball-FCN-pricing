"""Unified Monte Carlo engine for first-tier autocall structures."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt

import numpy as np

from .market import EngineConfig, MarketData
from .products import AutocallProduct


@dataclass(frozen=True)
class AutocallMCResult:
    price: float
    knock_in_probability: float
    knock_out_probability: float
    average_knock_out_time: float | None
    average_coupon_rate: float


def generate_normal_shocks(
    product: AutocallProduct,
    engine_config: EngineConfig,
) -> np.ndarray:
    rng = np.random.default_rng(engine_config.seed)
    return rng.standard_normal(
        (engine_config.n_paths, engine_config.total_mc_steps(product.maturity))
    )


def _simulate_paths(
    product: AutocallProduct,
    market: MarketData,
    engine_config: EngineConfig,
    shocks: np.ndarray | None = None,
) -> np.ndarray:
    total_steps = engine_config.total_mc_steps(product.maturity)
    dt = 1.0 / (engine_config.day_counter * engine_config.steps_per_day)
    normals = shocks if shocks is not None else generate_normal_shocks(product, engine_config)
    if normals.shape != (engine_config.n_paths, total_steps):
        raise ValueError("shocks shape does not match product maturity and engine config")

    drift = (market.rate - market.dividend_yield - 0.5 * market.volatility**2) * dt
    diffusion = market.volatility * sqrt(dt)
    growth = np.exp(drift + diffusion * normals)

    paths = np.empty((engine_config.n_paths, total_steps + 1), dtype=float)
    paths[:, 0] = product.s0
    paths[:, 1:] = product.s0 * np.cumprod(growth, axis=1)
    return paths


def _compute_loss_cashflow(product: AutocallProduct, terminal_spot: np.ndarray) -> np.ndarray:
    if product.loss_rule != "min(spot_return, 0)":
        raise NotImplementedError(f"Unsupported loss rule: {product.loss_rule}")
    spot_return = terminal_spot / product.s0 - 1.0
    return np.minimum(spot_return, 0.0) * product.notional


def price_autocall_mc(
    product: AutocallProduct,
    market: MarketData,
    engine_config: EngineConfig,
    *,
    shocks: np.ndarray | None = None,
    return_details: bool = False,
) -> float | AutocallMCResult:
    if product.knock_in_obs_rule != "daily":
        raise NotImplementedError("The refactor currently supports daily KI observation only")

    total_days = engine_config.maturity_days(product.maturity)
    total_steps = total_days * engine_config.steps_per_day
    paths = _simulate_paths(product, market, engine_config, shocks=shocks)

    ki_days = np.arange(max(1, product.knock_in_start_day), total_days + 1, dtype=int)
    ki_steps = ki_days * engine_config.steps_per_day
    if product.knock_in_barrier is None or len(ki_steps) == 0:
        ki_hits = np.zeros((engine_config.n_paths, 0), dtype=bool)
        knocked_in = np.zeros(engine_config.n_paths, dtype=bool)
        first_ki_days = np.full(engine_config.n_paths, total_days, dtype=int)
    else:
        ki_hits = paths[:, ki_steps] <= product.knock_in_barrier
        knocked_in = ki_hits.any(axis=1)
        first_ki_pos = ki_hits.argmax(axis=1)
        first_ki_days = np.where(knocked_in, ki_days[first_ki_pos], total_days)

    ko_days = np.asarray(product.knock_out_observation_days, dtype=int)
    ko_steps = ko_days * engine_config.steps_per_day
    ko_barriers = np.asarray(product.knock_out_barrier_schedule, dtype=float)
    ko_coupons = np.asarray(product.knock_out_coupon_schedule, dtype=float)

    if len(ko_steps) == 0:
        ko_hits = np.zeros((engine_config.n_paths, 0), dtype=bool)
        knocked_out = np.zeros(engine_config.n_paths, dtype=bool)
        first_ko_days = np.full(engine_config.n_paths, total_days, dtype=int)
        ko_index = np.full(engine_config.n_paths, -1, dtype=int)
        ko_coupon_rate = np.zeros(engine_config.n_paths, dtype=float)
    else:
        ko_hits = paths[:, ko_steps] >= ko_barriers
        knocked_out = ko_hits.any(axis=1)
        ko_index_raw = ko_hits.argmax(axis=1)
        ko_index = np.where(knocked_out, ko_index_raw, -1)
        first_ko_days = np.where(knocked_out, ko_days[ko_index_raw], total_days)
        ko_coupon_rate = np.where(knocked_out, ko_coupons[ko_index_raw], 0.0)

    knock_out_times = first_ko_days / engine_config.day_counter
    maturity_time = total_days / engine_config.day_counter
    terminal_spot = paths[:, total_steps]

    alive = np.ones(engine_config.n_paths, dtype=bool)
    final_coupon_rate = np.zeros(engine_config.n_paths, dtype=float)
    terminal_payoff = np.zeros(engine_config.n_paths, dtype=float)

    if knocked_out.any():
        ko_df = np.exp(-market.rate * knock_out_times[knocked_out])
        terminal_payoff[knocked_out] = (
            ko_coupon_rate[knocked_out]
            * knock_out_times[knocked_out]
            * product.notional
            * ko_df
        )
        final_coupon_rate[knocked_out] = ko_coupon_rate[knocked_out]
        alive[knocked_out] = False

    survives_to_maturity = alive
    no_ki_to_maturity = survives_to_maturity & (~knocked_in)
    if no_ki_to_maturity.any():
        terminal_payoff[no_ki_to_maturity] = (
            product.maturity_coupon
            * maturity_time
            * product.notional
            * exp(-market.rate * maturity_time)
        )
        final_coupon_rate[no_ki_to_maturity] = product.maturity_coupon

    ki_no_ko = survives_to_maturity & knocked_in
    if ki_no_ko.any():
        terminal_payoff[ki_no_ko] = (
            _compute_loss_cashflow(product, terminal_spot[ki_no_ko])
            * exp(-market.rate * maturity_time)
        )

    funding_interest = np.zeros(engine_config.n_paths, dtype=float)
    if product.margin_ratio < 1:
        funding_end_days = np.minimum(first_ki_days, first_ko_days)
        funding_end_time = funding_end_days / engine_config.day_counter
        funding_interest = (
            (1.0 - product.margin_ratio)
            * (1.0 - np.exp(-market.rate * funding_end_time))
            * product.notional
        )

    total_value = terminal_payoff + funding_interest
    price = float(np.mean(total_value))

    if not return_details:
        return price

    average_ko_time = float(np.mean(knock_out_times[knocked_out])) if knocked_out.any() else None
    return AutocallMCResult(
        price=price,
        knock_in_probability=float(np.mean(knocked_in)),
        knock_out_probability=float(np.mean(knocked_out)),
        average_knock_out_time=average_ko_time,
        average_coupon_rate=float(np.mean(final_coupon_rate)),
    )
