from typing import List, Dict


def _severity_from_issue(issue: Dict) -> str:
    # Heuristic mapping
    if issue.get("type") in ("security", "critical"):
        return "high"
    score = issue.get("severity_score") or 0
    if score >= 8:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


def generate_ticket_drafts(result: Dict) -> List[Dict]:
    """Generate developer-friendly ticket drafts from validation and governance results.

    Each ticket: title, category, severity, affected_component, description, suggested_fix, rationale, owner_hint
    """
    tickets = []

    validation_reports = result.get("validation_reports", {}) if result else {}
    # Flatten validation issues
    for vtype, report in validation_reports.items():
        issues = report.get("issues", []) if isinstance(report, dict) else report
        for iss in issues:
            title = iss.get("title") or f"Fix {vtype} issue: {iss.get('id') or iss.get('message','') }"
            affected = iss.get("affected_component") or iss.get("component") or iss.get("selector")
            severity = _severity_from_issue(iss)
            suggested = iss.get("suggested_fix") or iss.get("recommendation") or "Refer to validator guidance and update the component or markup."
            desc = iss.get("message") or iss.get("description") or "No description provided."
            tickets.append(
                {
                    "title": title,
                    "category": vtype,
                    "severity": severity,
                    "affected_component": affected,
                    "description": desc,
                    "suggested_fix": suggested,
                    "rationale": iss.get("rationale") or iss.get("evidence") or [],
                    "owner_hint": iss.get("owner_hint") or ("frontend" if vtype in ("accessibility", "brand") else "security" if vtype == "security" else "dev"),
                }
            )

    # Governance issues produce higher-priority tickets
    g_issues = result.get("governance_issues", []) if result else []
    for gi in g_issues:
        title = gi.get("title") or "Governance issue"
        affected = gi.get("affected_component")
        severity = "high" if gi.get("severity") in ("high", "critical") else "medium"
        suggested = gi.get("recommendation") or "Review governance guidance and replace or remove the component."
        tickets.append(
            {
                "title": f"Governance: {title}",
                "category": "governance",
                "severity": severity,
                "affected_component": affected,
                "description": gi.get("description"),
                "suggested_fix": suggested,
                "rationale": gi.get("evidence") or [],
                "owner_hint": gi.get("owner_hint") or "platform",
            }
        )

    return tickets


def tickets_to_markdown(tickets: List[Dict]) -> str:
    md_lines = ["# Ticket Drafts\n"]
    for i, t in enumerate(tickets, start=1):
        md_lines.append(f"## {i}. {t.get('title')}")
        md_lines.append(f"- **Category**: {t.get('category')}")
        md_lines.append(f"- **Severity**: {t.get('severity')}")
        md_lines.append(f"- **Affected Component**: {t.get('affected_component')}")
        md_lines.append("\n**Description**:\n")
        md_lines.append(t.get("description", ""))
        md_lines.append("\n**Suggested Fix**:\n")
        md_lines.append(t.get("suggested_fix", ""))
        if t.get("rationale"):
            md_lines.append("\n**Rationale / Evidence**:\n")
            for r in t.get("rationale"):
                md_lines.append(f"- {r}")
        md_lines.append(f"\n**Owner hint**: {t.get('owner_hint', '')}")
        md_lines.append("\n---\n")

    return "\n".join(md_lines)
