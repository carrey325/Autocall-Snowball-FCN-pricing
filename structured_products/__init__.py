"""Structured products pricing helpers."""

from .autocall_engine_mc import AutocallMCResult, price_autocall_mc
from .autocall_engine_pde import price_autocall_pde, support_matrix
from .greeks import mc_greeks
from .legacy_adapter import (
    legacy_coupon_search,
    legacy_greeks_compute,
    legacy_price,
    legacy_public_entry_points,
)
from .market import EngineConfig, MarketData
from .pricing import price
from .products import (
    AutocallProduct,
    build_monthly_observation_days,
    make_butterfly_autocall,
    make_classic_autocall,
    make_dividend_autocall,
    make_stepdown_autocall,
    make_wide_autocall,
)

__all__ = [
    "AutocallMCResult",
    "AutocallProduct",
    "EngineConfig",
    "MarketData",
    "build_monthly_observation_days",
    "legacy_coupon_search",
    "legacy_greeks_compute",
    "legacy_price",
    "legacy_public_entry_points",
    "make_butterfly_autocall",
    "make_classic_autocall",
    "make_dividend_autocall",
    "make_stepdown_autocall",
    "make_wide_autocall",
    "mc_greeks",
    "price",
    "price_autocall_mc",
    "price_autocall_pde",
    "support_matrix",
]
