# Structured Products Pricer

A clean-room Python framework for Snowballs, autocallable notes, fixed coupon
notes (FCNs), and multi-asset worst-of structures.

The package combines a reproducible batched Monte Carlo engine with an
independent one-dimensional Crank-Nicolson PDE benchmark. It also provides
fair-coupon solving, bump-and-revalue Greeks, strict JSON configuration, and a
command-line workflow.

## Features

| Product | Monte Carlo | PDE |
| --- | ---: | ---: |
| Classic/Wide/Butterfly/Dividend Snowball | Yes | Yes |
| Step-down Snowball | Yes | Yes |
| Standard/Discount-entry FCN | Yes | Yes |
| Worst-of Snowball/FCN | Yes | Explicitly unsupported |

- Immutable, composable product features and schedules.
- Total present value and net value relative to issue price.
- MC standard error, confidence interval, KI/KO probabilities, and expected life.
- Per-underlying Delta, Gamma, and Vega, plus Theta, Rho, and correlation risk.
- Runtime dependencies limited to NumPy, SciPy, and the Python standard library.

## Installation

~~~bash
python -m pip install -e ".[dev]"
~~~

Python 3.10 through 3.13 is supported.

## Command line

Price and calculate Greeks:

~~~bash
python main.py run --config configs/classic_snowball.json --method mc
~~~

Other workflows:

~~~bash
python main.py price --config configs/standard_fcn.json --method pde
python main.py greeks --config configs/classic_snowball.json --method mc
python main.py fair-coupon --config configs/classic_snowball.json --method pde \
  --target-pv 1000 --lower 0.01 --upper 0.40
python main.py compare --config configs/classic_snowball.json
~~~

Every command prints deterministic JSON and accepts `--output` to write the same
payload to a file. Common numerical controls can be overridden with `--paths`,
`--seed`, and `--grid-size`.

## Python API

~~~python
from structured_products import MCConfig, MarketData, make_classic_snowball, price

product = make_classic_snowball()
market = MarketData(
    spots=(100.0,),
    rate=0.03,
    dividend_yields=(0.0,),
    volatilities=(0.2,),
)
result = price(product, market, "mc", MCConfig(n_paths=20_000, seed=7))
print(result.to_dict())
~~~

The public calculation functions are `price`, `calculate_greeks`, and
`solve_fair_coupon`. Low-level random generators and PDE matrices are internal.

## Model conventions

- Risk-neutral geometric Brownian motion with flat continuously compounded
  rates, dividends, and volatilities.
- Integer trading-day schedules with ACT/252 year fractions by default.
- Daily-close knock-in monitoring.
- Same-day event priority: knock-out, knock-in, periodic coupon, maturity.
- Worst-of performance is the minimum current/reference ratio.
- Returned results include principal; net value is PV minus issue price.

See [MODEL_SPEC.md](MODEL_SPEC.md) for contract rules and
[VALIDATION.md](VALIDATION.md) for numerical tests and limitations.

## Clean-room statement

The runtime is self-contained. It does not load notebooks, dynamically execute
external source, or depend on any legacy pricing adapter.
