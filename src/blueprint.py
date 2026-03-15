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

compliance_engine = ComplianceEngine()


def create_blueprint(brief: str) -> dict:
    # 1. Analyze brief into structured requirements
    requirements = analyze_brief(brief)

    # 2. Retrieve relevant components with brand-aware boosting
    retrieved = retrieve_for_brief(brief, brand=requirements.get("brand"), top_k=6)

    # 3. Generate rule-based blueprint variants
    data = generate_variants(requirements, retrieved, num_variants=3)

    # 4. Attach retrieved evidence and run compliance checks
    compliance = compliance_engine.run(brief)
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
    return data