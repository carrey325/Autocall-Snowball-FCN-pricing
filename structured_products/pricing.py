"""Top-level dispatchers for legacy and refactored pricing flows."""

from __future__ import annotations

from .autocall_engine_mc import AutocallMCResult, price_autocall_mc
from .autocall_engine_pde import price_autocall_pde, support_matrix
from .legacy_adapter import legacy_coupon_search, legacy_greeks_compute, legacy_price
from .market import EngineConfig, MarketData
from .products import AutocallProduct


def price(
    product: AutocallProduct,
    market: MarketData,
    *,
    method: str = "MC",
    engine_config: EngineConfig | None = None,
    return_details: bool = False,
) -> float | AutocallMCResult:
    cfg = engine_config or EngineConfig()
    method_upper = method.upper()
    if method_upper == "MC":
        return price_autocall_mc(product, market, cfg, return_details=return_details)
    if return_details:
        raise ValueError("return_details is only available for MC pricing")
    if method_upper == "PDE":
        return price_autocall_pde(product, market, cfg)
    raise ValueError(f"Unsupported pricing method: {method}")


__all__ = [
    "legacy_coupon_search",
    "legacy_greeks_compute",
    "legacy_price",
    "price",
    "support_matrix",
]
