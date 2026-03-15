from __future__ import annotations

import json
import re
from typing import Dict, Any

from utils.loaders import load_market, load_brand, load_prompt
from src.llm import generate_json, is_available


# ── Regex fallbacks (used when Gemini is unavailable or returns unusable JSON) ─

def _regex_extract(brief: str, brand_hint: str | None, market_hint: str | None) -> Dict[str, Any]:
    text = (brief or "").strip()

    audience = None
    m = re.search(r"for ([a-zA-Z\-\s]+?)(?:\.|,|$)", text, re.IGNORECASE)
    if m:
        audience = m.group(1).strip()

    market = market_hint
    if not market:
        if re.search(r"\bEU\b|European\b", text, re.IGNORECASE):
            market = "EU"
        elif re.search(r"\bUK\b|United Kingdom|british\b", text, re.IGNORECASE):
            market = "UK"

    # Explicit brand words first, then null — do not default to blueprint_legal blindly
    brand = brand_hint
    if not brand:
        if re.search(r"blueprint[_\s-]?fit", text, re.IGNORECASE):
            brand = "blueprint_fit"
        elif re.search(r"blueprint[_\s-]?legal", text, re.IGNORECASE):
            brand = "blueprint_legal"

    if re.search(r"landing|homepage|hero", text, re.IGNORECASE):
        content_type = "LandingPage"
    elif re.search(r"product|treatment|service", text, re.IGNORECASE):
        content_type = "ProductPage"
    else:
        content_type = "GeneralPage"

    if re.search(r"privacy|gdpr|consent|regulator|safety|side effect|medical|patient|clinical", text, re.IGNORECASE):
        sensitivity = "High"
    elif re.search(r"legal|terms|policy|financial|insurance|investment", text, re.IGNORECASE):
        sensitivity = "Medium"
    else:
        sensitivity = "Low"

    if re.search(r"patient|medical|clinical|treatment|therapy|healthcare|hospital", text, re.IGNORECASE):
        industry = "healthcare"
    elif re.search(r"financial|finance|bank|investment|insurance|credit|loan|fintech", text, re.IGNORECASE):
        industry = "financial"
    else:
        industry = "general"

    return {
        "audience": audience or "general",
        "market": market or "global",
        "brand": brand,
        "content_type": content_type,
        "compliance_sensitivity": sensitivity,
        "industry": industry,
        "key_goals": [],
        "compliance_notes": [],
        "brand_tone": "conversational",
    }


def _llm_extract(brief: str) -> Dict[str, Any] | None:
    if not is_available():
        return None
    try:
        template = load_prompt("extract_requirements.txt")
        prompt = template.replace("{brief}", brief)
        raw = generate_json(prompt)
        if not raw:
            return None
        parsed = json.loads(raw)
        # Validate essential fields are present
        if not isinstance(parsed.get("audience"), str):
            return None
        return parsed
    except Exception:
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_brief(brief: str, brand_hint: str | None = None, market_hint: str | None = None) -> Dict[str, Any]:
    # Try Gemini first
    llm_result = _llm_extract(brief)
    if llm_result:
        extracted = llm_result
        # Honour explicit hints over LLM-extracted values
        if brand_hint:
            extracted["brand"] = brand_hint
        if market_hint:
            extracted["market"] = market_hint
    else:
        extracted = _regex_extract(brief, brand_hint, market_hint)

    brand = extracted.get("brand")

    brand_info: Dict[str, Any] = {}
    try:
        if brand:
            brand_info = load_brand(brand)
    except Exception:
        brand_info = {}

    market_info: Dict[str, Any] = {}
    try:
        market_val = extracted.get("market", "")
        if market_val and market_val.lower() != "global":
            market_info = load_market(market_val.lower())
    except Exception:
        market_info = {}

    return {
        "brief": brief,  # preserved for downstream LLM enrichment
        "audience": extracted.get("audience") or "general",
        "market": extracted.get("market") or "global",
        "brand": brand,
        "content_type": extracted.get("content_type") or "GeneralPage",
        "compliance_sensitivity": extracted.get("compliance_sensitivity") or "Low",
        "industry": extracted.get("industry") or "general",
        "key_goals": extracted.get("key_goals") or [],
        "compliance_notes": extracted.get("compliance_notes") or [],
        "brand_tone": extracted.get("brand_tone") or "conversational",
        "brand_info": brand_info,
        "market_info": market_info,
    }
