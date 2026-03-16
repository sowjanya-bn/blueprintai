from __future__ import annotations

import json

from typing import List, Dict, Any, Optional
from utils.loaders import make_component_id, load_prompt
from src.llm import generate_json, is_available


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


def _component_layout_role(name: str) -> str:
    mapping = {
        "Hero": "primary-entry",
        "SignupForm": "conversion-capture",
        "CTA Block": "conversion-prompt",
        "FeatureGrid": "benefit-explanation",
        "Safety Accordion": "risk-disclosure",
        "FAQ": "supporting-answers",
        "Disclaimer Footer": "legal-disclosure",
    }
    return mapping.get(name, "content-block")


def _component_props(name: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
    audience = requirements.get("audience") or "general audience"
    market = requirements.get("market") or "global"

    mapping = {
        "Hero": {
            "headline": f"Primary message for {audience}",
            "subheadline": f"Supporting message tailored to the {market} market",
            "ctaLabel": "Get Started",
        },
        "SignupForm": {
            "title": "Stay updated",
            "submitLabel": "Submit",
            "fields": ["firstName", "lastName", "email"],
            "consentRequired": True,
        },
        "CTA Block": {
            "title": "Ready for the next step?",
            "body": "Guide users to the primary conversion action.",
            "ctaLabel": "Continue",
        },
        "FeatureGrid": {
            "columns": 3,
            "showIcons": True,
        },
        "Safety Accordion": {
            "allowMultipleExpanded": False,
            "sections": ["Warnings", "Side Effects", "When to seek help"],
        },
        "FAQ": {
            "items": 4,
            "expandFirst": False,
        },
        "Disclaimer Footer": {
            "showPrivacyLink": True,
            "showRegulatoryCopy": True,
        },
    }
    return mapping.get(name, {"title": name})


def _component_slots(name: str) -> List[str]:
    mapping = {
        "Hero": ["headline", "subheadline", "cta"],
        "SignupForm": ["formTitle", "fields", "consentCopy", "submitAction"],
        "CTA Block": ["title", "body", "cta"],
        "FeatureGrid": ["sectionTitle", "cards"],
        "Safety Accordion": ["sectionTitle", "accordionItems"],
        "FAQ": ["sectionTitle", "questions"],
        "Disclaimer Footer": ["disclaimerText", "privacyLink"],
    }
    return mapping.get(name, ["content"])


def _component_data_dependencies(name: str) -> List[str]:
    mapping = {
        "SignupForm": ["consent status", "submission endpoint", "validation schema"],
        "Hero": ["campaign message content"],
        "FeatureGrid": ["feature cards content"],
        "Safety Accordion": ["approved safety copy"],
        "FAQ": ["approved FAQs"],
        "Disclaimer Footer": ["privacy URL", "legal copy"],
    }
    return mapping.get(name, [])


def _component_accessibility_notes(name: str) -> List[str]:
    mapping = {
        "Hero": ["Ensure one clear H1 and descriptive CTA text."],
        "SignupForm": ["Associate labels and errors with inputs.", "Support keyboard and screen-reader flows."],
        "CTA Block": ["Keep CTA text action-oriented and specific."],
        "FeatureGrid": ["Use semantic lists or landmark regions for cards."],
        "Safety Accordion": ["Expose expanded state and keyboard controls."],
        "FAQ": ["Use meaningful question headings and button semantics."],
        "Disclaimer Footer": ["Maintain readable contrast and link clarity."],
    }
    return mapping.get(name, ["Validate heading structure and text contrast."])


def _route_for_variant(variant: Dict[str, Any], requirements: Dict[str, Any]) -> str:
    page_type = str(requirements.get("content_type") or "page").replace("Page", "").lower()
    strategy = str(variant.get("strategy_key") or variant.get("pattern_name") or "default").replace("_", "-").lower()
    return f"/{page_type}/{strategy}"


def _build_page_blueprint(variant: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
    sections = []
    for idx, component in enumerate(variant.get("components", []), start=1):
        name = component.get("component_name", "Component")
        component_id = component.get("component_id") or make_component_id(name)
        sections.append(
            {
                "section_id": f"section_{idx}_{component_id.split('::')[-1]}",
                "order": idx,
                "component": name,
                "component_id": component_id,
                "layout_role": _component_layout_role(name),
                "summary": component.get("content_summary", ""),
                "props": _component_props(name, requirements),
                "content_slots": _component_slots(name),
                "data_dependencies": _component_data_dependencies(name),
                "accessibility_notes": _component_accessibility_notes(name),
            }
        )

    return {
        "variant_name": variant.get("pattern_name", "Untitled Variant"),
        "strategy_key": variant.get("strategy_key"),
        "page_type": requirements.get("content_type", "LandingPage"),
        "route": _route_for_variant(variant, requirements),
        "audience": requirements.get("audience", "general"),
        "sections": sections,
        "handoff_notes": [
            "Map approved copy to each section before implementation.",
            "Confirm analytics and compliance requirements for interactive elements.",
            "Validate responsive behavior for all content blocks.",
        ],
    }


def _build_component_composition(page_blueprint: Dict[str, Any]) -> Dict[str, Any]:
    composition = []
    previous_component_id = None
    for section in page_blueprint.get("sections", []):
        component_entry = {
            "component": section.get("component"),
            "component_id": section.get("component_id"),
            "position": section.get("order"),
            "composition_role": section.get("layout_role"),
            "parent": "page-root",
            "depends_on": [previous_component_id] if previous_component_id else [],
            "props": section.get("props", {}),
            "content_slots": section.get("content_slots", []),
            "data_dependencies": section.get("data_dependencies", []),
        }
        composition.append(component_entry)
        previous_component_id = section.get("component_id")

    return {
        "variant_name": page_blueprint.get("variant_name"),
        "route": page_blueprint.get("route"),
        "components": composition,
    }


def _template_component_name(name: str) -> str:
    parts = [part for part in str(name).replace("-", " ").split() if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Component"


def _jsx_prop_value(value: Any) -> str:
    if isinstance(value, str):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, bool):
        return "{true}" if value else "{false}"
    if isinstance(value, (int, float)):
        return f"{{{value}}}"
    if isinstance(value, list):
        rendered = ", ".join(_jsx_prop_value(item).strip("{}") if not isinstance(item, str) else f'\"{item}\"' for item in value)
        return f"{{[{rendered}]}}"
    return "{undefined}"


def _build_react_template(page_blueprint: Dict[str, Any]) -> str:
    imports = []
    blocks = []

    for section in page_blueprint.get("sections", []):
        component_name = _template_component_name(section.get("component"))
        import_stmt = f"import {component_name} from \"@/components/{component_name}\";"
        if import_stmt not in imports:
            imports.append(import_stmt)

        props = section.get("props", {})
        prop_lines = []
        for key, value in props.items():
            prop_lines.append(f"        {key}={_jsx_prop_value(value)}")
        if not prop_lines:
            prop_lines.append("        /* add props */")

        blocks.append(
            "\n".join(
                [
                    f"      <section data-section-id=\"{section.get('section_id')}\">",
                    f"        <{component_name}",
                    *prop_lines,
                    "        />",
                    "      </section>",
                ]
            )
        )

    page_component_name = _template_component_name(page_blueprint.get("variant_name", "BlueprintPage")) + "Page"
    imports_block = "\n".join(imports)
    sections_block = "\n\n".join(blocks)

    return (
        f"{imports_block}\n\n"
        f"export default function {page_component_name}() {{\n"
        "  return (\n"
        "    <main>\n"
        f"{sections_block}\n"
        "    </main>\n"
        "  );\n"
        "}\n"
    )


def _build_html_template(page_blueprint: Dict[str, Any]) -> str:
    sections = []
    for section in page_blueprint.get("sections", []):
        slots = "\n".join(f"      <div data-slot=\"{slot}\">{slot}</div>" for slot in section.get("content_slots", []))
        sections.append(
            "\n".join(
                [
                    f"  <section id=\"{section.get('section_id')}\" data-component=\"{section.get('component')}\">",
                    f"    <h2>{section.get('component')}</h2>",
                    slots or "      <div>content</div>",
                    "  </section>",
                ]
            )
        )

    body = "\n\n".join(sections)
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\" />\n"
        f"  <title>{page_blueprint.get('variant_name')}</title>\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        f"{body}\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


def _python_literal(value: Any) -> str:
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        return json.dumps(value)
    if isinstance(value, dict):
        return json.dumps(value, indent=4)
    return "None"


def _build_streamlit_template(page_blueprint: Dict[str, Any]) -> str:
    lines = [
        "import streamlit as st",
        "",
        "st.set_page_config(page_title=\"Blueprint Page\", layout=\"wide\")",
        "",
        f"st.title({_python_literal(page_blueprint.get('variant_name', 'Blueprint Page'))})",
        f"st.caption({_python_literal('Route: ' + str(page_blueprint.get('route', '/')) )})",
        "",
    ]

    for section in page_blueprint.get("sections", []):
        component = section.get("component", "Component")
        props = section.get("props", {})
        slots = section.get("content_slots", [])
        role = section.get("layout_role", "content-block")
        notes = section.get("accessibility_notes", [])

        lines.extend(
            [
                f"with st.container(border=True):",
                f"    st.markdown(\"### {component}\")",
                f"    st.caption({_python_literal('Layout role: ' + role)})",
            ]
        )

        if component == "Hero":
            lines.append(f"    st.header({_python_literal(props.get('headline', 'Headline'))})")
            lines.append(f"    st.write({_python_literal(props.get('subheadline', 'Supporting copy'))})")
            lines.append(f"    st.button({_python_literal(props.get('ctaLabel', 'Get Started'))})")
        elif component == "SignupForm":
            lines.append(f"    st.subheader({_python_literal(props.get('title', 'Stay updated'))})")
            for field in props.get("fields", []):
                label = field[:1].upper() + field[1:]
                lines.append(f"    st.text_input({_python_literal(label)}, key={_python_literal('field_' + field)})")
            if props.get("consentRequired"):
                lines.append("    st.checkbox(\"I agree to the privacy notice and consent terms\")")
            lines.append(f"    st.button({_python_literal(props.get('submitLabel', 'Submit'))}, key={_python_literal(section.get('section_id', 'submit'))})")
        elif component in {"FAQ", "Safety Accordion"}:
            for slot in slots or ["content"]:
                lines.append(f"    with st.expander({_python_literal(slot.replace('_', ' ').title())}):")
                lines.append(f"        st.write({_python_literal(slot + ' content goes here.')})")
        elif component == "FeatureGrid":
            lines.append("    col1, col2, col3 = st.columns(3)")
            lines.append("    col1.info('Card 1')")
            lines.append("    col2.info('Card 2')")
            lines.append("    col3.info('Card 3')")
        elif component == "CTA Block":
            lines.append(f"    st.write({_python_literal(props.get('body', 'Guide the user to the next step.'))})")
            lines.append(f"    st.button({_python_literal(props.get('ctaLabel', 'Continue'))}, key={_python_literal(section.get('section_id', 'cta'))})")
        elif component == "Disclaimer Footer":
            lines.append("    st.caption('Legal and privacy disclaimer copy.')")
            if props.get("showPrivacyLink"):
                lines.append("    st.markdown('[Privacy Policy](#)')")
        else:
            lines.append(f"    st.write({_python_literal(component + ' content placeholder')})")

        if props:
            lines.append(f"    st.json({_python_literal(props)})")

        if notes:
            lines.append("    st.markdown('**Accessibility Notes**')")
            for note in notes:
                lines.append(f"    st.write({_python_literal('- ' + note)})")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _llm_enrich_variants(
    brief: str,
    requirements: Dict[str, Any],
    variants: List[Dict[str, Any]],
    retrieved: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Ask Gemini for context-aware variant descriptions and per-component content guidance.
    Returns a dict keyed by strategy_key, or None if unavailable or on any error.
    """
    if not is_available():
        return None
    try:
        template = load_prompt("generate_blueprint.txt")
        all_component_names = sorted(
            {c["component_name"] for v in variants for c in v.get("components", [])}
        )
        prompt = (
            template
            .replace("{brief}", brief or "")
            .replace("{audience}", requirements.get("audience") or "general")
            .replace("{market}", requirements.get("market") or "global")
            .replace("{industry}", requirements.get("industry") or "general")
            .replace("{compliance_sensitivity}", requirements.get("compliance_sensitivity") or "Low")
            .replace("{component_names}", json.dumps(all_component_names))
        )
        raw = generate_json(prompt)
        if not raw:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


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

        # Enforce composition ordering constraints by construction so generated
        # artefacts satisfy the same rules the composition validator enforces.
        # Hero must lead; Disclaimer Footer must close.
        if "Hero" in order:
            order.remove("Hero")
            order.insert(0, "Hero")
        if "Disclaimer Footer" in order:
            order.remove("Disclaimer Footer")
            order.append("Disclaimer Footer")

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
                "rationale": f"Selected by strategy {strategy['label']}",  # overwritten by LLM below
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

    # ── LLM enrichment (best-effort; falls back to rule-based values) ────────
    brief_text = requirements.get("brief", "")
    enrichment = _llm_enrich_variants(brief_text, requirements, variants, retrieved)

    if enrichment:
        for variant in variants:
            skey = variant.get("strategy_key", "")
            vdata = enrichment.get(skey) or {}
            if vdata.get("description"):
                variant["description"] = vdata["description"]
            if vdata.get("content_guidance"):
                variant["content_guidance"] = vdata["content_guidance"]
            comp_summaries: Dict[str, str] = vdata.get("component_summaries") or {}
            for comp in variant.get("components", []):
                cname = comp.get("component_name", "")
                if comp_summaries.get(cname):
                    comp["content_summary"] = comp_summaries[cname]
                    comp["rationale"] = comp_summaries[cname]

    if enrichment:
        # Summarise the LLM's per-strategy descriptions into pattern_reasoning
        pattern_reasoning = [
            next(
                (
                    enrichment[skey]["description"]
                    for skey in ("conversion_first", "content_rich", "conservative")
                    if isinstance(enrichment.get(skey), dict) and enrichment[skey].get("description")
                ),
                "Variants generated to explore different tradeoffs between conversion, content depth, and legal conservatism.",
            ),
            f"Based on brand={requirements.get('brand')} and market={requirements.get('market')}",
            "Fit score is a weighted heuristic (evidence match + structure coverage + brief alignment), not a conversion-rate prediction.",
        ]
        # Collect handoff notes from the best-fit strategy for page blueprints
        handoff_from_llm = next(
            (
                enrichment[skey].get("handoff_notes")
                for skey in ("conversion_first", "content_rich", "conservative")
                if isinstance(enrichment.get(skey), dict) and enrichment[skey].get("handoff_notes")
            ),
            None,
        )
    else:
        pattern_reasoning = [
            "Variants generated to explore different tradeoffs between conversion, content depth, and legal conservatism.",
            f"Based on brand={requirements.get('brand')} and market={requirements.get('market')}",
            "Fit score is a weighted heuristic (evidence match + structure coverage + brief alignment), not a conversion-rate prediction.",
        ]
        handoff_from_llm = None

    strategy_definitions = {
        s["label"]: s["description"] for s in STRATEGIES
    }

    # Update handoff_notes in page blueprints if LLM provided them
    page_blueprints = [_build_page_blueprint(variant, requirements) for variant in variants]
    if handoff_from_llm:
        for bp in page_blueprints:
            bp["handoff_notes"] = handoff_from_llm
    component_compositions = [_build_component_composition(blueprint) for blueprint in page_blueprints]

    best_variant = max(
        variants,
        key=lambda variant: variant.get("fit_score", 0.0) if isinstance(variant.get("fit_score", 0.0), (int, float)) else 0.0,
        default=variants[0] if variants else {},
    )
    best_page_blueprint = next(
        (blueprint for blueprint in page_blueprints if blueprint.get("variant_name") == best_variant.get("pattern_name")),
        page_blueprints[0] if page_blueprints else {},
    )

    page_spec = {
        "page_type": best_page_blueprint.get("page_type", requirements.get("content_type", "LandingPage")),
        "route": best_page_blueprint.get("route", "/page/default"),
        "layout": [
            {
                "component": section.get("component"),
                "props": section.get("props", {}),
                "accessibility_notes": section.get("accessibility_notes", []),
                "layout_role": section.get("layout_role"),
                "data_dependencies": section.get("data_dependencies", []),
            }
            for section in best_page_blueprint.get("sections", [])
        ],
    }

    code_templates = {
        "recommended_variant": best_variant.get("pattern_name", "Untitled Variant"),
        "react_tsx": _build_react_template(best_page_blueprint) if best_page_blueprint else "",
        "html": _build_html_template(best_page_blueprint) if best_page_blueprint else "",
        "streamlit_py": _build_streamlit_template(best_page_blueprint) if best_page_blueprint else "",
    }

    result = {
        "requirements": {
            "audience": requirements.get("audience"),
            "market": requirements.get("market"),
            "brand": requirements.get("brand"),
            "content_type": requirements.get("content_type"),
            "compliance_sensitivity": requirements.get("compliance_sensitivity"),
            "industry": requirements.get("industry"),
            "key_goals": requirements.get("key_goals"),
            "brand_tone": requirements.get("brand_tone"),
        },
        "pattern_reasoning": pattern_reasoning,
        "strategy_definitions": strategy_definitions,
        "variants": variants,
        "page_blueprints": page_blueprints,
        "component_compositions": component_compositions,
        "code_templates": code_templates,
        "human_review_required": ["designer", "compliance"] if requirements.get("compliance_sensitivity") == "High" else ["designer"],
        "page_specification": page_spec,
    }

    return result
