from __future__ import annotations

import json

from src.compliance import check_compliance
from agents.brief_analyzer import analyze_brief
from agents.retrieval_agent import retrieve_for_brief
from agents.blueprint_generator import generate_variants
from src.compliance_engine import ComplianceEngine
from knowledge.graph_builder import build_graph, serialize_graph
from validation.accessibility_validator import run_accessibility_validator
from validation.brand_validator import run_brand_validator
from validation.compliance_validator import run_compliance_validator
from validation.security_validator import run_security_validator
from governance.drift_detector import detect_governance_drift
from agents.explainability import build_explainability

compliance_engine = ComplianceEngine()


def _infer_solution_domain(brief: str) -> str:
    text = (brief or "").lower()
    if any(token in text for token in ["patient", "medical", "clinical", "treatment", "therapy", "healthcare", "hospital"]):
        return "healthcare"
    if any(token in text for token in ["financial", "finance", "bank", "investment", "insurance", "credit", "loan", "fintech"]):
        return "financial"
    return "general"


def _build_architecture_plan(brief: str, requirements: dict, retrieved: list[dict]) -> dict:
    domain = _infer_solution_domain(brief)
    market = requirements.get("market", "global")
    audience = requirements.get("audience", "general users")
    collects_personal_data = any(token in (brief or "").lower() for token in [
        "signup", "sign up", "register", "form", "contact", "email", "phone", "book", "appointment", "lead",
    ])

    services = [
        {
            "name": "Experience Frontend",
            "responsibility": "Render the approved user journey and serve content through an edge-delivered web application.",
            "scale_note": "Cache static assets at the edge and keep frontend runtime stateless.",
        },
        {
            "name": "Blueprint Orchestrator API",
            "responsibility": "Coordinate brief analysis, retrieval, blueprint generation, validation, and approval workflows.",
            "scale_note": "Run as a horizontally scalable stateless service behind a load balancer.",
        },
        {
            "name": "Retrieval and Policy Service",
            "responsibility": "Resolve design-system evidence, policy rules, and market constraints used during generation.",
            "scale_note": "Back with indexed storage and cache high-frequency lookups.",
        },
        {
            "name": "Validation Workers",
            "responsibility": "Execute accessibility, brand, compliance, and security checks asynchronously for larger workloads.",
            "scale_note": "Queue-driven workers allow burst handling and parallel validation runs.",
        },
        {
            "name": "Governance and Audit Store",
            "responsibility": "Persist explainability records, approvals, governance drift, and release decisions.",
            "scale_note": "Use immutable audit logging for regulated change history.",
        },
    ]

    if collects_personal_data:
        services.append(
            {
                "name": "Consent and Preference Service",
                "responsibility": "Manage consent capture, privacy notices, and preference storage for personal-data workflows.",
                "scale_note": "Separate privacy-sensitive concerns from presentation and content services.",
            }
        )

    if domain == "healthcare":
        services.append(
            {
                "name": "Medical and Regulatory Review Queue",
                "responsibility": "Route claims, safety language, and patient-facing content to medical/legal review before release.",
                "scale_note": "Treat review outcomes as blocking approvals in regulated releases.",
            }
        )
    elif domain == "financial":
        services.append(
            {
                "name": "Disclosure and Risk Review Queue",
                "responsibility": "Validate financial promotions, disclosures, and risk language before publication.",
                "scale_note": "Require approval evidence for release of customer-facing financial content.",
            }
        )

    data_stores = [
        "Content and blueprint artifact store",
        "Policy and compliance rule store",
        "Vector or indexed retrieval store",
        "Audit log for approvals and explainability",
    ]
    if collects_personal_data:
        data_stores.append("Consent/preference store with region-aware retention controls")

    approval_checkpoints = [
        {
            "id": "architecture_review",
            "label": "Architecture Review",
            "owner": "Solution Architect",
            "description": "Validate service boundaries, integrations, scalability, observability, and failure handling.",
        },
        {
            "id": "ux_review",
            "label": "UX Review",
            "owner": "UX Lead",
            "description": "Validate the chosen journey, information architecture, and interaction flow before build.",
        },
        {
            "id": "validation_review",
            "label": "Validation Review",
            "owner": "QA / Compliance",
            "description": "Resolve validator failures, governance issues, and unresolved compliance flags before release.",
        },
        {
            "id": "deployment_approval",
            "label": "Deployment Approval",
            "owner": "Release Manager",
            "description": "Approve environment readiness, rollout plan, rollback path, and monitoring coverage.",
        },
    ]

    return {
        "domain": domain,
        "audience": audience,
        "market": market,
        "architecture_style": "Modular service-oriented delivery platform",
        "system_summary": (
            f"Designed as a large-scale web delivery workflow for {domain} use cases targeting {market} "
            f"with stateless APIs, async validation, and auditable approval gates."
        ),
        "frontend_pattern": "Edge-served web frontend backed by stateless orchestration APIs",
        "deployment_model": [
            "Development and preview environments for rapid iteration",
            "Staging environment with full validation and governance checks",
            "Production rollout with monitoring, alerting, and rollback support",
        ],
        "non_functional_requirements": [
            "Horizontal scalability for orchestration and validation services",
            "Auditability of approvals, policy checks, and explainability traces",
            "Environment promotion gates before production deployment",
            "Observability across generation, validation, and release steps",
        ],
        "services": services,
        "data_stores": data_stores,
        "approval_checkpoints": approval_checkpoints,
        "suggested_components": [r.get("component", {}).get("name") for r in retrieved[:5] if r.get("component", {}).get("name")],
    }


def create_blueprint(brief: str) -> dict:
    # 1. Analyze brief into structured requirements
    requirements = analyze_brief(brief)

    # 2. Retrieve relevant components with brand-aware boosting
    retrieved = retrieve_for_brief(brief, brand=requirements.get("brand"), top_k=6)

    # 3. Generate rule-based blueprint variants
    data = generate_variants(requirements, retrieved, num_variants=3)
    data["architecture_plan"] = _build_architecture_plan(brief, requirements, retrieved)

    # 4. Attach retrieved evidence and run compliance checks
    compliance = compliance_engine.run(brief, requirements=requirements)
    data["compliance_flags"] = compliance
    data["retrieved_evidence"] = retrieved
    # 5. Build lightweight knowledge graph for explainability and traceability
    try:
        G = build_graph(requirements, data.get("variants", []), retrieved)
        data["knowledge_graph"] = serialize_graph(G)
    except Exception:
        data["knowledge_graph"] = {"nodes": [], "edges": []}
    # 6. Run validators (Accessibility, Brand, Compliance, Security)
    try:
        accessibility_report = run_accessibility_validator(data)
    except Exception:
        accessibility_report = {"issues": [], "passed": False}

    try:
        brand_report = run_brand_validator(data)
    except Exception:
        brand_report = {"issues": [], "passed": False}

    try:
        compliance_report = run_compliance_validator(data)
    except Exception:
        compliance_report = {"issues": [], "passed": False}

    try:
        security_report = run_security_validator(data)
    except Exception:
        security_report = {"issues": [], "passed": False}

    data["validation_reports"] = {
        "accessibility": accessibility_report,
        "brand": brand_report,
        "compliance": compliance_report,
        "security": security_report,
    }
    # 7. Governance drift detection
    try:
        governance_issues = detect_governance_drift(data)
    except Exception:
        governance_issues = []

    data["governance_issues"] = governance_issues
    # 8. Explainability records and decision traces
    try:
        explainability = build_explainability(data)
    except Exception:
        explainability = {"records": [], "decision_traces": []}

    data["explainability"] = explainability
    return data