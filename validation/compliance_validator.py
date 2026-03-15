from __future__ import annotations

from typing import Dict, Any, List
from utils.loaders import load_compliance_rules, normalize_component_name


def run_compliance_validator(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    req = blueprint.get("requirements", {})
    market = (req.get("market") or "").upper()

    compliance_rules = load_compliance_rules().get("rules", [])

    has_form = False
    for variant in blueprint.get("variants", []):
        for comp in variant.get("components", []):
            if normalize_component_name(comp.get("component_name", "")) == "signupform":
                has_form = True

    page_blueprints = blueprint.get("page_blueprints", [])
    code_templates = blueprint.get("code_templates", {}) or {}

    artefact_texts = [str(ev.get("evidence", "")) for ev in blueprint.get("retrieved_evidence", [])]
    artefact_texts.extend(str(value) for value in code_templates.values() if isinstance(value, str))

    blueprint_slots: List[str] = []
    for page_blueprint in page_blueprints:
        for section in page_blueprint.get("sections", []):
            if normalize_component_name(section.get("component", "")) == "signupform":
                blueprint_slots.extend(section.get("content_slots", []))

    found_consent = any("consent" in text.lower() or "privacy" in text.lower() for text in artefact_texts) or any(
        "consent" in slot.lower() or "privacy" in slot.lower() for slot in blueprint_slots
    )

    if has_form and market == "EU" and not found_consent:
        rule_id = "compliance.personal_data_requires_consent"
        issues.append({
            "status": "FAIL",
            "category": "Compliance",
            "title": "Personal data collection requires consent in EU",
            "description": "Generated artefacts include a signup flow for the EU market but do not surface consent UI or privacy handling.",
            "rule_triggered": rule_id,
            "evidence": "No consent or privacy handling detected in retrieved evidence, page blueprints, or generated code templates.",
            "severity": "high",
            "suggested_fix": "Add an explicit consent checkbox and a privacy policy link to page blueprints and generated templates.",
            "human_review_required": True,
        })

    has_privacy_footer = any(
        any(normalize_component_name(comp.get("component_name", "")) == "disclaimerfooter" for comp in variant.get("components", []))
        for variant in blueprint.get("variants", [])
    )
    has_privacy_link = has_privacy_footer or any("privacy" in text.lower() for text in artefact_texts) or any(
        "privacy" in slot.lower() for slot in blueprint_slots
    )

    if has_form and not has_privacy_link:
        issues.append({
            "status": "WARN",
            "category": "Compliance",
            "title": "Privacy link missing near data collection",
            "description": "Generated form artefacts should contain a clear link to the privacy policy.",
            "rule_triggered": "compliance.privacy_link_required",
            "evidence": "No privacy link detected in generated page blueprints, variants, or code templates.",
            "severity": "medium",
            "suggested_fix": "Add a privacy policy link in the footer or near the form in generated handoff artefacts.",
            "human_review_required": True,
        })

    template_entries = [
        (name, value)
        for name, value in code_templates.items()
        if name != "recommended_variant" and isinstance(value, str)
    ]
    for template_name, template_text in template_entries:
        lowered = template_text.lower()
        if has_form and market == "EU" and "checkbox" not in lowered and "consent" not in lowered:
            issues.append({
                "status": "FAIL",
                "category": "Compliance",
                "title": f"Generated {template_name} template omits EU consent handling",
                "description": "Release-ready code templates for EU form flows should include explicit consent handling.",
                "rule_triggered": "compliance.personal_data_requires_consent",
                "evidence": f"Template {template_name} does not include a consent checkbox or equivalent consent copy.",
                "severity": "high",
                "suggested_fix": f"Inject consent controls into the generated {template_name} template.",
                "human_review_required": True,
            })
        if has_form and "privacy" not in lowered:
            issues.append({
                "status": "WARN",
                "category": "Compliance",
                "title": f"Generated {template_name} template omits privacy link handling",
                "description": "Generated templates for data capture should contain privacy-link handling before release.",
                "rule_triggered": "compliance.privacy_link_required",
                "evidence": f"Template {template_name} does not contain privacy-related copy or links.",
                "severity": "medium",
                "suggested_fix": f"Add a privacy policy link or footer to the generated {template_name} template.",
                "human_review_required": True,
            })

    passed = len([i for i in issues if i.get("status") == "FAIL"]) == 0
    return {"issues": issues, "passed": passed}
