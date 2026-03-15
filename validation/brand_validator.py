from __future__ import annotations

from typing import Dict, Any, List
from utils.loaders import load_brand


def run_brand_validator(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    req = blueprint.get("requirements", {})
    brand_id = req.get("brand")

    if not brand_id:
        return {"issues": issues, "passed": True}

    try:
        brand = load_brand(brand_id)
    except Exception:
        brand = {}

    approved = set(brand.get("approved_components", []))
    restricted = set(brand.get("restricted_components", []))

    # Check variants/components against brand rules
    for v in blueprint.get("variants", []):
        for comp in v.get("components", []):
            name = comp.get("component_name")
            if not name:
                continue

            if name in restricted:
                issues.append({
                    "status": "FAIL",
                    "category": "Brand",
                    "title": f"Restricted component used: {name}",
                    "description": f"Component {name} is listed as restricted for brand {brand_id}.",
                    "rule_triggered": "brand.restricted_component",
                    "evidence": f"Brand restricted list includes {name}",
                    "severity": "high",
                    "suggested_fix": f"Replace {name} with an approved alternative from {brand_id}.",
                    "human_review_required": True,
                })
            elif approved and name not in approved:
                # components used but not explicitly approved — warn
                issues.append({
                    "status": "WARN",
                    "category": "Brand",
                    "title": f"Unapproved component used: {name}",
                    "description": f"Component {name} is not listed as approved for brand {brand_id}.",
                    "rule_triggered": "brand.approved_components",
                    "evidence": f"Brand approved list: {sorted(list(approved))}",
                    "severity": "medium",
                    "suggested_fix": f"Consider using an approved component or obtain brand approval for {name}.",
                    "human_review_required": True,
                })

    passed = len([i for i in issues if i.get("status") == "FAIL"]) == 0
    return {"issues": issues, "passed": passed}
