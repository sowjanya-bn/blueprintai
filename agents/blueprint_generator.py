from __future__ import annotations

from typing import List, Dict, Any


def generate_variants(requirements: Dict[str, Any], retrieved: List[Dict[str, Any]], num_variants: int = 3) -> Dict[str, Any]:
    # Simple rule-based blueprint generator that composes variants from retrieved components
    components = [r["component"]["name"] for r in retrieved]

    variants: List[Dict[str, Any]] = []

    # Variant strategies
    strategies = ["conversion_first", "content_rich", "conservative"]

    for i in range(num_variants):
        strat = strategies[i] if i < len(strategies) else strategies[0]
        comps = []

        if strat == "conversion_first":
            # prioritize Hero and SignupForm
            order = [c for c in ["Hero", "SignupForm", "CTA Block"] + components if c in components]
        elif strat == "content_rich":
            order = [c for c in ["Hero", "FeatureGrid", "FAQ", "Safety Accordion"] + components if c in components]
        else:
            order = [c for c in ["Hero", "Disclaimer Footer", "Safety Accordion"] + components if c in components]

        # build components with summaries and confidence based on retrieved scores
        for name in order:
            match = next((r for r in retrieved if r["component"]["name"] == name), None)
            confidence = float(match["score"]) if match else 0.5
            comps.append({
                "component_name": name,
                "content_summary": match["evidence"][:200] if match else "",
                "rationale": f"Selected by strategy {strat}",
                "confidence": confidence,
            })

        fit_score = 0.0
        if comps:
            fit_score = sum(c.get("confidence", 0.0) for c in comps) / len(comps)

        variants.append({
            "pattern_name": strat.replace("_", " ").title(),
            "fit_score": round(min(1.0, fit_score), 3),
            "description": f"Generated with strategy {strat}",
            "components": comps,
        })

    pattern_reasoning = [
        "Variants generated to explore different tradeoffs between conversion, content depth, and legal conservatism.",
        f"Based on brand={requirements.get('brand')} and market={requirements.get('market')}",
    ]

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
        "variants": variants,
        "human_review_required": ["designer", "compliance"] if requirements.get("compliance_sensitivity") == "High" else ["designer"],
        "page_specification": page_spec,
    }

    return result
