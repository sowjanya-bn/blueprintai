from __future__ import annotations

from typing import Dict, Any, List
from utils.loaders import load_compliance_rules


def run_compliance_validator(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    req = blueprint.get("requirements", {})
    market = (req.get("market") or "").upper()

    compliance_rules = load_compliance_rules().get("rules", [])

    # If any SignupForm is present and market = EU, require explicit consent and privacy link
    has_form = False
    for v in blueprint.get("variants", []):
        for comp in v.get("components", []):
            if comp.get("component_name") and comp.get("component_name").lower().find("signup") != -1:
                has_form = True

    if has_form and market == "EU":
        # check retrieved evidence or page_spec for 'consent' or 'privacy'
        evidence_texts = []
        for ev in blueprint.get("retrieved_evidence", []):
            evidence_texts.append(str(ev.get("evidence", "")))

        found_consent = any("consent" in t.lower() or "privacy" in t.lower() for t in evidence_texts)

        if not found_consent:
            # find matching rule id
            rule_id = "compliance.personal_data_requires_consent"
            matched_rule = next((r for r in compliance_rules if r.get("id") == rule_id), None)

            issues.append({
                "status": "FAIL",
                "category": "Compliance",
                "title": "Personal data collection requires consent in EU",
                "description": "Signup form collects personal data but no consent UI or privacy link was detected in retrieved evidence.",
                "rule_triggered": rule_id,
                "evidence": "No 'consent' or 'privacy' text found in retrieved evidence for form components.",
                "severity": "high",
                "suggested_fix": "Add an explicit consent checkbox and a privacy policy link on the form (EU GDPR requirement).",
                "human_review_required": True,
            })

    # Also check for privacy link presence when forms exist regardless of market
    if has_form:
        has_privacy_footer = any(
            any(f.get("component_name") == "Disclaimer Footer" for f in v.get("components", []))
            for v in blueprint.get("variants", [])
        )
        if not has_privacy_footer:
            issues.append({
                "status": "WARN",
                "category": "Compliance",
                "title": "Privacy link missing near data collection",
                "description": "Pages that collect personal data should contain a clear link to the privacy policy.",
                "rule_triggered": "compliance.privacy_link_required",
                "evidence": "No Disclaimer Footer component detected in generated variants.",
                "severity": "medium",
                "suggested_fix": "Add a privacy policy link in the footer or near the form.",
                "human_review_required": True,
            })

    passed = len([i for i in issues if i.get("status") == "FAIL"]) == 0
    return {"issues": issues, "passed": passed}
