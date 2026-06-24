from __future__ import annotations

import math
import unittest

from structured_products import (
    EngineConfig,
    MarketData,
    legacy_price,
    make_butterfly_autocall,
    make_classic_autocall,
    make_dividend_autocall,
    make_stepdown_autocall,
    make_wide_autocall,
    mc_greeks,
    price,
)
from structured_products.legacy_adapter import default_legacy_notebook_path


MARKET = MarketData(rate=0.03, dividend_yield=0.0, volatility=0.2)
MC_CONFIG = EngineConfig(n_paths=12_000, day_counter=252, steps_per_day=2, seed=7)
PDE_CONFIG = EngineConfig(day_counter=252, steps_per_day=2, pde_spot_steps=300)
LEGACY_NOTEBOOK_PATH = default_legacy_notebook_path()
LEGACY_NOTEBOOK_AVAILABLE = LEGACY_NOTEBOOK_PATH.exists()


class PricingTests(unittest.TestCase):
    @unittest.skipUnless(
        LEGACY_NOTEBOOK_AVAILABLE,
        f"optional legacy PDE notebook not found: {LEGACY_NOTEBOOK_PATH.name}",
    )
    def test_legacy_pde_price_runs_and_matches_regression(self) -> None:
        snowball = legacy_price(
            method="PDE",
            Type=2,
            margin_rate=1.0,
            S=1.0,
            K=1.0,
            T=1.0,
            R=0.18,
            N=1.0,
            Ll=0.8,
            Lh=1.0,
            r=0.03,
            q=0.0,
            sigma=0.2,
            size=10_000,
            obs_start_day=21,
            obs_in=0,
            day_counter=252,
            _freq_num=21,
            KI_freq="daily",
            KO_freq="monthly",
            RFlag=0,
        )
        standard_fcn = legacy_price(
            method="PDE",
            Type=0,
            margin_rate=1.0,
            S=1.0,
            K=1.0,
            T=1.0,
            R=0.18,
            N=1.0,
            Ll=0.8,
            Lh=1.0,
            r=0.03,
            q=0.0,
            sigma=0.2,
            size=10_000,
            obs_start_day=21,
            obs_in=0,
            day_counter=252,
            _freq_num=21,
            KI_freq="daily",
            KO_freq="monthly",
            RFlag=0,
        )
        self.assertAlmostEqual(snowball, 0.00958504575245537, places=12)
        self.assertAlmostEqual(standard_fcn, 0.029995513261795982, places=12)

    def test_all_new_products_price_with_mc(self) -> None:
        products = [
            make_classic_autocall(),
            make_wide_autocall(),
            make_dividend_autocall(),
            make_butterfly_autocall(),
            make_stepdown_autocall(),
        ]
        for product in products:
            value = price(product, MARKET, method="MC", engine_config=MC_CONFIG)
            self.assertTrue(math.isfinite(value), product.product_name)

    def test_lower_ki_barrier_improves_value(self) -> None:
        higher_ki = make_classic_autocall(knock_in_ratio=0.8)
        lower_ki = make_classic_autocall(knock_in_ratio=0.7)
        higher_ki_value = price(higher_ki, MARKET, method="MC", engine_config=MC_CONFIG)
        lower_ki_value = price(lower_ki, MARKET, method="MC", engine_config=MC_CONFIG)
        self.assertGreaterEqual(lower_ki_value, higher_ki_value)

    def test_lower_coupon_reduces_value(self) -> None:
        rich = make_classic_autocall(knock_out_coupon=0.18)
        cheap = make_classic_autocall(knock_out_coupon=0.1)
        rich_value = price(rich, MARKET, method="MC", engine_config=MC_CONFIG)
        cheap_value = price(cheap, MARKET, method="MC", engine_config=MC_CONFIG)
        self.assertGreaterEqual(rich_value, cheap_value)

    def test_lower_ko_barrier_increases_ko_probability(self) -> None:
        easier = make_classic_autocall(knock_out_ratio=0.95)
        harder = make_classic_autocall(knock_out_ratio=1.03)
        easier_result = price(easier, MARKET, method="MC", engine_config=MC_CONFIG, return_details=True)
        harder_result = price(harder, MARKET, method="MC", engine_config=MC_CONFIG, return_details=True)
        self.assertGreaterEqual(easier_result.knock_out_probability, harder_result.knock_out_probability)

    def test_butterfly_schedule_changes_price(self) -> None:
        butterfly = make_butterfly_autocall(front_coupon=0.22, back_coupon=0.1)
        flat = make_classic_autocall(knock_out_coupon=0.16, maturity_coupon=0.16)
        butterfly_value = price(butterfly, MARKET, method="MC", engine_config=MC_CONFIG)
        flat_value = price(flat, MARKET, method="MC", engine_config=MC_CONFIG)
        self.assertGreater(abs(butterfly_value - flat_value), 1.0e-4)

    @unittest.skipUnless(
        LEGACY_NOTEBOOK_AVAILABLE,
        f"optional legacy PDE notebook not found: {LEGACY_NOTEBOOK_PATH.name}",
    )
    def test_supported_products_run_with_pde_when_expected(self) -> None:
        for product in [
            make_classic_autocall(),
            make_wide_autocall(),
            make_dividend_autocall(),
            make_butterfly_autocall(),
        ]:
            value = price(product, MARKET, method="PDE", engine_config=PDE_CONFIG)
            self.assertTrue(math.isfinite(value), product.product_name)

    def test_stepdown_is_mc_only(self) -> None:
        with self.assertRaises(NotImplementedError):
            price(make_stepdown_autocall(), MARKET, method="PDE", engine_config=PDE_CONFIG)

    def test_mc_greeks_run(self) -> None:
        result = mc_greeks(make_classic_autocall(), MARKET, MC_CONFIG)
        self.assertEqual(set(result), {"price", "delta", "gamma", "vega", "theta"})
        self.assertTrue(all(math.isfinite(value) for value in result.values()))


if __name__ == "__main__":
    unittest.main()
