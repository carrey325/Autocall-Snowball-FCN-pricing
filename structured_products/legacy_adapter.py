"""Compatibility layer that freezes the legacy notebook entry points."""

from __future__ import annotations

from functools import lru_cache
import json
import os
from pathlib import Path
from typing import Any


LEGACY_NOTEBOOK_NAME = "雪球fcn.ipynb"


def default_legacy_notebook_path() -> Path:
    return Path(__file__).resolve().parent.parent / LEGACY_NOTEBOOK_NAME


def _clean_legacy_source(source: str) -> str:
    for marker in (
        "s = 3808  # underlying asset price",
        "call_price = bs_option_price(",
        "## 报价函数",
        "# ## 算greek函数",
    ):
        if marker in source:
            source = source.split(marker)[0]
            break
    # Drop the example invocations at the bottom of the notebook.
    return source


def _load_legacy_source(notebook_path: Path) -> str:
    if not notebook_path.exists():
        raise FileNotFoundError(
            f"Legacy notebook not found at {notebook_path}. "
            "Pass notebook_path=... to a legacy wrapper, or place the legacy "
            "notebook at the default path."
        )
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    parts: list[str] = []
    for cell in payload["cells"]:
        if cell.get("cell_type") != "code":
            continue
        parts.append(_clean_legacy_source("".join(cell.get("source", []))))
    return "\n\n".join(parts)


@lru_cache(maxsize=None)
def load_legacy_namespace(notebook_path: str | None = None) -> dict[str, Any]:
    path = Path(notebook_path) if notebook_path else default_legacy_notebook_path()
    mpl_dir = path.parent / ".mplconfig"
    mpl_dir.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir))
    namespace: dict[str, Any] = {"__name__": "legacy_notebook_namespace"}
    source = _load_legacy_source(path)
    exec(compile(source, str(path), "exec"), namespace)
    return namespace


def legacy_public_entry_points(notebook_path: str | None = None) -> dict[str, Any]:
    namespace = load_legacy_namespace(notebook_path)
    return {
        "payoff": namespace["payoff"],
        "coupon_search": namespace["coupon_search"],
        "greeks_compute": namespace["greeks_compute"],
        "greeks_fcn_snowball": namespace["greeks_fcn_snowball"],
    }


def legacy_price(*args: Any, notebook_path: str | None = None, **kwargs: Any) -> Any:
    return load_legacy_namespace(notebook_path)["payoff"](*args, **kwargs)


def legacy_coupon_search(*args: Any, notebook_path: str | None = None, **kwargs: Any) -> Any:
    return load_legacy_namespace(notebook_path)["coupon_search"](*args, **kwargs)


def legacy_greeks_compute(*args: Any, notebook_path: str | None = None, **kwargs: Any) -> Any:
    return load_legacy_namespace(notebook_path)["greeks_compute"](*args, **kwargs)
