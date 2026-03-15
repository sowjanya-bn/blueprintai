from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import re


ROOT = Path(__file__).resolve().parents[1]


def _read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_design_system() -> dict:
    p = ROOT / "knowledge" / "design_system.json"
    return _read_json(p)


def load_accessibility_rules() -> dict:
    p = ROOT / "knowledge" / "accessibility_rules.json"
    return _read_json(p)


def load_compliance_rules() -> dict:
    p = ROOT / "knowledge" / "compliance_rules.json"
    return _read_json(p)


def load_brand(brand_name: str) -> dict:
    # brand files are named like brand_{brand_name}.json
    p = ROOT / "knowledge" / "brands" / f"brand_{brand_name}.json"
    return _read_json(p)


def load_market(market_name: str) -> dict:
    # market files are named like market_{market_name}.json
    p = ROOT / "knowledge" / "markets" / f"market_{market_name}.json"
    return _read_json(p)


def make_component_id(name: str) -> str:
    """Create a stable component id from a component name.

    Returns a string like `component::hero`.
    """
    if not name:
        return "component::unknown"
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"component::{slug}"
