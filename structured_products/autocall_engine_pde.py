"""Partial PDE support for autocall products built on top of the legacy PDE blocks."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .legacy_adapter import load_legacy_namespace
from .market import EngineConfig, MarketData
from .products import AutocallProduct


SUPPORTED_PDE_PRODUCTS = {
    "classic_autocall",
    "wide_autocall",
    "dividend_autocall",
    "butterfly_autocall",
}


@dataclass(frozen=True)
class PDESupport:
    mc_products: tuple[str, ...]
    pde_products: tuple[str, ...]


def support_matrix() -> PDESupport:
    return PDESupport(
        mc_products=(
            "classic_autocall",
            "wide_autocall",
            "dividend_autocall",
            "butterfly_autocall",
            "stepdown_autocall",
        ),
        pde_products=tuple(sorted(SUPPORTED_PDE_PRODUCTS)),
    )


def _is_flat_schedule(values: tuple[float, ...]) -> bool:
    return len(set(round(value, 12) for value in values)) <= 1


def _validate_pde_product(product: AutocallProduct) -> None:
    if product.product_name not in SUPPORTED_PDE_PRODUCTS:
        raise NotImplementedError(f"{product.product_name} is MC-only in this version")
    if product.knock_in_obs_rule != "daily":
        raise NotImplementedError("PDE adapter currently supports daily KI only")
    if not _is_flat_schedule(product.knock_out_barrier_schedule):
        raise NotImplementedError("PDE adapter supports flat KO barriers only")


def _downside_component(
    namespace: dict[str, object],
    product: AutocallProduct,
    market: MarketData,
    engine_config: EngineConfig,
    observation_times: np.ndarray,
) -> float:
    if product.knock_in_barrier is None:
        return 0.0

    sb_ko_cls = namespace["SB_KO_CN"]
    db_ko_cls = namespace["DB_KO_CN"]
    pde_time_steps = engine_config.pde_time_steps(product.maturity)
    pde_spot_steps = engine_config.pde_spot_steps

    zero_rebate = 0.0
    ko_freq = [product.knock_in_obs_rule, "monthly"]
    ko_times = [np.array([]), observation_times]

    uop = sb_ko_cls(
        2,
        "UOP",
        product.s0,
        product.strike or product.s0,
        product.maturity,
        market.rate,
        market.dividend_yield,
        market.volatility,
        product.knock_out_barrier_schedule[0],
        zero_rebate,
        0,
        pde_spot_steps,
        pde_time_steps,
        "monthly",
        observation_times,
    )
    dkop = db_ko_cls(
        2,
        "DKOP",
        product.s0,
        product.strike or product.s0,
        product.maturity,
        market.rate,
        market.dividend_yield,
        market.volatility,
        product.knock_in_barrier,
        product.knock_out_barrier_schedule[0],
        [zero_rebate, zero_rebate],
        [0, 0],
        pde_spot_steps,
        pde_time_steps,
        ko_freq,
        ko_times,
    )
    return (dkop.price() - uop.price()) / product.s0 * product.notional


def _survival_unit_value(
    namespace: dict[str, object],
    product: AutocallProduct,
    market: MarketData,
    engine_config: EngineConfig,
    observation_times: np.ndarray,
) -> float:
    if product.knock_in_barrier is None:
        return float(np.exp(-market.rate * product.maturity))

    dot_cls = namespace["DOTV_CN"]
    pde_time_steps = engine_config.pde_time_steps(product.maturity)
    pde_spot_steps = engine_config.pde_spot_steps

    dot = dot_cls(
        0,
        "DOT",
        product.s0,
        product.maturity,
        market.rate,
        market.dividend_yield,
        market.volatility,
        product.knock_in_barrier,
        product.knock_out_barrier_schedule[0],
        [1.0, 1.0],
        [1, 1],
        pde_spot_steps,
        pde_time_steps,
        [product.knock_in_obs_rule, "monthly"],
        [np.array([]), observation_times],
    )
    cash = float(np.exp(-market.rate * product.maturity))
    return cash - dot.price()


def _funding_interest_component(
    namespace: dict[str, object],
    product: AutocallProduct,
    market: MarketData,
    engine_config: EngineConfig,
    observation_times: np.ndarray,
) -> float:
    if product.margin_ratio >= 1:
        return 0.0
    dot_cls = namespace["DOTV_CN"]
    pde_time_steps = engine_config.pde_time_steps(product.maturity)
    pde_spot_steps = engine_config.pde_spot_steps
    freq = [product.knock_in_obs_rule, "monthly"]
    ko_times = [np.array([]), observation_times]

    interest_touch = dot_cls(
        1,
        "DOT",
        product.s0,
        product.maturity,
        market.rate,
        market.dividend_yield,
        market.volatility,
        product.knock_in_barrier,
        product.knock_out_barrier_schedule[0],
        [market.rate, market.rate],
        [0, 0],
        pde_spot_steps,
        pde_time_steps,
        freq,
        ko_times,
    ).price()
    interest_survive = (1.0 - np.exp(-market.rate * product.maturity)) - dot_cls(
        2,
        "DOT",
        product.s0,
        product.maturity,
        market.rate,
        market.dividend_yield,
        market.volatility,
        product.knock_in_barrier,
        product.knock_out_barrier_schedule[0],
        [market.rate, market.rate],
        [1, 1],
        pde_spot_steps,
        pde_time_steps,
        freq,
        ko_times,
    ).price()
    return product.notional * (1.0 - product.margin_ratio) * (interest_touch + interest_survive)


def price_autocall_pde(
    product: AutocallProduct,
    market: MarketData,
    engine_config: EngineConfig,
) -> float:
    _validate_pde_product(product)
    namespace = load_legacy_namespace()
    otv_cls = namespace["OTV_CN"]
    pde_time_steps = engine_config.pde_time_steps(product.maturity)
    pde_spot_steps = engine_config.pde_spot_steps

    observation_times = np.asarray(product.knock_out_observation_days, dtype=float) / engine_config.day_counter
    ko_coupon_cash = np.asarray(product.knock_out_coupon_schedule, dtype=float) * observation_times
    ko_leg = otv_cls(
        "OTU",
        product.s0,
        product.maturity,
        market.rate,
        market.dividend_yield,
        market.volatility,
        product.knock_out_barrier_schedule[0],
        ko_coupon_cash,
        0,
        pde_spot_steps,
        pde_time_steps,
        "monthly",
        observation_times,
    ).price() * product.notional

    survival_unit = _survival_unit_value(namespace, product, market, engine_config, observation_times)
    maturity_coupon_leg = survival_unit * product.maturity_coupon * product.maturity * product.notional
    downside_leg = _downside_component(namespace, product, market, engine_config, observation_times)
    funding_leg = _funding_interest_component(namespace, product, market, engine_config, observation_times)
    return float(ko_leg + maturity_coupon_leg + downside_leg + funding_leg)
