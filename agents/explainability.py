from __future__ import annotations

from typing import Dict, Any, List


def build_explainability(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """Generate explanation records and decision traces for the generated blueprint.

    The function is intentionally simple and deterministic: it synthesizes
    decisions from the pipeline (variants, retrieval evidence, validators,
    governance findings) into human-readable records.
    """
    records: List[Dict[str, Any]] = []
    traces: List[Dict[str, Any]] = []

    requirements = blueprint.get("requirements", {})
    retrieved = blueprint.get("retrieved_evidence", [])
    variants = blueprint.get("variants", [])
    validation = blueprint.get("validation_reports", {}) or {}
    compliance_flags = blueprint.get("compliance_flags", {}).get("flags", []) if blueprint.get("compliance_flags") else []
    governance = blueprint.get("governance_issues", []) or []

    # Explain retrieval: top evidence items
    top_evidence = []
    for ev in (retrieved or [])[:3]:
        comp = ev.get("component", {})
        top_evidence.append(f"{comp.get('name')} (score={ev.get('score')})")

    records.append({
        "decision": "Retrieved Components",
        "confidence": 0.9,
        "evidence": top_evidence,
        "rules_applied": ["retriever.semantic_search", "brand.boost"],
        "human_review": None,
    })

    # Explain each variant selection
    for v in variants:
        comp_list = [c.get("component_name") for c in v.get("components", [])]
        evidence_for_variant = []
        for name in comp_list:
            # find retrieved evidence for this component
            match = next((r for r in (retrieved or []) if r.get("component", {}).get("name") == name), None)
            if match:
                evidence_for_variant.append(f"{name}: score={match.get('score')}")

        rule_list = ["blueprint.strategy"]
        # include brand/compliance hints
        if requirements.get("brand"):
            rule_list.append("brand.approved_components")
        if requirements.get("compliance_sensitivity") == "High":
            rule_list.append("policy.strict_mode")

        rec = {
            "decision": f"Choose pattern {v.get('pattern_name')}",
            "confidence": float(v.get("fit_score", 0.0)),
            "evidence": evidence_for_variant,
            "rules_applied": rule_list,
            "human_review": "Recommended" if v.get("fit_score", 0) < 0.6 else "Optional",
        }
        records.append(rec)
        traces.append(rec)

    # Explain validation outcomes (summarize failing rules)
    validation_notes = []
    for name, report in (validation or {}).items():
        for issue in (report.get("issues") or []):
            validation_notes.append(f"{name}: {issue.get('title')} ({issue.get('severity')})")

    if validation_notes:
        records.append({
            "decision": "Validation Issues",
            "confidence": 0.95,
            "evidence": validation_notes,
            "rules_applied": ["validators.accessibility", "validators.brand", "validators.compliance", "validators.security"],
            "human_review": "Required",
        })

    # Explain governance
    if governance:
        gov_notes = [g.get("title") for g in governance]
        records.append({
            "decision": "Governance Findings",
            "confidence": 0.9,
            "evidence": gov_notes,
            "rules_applied": ["governance.drift_detection"],
            "human_review": "Required",
        })

    # Add a short summary decision
    summary = f"Selected {len(variants)} variant(s); {len(validation_notes)} validation issues; {len(governance)} governance issues."
    records.append({
        "decision": "Summary",
        "confidence": 0.9,
        "evidence": [summary],
        "rules_applied": [],
        "human_review": "Recommended",
    })

    return {"records": records, "decision_traces": traces}
