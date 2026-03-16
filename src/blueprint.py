from __future__ import annotations

from agents.brief_analyzer import analyze_brief
from agents.retrieval_agent import retrieve_for_brief
from agents.blueprint_generator import generate_variants
from src.compliance_engine import ComplianceEngine
from knowledge.graph_builder import build_graph, serialize_graph
from validation.accessibility_validator import run_accessibility_validator
from validation.brand_validator import run_brand_validator
from validation.compliance_validator import run_compliance_validator
from validation.composition_validator import run_composition_validator
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

    service_flow = [
        {
            "step": "Ingress and Experience Delivery",
            "summary": "Users access the frontend through CDN or edge delivery, which forwards dynamic requests to the orchestration API.",
        },
        {
            "step": "Brief Analysis and Retrieval",
            "summary": "The orchestration API analyzes the brief, queries retrieval and policy services, and assembles domain and market context.",
        },
        {
            "step": "Blueprint Generation",
            "summary": "Generation services compose variants, architecture recommendations, and page specifications from retrieved evidence.",
        },
        {
            "step": "Async Validation and Governance",
            "summary": "Validation workers execute accessibility, brand, compliance, and security checks asynchronously, then publish outcomes to the audit store.",
        },
        {
            "step": "Approval and Release",
            "summary": "Review gates consume validation and governance results to approve UX, architecture, platform, security, and deployment readiness.",
        },
    ]

    if collects_personal_data:
        service_flow.insert(
            4,
            {
                "step": "Consent and Privacy Processing",
                "summary": "Personal-data capture requests are routed through consent and preference services before persistence or downstream processing.",
            },
        )

    environment_promotion_policy = [
        "Promote changes from development to preview only after unit and smoke checks pass.",
        "Promote preview to staging only after architecture, UX, and validation checkpoints are approved.",
        "Run full regression, security, and governance review in staging before production release.",
        "Require explicit deployment approval with rollback owner and monitoring owner assigned before production rollout.",
    ]

    rollback_strategy = [
        "Use immutable build artifacts and versioned releases so the previous known-good version can be restored quickly.",
        "Deploy with progressive rollout or canary promotion to limit blast radius.",
        "On health-check degradation, automatically halt rollout and revert traffic to the previous stable release.",
        "Preserve approval and audit metadata for both failed and rolled-back releases.",
    ]

    monitoring_checklist = [
        "API latency, error rate, and saturation dashboards for orchestration and validation services",
        "Queue depth and worker failure alerts for asynchronous validators",
        "Frontend performance, availability, and client error monitoring",
        "Release health indicators tied to current deployment version",
        "Audit alerts for failed approvals, policy drift, or repeated compliance exceptions",
    ]

    security_controls = [
        "Centralized authentication and authorization for internal review and admin workflows",
        "Secrets managed outside application code with environment-specific rotation",
        "Encrypted transport between all services and encrypted storage for sensitive records",
        "Least-privilege access to audit, consent, and retrieval stores",
    ]

    platform_controls = [
        "Stateless service deployment behind load balancers",
        "Autoscaling for orchestration APIs and queue workers",
        "Environment-isolated configuration and release promotion pipeline",
        "Centralized logging, metrics, and tracing across the platform",
    ]

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
            "id": "platform_review",
            "label": "Platform Review",
            "owner": "Platform Engineering",
            "description": "Validate environment promotion, observability, scalability controls, and rollback readiness.",
        },
        {
            "id": "security_review",
            "label": "Security Review",
            "owner": "Security Lead",
            "description": "Validate authentication, secrets handling, data protection, and any unresolved security findings.",
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
        "service_flow": service_flow,
        "deployment_model": [
            "Development and preview environments for rapid iteration",
            "Staging environment with full validation and governance checks",
            "Production rollout with monitoring, alerting, and rollback support",
        ],
        "environment_promotion_policy": environment_promotion_policy,
        "rollback_strategy": rollback_strategy,
        "monitoring_checklist": monitoring_checklist,
        "security_controls": security_controls,
        "platform_controls": platform_controls,
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
        composition_report = run_composition_validator(data)
    except Exception:
        composition_report = {"issues": [], "passed": False}

    try:
        security_report = run_security_validator(data)
    except Exception:
        security_report = {"issues": [], "passed": False}

    data["validation_reports"] = {
        "accessibility": accessibility_report,
        "brand": brand_report,
        "compliance": compliance_report,
        "composition": composition_report,
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