# Contributing

Thanks for contributing. Changes must preserve the clean-room boundary, the
composable product model, and reproducible numerical behavior.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run tests

```bash
python -m coverage run -m pytest
python -m coverage report
```

## Contribution guidelines

- Never add or execute legacy notebooks or employer-specific source.
- Express marketing variants with feature and schedule data, not new engines.
- Add hand-calculated payoff tests before extending a numerical engine.
- Use common random numbers for Monte Carlo comparisons.
- Document and justify numerical tolerances in `VALIDATION.md`.
- Do not commit generated files such as `__pycache__`, `.DS_Store`, build
  outputs, or notebook checkpoints.
