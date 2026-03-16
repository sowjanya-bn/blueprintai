from __future__ import annotations

import re
from typing import Dict, Any, List

from utils.loaders import load_brand, load_design_system, normalize_component_name


# ── Helpers ──────────────────────────────────────────────────────────────────

def _collect_used_components(blueprint: Dict[str, Any]) -> Dict[str, set[str]]:
    """Return {normalized_name: {artefact_type, ...}} for every component referenced
    across variants, page blueprints, and component compositions."""
    found: Dict[str, set[str]] = {}

    for variant in blueprint.get("variants", []):
        for comp in variant.get("components", []):
            n = normalize_component_name(comp.get("component_name", ""))
            if n:
                found.setdefault(n, set()).add("variant")

    for pb in blueprint.get("page_blueprints", []):
        for section in pb.get("sections", []):
            n = normalize_component_name(section.get("component", ""))
            if n:
                found.setdefault(n, set()).add("page_blueprint")

    for comp_comp in blueprint.get("component_compositions", []):
        for item in comp_comp.get("components", []):
            n = normalize_component_name(item.get("component", ""))
            if n:
                found.setdefault(n, set()).add("composition")

    return found


def _build_ds_lookup(design: dict) -> Dict[str, dict]:
    """Keyed by normalized component name → component dict."""
    return {normalize_component_name(c.get("name", "")): c for c in design.get("components", [])}


def _build_token_lookup(registry: list) -> Dict[str, dict]:
    """Keyed by token id → token dict."""
    return {t.get("id", ""): t for t in registry}


def _source_label(sources: set[str]) -> str:
    pretty = {"variant": "Variants", "page_blueprint": "Page Blueprints", "composition": "Compositions"}
    return ", ".join(sorted(pretty.get(s, s) for s in sources))


# ── Checkers ─────────────────────────────────────────────────────────────────

def _check_deprecated_components(
    used: Dict[str, set[str]],
    ds_lookup: Dict[str, dict],
    brand: dict,
) -> List[Dict[str, Any]]:
    issues = []
    brand_deprecated = {normalize_component_name(n) for n in brand.get("deprecated_components", [])}

    for norm_name, sources in used.items():
        ds_comp = ds_lookup.get(norm_name)
        display_name = (ds_comp or {}).get("name", norm_name)

        # Design-system-level deprecation
        if ds_comp and ds_comp.get("status") == "deprecated":
            replacement = ds_comp.get("replacement", "a newer component")
            issues.append({
                "category": "deprecated",
                "title": f"Deprecated component: {display_name}",
                "description": (
                    f"{display_name} was deprecated in design system v{ds_comp.get('deprecated_since', '?')}. "
                    f"All new implementations should use {replacement} instead."
                ),
                "affected_component": display_name,
                "artefact_sources": _source_label(sources),
                "recommendation": f"Replace {display_name} with {replacement}.",
                "severity": "high",
            })

        # Brand-level deprecation (separate — brand may retire components ahead of DS)
        elif norm_name in brand_deprecated:
            issues.append({
                "category": "deprecated",
                "title": f"Brand-deprecated component: {display_name}",
                "description": (
                    f"{display_name} has been retired by this brand even if it is still in the design system."
                ),
                "affected_component": display_name,
                "artefact_sources": _source_label(sources),
                "recommendation": f"Check brand guidelines for the approved replacement for {display_name}.",
                "severity": "medium",
            })

    return issues


