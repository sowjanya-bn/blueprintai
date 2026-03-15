from __future__ import annotations

from typing import Dict, Any, List

from utils.loaders import load_composition_rules, normalize_component_name


def run_composition_validator(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    rules_data = load_composition_rules()
    rules = rules_data.get("rules", [])
    rule_meta = {rule.get("id"): rule for rule in rules}

    requirements = blueprint.get("requirements", {}) or {}
    brand_id = (requirements.get("brand") or "").lower()
    content_type = normalize_component_name(requirements.get("content_type") or "")
    brief_text = " ".join([
        str(requirements.get("audience") or ""),
        str(requirements.get("market") or ""),
        content_type,
    ]).lower()

    contextual_components = {
        "hero",
        "featuregrid",
        "faq",
        "safetyaccordion",
    }

    # ── Per-composition ordering / dependency checks ─────────────────────────
    for composition in blueprint.get("component_compositions", []):
        items = composition.get("components", [])
        if not items:
            continue

        route = composition.get("route", "unknown")
        variant_name = composition.get("variant_name", "Unknown Variant")
        component_ids = {item.get("component_id"): item for item in items if item.get("component_id")}
        normalized_names = [normalize_component_name(item.get("component", "")) for item in items]
        normalized_set = set(normalized_names)

        # Hero-first
        if "hero" in normalized_set and normalized_names[0] != "hero":
            rule = rule_meta.get("composition.hero_first", {})
            issues.append({
                "status": "FAIL",
                "category": "Composition",
                "title": f"Hero does not lead composition for {variant_name}",
                "description": rule.get("description"),
                "rule_triggered": rule.get("id", "composition.hero_first"),
                "evidence": f"Route {route} starts with {items[0].get('component')} instead of Hero.",
                "severity": rule.get("severity", "medium"),
                "suggested_fix": "Move Hero to the first section or remove it from the composition if not needed.",
                "human_review_required": True,
            })

        # Disclaimer Footer last
        if "disclaimerfooter" in normalized_set and normalized_names[-1] != "disclaimerfooter":
            rule = rule_meta.get("composition.disclaimer_last", {})
            issues.append({
                "status": "FAIL",
                "category": "Composition",
                "title": f"Disclaimer Footer is not last in {variant_name}",
                "description": rule.get("description"),
                "rule_triggered": rule.get("id", "composition.disclaimer_last"),
                "evidence": f"Route {route} ends with {items[-1].get('component')} instead of Disclaimer Footer.",
                "severity": rule.get("severity", "high"),
                "suggested_fix": "Move Disclaimer Footer to the final section of the composition.",
                "human_review_required": True,
            })

        # Signup after context
        for idx, item in enumerate(items):
            normalized_name = normalize_component_name(item.get("component", ""))
            if normalized_name == "signupform":
                if idx == 0 or normalize_component_name(items[idx - 1].get("component", "")) not in contextual_components:
                    rule = rule_meta.get("composition.signup_after_context", {})
                    issues.append({
                        "status": "FAIL",
                        "category": "Composition",
                        "title": f"SignupForm lacks contextual lead-in for {variant_name}",
                        "description": rule.get("description"),
                        "rule_triggered": rule.get("id", "composition.signup_after_context"),
                        "evidence": f"SignupForm appears at position {item.get('position')} on route {route}.",
                        "severity": rule.get("severity", "medium"),
                        "suggested_fix": "Place Hero, FAQ, FeatureGrid, or Safety Accordion before SignupForm.",
                        "human_review_required": True,
                    })

            # Backward-only dependencies
            current_position = int(item.get("position", idx + 1))
            for dependency in item.get("depends_on", []):
                target = component_ids.get(dependency)
                rule = rule_meta.get("composition.dependencies_backward_only", {})
                if not target:
                    issues.append({
                        "status": "FAIL",
                        "category": "Composition",
                        "title": f"Missing dependency target for {item.get('component')}",
                        "description": rule.get("description"),
                        "rule_triggered": rule.get("id", "composition.dependencies_backward_only"),
                        "evidence": f"Dependency {dependency} was not found in composition for route {route}.",
                        "severity": rule.get("severity", "high"),
                        "suggested_fix": "Update dependency references to valid preceding component ids.",
                        "human_review_required": True,
                    })
                    continue

                target_position = int(target.get("position", 0))
                if target_position >= current_position:
                    issues.append({
                        "status": "FAIL",
                        "category": "Composition",
                        "title": f"Forward dependency detected in {variant_name}",
                        "description": rule.get("description"),
                        "rule_triggered": rule.get("id", "composition.dependencies_backward_only"),
                        "evidence": (
                            f"{item.get('component')} depends on {target.get('component')} "
                            f"at position {target_position}, which is not earlier than position {current_position}."
                        ),
                        "severity": rule.get("severity", "high"),
                        "suggested_fix": "Ensure dependencies reference only earlier components in the composition order.",
                        "human_review_required": True,
                    })

    # ── Global blueprint-level checks (pairing, required sections, brand) ────
    all_compositions = blueprint.get("component_compositions", [])
    # Collect all normalized component names across all compositions (deduplicated).
    all_component_names: set[str] = set()
    for composition in all_compositions:
        for item in composition.get("components", []):
            n = normalize_component_name(item.get("component", ""))
            if n:
                all_component_names.add(n)

    # Pairing rules
    for pairing_rule in rules_data.get("pairing_rules", []):
        trigger = normalize_component_name(pairing_rule.get("trigger_component", ""))
        must_coexist = [normalize_component_name(c) for c in pairing_rule.get("must_coexist_with", [])]
        if trigger in all_component_names and not any(m in all_component_names for m in must_coexist):
            issues.append({
                "status": "FAIL",
                "category": "Composition",
                "title": pairing_rule.get("title"),
                "description": pairing_rule.get("description"),
                "rule_triggered": pairing_rule.get("id"),
                "evidence": (
                    f"'{trigger}' is present but none of {must_coexist} were found across all compositions."
                ),
                "severity": pairing_rule.get("severity", "medium"),
                "suggested_fix": (
                    f"Add at least one of [{', '.join(pairing_rule.get('must_coexist_with', []))}] "
                    f"to accompany {pairing_rule.get('trigger_component')}."
                ),
                "human_review_required": True,
            })

    # Required-section rules
    for req_rule in rules_data.get("required_section_rules", []):
        required = normalize_component_name(req_rule.get("required_component", ""))

        # Page-type check
        page_types = [normalize_component_name(pt) for pt in req_rule.get("page_types", [])]
        if page_types and content_type in page_types and required not in all_component_names:
            issues.append({
                "status": "FAIL",
                "category": "Composition",
                "title": req_rule.get("title"),
                "description": req_rule.get("description"),
                "rule_triggered": req_rule.get("id"),
                "evidence": (
                    f"Page type '{content_type}' matched rule but '{required}' was not found in compositions."
                ),
                "severity": req_rule.get("severity", "medium"),
                "suggested_fix": f"Add a {req_rule.get('required_component')} section to the composition.",
                "human_review_required": True,
            })

        # Industry keyword check (uses brief_text proxy from requirements)
        industries = [ind.lower() for ind in req_rule.get("industries", [])]
        if industries and any(ind in brief_text for ind in industries) and required not in all_component_names:
            issues.append({
                "status": "FAIL",
                "category": "Composition",
                "title": req_rule.get("title"),
                "description": req_rule.get("description"),
                "rule_triggered": req_rule.get("id"),
                "evidence": (
                    f"Industry context '{brief_text.strip()}' matched rule "
                    f"but '{required}' was not found in compositions."
                ),
                "severity": req_rule.get("severity", "medium"),
                "suggested_fix": f"Add a {req_rule.get('required_component')} section to the composition.",
                "human_review_required": True,
            })

    # Brand policy rules
    for brand_policy in rules_data.get("brand_policies", []):
        if normalize_component_name(brand_policy.get("brand_id", "")) != normalize_component_name(brand_id):
            continue
        trigger = normalize_component_name(brand_policy.get("trigger_component", ""))
        required = normalize_component_name(brand_policy.get("required_component", ""))
        if trigger in all_component_names and required not in all_component_names:
            issues.append({
                "status": "FAIL",
                "category": "Composition",
                "title": brand_policy.get("title"),
                "description": brand_policy.get("description"),
                "rule_triggered": brand_policy.get("id"),
                "evidence": (
                    f"Brand '{brand_id}' policy: '{trigger}' present "
                    f"but required companion '{required}' is missing."
                ),
                "severity": brand_policy.get("severity", "high"),
                "suggested_fix": (
                    f"Add {brand_policy.get('required_component')} to satisfy the "
                    f"{brand_policy.get('brand_id')} brand composition policy."
                ),
                "human_review_required": True,
            })

    passed = not any(issue.get("status") == "FAIL" for issue in issues)
    return {"issues": issues, "passed": passed}
