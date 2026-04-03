"""Product specifications and lightweight builders for autocall structures."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence


def _as_tuple(values: Sequence[float | int] | None) -> tuple[float | int, ...]:
    if values is None:
        return ()
    return tuple(values)


def build_monthly_observation_days(
    maturity_years: float,
    day_counter: int = 252,
    start_month: int = 1,
    step_months: int = 1,
) -> tuple[int, ...]:
    """Build monthly KO observation days using the notebook's day count style."""

    total_months = max(1, int(round(maturity_years * 12)))
    days: list[int] = []
    total_days = max(1, int(round(maturity_years * day_counter)))
    for month in range(start_month, total_months + 1, step_months):
        day = min(total_days, int(round(month * day_counter / 12)))
        if not days or day != days[-1]:
            days.append(day)
    if not days:
        days.append(total_days)
    return tuple(days)


@dataclass(frozen=True)
class AutocallProduct:
    """Unified product spec for first-tier autocall notes.

    Pricing follows the legacy notebook convention: returned notional is not
    included in the product value. Coupon legs and KI downside only are priced.
    """

    product_name: str
    s0: float
    maturity: float
    notional: float = 1.0
    margin_ratio: float = 1.0
    knock_in_barrier: float | None = None
    knock_in_obs_rule: str = "daily"
    knock_in_start_day: int = 0
    knock_out_barrier_schedule: tuple[float, ...] = ()
    knock_out_coupon_schedule: tuple[float, ...] = ()
    maturity_coupon: float = 0.0
    knock_out_observation_days: tuple[int, ...] = ()
    loss_rule: str = "min(spot_return, 0)"
    principal_redemption_rule: str = "full_notional"
    strike: float | None = None
    pricing_convention: str = "net_return_excluding_principal"

    def __post_init__(self) -> None:
        if self.s0 <= 0:
            raise ValueError("s0 must be positive")
        if self.notional <= 0:
            raise ValueError("notional must be positive")
        if self.maturity <= 0:
            raise ValueError("maturity must be positive")
        if not 0 < self.margin_ratio <= 1:
            raise ValueError("margin_ratio must be in (0, 1]")
        if self.knock_in_barrier is not None and self.knock_in_barrier <= 0:
            raise ValueError("knock_in_barrier must be positive when provided")
        if len(self.knock_out_barrier_schedule) != len(self.knock_out_coupon_schedule):
            raise ValueError("KO barrier and coupon schedules must have the same length")
        if len(self.knock_out_barrier_schedule) != len(self.knock_out_observation_days):
            raise ValueError("KO barrier schedule must align with KO observation days")
        if any(day <= 0 for day in self.knock_out_observation_days):
            raise ValueError("KO observation days must be strictly positive")
        if self.knock_out_observation_days and tuple(sorted(self.knock_out_observation_days)) != self.knock_out_observation_days:
            raise ValueError("KO observation days must be sorted")

    def maturity_days(self, day_counter: int) -> int:
        return max(1, int(round(self.maturity * day_counter)))

    def with_updates(self, **updates: object) -> "AutocallProduct":
        return replace(self, **updates)


def make_classic_autocall(
    *,
    s0: float = 1.0,
    maturity: float = 1.0,
    notional: float = 1.0,
    margin_ratio: float = 1.0,
    knock_in_ratio: float = 0.8,
    knock_out_ratio: float = 1.0,
    knock_out_coupon: float = 0.18,
    maturity_coupon: float | None = None,
    day_counter: int = 252,
    observation_days: Sequence[int] | None = None,
) -> AutocallProduct:
    obs_days = tuple(observation_days or build_monthly_observation_days(maturity, day_counter))
    coupon = knock_out_coupon if maturity_coupon is None else maturity_coupon
    return AutocallProduct(
        product_name="classic_autocall",
        s0=s0,
        maturity=maturity,
        notional=notional,
        margin_ratio=margin_ratio,
        knock_in_barrier=s0 * knock_in_ratio,
        knock_out_barrier_schedule=tuple(s0 * knock_out_ratio for _ in obs_days),
        knock_out_coupon_schedule=tuple(knock_out_coupon for _ in obs_days),
        maturity_coupon=coupon,
        knock_out_observation_days=obs_days,
        strike=s0,
    )


