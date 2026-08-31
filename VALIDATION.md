# Numerical Validation

## Test strategy

The suite starts with deterministic, hand-calculated paths for every payoff
branch: early autocall, knock-in then autocall, knock-in loss, recovery,
no-event maturity, exact barrier touches, same-day priority, fixed coupons,
discount entry, and worst-of aggregation.

Monte Carlo tests cover fixed-seed reproducibility, batch-size invariance,
antithetic handling, the zero-volatility limit, confidence intervals, standard
error behavior, and the rule that knock-in cannot occur after redemption.

PDE tests cover the deterministic limit, spot-grid refinement, all supported
single-asset schedule variants, and explicit rejection of multi-asset products.
Cross-engine acceptance uses
`abs(MC - PDE) <= max(4 * MC standard error, 0.002 * notional)`.

This tolerance combines simulation uncertainty with finite-difference
discretization and replaces brittle equality at twelve decimal places.

## Reference comparison

For `configs/classic_snowball.json` with 20,000 antithetic paths and a
401-point PDE grid:

| Method | Present value | Standard error / interval |
| --- | ---: | --- |
| Monte Carlo | 1000.693524 | SE 0.703762; 95% CI [999.314176, 1002.072872] |
| PDE | 1000.487825 | Not applicable |

The absolute difference is 0.205699 on a 1,000 notional and the PDE value lies
inside the MC confidence interval. These values are regression references with
documented tolerances, not exact-equality requirements.

## Reproducibility

- MC innovations use NumPy Philox streams keyed by seed and relative day.
- Processing batch size does not change the generated innovations.
- Fair-coupon trials and Greeks restart the same stream.
- JSON output rejects NaN and NumPy-only scalar types.

## Known limitations

- Flat Black-Scholes market inputs only.
- Daily-close monitoring; no intraday bridge correction.
- No local/stochastic volatility, rate curves, discrete dividends, credit risk,
  business-day calendars, or physical-settlement inventory accounting.
- PDE supports one underlying only. Worst-of products are Monte Carlo only.
