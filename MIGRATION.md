# Structured Products Refactor Notes

## What changed

- Legacy notebook pricing is now frozen behind `structured_products.legacy_adapter`.
- New autocall products use a unified `AutocallProduct` dataclass plus helper builders.
- Monte Carlo pricing now goes through one state-machine-style path pricer in `autocall_engine_mc.py`.
- PDE support is preserved for legacy FCN / Snowball and extended only where the mapping is clean.

## Legacy compatibility

The following legacy entry points are preserved through wrappers:

- `legacy_price(...)`
- `legacy_coupon_search(...)`
- `legacy_greeks_compute(...)`
- `legacy_public_entry_points()["greeks_fcn_snowball"]`

These wrappers execute the copied notebook source, excluding the demo call at the bottom.

## Product support in this version

- MC: `classic_autocall`, `wide_autocall`, `dividend_autocall`, `butterfly_autocall`, `stepdown_autocall`
- PDE: `classic_autocall`, `wide_autocall`, `dividend_autocall`, `butterfly_autocall`
- MC-only: `stepdown_autocall`

## Pricing convention


- returned principal is not included in the product value
- coupon legs are priced as net coupon cashflows
- KI with no KO uses downside loss only, consistent with Snowball-style net payoff logic


