"""Market and engine configuration objects for structured-product pricing."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class MarketData:
    """Simple flat market inputs reused by both MC and PDE engines."""

    rate: float
    dividend_yield: float = 0.0
    volatility: float = 0.2


@dataclass(frozen=True)
class EngineConfig:
    """Shared numerical configuration.

    The defaults intentionally stay close to the legacy notebook:
    two Monte Carlo steps per day and 252 trading days per year.
    """

    n_paths: int = 20_000
    day_counter: int = 252
    steps_per_day: int = 2
    seed: int | None = None
    pde_spot_steps: int = 1_000

    def maturity_days(self, maturity_years: float) -> int:
        return max(1, int(round(maturity_years * self.day_counter)))

    def total_mc_steps(self, maturity_years: float) -> int:
        return self.maturity_days(maturity_years) * self.steps_per_day

    def pde_time_steps(self, maturity_years: float) -> int:
        # Mirrors the legacy notebook's Nt = ceil(2 * T * day_counter).
        return max(2, int(ceil(2 * maturity_years * self.day_counter)))
