from __future__ import annotations

from typing import Dict, Any, List
import networkx as nx

from utils.loaders import load_design_system, load_compliance_rules, load_brand, load_market


def build_graph(requirements: Dict[str, Any], variants: List[Dict[str, Any]], retrieved: List[Dict[str, Any]]) -> nx.DiGraph:
    G = nx.DiGraph()

    # Nodes: requirement, pages (variants), components, tokens, policies
    req_id = "requirement_1"
    G.add_node(req_id, type="requirement", **{k: v for k, v in requirements.items() if k in ["audience", "market", "brand", "content_type", "compliance_sensitivity"]})

    # Load auxiliary knowledge
    design = load_design_system()
    compliance = load_compliance_rules()

    # Brand tokens (if available)
    brand_tokens = {}
    try:
        if requirements.get("brand"):
            b = load_brand(requirements.get("brand"))
            brand_tokens = b.get("tokens", {})
            # Brand node
            G.add_node(b.get("brand_id", requirements.get("brand")), type="brand", display_name=b.get("display_name"))
            # connect brand -> requirement
            G.add_edge(b.get("brand_id", requirements.get("brand")), req_id, relation="brand_applied_to")
    except Exception:
        brand_tokens = {}

    # Market node
    market_node = None
    try:
        if requirements.get("market"):
            m = load_market(requirements.get("market").lower())
            market_node = f"market_{m.get('market', requirements.get('market'))}"
            G.add_node(market_node, type="market", **m)
            G.add_edge(market_node, req_id, relation="market_applied_to")
    except Exception:
        market_node = None

    # Components: from retrieved and design system
    comp_names = set()
    for r in retrieved:
        comp = r.get("component", {})
        name = comp.get("name")
        if not name:
            continue
        node_id = f"component::{name}"
        comp_names.add(name)
        G.add_node(node_id, type="component", name=name, purpose=comp.get("purpose"))
        # link requirement -> component (traceability)
        G.add_edge(req_id, node_id, relation="requires_component")
        # connect to brand approval if applicable
        approved_brands = comp.get("approved_brands", [])
        for ab in approved_brands:
            G.add_edge(f"brand_{ab}" if not ab.startswith("brand_") else ab, node_id, relation="brand_approves")

    # Add design system components as nodes (if not already present)
    for comp in design.get("components", []):
        name = comp.get("name")
        node_id = f"component::{name}"
        if not G.has_node(node_id):
            G.add_node(node_id, type="component", name=name, purpose=comp.get("purpose"))

    # Design tokens from brand
    for token_type, tokens in brand_tokens.items():
        for tk_name, tk_value in tokens.items():
            token_node = f"token::{token_type}::{tk_name}"
            G.add_node(token_node, type="design_token", token_type=token_type, name=tk_name, value=tk_value)
            # Connect brand -> token
            if requirements.get("brand"):
                G.add_edge(requirements.get("brand"), token_node, relation="brand_has_token")

    # Forms -> compliance obligations: detect common patterns
    market_gdpr = False
    if market_node:
        market_attrs = G.nodes[market_node]
        market_gdpr = bool(market_attrs.get("gdpr", False))

    for name in comp_names:
        if any(k in name.lower() for k in ["form", "signup", "contact"]):
            form_node = f"form::{name}"
            G.add_node(form_node, type="form", name=name)
            G.add_edge(f"component::{name}", form_node, relation="has_form")

            # If market is EU/GDPR, add obligation node
            if market_gdpr:
                for rule in compliance.get("rules", []):
                    if rule.get("id") == "compliance.personal_data_requires_consent":
                        pol_node = f"policy::{rule.get('id')}"
                        G.add_node(pol_node, type="policy", **rule)
                        G.add_edge(form_node, pol_node, relation="triggers_policy")

    # Pages (variants)
    for idx, v in enumerate(variants, start=1):
        page_node = f"page::variant::{idx}"
        G.add_node(page_node, type="page_variant", name=v.get("pattern_name"), fit_score=v.get("fit_score"))
        G.add_edge(req_id, page_node, relation="produces_page")
        # page -> components
        for comp in v.get("components", []):
            cname = comp.get("component_name")
            if cname:
                G.add_edge(page_node, f"component::{cname}", relation="uses_component")

    return G


def serialize_graph(G: nx.DiGraph) -> Dict[str, Any]:
    nodes = []
    for n, attrs in G.nodes(data=True):
        nodes.append({"id": n, "attrs": attrs})

    edges = []
    for u, v, attrs in G.edges(data=True):
        edges.append({"source": u, "target": v, "attrs": attrs})

    return {"nodes": nodes, "edges": edges}
