# Structured Products Pricer

[![Tests](https://github.com/carrey325/Autocall-Snowball-FCN-pricing/actions/workflows/tests.yml/badge.svg)](https://github.com/carrey325/Autocall-Snowball-FCN-pricing/actions/workflows/tests.yml)

A lightweight Python pricing framework for Snowball, FCN, and autocallable
structured products.

The project focuses on practical product comparison: a unified product
interface, a reusable Monte Carlo engine, legacy PDE compatibility hooks, and
regression tests for core payoff behavior.

## What this repo demonstrates

- Unified product specifications through `AutocallProduct` and builder helpers.
- Monte Carlo pricing for classic, wide, dividend, butterfly, and step-down
  autocall structures.
- Optional PDE adapter for legacy notebook-based pricing blocks.
- Basic Greeks through repeated Monte Carlo repricing.
- Tests for finite prices, product monotonicity, MC-only structures, and legacy
  PDE regressions when the optional notebook dependency is present.

## Product and engine support

| Product | Monte Carlo | PDE adapter |
|---|---:|---:|
| Snowball / legacy FCN | Via legacy wrapper | Optional legacy notebook |
| Classic autocall | Yes | Optional legacy notebook |
| Wide autocall | Yes | Optional legacy notebook |
| Dividend autocall | Yes | Optional legacy notebook |
| Butterfly autocall | Yes | Optional legacy notebook |
| Step-down autocall | Yes | No |

The Monte Carlo engine is self-contained. PDE support is preserved through a
legacy notebook adapter and is available only when the expected legacy notebook
source is supplied locally.

## Quick start

```bash
git clone https://github.com/carrey325/Autocall-Snowball-FCN-pricing.git
cd Autocall-Snowball-FCN-pricing

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

python -m unittest discover -s tests -v
```

If you only need the runtime dependency without editable installation:

```bash
python -m pip install -r requirements.txt
```

## Basic usage

```python
from structured_products import (
    EngineConfig,
    MarketData,
    make_classic_autocall,
    mc_greeks,
    price,
)

market = MarketData(rate=0.03, dividend_yield=0.0, volatility=0.20)
product = make_classic_autocall(
    s0=1.0,
    maturity=1.0,
    knock_in_ratio=0.80,
    knock_out_ratio=1.00,
    knock_out_coupon=0.18,
)
engine = EngineConfig(n_paths=20_000, day_counter=252, steps_per_day=2, seed=7)

value = price(product, market, method="MC", engine_config=engine)
details = price(product, market, method="MC", engine_config=engine, return_details=True)
greeks = mc_greeks(product, market, engine)
```

`details` contains the price, knock-in probability, knock-out probability,
average knock-out time, and average coupon rate.

## Product overview

### Snowball

A structured product with knock-in and knock-out features, designed for
range-bound market views with enhanced coupon potential.

### FCN

A fixed coupon note that offers coupon income under predefined barrier
conditions.

### Classic autocall

A standard autocallable structure with fixed knock-in barrier, fixed knock-out
barrier, and fixed coupon.

### Wide autocall

A more defensive version of the classic autocall, usually with a lower knock-in
barrier, a wider payoff range, and a lower coupon.

### Dividend autocall

An autocall structure with two coupon outcomes: a higher coupon if the product
knocks out early, and a lower maturity coupon if it survives without knock-in
and knock-out.

### Butterfly autocall

An autocall structure with a time-varying coupon schedule, typically offering
higher coupons for earlier redemption and lower coupons later.

### Step-down autocall

An autocall structure with a knock-out barrier that decreases over time, making
redemption easier in later observation periods.

## Pricing framework

All autocall products are handled through a common event-driven framework based
on:

- knock-in monitoring
- knock-out observation
- coupon schedule evaluation
- maturity payoff handling

Monte Carlo is the primary pricing method for the full autocall family. The PDE
adapter is intentionally narrower and is used only for products whose payoff can
be mapped cleanly to the preserved legacy blocks.

## Model assumptions and conventions

- Flat risk-free rate, dividend yield, and volatility through `MarketData`.
- Geometric Brownian motion path simulation for Monte Carlo pricing.
- Daily knock-in monitoring by default.
- Monthly knock-out observation days generated from a 252 trading-day year.
- Returned principal is not included in the quoted product value.
- Coupon legs are priced as net coupon cash flows.
- Knock-in with no knock-out uses downside loss only, consistent with
  Snowball-style net payoff logic.

## Validation

The test suite currently covers:

- all self-contained Monte Carlo product builders
- monotonicity for knock-in barrier, knock-out barrier, and coupon changes
- finite MC Greeks under a fixed seed
- step-down autocall as MC-only
- legacy PDE regression values when the optional legacy notebook is present

Run:

```bash
python -m unittest discover -s tests -v
```

## Repository layout

```text
.
├── structured_products/       # Pricing package
│   ├── products.py            # Product dataclass and builders
│   ├── market.py              # MarketData and EngineConfig
│   ├── autocall_engine_mc.py   # Self-contained Monte Carlo engine
│   ├── autocall_engine_pde.py  # Legacy PDE adapter
│   ├── greeks.py              # MC Greek calculations
│   └── pricing.py             # Top-level price dispatcher
├── tests/                     # Unit tests
├── Pricer.ipynb               # Demo notebook
├── MIGRATION.md               # Refactor notes
└── pyproject.toml             # Install and dependency metadata
```

## Roadmap

- Add self-contained PDE implementations that do not depend on the legacy
  notebook source.
- Add small reproducible examples for sensitivity analysis and product
  comparison.
- Extend validation with convergence checks for path count, time step, and PDE
  grid size.
- Add calibration utilities for market volatility and dividend assumptions.

## Disclaimer

This repository is for research and educational use. It is not investment
advice, a production risk system, or a substitute for independent model
validation.