def _check_off_system_patterns(
    used: Dict[str, set[str]],
    ds_lookup: Dict[str, dict],
    blueprint: Dict[str, Any],
) -> List[Dict[str, Any]]:
    issues = []
    requirements = blueprint.get("requirements", {}) or {}
    brief_context = " ".join([
        str(requirements.get("audience") or ""),
        str(requirements.get("market") or ""),
        str(requirements.get("content_type") or ""),
        str(requirements.get("compliance_sensitivity") or ""),
    ]).lower()

    for norm_name, sources in used.items():
        ds_comp = ds_lookup.get(norm_name)
        display_name = (ds_comp or {}).get("name", norm_name)

        # Component not in design system at all
        if ds_comp is None:
            issues.append({
                "category": "off_system",
                "title": f"Off-system component: {display_name}",
                "description": (
                    f"{display_name} does not appear in the canonical design system. "
                    "It may be an ad-hoc pattern, a project-specific component, or a naming mismatch."
                ),
                "affected_component": display_name,
                "artefact_sources": _source_label(sources),
                "recommendation": (
                    "Register this component in the design system, rename it to match an existing system component, "
                    "or replace it with an approved alternative."
                ),
                "severity": "medium",
            })
            continue

        # Experimental — not yet approved for production use
        if ds_comp.get("status") == "experimental":
            issues.append({
                "category": "off_system",
                "title": f"Experimental component in production blueprint: {display_name}",
                "description": (
                    f"{display_name} is marked experimental in design system v{ds_comp.get('added_in', '?')}. "
                    "It has not been fully ratified and may change or be removed."
                ),
                "affected_component": display_name,
                "artefact_sources": _source_label(sources),
                "recommendation": "Obtain design system council sign-off before shipping with experimental components.",
                "severity": "medium",
            })

        # avoid_when context violation (pattern misuse)
        avoid_clauses = ds_comp.get("avoid_when", [])
        for clause in avoid_clauses:
            clause_words = [w for w in re.split(r"\W+", clause.lower()) if len(w) > 3]
            if clause_words and any(w in brief_context for w in clause_words):
                issues.append({
                    "category": "off_system",
                    "title": f"Pattern misuse: {display_name} in disallowed context",
                    "description": (
                        f"The design system advises avoiding {display_name} when: \"{clause}\". "
                        f"The brief/requirements context appears to match this constraint."
                    ),
                    "affected_component": display_name,
                    "artefact_sources": _source_label(sources),
                    "recommendation": (
                        f"Review whether {display_name} is appropriate for this usage context "
                        "or swap for a component better suited to this pattern."
                    ),
                    "severity": "medium",
                })
                break  # one pattern misuse issue per component is enough

    return issues


