from __future__ import annotations

import re
from typing import Dict, Any

from utils.loaders import load_market, load_brand


def analyze_brief(brief: str, brand_hint: str | None = None, market_hint: str | None = None) -> Dict[str, Any]:
    text = (brief or "").strip()

    # Simple heuristics to extract audience, market, content type, compliance sensitivity
    audience = None
    m = re.search(r"for ([a-zA-Z\-\s]+?)(?:\.|,|$)", text, re.IGNORECASE)
    if m:
        audience = m.group(1).strip()

    market = None
    if market_hint:
        market = market_hint
    else:
        if re.search(r"\bEU\b|European|european\b", text, re.IGNORECASE):
            market = "EU"
        elif re.search(r"\bUK\b|United Kingdom|british\b", text, re.IGNORECASE):
            market = "UK"

    brand = brand_hint or ("blueprint_fit" if "fit" in (brief or "").lower() else "blueprint_legal")

    content_type = None
    if re.search(r"landing|homepage|hero|landing page", text, re.IGNORECASE):
        content_type = "LandingPage"
    elif re.search(r"product|treatment|service", text, re.IGNORECASE):
        content_type = "ProductPage"
    else:
        content_type = "GeneralPage"

    # Compliance sensitivity heuristics
    sensitivity = "Low"
    if re.search(r"privacy|gdpr|consent|regulator|safety|side effect|medical", text, re.IGNORECASE):
        sensitivity = "High"
    elif re.search(r"legal|terms|policy", text, re.IGNORECASE):
        sensitivity = "Medium"

    # enrich with brand and market files when available
    brand_info = None
    market_info = None
    try:
        brand_info = load_brand(brand)
    except Exception:
        brand_info = {}

    try:
        if market:
            market_info = load_market(market.lower())
        elif market_hint:
            market_info = load_market(market_hint.lower())
        else:
            market_info = {}
    except Exception:
        market_info = {}

    return {
        "audience": audience or "general",
        "market": market or "global",
        "brand": brand,
        "content_type": content_type,
        "compliance_sensitivity": sensitivity,
        "brand_info": brand_info,
        "market_info": market_info,
    }
