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
from .enums import BasketRule, CouponRule, PricingMethod, SameDayPriority
from .market import MarketData
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
    "FairCouponResult",
    "GreeksResult",
    "KnockInFeature",
    "MarketData",
    "PricingMethod",
    "PricingResult",
    "RedemptionFeature",
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
]
