from __future__ import annotations

from typing import List, Dict, Any
from utils.loaders import make_component_id


STRATEGIES: list[dict[str, Any]] = [
    {
        "key": "conversion_first",
        "label": "Conversion First",
        "description": "Front-loads lead capture and clear calls-to-action for users ready to act.",
        "target_components": ["Hero", "SignupForm", "CTA Block"],
    },
    {
        "key": "content_rich",
        "label": "Content Rich",
        "description": "Emphasizes depth and education before asking users to convert.",
        "target_components": ["Hero", "FeatureGrid", "FAQ", "Safety Accordion"],
    },
    {
        "key": "conservative",
        "label": "Conservative",
        "description": "Prioritizes risk-aware structure with stronger safety/disclaimer emphasis.",
        "target_components": ["Hero", "Disclaimer Footer", "Safety Accordion"],
    },
]


def _normalize_confidence(score: float) -> float:
    # Retriever scores may be outside [0, 1]. Normalize to a user-friendly range.
    return max(0.0, min(1.0, float(score)))


def _brief_alignment_score(strategy_key: str, requirements: Dict[str, Any]) -> float:
    content_type = str(requirements.get("content_type", "")).lower()
    compliance = str(requirements.get("compliance_sensitivity", "")).lower()

    score = 0.6

    if strategy_key == "conservative" and compliance in {"high", "strict", "sensitive"}:
        score += 0.25
    if strategy_key == "content_rich" and any(k in content_type for k in ["educ", "info", "guide", "learn"]):
        score += 0.25
    if strategy_key == "conversion_first" and any(k in content_type for k in ["landing", "campaign", "signup", "lead"]):
        score += 0.25

    return max(0.0, min(1.0, score))


def generate_variants(requirements: Dict[str, Any], retrieved: List[Dict[str, Any]], num_variants: int = 3) -> Dict[str, Any]:
    # Simple rule-based blueprint generator that composes variants from retrieved components
    components = [r["component"]["name"] for r in retrieved]

    variants: List[Dict[str, Any]] = []

    strategy_defs = STRATEGIES[: max(1, num_variants)]

    for i in range(num_variants):
        strategy = strategy_defs[i] if i < len(strategy_defs) else strategy_defs[0]
        strat = strategy["key"]
        target_components = strategy["target_components"]
        comps = []

        # De-duplicate while preserving order.
        order: list[str] = []
        for c in target_components + components:
            if c in components and c not in order:
                order.append(c)

        # build components with summaries and confidence based on retrieved scores
        for name in order:
            match = next((r for r in retrieved if r["component"]["name"] == name), None)
            confidence = _normalize_confidence(float(match["score"])) if match else 0.4
            comp_id = None
            if match:
                comp_id = match.get("component", {}).get("component_id")

            comps.append({
                "component_name": name,
                "component_id": comp_id or make_component_id(name),
                "content_summary": match["evidence"][:200] if match else "",
                "rationale": f"Selected by strategy {strategy['label']}",
                "confidence": confidence,
            })

        evidence_score = 0.0
        if comps:
            evidence_score = sum(c.get("confidence", 0.0) for c in comps) / len(comps)

        coverage_score = 0.0
        if target_components:
            present = {c.get("component_name") for c in comps}
            coverage_score = len([c for c in target_components if c in present]) / len(target_components)

        alignment_score = _brief_alignment_score(strat, requirements)

        fit_score = (0.55 * evidence_score) + (0.25 * coverage_score) + (0.20 * alignment_score)

        variants.append({
            "strategy_key": strat,
            "pattern_name": strategy["label"],
            "fit_score": round(min(1.0, fit_score), 3),
            "fit_score_breakdown": {
                "evidence_match": round(evidence_score, 3),
                "structure_coverage": round(coverage_score, 3),
                "brief_alignment": round(alignment_score, 3),
            },
            "description": strategy["description"],
            "components": comps,
        })

    pattern_reasoning = [
        "Variants generated to explore different tradeoffs between conversion, content depth, and legal conservatism.",
        f"Based on brand={requirements.get('brand')} and market={requirements.get('market')}",
        "Fit score is a weighted heuristic (evidence match + structure coverage + brief alignment), not a conversion-rate prediction.",
    ]

    strategy_definitions = {
        s["label"]: s["description"] for s in STRATEGIES
    }

    page_spec = {
        "page_type": requirements.get("content_type", "LandingPage"),
        "layout": [
            {"component": c["component_name"], "props": {}, "accessibility_notes": []}
            for c in variants[0]["components"]
        ],
    }

    result = {
        "requirements": {
            "audience": requirements.get("audience"),
            "market": requirements.get("market"),
            "content_type": requirements.get("content_type"),
            "compliance_sensitivity": requirements.get("compliance_sensitivity"),
        },
        "pattern_reasoning": pattern_reasoning,
        "strategy_definitions": strategy_definitions,
        "variants": variants,
        "human_review_required": ["designer", "compliance"] if requirements.get("compliance_sensitivity") == "High" else ["designer"],
        "page_specification": page_spec,
    }

    return result
