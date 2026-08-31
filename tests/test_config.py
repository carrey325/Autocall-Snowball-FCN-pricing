from __future__ import annotations

import json
from pathlib import Path

import pytest

from structured_products.config import load_config


def test_all_example_configs_parse_and_serialize() -> None:
    for path in sorted(Path("configs").glob("*.json")):
        resolved = load_config(path)
        json.dumps(resolved.to_dict(), allow_nan=False)


def test_unknown_top_level_field_is_rejected(tmp_path: Path) -> None:
    payload = json.loads(Path("configs/classic_snowball.json").read_text())
    payload["typo"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="top-level"):
        load_config(path)


def test_unknown_product_parameter_is_rejected(tmp_path: Path) -> None:
    payload = json.loads(Path("configs/classic_snowball.json").read_text())
    payload["product"]["parameters"]["couopn_rate"] = 0.2
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="product parameters"):
        load_config(path)
