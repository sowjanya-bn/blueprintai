from __future__ import annotations

from typing import Dict, Any, List
from utils.loaders import load_design_system, load_accessibility_rules, normalize_component_name


def run_accessibility_validator(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    design = load_design_system()
    acc_rules = load_accessibility_rules().get("rules", [])

    def find_design_component(name: str):
        normalized = normalize_component_name(name)
        for component in design.get("components", []):
            if normalize_component_name(component.get("name", "")) == normalized:
                return component
        return None

    def get_accessibility_notes(component_name: str) -> List[str]:
        design_comp = find_design_component(component_name)
        return list((design_comp or {}).get("accessibility_notes", []))

    variants = blueprint.get("variants", [])
    page_blueprints = blueprint.get("page_blueprints", [])

    components_checked = set()

    for variant in variants:
        for comp in variant.get("components", []):
            cname = comp.get("component_name")
            normalized_name = normalize_component_name(cname)
            if not cname or normalized_name in components_checked:
                continue
            components_checked.add(normalized_name)

            notes = get_accessibility_notes(cname)
            if not notes:
                issues.append({
                    "status": "FAIL",
                    "category": "Accessibility",
                    "title": f"Missing accessibility guidance for {cname}",
                    "description": f"Design system has no accessibility notes for component {cname}.",
                    "rule_triggered": "a11y.missing_guidance",
                    "evidence": f"Component {cname} lacks accessibility notes in design_system.json",
                    "severity": "medium",
                    "suggested_fix": "Add clear accessibility guidance to the design system entry for this component (labels, roles, contrast, keyboard support).",
                    "human_review_required": True,
                })

            if normalized_name == "signupform":
                rule_present = any(rule.get("id") == "a11y.form_labels" for rule in acc_rules)
                has_label_note = any("label" in (note or "").lower() for note in notes)
                if rule_present and not has_label_note:
                    issues.append({
                        "status": "FAIL",
                        "category": "Accessibility",
                        "title": "SignupForm missing form label guidance",
                        "description": "Forms must have explicit, associated labels for inputs to meet accessibility guidelines.",
                        "rule_triggered": "a11y.form_labels",
                        "evidence": comp.get("content_summary", ""),
                        "severity": "high",
                        "suggested_fix": "Ensure all inputs in SignupForm have associated labels and aria descriptors.",
                        "human_review_required": True,
                    })

    for page_blueprint in page_blueprints:
        for section in page_blueprint.get("sections", []):
            component_name = section.get("component")
            normalized_name = normalize_component_name(component_name)
            section_notes = section.get("accessibility_notes", [])
            content_slots = section.get("content_slots", [])

            if not section_notes:
                issues.append({
                    "status": "FAIL",
                    "category": "Accessibility",
                    "title": f"Page blueprint section missing accessibility notes: {component_name}",
                    "description": "Generated page blueprints should carry explicit accessibility implementation notes for each section.",
                    "rule_triggered": "a11y.page_blueprint_notes",
                    "evidence": f"Variant {page_blueprint.get('variant_name')} section {section.get('section_id')} has no accessibility notes.",
                    "severity": "medium",
                    "suggested_fix": "Propagate accessibility notes from the design system into each generated page blueprint section.",
                    "human_review_required": True,
                })

            if normalized_name == "hero" and "headline" not in content_slots:
                issues.append({
                    "status": "FAIL",
                    "category": "Accessibility",
                    "title": "Hero section missing headline slot",
                    "description": "Primary entry sections should expose a headline slot to support proper heading structure.",
                    "rule_triggered": "a11y.heading_structure",
                    "evidence": f"Variant {page_blueprint.get('variant_name')} hero section slots: {content_slots}",
                    "severity": "medium",
                    "suggested_fix": "Add a headline content slot for Hero sections and map it to a semantic heading element.",
                    "human_review_required": True,
                })

            if normalized_name == "signupform":
                has_fields = "fields" in content_slots
                has_consent = any("consent" in slot.lower() for slot in content_slots)
                if not has_fields or not has_consent:
                    issues.append({
                        "status": "FAIL",
                        "category": "Accessibility",
                        "title": "SignupForm blueprint missing accessible form slots",
                        "description": "Generated form blueprints should include explicit fields and consent-related slots for accessible implementation.",
                        "rule_triggered": "a11y.form_labels",
                        "evidence": f"Variant {page_blueprint.get('variant_name')} signup slots: {content_slots}",
                        "severity": "high",
                        "suggested_fix": "Include fields and consent-related content slots so labels, help text, and consent copy are implemented accessibly.",
                        "human_review_required": True,
                    })

    passed = len(issues) == 0
    return {"issues": issues, "passed": passed}
