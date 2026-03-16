from __future__ import annotations

from typing import Dict, Any, List


def run_security_validator(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []

    texts = []
    for ev in blueprint.get("retrieved_evidence", []) or []:
        texts.append(str(ev.get("evidence", "")))

    for variant in blueprint.get("variants", []):
        for comp in variant.get("components", []):
            texts.append(str(comp.get("content_summary", "")))

    code_templates = blueprint.get("code_templates", {}) or {}
    template_blob = "\n".join(str(value) for value in code_templates.values() if isinstance(value, str))
    texts.append(template_blob)

    combined = "\n".join(texts).lower()

    if "http://" in combined:
        issues.append({
            "status": "FAIL",
            "category": "Security",
            "title": "Insecure HTTP resources detected",
            "description": "Detected references to insecure (http://) resources in evidence or generated code templates.",
            "rule_triggered": "security.insecure_resources",
            "evidence": "Found 'http://' in retrieved evidence, summaries, or generated templates.",
            "severity": "high",
            "suggested_fix": "Use HTTPS resources and avoid mixed content.",
            "human_review_required": True,
        })

    dangerous_patterns = {
        "security.inline_script": ["<script", "eval(", "dangerouslysetinnerhtml", "innerhtml ="],
        "security.unsafe_html": ["unsafe_allow_html=true"],
        "security.command_execution": ["os.system(", "subprocess.run(", "subprocess.popen("],
    }

    for rule_id, patterns in dangerous_patterns.items():
        matched = [pattern for pattern in patterns if pattern in combined]
        if matched:
            issues.append({
                "status": "FAIL",
                "category": "Security",
                "title": f"Dangerous template pattern detected: {rule_id.split('.')[-1]}",
                "description": "Generated artefacts contain code patterns that should be reviewed before release.",
                "rule_triggered": rule_id,
                "evidence": f"Matched patterns: {', '.join(matched)}",
                "severity": "high",
                "suggested_fix": "Remove dangerous dynamic execution or unsafe HTML rendering from generated templates.",
                "human_review_required": True,
            })

    passed = len([i for i in issues if i.get("status") == "FAIL"]) == 0
    return {"issues": issues, "passed": passed}
