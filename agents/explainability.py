from __future__ import annotations

from typing import Dict, Any, List


def build_explainability(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """Produce structured, human-friendly explainability records.

    Records include:
    - `id`: unique decision id
    - `decision`: short title
    - `confidence`: float 0..1
    - `rationale`: short explanation why
    - `evidence`: list of supporting strings
    - `rules_applied`: list of rule identifiers
    - `linked_components`: components referenced by the decision
    - `human_review`: recommendation string
    """
    records: List[Dict[str, Any]] = []
    traces: List[Dict[str, Any]] = []

    requirements = blueprint.get("requirements", {})
    retrieved = blueprint.get("retrieved_evidence", []) or []
    variants = blueprint.get("variants", []) or []
    validation = blueprint.get("validation_reports", {}) or {}
    governance = blueprint.get("governance_issues", []) or []

    # Helper to produce an id
    def _id(prefix: str, idx: int) -> str:
        return f"{prefix}_{idx}"

    # 1) Retrieval summary
    top_evidence = []
    for ev in retrieved[:3]:
        comp = ev.get("component", {})
        cid = comp.get("component_id") or comp.get("name")
        top_evidence.append(f"{comp.get('name')} (id={cid}, score={ev.get('score')})")

    rec = {
        "id": _id("retrieval", 1),
        "decision": "Retrieved components",
        "confidence": 0.9,
        "rationale": "Top semantically relevant components were selected and brand-approved items were boosted.",
        "evidence": top_evidence,
        "rules_applied": ["retriever.semantic_search", "retrieval.brand_boost"],
        "linked_components": [ev.get("component", {}).get("component_id") or ev.get("component", {}).get("name") for ev in retrieved[:5]],
        "human_review": "Optional",
    }
    records.append(rec)
    traces.append(rec)

    # 2) Variant explanations
    for i, v in enumerate(variants, start=1):
        comp_list = [c.get("component_name") for c in v.get("components", []) if c.get("component_name")]
        evidence_for_variant = []
        for name in comp_list:
            match = next((r for r in retrieved if r.get("component", {}).get("name") == name), None)
            if match:
                evidence_for_variant.append(f"{name}: score={match.get('score')}")

        rationale = f"Pattern '{v.get('pattern_name')}' balances {len(comp_list)} components to meet brief goals."
        if requirements.get("compliance_sensitivity") == "High":
            rationale += " Compliance sensitivity increased conservative choices."

        rec = {
            "id": _id("variant", i),
            "decision": f"Pattern — {v.get('pattern_name')}",
            "confidence": float(v.get("fit_score", 0.0)),
            "rationale": rationale,
            "evidence": evidence_for_variant,
            "rules_applied": ["blueprint.strategy"] + (["brand.approved_components"] if requirements.get("brand") else []),
            # map to component_ids when available
            "linked_components": [
                next((r.get("component", {}).get("component_id") for r in retrieved if r.get("component", {}).get("name") == n), n)
                for n in comp_list
            ],
            "human_review": "Recommended" if float(v.get("fit_score", 0)) < 0.6 else "Optional",
        }
        records.append(rec)
        traces.append(rec)

    # 3) Validation summary (collect failing/high-severity items)
    val_evidence = []
    for name, report in validation.items():
        for issue in report.get("issues", []):
            snippet = f"{name}: {issue.get('title')} — {issue.get('severity')}"
            val_evidence.append(snippet)

    if val_evidence:
        rec = {
            "id": _id("validation", 1),
            "decision": "Validation summary",
            "confidence": 0.95,
            "rationale": "Validators identified issues requiring remediation or human review.",
            "evidence": val_evidence,
            "rules_applied": ["validators.accessibility", "validators.brand", "validators.compliance", "validators.security"],
            "linked_components": [],
            "human_review": "Required",
        }
        records.append(rec)
        traces.append(rec)

    # 4) Governance summary
    if governance:
        gov_notes = [g.get("title") for g in governance]
        rec = {
            "id": _id("governance", 1),
            "decision": "Governance findings",
            "confidence": 0.9,
            "rationale": "Governance checks surfaced drift or restricted components.",
            "evidence": gov_notes,
            "rules_applied": ["governance.drift_detection"],
            "linked_components": [g.get("affected_component") for g in governance if g.get("affected_component")],
            "human_review": "Required",
        }
        records.append(rec)
        traces.append(rec)

    # 5) Final summary
    summary = f"{len(variants)} variant(s); {sum(1 for r in records if r.get('decision').lower().startswith('validation'))} validation groups; {len(governance)} governance issues."
    rec = {
        "id": _id("summary", 1),
        "decision": "Overall summary",
        "confidence": 0.9,
        "rationale": summary,
        "evidence": [summary],
        "rules_applied": [],
        "linked_components": [],
        "human_review": "Recommended",
    }
    records.append(rec)
    traces.append(rec)

    return {"records": records, "decision_traces": traces}
