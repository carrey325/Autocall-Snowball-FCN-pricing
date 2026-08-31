"""Public pricing dispatcher with explicit capability validation."""

from __future__ import annotations

from .config import MCConfig, PDEConfig
from .engines.mc import price_mc
from .engines.pde import price_pde
from .enums import PricingMethod
from .market import MarketData
from .products import StructuredNote
from .results import PricingResult


def price(
    product: StructuredNote,
    market: MarketData,
    method: PricingMethod | str,
    engine_config: MCConfig | PDEConfig | None = None,
) -> PricingResult:
    try:
        selected = method if isinstance(method, PricingMethod) else PricingMethod(method.lower())
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"unsupported pricing method: {method}") from exc
    if selected is PricingMethod.MC:
        if engine_config is not None and not isinstance(engine_config, MCConfig):
            raise TypeError("MC pricing requires MCConfig")
        return price_mc(product, market, engine_config or MCConfig())
    if engine_config is not None and not isinstance(engine_config, PDEConfig):
        raise TypeError("PDE pricing requires PDEConfig")
    return price_pde(product, market, engine_config or PDEConfig())


__all__ = ["price"]
