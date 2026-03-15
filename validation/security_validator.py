from __future__ import annotations

from typing import Dict, Any, List


def run_security_validator(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    # Look for evidence of insecure links, inline scripts, or suspicious patterns
    texts = []
    for ev in blueprint.get("retrieved_evidence", []) or []:
        texts.append(str(ev.get("evidence", "")))

    for v in blueprint.get("variants", []):
        for comp in v.get("components", []):
            texts.append(str(comp.get("content_summary", "")))

    combined = "\n".join(texts).lower()

    if "http://" in combined:
        issues.append({
            "status": "FAIL",
            "category": "Security",
            "title": "Insecure HTTP resources detected",
            "description": "Detected references to insecure (http://) resources in component evidence or summaries.",
            "rule_triggered": "security.insecure_resources",
            "evidence": "Found 'http://' in retrieved evidence or component summaries.",
            "severity": "high",
            "suggested_fix": "Use HTTPS resources and avoid mixed content.",
            "human_review_required": True,
        })

    if "<script" in combined or "eval(" in combined:
        issues.append({
            "status": "FAIL",
            "category": "Security",
            "title": "Embedded script or dynamic eval detected",
            "description": "Evidence suggests inline scripts or dynamic code execution that could introduce XSS or injection risks.",
            "rule_triggered": "security.inline_script",
            "evidence": "Found '<script' or 'eval(' in evidence or component summaries.",
            "severity": "high",
            "suggested_fix": "Avoid inline scripts; sanitize inputs and use CSP headers.",
            "human_review_required": True,
        })

    passed = len([i for i in issues if i.get("status") == "FAIL"]) == 0
    return {"issues": issues, "passed": passed}
