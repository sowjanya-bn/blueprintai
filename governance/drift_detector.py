from __future__ import annotations

from typing import Dict, Any, List
from utils.loaders import load_brand, load_design_system


def detect_governance_drift(blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    req = blueprint.get("requirements", {})
    brand_id = req.get("brand")

    # gather used components
    used = set()
    for v in blueprint.get("variants", []):
        for c in v.get("components", []):
            name = c.get("component_name")
            if name:
                used.add(name)

    # load design system and brand
    try:
        design = load_design_system()
    except Exception:
        design = {"components": []}

    design_names = {c.get("name") for c in design.get("components", [])}

    brand = {}
    try:
        if brand_id:
            brand = load_brand(brand_id)
    except Exception:
        brand = {}

    approved = set(brand.get("approved_components", []))
    restricted = set(brand.get("restricted_components", []))
    deprecated = set(brand.get("deprecated_components", [])) if brand.get("deprecated_components") else set()

    for name in sorted(used):
        if name in restricted:
            issues.append({
                "title": f"Restricted component used: {name}",
                "description": f"{name} is listed as restricted for brand {brand_id} and should not be used.",
                "affected_component": name,
                "recommendation": f"Replace {name} with an approved component from the brand or consult governance to waive.",
            })
            continue

        if deprecated and name in deprecated:
            issues.append({
                "title": f"Deprecated component used: {name}",
                "description": f"{name} is deprecated by the design system and may be removed in future releases.",
                "affected_component": name,
                "recommendation": f"Migrate to the recommended replacement component from the design system.",
            })

        if approved and name not in approved:
            issues.append({
                "title": f"Unapproved component used: {name}",
                "description": f"Component {name} is not explicitly approved for brand {brand_id}.",
                "affected_component": name,
                "recommendation": f"Request approval for {name} or substitute with an approved component.",
            })

        if name not in design_names:
            issues.append({
                "title": f"Off-system component detected: {name}",
                "description": f"Component {name} is not present in the canonical design system documentation.",
                "affected_component": name,
                "recommendation": "Add the component to the design system or replace it with an approved component.",
            })

    # token drift check: examine page_spec props for tokens not in brand tokens
    tokens_used = set()
    for block in blueprint.get("page_specification", {}).get("layout", []):
        props = block.get("props", {}) or {}
        for v in props.values():
            if isinstance(v, str) and v.startswith("token:"):
                tokens_used.add(v.split(":",1)[1])

    brand_tokens = set()
    for tt, vals in (brand.get("tokens", {}) or {}).items():
        brand_tokens.update(vals.keys() if isinstance(vals, dict) else [])

    for t in tokens_used:
        if t not in brand_tokens:
            issues.append({
                "title": f"Design token drift: {t}",
                "description": f"Token {t} used in page props but not defined in brand tokens for {brand_id}.",
                "affected_component": None,
                "recommendation": "Align tokens to brand tokens or update brand token definitions.",
            })

    return issues
