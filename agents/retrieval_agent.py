from __future__ import annotations

from typing import List, Dict, Any

from src.retriever import retrieve_components
from utils.loaders import load_brand


def retrieve_for_brief(brief: str, brand: str | None = None, top_k: int = 5) -> List[Dict[str, Any]]:
    # Use underlying retriever (semantic) then apply brand filtering / boosting
    results = retrieve_components(brief, top_k=top_k * 2)

    approved = None
    try:
        if brand:
            b = load_brand(brand)
            approved = set(b.get("approved_components", []))
    except Exception:
        approved = None

    processed = []
    for r in results:
        comp = r.get("component", {})
        name = comp.get("name")
        score = float(r.get("score", 0.0))

        # boost score if component is approved for brand
        if approved and name in approved:
            score = min(1.0, score + 0.15)

        processed.append({
            "component": comp,
            "evidence": r.get("evidence"),
            "score": round(score, 3),
        })

    # sort and return top_k
    processed = sorted(processed, key=lambda x: x["score"], reverse=True)
    return processed[:top_k]
