# Contributing

Thanks for taking a look at this project. The repository is intentionally small,
so changes should keep the pricing API easy to inspect and reproduce.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run tests

```bash
python -m unittest discover -s tests -v
```

Monte Carlo tests are self-contained. PDE regression tests run only when the
optional legacy notebook expected by `structured_products.legacy_adapter` is
available at the default path.

## Contribution guidelines

- Keep product builders and pricing engines explicit rather than hiding payoff
  behavior behind broad configuration dictionaries.
- Add tests for new product variants, especially monotonicity checks and finite
  price checks under fixed random seeds.
- Document pricing conventions whenever a change affects coupons, redemption,
  knock-in/knock-out monitoring, or returned principal.
- Do not commit generated files such as `__pycache__`, `.DS_Store`, build
  outputs, or notebook checkpoints.
