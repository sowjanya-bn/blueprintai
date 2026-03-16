from __future__ import annotations

from typing import Dict, Any, List
from utils.loaders import load_brand, normalize_component_name


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

    approved_lookup = {
        normalize_component_name(name): name for name in brand.get("approved_components", [])
    }
    restricted_lookup = {
        normalize_component_name(name): name for name in brand.get("restricted_components", [])
    }

    component_sources: Dict[str, Dict[str, Any]] = {}

    for variant in blueprint.get("variants", []):
        for comp in variant.get("components", []):
            name = comp.get("component_name")
            normalized = normalize_component_name(name)
            if not normalized:
                continue
            component_sources.setdefault(normalized, {"display": name, "sources": set()})["sources"].add("variant")

    for page_blueprint in blueprint.get("page_blueprints", []):
        for section in page_blueprint.get("sections", []):
            name = section.get("component")
            normalized = normalize_component_name(name)
            if not normalized:
                continue
            component_sources.setdefault(normalized, {"display": name, "sources": set()})["sources"].add("page_blueprint")

    for composition in blueprint.get("component_compositions", []):
        for item in composition.get("components", []):
            name = item.get("component")
            normalized = normalize_component_name(name)
            if not normalized:
                continue
            component_sources.setdefault(normalized, {"display": name, "sources": set()})["sources"].add("component_composition")

    for normalized_name, source_info in component_sources.items():
        display_name = source_info.get("display") or normalized_name
        source_list = sorted(source_info.get("sources", []))

        if normalized_name in restricted_lookup:
            issues.append({
                "status": "FAIL",
                "category": "Brand",
                "title": f"Restricted component used: {display_name}",
                "description": f"Component {display_name} is listed as restricted for brand {brand_id}.",
                "rule_triggered": "brand.restricted_component",
                "evidence": f"Detected in artefacts: {', '.join(source_list)}. Brand restricted list includes {restricted_lookup[normalized_name]}.",
                "severity": "high",
                "suggested_fix": f"Replace {display_name} with an approved alternative from {brand_id}.",
                "human_review_required": True,
            })
        elif approved_lookup and normalized_name not in approved_lookup:
            issues.append({
                "status": "WARN",
                "category": "Brand",
                "title": f"Unapproved component used: {display_name}",
                "description": f"Component {display_name} is not listed as approved for brand {brand_id}.",
                "rule_triggered": "brand.approved_components",
                "evidence": f"Detected in artefacts: {', '.join(source_list)}. Brand approved list: {sorted(approved_lookup.values())}",
                "severity": "medium",
                "suggested_fix": f"Consider using an approved component or obtain brand approval for {display_name}.",
                "human_review_required": True,
            })

    passed = len([i for i in issues if i.get("status") == "FAIL"]) == 0
    return {"issues": issues, "passed": passed}
