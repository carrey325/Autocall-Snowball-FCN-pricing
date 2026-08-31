"""Clean-room structured-products pricing framework."""

from .builders import (
    make_butterfly_snowball,
    make_classic_snowball,
    make_discount_entry_fcn,
    make_dividend_snowball,
    make_standard_fcn,
    make_stepdown_snowball,
    make_wide_snowball,
    make_worst_of_fcn,
    make_worst_of_snowball,
)
from .analytics import calculate_greeks, solve_fair_coupon
from .enums import BasketRule, CouponRule, PricingMethod, SameDayPriority
from .config import GreekConfig, MCConfig, PDEConfig, ResolvedConfig, load_config
from .market import MarketData
from .pricing import price
from .products import (
    AutocallFeature,
    CouponFeature,
    KnockInFeature,
    RedemptionFeature,
    StructuredNote,
)
from .results import FairCouponResult, GreeksResult, PricingResult

__version__ = "0.2.0"

__all__ = [
    "AutocallFeature",
    "BasketRule",
    "CouponFeature",
    "CouponRule",
    "calculate_greeks",
    "FairCouponResult",
    "GreeksResult",
    "GreekConfig",
    "KnockInFeature",
    "MarketData",
    "MCConfig",
    "PDEConfig",
    "PricingMethod",
    "PricingResult",
    "RedemptionFeature",
    "ResolvedConfig",
    "SameDayPriority",
    "StructuredNote",
    "make_butterfly_snowball",
    "make_classic_snowball",
    "make_discount_entry_fcn",
    "make_dividend_snowball",
    "make_standard_fcn",
    "make_stepdown_snowball",
    "make_wide_snowball",
    "make_worst_of_fcn",
    "make_worst_of_snowball",
    "load_config",
    "price",
    "solve_fair_coupon",
]
