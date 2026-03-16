from typing import List, Dict, Optional
import os
import requests


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


def _ticket_to_issue_body(ticket: Dict) -> str:
    parts = []
    parts.append(f"### Description\n\n{ticket.get('description','No description provided.')}")
    parts.append(f"\n### Suggested Fix\n\n{ticket.get('suggested_fix','')}")
    if ticket.get('rationale'):
        parts.append("\n### Rationale / Evidence\n")
        for r in ticket.get('rationale'):
            parts.append(f"- {r}")
    parts.append(f"\n**Affected component**: {ticket.get('affected_component','')}\n")
    parts.append(f"\n**Owner hint**: {ticket.get('owner_hint','')}")
    return "\n".join(parts)


def create_github_issue(repo_full_name: str, title: str, body: str, labels: Optional[List[str]] = None, token_env: str = "GITHUB_TOKEN") -> Dict:
    """Create a GitHub issue in the given `owner/repo` using a token from `token_env`.

    Returns the JSON response from GitHub for the created issue.
    """
    token = os.getenv(token_env)
    if not token:
        raise EnvironmentError(f"GitHub token not found in environment variable {token_env}")

    url = f"https://api.github.com/repos/{repo_full_name}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def create_github_issues_from_tickets(tickets: List[Dict], repo_full_name: str, token_env: str = "GITHUB_TOKEN") -> List[Dict]:
    """Create one GitHub issue per ticket and return list of issue metadata (url, number, title).

    Labels applied: `category`, `severity` when present.
    """
    created = []
    for t in tickets:
        title = t.get("title")
        body = _ticket_to_issue_body(t)
        labels = []
        if t.get("category"):
            labels.append(t.get("category"))
        if t.get("severity"):
            labels.append(t.get("severity"))
        try:
            issue = create_github_issue(repo_full_name, title, body, labels=labels or None, token_env=token_env)
            created.append({"url": issue.get("html_url"), "number": issue.get("number"), "title": issue.get("title")})
        except Exception as e:
            # include failure info inline so callers can surface errors
            created.append({"error": str(e), "title": title})
    return created