def _check_token_drift(
    brand: dict,
    brand_id: str,
    design: Dict[str, Any],
    blueprint: Dict[str, Any],
) -> List[Dict[str, Any]]:
    issues = []

    token_registry = _build_token_lookup(design.get("token_registry", []))

    # 1. Design system version sync check
    ds_version = design.get("version", "")
    brand_synced_version = brand.get("ds_version_synced", "")
    if ds_version and brand_synced_version and brand_synced_version != ds_version:
        issues.append({
            "category": "token_drift",
            "title": f"Brand token registry out of sync: {brand_id}",
            "description": (
                f"Brand '{brand_id}' was last validated against design system v{brand_synced_version}, "
                f"but the current design system is v{ds_version}. "
                "Token values, deprecated tokens, or new canonical tokens may have changed."
            ),
            "affected_component": None,
            "artefact_sources": "Brand Token Registry",
            "recommendation": (
                f"Re-sync brand '{brand_id}' tokens against design system v{ds_version}. "
                "Review deprecated token entries and update any stale values."
            ),
            "severity": "medium",
        })

    # 2. Brand token values that match deprecated DS token values
    #    (color category only — typography is handled separately below to deduplicate)
    deprecated_token_values = {
        t.get("value"): t for t in design.get("token_registry", []) if t.get("status") == "deprecated"
    }
    deprecated_font_values = {
        t.get("value"): t
        for t in design.get("token_registry", [])
        if t.get("status") == "deprecated" and t.get("category") == "typography"
    }
    brand_tokens: Dict[str, Any] = brand.get("tokens", {}) or {}
    for category, entries in brand_tokens.items():
        if not isinstance(entries, dict):
            continue
        if category == "typography":
            continue  # handled below with richer messaging
        for token_key, token_value in entries.items():
            if token_value in deprecated_token_values:
                deprecated_entry = deprecated_token_values[token_value]
                replacement_id = deprecated_entry.get("replaced_by", "a newer token")
                replacement_token = token_registry.get(replacement_id, {})
                replacement_value = replacement_token.get("value", "see design system")
                issues.append({
                    "category": "token_drift",
                    "title": f"Stale token value in brand '{brand_id}': {category}.{token_key}",
                    "description": (
                        f"Brand token '{category}.{token_key}' uses value '{token_value}' which matches "
                        f"the now-deprecated design system token '{deprecated_entry.get('id')}'. "
                        f"The canonical replacement is '{replacement_id}' with value '{replacement_value}'."
                    ),
                    "affected_component": None,
                    "artefact_sources": f"Brand Token: {brand_id} / {category}.{token_key}",
                    "recommendation": (
                        f"Update brand token '{category}.{token_key}' from '{token_value}' "
                        f"to the current canonical value '{replacement_value}' (token: {replacement_id})."
                    ),
                    "severity": "high",
                })

    # 3. Brand typography referencing deprecated font values
    brand_typography = brand_tokens.get("typography", {}) or {}
    for font_key, font_value in brand_typography.items():
        if font_value in deprecated_font_values:
            deprecated_entry = deprecated_font_values[font_value]
            replacement_id = deprecated_entry.get("replaced_by", "a newer font token")
            replacement_token = token_registry.get(replacement_id, {})
            replacement_value = replacement_token.get("value", "see design system")
            issues.append({
                "category": "token_drift",
                "title": f"Deprecated font in brand '{brand_id}': typography.{font_key} = '{font_value}'",
                "description": (
                    f"Brand '{brand_id}' uses font '{font_value}' for '{font_key}'. "
                    f"This font maps to the deprecated design system token '{deprecated_entry.get('id')}'. "
                    f"The canonical replacement font is '{replacement_value}'."
                ),
                "affected_component": None,
                "artefact_sources": f"Brand Token: {brand_id} / typography.{font_key}",
                "recommendation": (
                    f"Replace brand font '{font_value}' with '{replacement_value}' (token: {replacement_id})."
                ),
                "severity": "high",
            })

    # 4. Hardcoded hex colors in code templates
    code_templates = blueprint.get("code_templates", {}) or {}
    known_hex_values: set[str] = set()
    for t in design.get("token_registry", []):
        if t.get("category") == "color":
            known_hex_values.add(t.get("value", "").lower())
    for cat_entries in brand_tokens.values():
        if isinstance(cat_entries, dict):
            for v in cat_entries.values():
                if isinstance(v, str) and v.startswith("#"):
                    known_hex_values.add(v.lower())

    hardcoded_found: set[str] = set()
    for tmpl_name, tmpl_text in code_templates.items():
        if not isinstance(tmpl_text, str):
            continue
        for match in re.finditer(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", tmpl_text):
            hex_val = match.group(0).lower()
            if hex_val not in known_hex_values:
                hardcoded_found.add(hex_val)

    if hardcoded_found:
        issues.append({
            "category": "token_drift",
            "title": "Hardcoded color values in generated templates",
            "description": (
                "The following color values appear in generated code templates but do not correspond "
                f"to any registered design system or brand token: {', '.join(sorted(hardcoded_found))}. "
                "Hardcoded values make future theme changes error-prone."
            ),
            "affected_component": None,
            "artefact_sources": "Code Templates",
            "recommendation": (
                "Replace hardcoded hex values with design token references "
                "(e.g., CSS custom properties like var(--color-brand-primary))."
            ),
            "severity": "medium",
        })

    return issues


# ── Main entry point ──────────────────────────────────────────────────────────

def detect_governance_drift(blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    req = blueprint.get("requirements", {}) or {}
    brand_id = req.get("brand") or ""

    try:
        design = load_design_system()
    except Exception:
        design = {"components": [], "token_registry": []}

    brand = {}
    try:
        if brand_id:
            brand = load_brand(brand_id)
    except Exception:
        brand = {}

    approved = set(brand.get("approved_components", []))
    restricted = set(brand.get("restricted_components", []))

    ds_lookup = _build_ds_lookup(design)
    used = _collect_used_components(blueprint)

    # ── Deprecated components ─────────────────────────────────────────────────
    issues.extend(_check_deprecated_components(used, ds_lookup, brand))

    # ── Off-system components and pattern misuse ──────────────────────────────
    issues.extend(_check_off_system_patterns(used, ds_lookup, blueprint))

    # ── Token drift ───────────────────────────────────────────────────────────
    if brand_id:
        issues.extend(_check_token_drift(brand, brand_id, design, blueprint))

    # ── Brand access control (restricted / unapproved) ────────────────────────
    for norm_name, sources in used.items():
        ds_comp = ds_lookup.get(norm_name)
        display_name = (ds_comp or {}).get("name", norm_name)

        # Skip deprecated — already emitted above
        if ds_comp and ds_comp.get("status") == "deprecated":
            continue

        original_name = next(
            (c.get("name", "") for c in design.get("components", []) if normalize_component_name(c.get("name", "")) == norm_name),
            display_name,
        )

        if original_name in restricted:
            issues.append({
                "category": "restricted",
                "title": f"Restricted component used: {display_name}",
                "description": f"{display_name} is listed as restricted for brand '{brand_id}'.",
                "affected_component": display_name,
                "artefact_sources": _source_label(sources),
                "recommendation": f"Replace {display_name} with a brand-approved component or submit a waiver request.",
                "severity": "high",
            })

        elif approved and original_name not in approved and brand_id:
            issues.append({
                "category": "unapproved",
                "title": f"Unapproved component: {display_name}",
                "description": f"{display_name} is not in the approved component list for brand '{brand_id}'.",
                "affected_component": display_name,
                "artefact_sources": _source_label(sources),
                "recommendation": f"Obtain brand approval for {display_name} or substitute with an approved component.",
                "severity": "low",
            })

    return issues