def make_wide_autocall(
    *,
    s0: float = 1.0,
    maturity: float = 1.0,
    notional: float = 1.0,
    margin_ratio: float = 1.0,
    knock_in_ratio: float = 0.75,
    knock_out_ratio: float = 1.02,
    knock_out_coupon: float = 0.12,
    maturity_coupon: float | None = None,
    day_counter: int = 252,
    observation_days: Sequence[int] | None = None,
) -> AutocallProduct:
    obs_days = tuple(observation_days or build_monthly_observation_days(maturity, day_counter))
    coupon = knock_out_coupon if maturity_coupon is None else maturity_coupon
    return AutocallProduct(
        product_name="wide_autocall",
        s0=s0,
        maturity=maturity,
        notional=notional,
        margin_ratio=margin_ratio,
        knock_in_barrier=s0 * knock_in_ratio,
        knock_out_barrier_schedule=tuple(s0 * knock_out_ratio for _ in obs_days),
        knock_out_coupon_schedule=tuple(knock_out_coupon for _ in obs_days),
        maturity_coupon=coupon,
        knock_out_observation_days=obs_days,
        strike=s0,
    )


def make_dividend_autocall(
    *,
    s0: float = 1.0,
    maturity: float = 1.0,
    notional: float = 1.0,
    margin_ratio: float = 1.0,
    knock_in_ratio: float = 0.8,
    knock_out_ratio: float = 1.0,
    knock_out_coupon: float = 0.2,
    maturity_coupon: float = 0.08,
    day_counter: int = 252,
    observation_days: Sequence[int] | None = None,
) -> AutocallProduct:
    obs_days = tuple(observation_days or build_monthly_observation_days(maturity, day_counter))
    return AutocallProduct(
        product_name="dividend_autocall",
        s0=s0,
        maturity=maturity,
        notional=notional,
        margin_ratio=margin_ratio,
        knock_in_barrier=s0 * knock_in_ratio,
        knock_out_barrier_schedule=tuple(s0 * knock_out_ratio for _ in obs_days),
        knock_out_coupon_schedule=tuple(knock_out_coupon for _ in obs_days),
        maturity_coupon=maturity_coupon,
        knock_out_observation_days=obs_days,
        strike=s0,
    )


def make_butterfly_autocall(
    *,
    s0: float = 1.0,
    maturity: float = 1.0,
    notional: float = 1.0,
    margin_ratio: float = 1.0,
    knock_in_ratio: float = 0.8,
    knock_out_ratio: float = 1.0,
    front_coupon: float = 0.22,
    back_coupon: float = 0.1,
    maturity_coupon: float | None = None,
    day_counter: int = 252,
    observation_days: Sequence[int] | None = None,
) -> AutocallProduct:
    obs_days = tuple(observation_days or build_monthly_observation_days(maturity, day_counter))
    if len(obs_days) == 1:
        coupons = (front_coupon,)
    else:
        step = (back_coupon - front_coupon) / (len(obs_days) - 1)
        coupons = tuple(front_coupon + step * idx for idx in range(len(obs_days)))
    final_coupon = coupons[-1] if maturity_coupon is None else maturity_coupon
    return AutocallProduct(
        product_name="butterfly_autocall",
        s0=s0,
        maturity=maturity,
        notional=notional,
        margin_ratio=margin_ratio,
        knock_in_barrier=s0 * knock_in_ratio,
        knock_out_barrier_schedule=tuple(s0 * knock_out_ratio for _ in obs_days),
        knock_out_coupon_schedule=coupons,
        maturity_coupon=final_coupon,
        knock_out_observation_days=obs_days,
        strike=s0,
    )


def make_stepdown_autocall(
    *,
    s0: float = 1.0,
    maturity: float = 1.0,
    notional: float = 1.0,
    margin_ratio: float = 1.0,
    knock_in_ratio: float = 0.8,
    first_knock_out_ratio: float = 1.03,
    step_down_ratio: float = 0.01,
    knock_out_coupon: float = 0.18,
    maturity_coupon: float | None = None,
    day_counter: int = 252,
    observation_days: Sequence[int] | None = None,
) -> AutocallProduct:
    obs_days = tuple(observation_days or build_monthly_observation_days(maturity, day_counter))
    barrier_schedule = tuple(
        s0 * max(0.0, first_knock_out_ratio - step_down_ratio * idx)
        for idx in range(len(obs_days))
    )
    coupon = knock_out_coupon if maturity_coupon is None else maturity_coupon
    return AutocallProduct(
        product_name="stepdown_autocall",
        s0=s0,
        maturity=maturity,
        notional=notional,
        margin_ratio=margin_ratio,
        knock_in_barrier=s0 * knock_in_ratio,
        knock_out_barrier_schedule=barrier_schedule,
        knock_out_coupon_schedule=tuple(knock_out_coupon for _ in obs_days),
        maturity_coupon=coupon,
        knock_out_observation_days=obs_days,
        strike=s0,
    )
