from __future__ import annotations

from typing import Dict, Any, List
from utils.loaders import load_design_system, load_accessibility_rules


def run_accessibility_validator(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    design = load_design_system()
    acc_rules = load_accessibility_rules().get("rules", [])

    # helper: find design entry
    def find_design_component(name: str):
        for c in design.get("components", []):
            if c.get("name") == name:
                return c
        return None

    # Check variants and page_spec components
    variants = blueprint.get("variants", [])
    page_spec = blueprint.get("page_specification", {})

    components_checked = set()

    for v in variants:
        for comp in v.get("components", []):
            cname = comp.get("component_name")
            if not cname or cname in components_checked:
                continue
            components_checked.add(cname)

            design_comp = find_design_component(cname)
            notes = (design_comp or {}).get("accessibility_notes", [])

            # If there are no accessibility notes provided by design system, flag for review
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

            # Specific check: SignupForm must enforce form labels
            if cname and cname.lower().find("signup") != -1:
                rule_present = any(r.get("id") == "a11y.form_labels" for r in acc_rules)
                has_label_note = any("label" in (n or "").lower() for n in notes)
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

    # Build a report
    passed = len(issues) == 0
    return {"issues": issues, "passed": passed}
