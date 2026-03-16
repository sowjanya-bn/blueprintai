import json
import hashlib
import streamlit as st
from src.blueprint import create_blueprint

st.set_page_config(
    page_title="BlueprintAI",
    page_icon="🧠",
    layout="wide"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.15rem;
    }

    [data-testid="stMetricLabel"] p {
        font-weight: 600;
    }

    .app-subtitle {
        margin-top: -0.2rem;
        color: #94a3b8;
        font-size: 0.98rem;
    }

    .approved-banner {
        padding: 0.85rem 1rem;
        border-radius: 12px;
        border: 1px solid rgba(34, 197, 94, 0.25);
        background: rgba(34, 197, 94, 0.08);
        margin-bottom: 1rem;
        font-weight: 600;
    }

    .section-caption {
        color: #94a3b8;
        margin-top: -0.35rem;
        margin-bottom: 0.8rem;
        font-size: 0.92rem;
    }

    .wireframe-box {
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.85rem;
        background: rgba(255, 255, 255, 0.02);
    }

    .wireframe-label {
        font-size: 0.8rem;
        font-weight: 700;
        color: #94a3b8;
        margin-bottom: 0.5rem;
        letter-spacing: 0.04em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "result" not in st.session_state:
    st.session_state.result = None

if "brief" not in st.session_state:
    st.session_state.brief = ""

if "approved_variant" not in st.session_state:
    st.session_state.approved_variant = None

if "flag_status" not in st.session_state:
    st.session_state.flag_status = {}

if "governance_issue_status" not in st.session_state:
    st.session_state.governance_issue_status = {}

if "review_gate_status" not in st.session_state:
    st.session_state.review_gate_status = {}


def safe_serialize_for_download(obj):
    """Return a bytes/str suitable for Streamlit download_button.

    - bytes/bytearray returned as-is
    - str returned as-is
    - dict/list/other serialized to pretty JSON where possible
    - fallback to str()
    """
    if obj is None:
        return ""
    if isinstance(obj, (bytes, bytearray)):
        return obj
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, indent=2)
    except Exception:
        try:
            return str(obj)
        except Exception:
            return ""


def blueprint_to_markdown(result: dict) -> str:
    md = "# Blueprint Plan\n\n"

    requirements = result.get("requirements", {})
    if requirements:
        md += "## Requirements\n"
        for k, v in requirements.items():
            md += f"- **{k}**: {v}\n"

    variants = result.get("variants", [])
    if variants:
        md += "\n## Variants\n"
        for variant in variants:
            md += f"\n### {variant.get('pattern_name', 'Untitled Variant')}\n"
            md += f"{variant.get('description', '')}\n\n"
            for comp in variant.get("components", []):
                md += f"- **{comp.get('component_name', 'Unknown')}**: {comp.get('content_summary', '')}\n"

    page_blueprints = result.get("page_blueprints", [])
    if page_blueprints:
        md += "\n## Page Blueprints\n"
        for blueprint in page_blueprints:
            md += f"\n### {blueprint.get('variant_name', 'Untitled Variant')}\n"
            md += f"- Route: {blueprint.get('route', 'N/A')}\n"
            for section in blueprint.get("sections", []):
                md += f"- {section.get('order')}. **{section.get('component')}** ({section.get('layout_role')})\n"

    code_templates = result.get("code_templates", {})
    if code_templates:
        md += "\n## Code Templates\n"
        md += f"- Recommended variant: {code_templates.get('recommended_variant', 'N/A')}\n"

    compliance = result.get("compliance_flags", {})
    compliance_items = compliance.get("flags", []) if isinstance(compliance, dict) else compliance
    if compliance_items:
        md += "\n## Compliance Flags\n"
        for flag in compliance_items:
            md += f"- **{flag.get('label', 'Flag')}** ({flag.get('severity', 'unknown')}): {flag.get('reason', flag.get('description', ''))}\n"

    return md


def render_requirements(requirements: dict):
    st.subheader("🧠 Extracted Requirements")
    st.markdown(
        '<div class="section-caption">What the system understood from the brief.</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Audience", requirements.get("audience", "N/A"))
    col2.metric("Market", requirements.get("market", "N/A"))
    col3.metric("Content Type", requirements.get("content_type", "N/A"))
    col4.metric("Compliance", requirements.get("compliance_sensitivity", "N/A"))


def render_summary(result: dict):
    st.subheader("📊 Generation Summary")
    st.markdown(
        '<div class="section-caption">A quick overview of what was generated.</div>',
        unsafe_allow_html=True,
    )

    variants = result.get("variants", [])
    compliance = result.get("compliance_flags", {})
    compliance_flags = compliance.get("flags", []) if isinstance(compliance, dict) else compliance
    component_count = sum(len(v.get("components", [])) for v in variants)

    col1, col2, col3 = st.columns(3)
    col1.metric("Variants Generated", len(variants))
    col2.metric("Components Suggested", component_count)
    col3.metric("Compliance Flags", len(compliance_flags))


def render_variant_card(variant: dict, idx: int):
    with st.container(border=True):

        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"### Variant {idx}: {variant.get('pattern_name', 'Untitled')}")

        with col2:
            if st.button("Approve", key=f"approve_variant_{idx}"):
                st.session_state.approved_variant = variant
                st.success("Variant approved!")

        render_variant_fit_score(variant, is_best=((idx - 1) == best_idx))

        st.write(variant.get("description", ""))

        st.markdown("**Page Flow**")

        flow = " → ".join(
            [c.get("component_name") for c in variant.get("components", [])]
        )

        st.markdown(f"**{flow}**")

        st.divider()

        for step, comp in enumerate(variant.get("components", []), start=1):

            with st.expander(f"{step}. {comp.get('component_name', 'Component')}"):

                st.write(comp.get("content_summary", ""))
                st.caption(comp.get("rationale", ""))

                conf = comp.get("confidence", 0)

                if isinstance(conf, (int, float)):
                    st.metric("Confidence", f"{conf:.2f}")


def render_compliance_flags(flags: list[dict]):
    st.subheader("⚠ Compliance Flags")
    st.markdown(
        '<div class="section-caption">Checks and concerns that may require governance review.</div>',
        unsafe_allow_html=True,
    )

    if not flags:
        st.success("No compliance flags detected.")
        return

    for flag in flags:
        st.warning(f"**{flag.get('type', 'flag')}**\n\n{flag.get('description', '')}")


def render_human_review(review_items: list[str]):
    st.subheader("👥 Human Review Required")
    st.markdown(
        '<div class="section-caption">Stakeholders who should validate the blueprint before delivery.</div>',
        unsafe_allow_html=True,
    )

    if not review_items:
        st.success("No additional human review steps listed.")
        return

    cols = st.columns(len(review_items)) if len(review_items) <= 4 else None

    if cols:
        for col, item in zip(cols, review_items):
            with col:
                st.info(item)
    else:
        for item in review_items:
            st.info(item)


def render_page_spec(page_spec: dict):
    st.subheader("🧩 Developer Handoff")
    st.markdown(
        '<div class="section-caption">Implementation-oriented page structure for engineering teams.</div>',
        unsafe_allow_html=True,
    )

    if not page_spec:
        st.info("Developer handoff will be shown here once generated.")
        return

    st.markdown(f"**Page Type:** {page_spec.get('page_type', 'N/A')}")
    if page_spec.get("route"):
        st.markdown(f"**Route:** {page_spec.get('route')}")

    layout = page_spec.get("layout", [])
    if not layout:
        st.info("No page specification returned.")
        return

    cols = st.columns(2)

    for idx, block in enumerate(layout, start=1):
        component_name = block.get("component", "Unknown Component")

        with cols[(idx - 1) % 2]:
            with st.expander(f"{idx}. {component_name}", expanded=False):
                props = block.get("props", {})
                notes = block.get("accessibility_notes", [])

                if props:
                    st.markdown("**Props**")
                    for key, value in props.items():
                        st.write(f"- **{key}**: {value}")

                if block.get("layout_role"):
                    st.markdown(f"**Layout Role:** {block.get('layout_role')}")

                data_dependencies = block.get("data_dependencies", [])
                if data_dependencies:
                    st.markdown("**Data Dependencies**")
                    for item in data_dependencies:
                        st.write(f"- {item}")

                if notes:
                    st.markdown("**Accessibility Notes**")
                    for note in notes:
                        st.write(f"- {note}")


def render_page_blueprints(page_blueprints: list[dict]):
    st.subheader("🗺️ Page Blueprints")
    st.markdown(
        '<div class="section-caption">Page-level section maps for each generated variant.</div>',
        unsafe_allow_html=True,
    )

    if not page_blueprints:
        st.info("Page blueprints will appear here once generated.")
        return

    blueprint_tabs = st.tabs([bp.get("variant_name", f"Variant {idx + 1}") for idx, bp in enumerate(page_blueprints)])
    for tab, blueprint in zip(blueprint_tabs, page_blueprints):
        with tab:
            st.markdown(f"**Route:** {blueprint.get('route', 'N/A')}")
            st.markdown(f"**Page Type:** {blueprint.get('page_type', 'N/A')}")
            for section in blueprint.get("sections", []):
                with st.expander(f"{section.get('order')}. {section.get('component')}", expanded=False):
                    st.write(section.get("summary", ""))
                    st.markdown(f"**Layout Role:** {section.get('layout_role', 'content-block')}")
                    slots = section.get("content_slots", [])
                    if slots:
                        st.markdown("**Content Slots**")
                        for slot in slots:
                            st.write(f"- {slot}")
                    dependencies = section.get("data_dependencies", [])
                    if dependencies:
                        st.markdown("**Data Dependencies**")
                        for item in dependencies:
                            st.write(f"- {item}")
                    notes = section.get("accessibility_notes", [])
                    if notes:
                        st.markdown("**Accessibility Notes**")
                        for note in notes:
                            st.write(f"- {note}")


def render_component_compositions(component_compositions: list[dict]):
    st.subheader("🧱 Component Compositions")
    st.markdown(
        '<div class="section-caption">Implementation-ready component stack showing order, dependencies, props, and content slots.</div>',
        unsafe_allow_html=True,
    )

    if not component_compositions:
        st.info("Component compositions will appear here once generated.")
        return

    composition_tabs = st.tabs([comp.get("variant_name", f"Variant {idx + 1}") for idx, comp in enumerate(component_compositions)])
    for tab, composition in zip(composition_tabs, component_compositions):
        with tab:
            rows = []
            for item in composition.get("components", []):
                rows.append(
                    {
                        "position": item.get("position"),
                        "component": item.get("component"),
                        "role": item.get("composition_role"),
                        "depends_on": ", ".join(item.get("depends_on", [])),
                        "slots": ", ".join(item.get("content_slots", [])),
                    }
                )
            st.dataframe(rows, use_container_width=True)

            for item in composition.get("components", []):
                with st.expander(f"{item.get('position')}. {item.get('component')}"):
                    props = item.get("props", {})
                    if props:
                        st.markdown("**Props**")
                        for key, value in props.items():
                            st.write(f"- **{key}**: {value}")
                    dependencies = item.get("data_dependencies", [])
                    if dependencies:
                        st.markdown("**Data Dependencies**")
                        for dep in dependencies:
                            st.write(f"- {dep}")


def render_code_templates(code_templates: dict):
    st.subheader("💻 Code Templates")
    st.markdown(
        '<div class="section-caption">Starter implementation templates for the recommended variant.</div>',
        unsafe_allow_html=True,
    )

    if not code_templates:
        st.info("Code templates will appear here once generated.")
        return

    st.markdown(f"**Recommended Variant:** {code_templates.get('recommended_variant', 'N/A')}")
    template_tab1, template_tab2, template_tab3 = st.tabs(["React TSX", "HTML", "Streamlit"])
    with template_tab1:
        st.code(code_templates.get("react_tsx", ""), language="tsx")
    with template_tab2:
        st.code(code_templates.get("html", ""), language="html")
    with template_tab3:
        st.code(code_templates.get("streamlit_py", ""), language="python")


def render_evidence(evidence_items: list[dict]):
    st.subheader("🔍 Evidence Used")
    st.markdown(
        '<div class="section-caption">Retrieved design-system evidence used to support recommendations.</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    if not st.session_state.result:

        with col1:
            st.button("Download JSON", disabled=True, width="stretch")
        with col2:
            st.button("Download MD", disabled=True, width="stretch")

    else:

        with col1:
            st.download_button(
                "Download JSON",
                data=safe_serialize_for_download(st.session_state.result),
                file_name="blueprint_plan.json",
                mime="application/json",
                width="stretch",
            )

        with col2:
            md_plan = blueprint_to_markdown(st.session_state.result)
            st.download_button(
                "Download MD",
                data=safe_serialize_for_download(md_plan),
                file_name="blueprint_plan.md",
                mime="text/markdown",
                width="stretch",
            )

    if not evidence_items:
        st.info("No evidence retrieved.")
        return

    for item in evidence_items:
        comp = item.get("component", {})
        score = item.get("score", 0.0)
        evidence = item.get("evidence", "")

        with st.expander(f"{comp.get('name', 'Unknown')}  •  relevance {score:.2f}"):
            st.markdown(f"**Purpose:** {comp.get('purpose', 'N/A')}")

            use_when = comp.get("use_when", [])
            avoid_when = comp.get("avoid_when", [])
            acc_notes = comp.get("accessibility_notes", [])

            if use_when:
                st.markdown("**Use when**")
                for use_item in use_when:
                    st.write(f"- {use_item}")

            if avoid_when:
                st.markdown("**Avoid when**")
                for avoid_item in avoid_when:
                    st.write(f"- {avoid_item}")

            if acc_notes:
                st.markdown("**Accessibility notes**")
                for acc_item in acc_notes:
                    st.write(f"- {acc_item}")

            st.markdown("**Retrieved Evidence Text**")
            st.code(evidence, language="text")


def explainability_to_markdown(expl: dict) -> str:
    md = "# Explainability Report\n\n"
    if not expl:
        return md + "No explainability records."

    for rec in expl.get("records", []):
        md += f"## {rec.get('decision')}\n"
        md += f"- id: {rec.get('id')}\n"
        md += f"- confidence: {rec.get('confidence')}\n"
        if rec.get('rationale'):
            md += f"- rationale: {rec.get('rationale')}\n"
        if rec.get('evidence'):
            md += "- evidence:\n"
            for e in rec.get('evidence'):
                md += f"  - {e}\n"
        if rec.get('rules_applied'):
            md += "- rules_applied:\n"
            for r in rec.get('rules_applied'):
                md += f"  - {r}\n"
        if rec.get('linked_components'):
            md += "- linked_components: " + ", ".join([str(x) for x in rec.get('linked_components')]) + "\n"
        md += "\n"

    return md

def render_pattern_reasoning(result: dict):
    reasons = result.get("pattern_reasoning", [])
    strategy_definitions = result.get("strategy_definitions", {})

    if not reasons and not strategy_definitions:
        return

    st.subheader("🧠 Why this page pattern?")
    st.caption("Explanation of how the system mapped the brief to a page structure.")

    for reason in reasons:
        st.write(f"• {reason}")

    if strategy_definitions:
        st.markdown("**Variant strategy meanings**")
        for name, definition in strategy_definitions.items():
            st.write(f"• **{name}**: {definition}")


def compute_risk_score(count):
    if count == 0:
        return 1.0, "Low"
    elif count <= 2:
        return 0.7, "Medium"
    else:
        return 0.4, "High"


def get_flag_id(flag: dict, idx: int) -> str:
    base = "|".join([
        str(flag.get("policy_id", "")),
        str(flag.get("matched_brief_text", "")),
        str(flag.get("matched_policy_example", "")),
        str(idx),
    ])
    return hashlib.md5(base.encode("utf-8")).hexdigest()[:12]


def get_flag_groups(flags: dict) -> dict:
    grouped = {}
    for flag in flags.get("flags", []):
        key = flag.get("review_type", "unknown")
        grouped.setdefault(key, []).append(flag)
    return grouped


def normalize_label(value: str) -> str:
    return value.replace("_", " ").title() if value else "Unknown"


def render_compliance_summary(flags):

    st.subheader("⚖️ Compliance Risk Assessment")

    grouped_flags = get_flag_groups(flags)
    if not grouped_flags:
        st.success("No compliance risks detected.")
        return

    severity_rank = {"high": 3, "medium": 2, "low": 1}
    badge_styles = {
        "high": ("#4b1d1d", "#ff8a8a", "High"),
        "medium": ("#4b3915", "#ffd37a", "Medium"),
        "low": ("#183824", "#7ef2b3", "Low"),
    }

    for review_type, items in grouped_flags.items():
        highest_severity = max(
            (item.get("severity", "low") for item in items),
            key=lambda s: severity_rank.get(s, 0),
        )
        bg, fg, label = badge_styles.get(highest_severity, badge_styles["low"])

        left, right = st.columns([5, 1])
        with left:
            st.markdown(f"**{normalize_label(review_type)}**")
        with right:
            st.markdown(
                f"""
                <div style="
                    background:{bg};
                    color:{fg};
                    padding:6px 10px;
                    border-radius:999px;
                    text-align:center;
                    font-weight:600;
                    font-size:0.85rem;
                    width:100%;
                "">{label}</div>
                """,
                unsafe_allow_html=True,
            )


def render_compliance_flags(flags):

    st.subheader("⚠ Compliance Checks")

    flag_items = flags.get("flags", []) if isinstance(flags, dict) else flags
    if not flag_items:
        st.success("No compliance risks detected.")
        return

    for idx, flag in enumerate(flag_items):
        flag_id = get_flag_id(flag, idx)
        status = st.session_state.flag_status.get(flag_id, "open")

        with st.container(border=True):
            title = flag.get("label") or normalize_label(flag.get("policy_id", "flag"))
            severity = flag.get("severity", "unknown").title()
            confidence = flag.get("confidence", "unknown").title()

            st.markdown(f"### {title}")
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            meta_col1.caption(f"Severity: {severity}")
            meta_col2.caption(f"Confidence: {confidence}")
            meta_col3.caption(f"Status: {status.replace('_', ' ').title()}")

            st.write(flag.get("description", ""))

            if flag.get("matched_brief_text"):
                st.markdown("**Detected Text**")
                st.code(flag.get("matched_brief_text", ""), language="text")

            if flag.get("matched_policy_example"):
                st.markdown("**Matched Pattern**")
                st.caption(flag.get("matched_policy_example", ""))

            if flag.get("reason"):
                st.markdown("**Why this was flagged**")
                st.write(flag.get("reason", ""))

            st.markdown("**Recommended Action**")
            st.write("• Review wording with compliance team")
            if flag.get("review_type") == "safety_review":
                st.write("• Validate side-effect and safety language before approval")
            elif flag.get("review_type") == "medical_legal_review":
                st.write("• Confirm treatment benefit wording is medically and legally approved")
            else:
                st.write("• Ensure regulatory language is approved")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Mark Reviewed", key=f"review_flag_{flag_id}", use_container_width=True):
                    st.session_state.flag_status[flag_id] = "reviewed"
                    st.rerun()
            with col2:
                if st.button("Waive", key=f"waive_flag_{flag_id}", use_container_width=True):
                    st.session_state.flag_status[flag_id] = "waived"
                    st.rerun()
            with col3:
                if st.button("Needs Fix", key=f"fix_flag_{flag_id}", use_container_width=True):
                    st.session_state.flag_status[flag_id] = "needs_fix"
                    st.rerun()


def render_compliance_status(flags):

    st.subheader("Compliance Status")

    flag_items = flags.get("flags", []) if isinstance(flags, dict) else flags
    if not flag_items:
        st.success("✔ Ready for publication")
        return

    statuses = [
        st.session_state.flag_status.get(get_flag_id(flag, idx), "open")
        for idx, flag in enumerate(flag_items)
    ]

    resolved = sum(1 for status in statuses if status != "open")
    progress = resolved / len(flag_items) if flag_items else 1.0
    st.progress(progress)
    st.caption(f"Review progress: {resolved}/{len(flag_items)} flags resolved")

    if "needs_fix" in statuses:
        st.error("🚨 Content changes required before approval")
    elif "open" in statuses:
        st.warning("⚠ Pending compliance review")
    else:
        st.success("✅ Compliance review completed")


def render_composition_report(composition_report: dict, component_compositions: list):
    st.subheader("🧱 Composition Validation")
    st.markdown(
        '<div class="section-caption">Structural ordering, pairing, and brand policy rules across all generated compositions.</div>',
        unsafe_allow_html=True,
    )

    if not composition_report:
        st.info("No composition report available.")
        return

    passed = composition_report.get("passed", False)
    issues = composition_report.get("issues", [])
    fail_issues = [i for i in issues if i.get("status") == "FAIL"]
    warn_issues = [i for i in issues if i.get("status") == "WARN"]

    status_col, meta_col = st.columns([1, 3])
    with status_col:
        if passed:
            st.success("✅ All composition rules passed")
        else:
            st.error(f"❌ {len(fail_issues)} rule violation(s)")
    with meta_col:
        total_components = sum(len(c.get("components", [])) for c in component_compositions)
        warn_label = f"  ·  {len(warn_issues)} warning(s)" if warn_issues else ""
        st.markdown(
            f"**{len(component_compositions)}** composition(s) · **{total_components}** component(s) total{warn_label}"
        )

    if component_compositions:
        st.markdown("**Composition Order by Variant**")
        for composition in component_compositions:
            comps = composition.get("components", [])
            names = [item.get("component", "?") for item in comps]
            route = composition.get("route", "N/A")
            with st.expander(f"{composition.get('variant_name', 'Variant')}  ·  `{route}`"):
                for pos, name in enumerate(names, start=1):
                    if pos == 1 and name == "Hero":
                        icon = "🟢"
                    elif name == "Disclaimer Footer" and pos == len(names):
                        icon = "🔵"
                    elif name == "Disclaimer Footer":
                        icon = "🔴"
                    else:
                        icon = "⚪"
                    st.markdown(f"{icon} **{pos}.** {name}")

    if fail_issues:
        st.markdown("**Rule Violations**")
        for issue in fail_issues:
            with st.expander(f"🚨 {issue.get('title')}  —  {issue.get('severity', '').title()}"):
                st.markdown(f"**Rule:** `{issue.get('rule_triggered')}`")
                st.write(issue.get("description"))
                if issue.get("evidence"):
                    st.code(issue.get("evidence"), language="text")
                st.markdown(f"**Fix:** {issue.get('suggested_fix')}")
                if issue.get("human_review_required"):
                    st.warning("Human review required")

    if warn_issues:
        st.markdown("**Warnings**")
        for issue in warn_issues:
            with st.expander(f"⚠ {issue.get('title')}  —  {issue.get('severity', '').title()}"):
                st.markdown(f"**Rule:** `{issue.get('rule_triggered')}`")
                st.write(issue.get("description"))
                if issue.get("evidence"):
                    st.code(issue.get("evidence"), language="text")
                st.markdown(f"**Fix:** {issue.get('suggested_fix')}")

    if not issues:
        st.success("No composition issues detected.")


def render_validation_summary(reports: dict):
    st.subheader("🔎 Validation Summary")
    st.markdown(
        '<div class="section-caption">High-level pass/fail across validators and actionable issues.</div>',
        unsafe_allow_html=True,
    )

    if not reports:
        st.info("No validation reports available.")
        return

    # Determine pass/fail per validator
    pass_list = [name for name, r in reports.items() if r.get("passed")]
    fail_list = [name for name, r in reports.items() if not r.get("passed")]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Passing Validators**")
        if pass_list:
            for p in pass_list:
                st.success(p.title())
        else:
            st.info("None")

    with col2:
        st.markdown("**Failing/Attention Validators**")
        if fail_list:
            for f in fail_list:
                st.error(f.title())
        else:
            st.info("None")

    # Show detailed failing issues grouped by validator
    st.divider()
    st.markdown("**Details: Failing Issues**")
    any_fail = False
    for name, r in reports.items():
        issues = r.get("issues", [])
        failing = [i for i in issues if i.get("status") == "FAIL"]
        if not failing:
            continue
        any_fail = True
        with st.expander(f"{name.title()} — {len(failing)} failing issue(s)"):
            for idx, issue in enumerate(failing, start=1):
                st.markdown(f"**{idx}. {issue.get('title')}**  —  {issue.get('severity', '').title()}")
                st.write(issue.get("description"))
                st.markdown(f"**Rule:** {issue.get('rule_triggered')}")
                if issue.get("evidence"):
                    st.markdown("**Evidence**")
                    st.code(issue.get("evidence"), language="text")
                st.markdown("**Suggested Fix**")
                st.write(issue.get("suggested_fix"))
                if issue.get("human_review_required"):
                    st.warning("Human review required")

    if not any_fail:
        st.success("No failing validation issues detected.")


def count_validation_failures(reports: dict) -> int:
    if not reports:
        return 0
    return sum(
        1
        for report in reports.values()
        for issue in report.get("issues", [])
        if issue.get("status") == "FAIL"
    )


def count_validator_failures(reports: dict, validator_name: str) -> int:
    if not reports:
        return 0
    report = reports.get(validator_name, {}) or {}
    return sum(1 for issue in report.get("issues", []) if issue.get("status") == "FAIL")


def count_unresolved_compliance_flags(flags) -> int:
    flag_items = flags.get("flags", []) if isinstance(flags, dict) else flags
    unresolved = 0
    for idx, flag in enumerate(flag_items):
        status = st.session_state.flag_status.get(get_flag_id(flag, idx), "open")
        if status in {"open", "needs_fix"}:
            unresolved += 1
    return unresolved


def get_governance_issue_id(issue: dict, idx: int) -> str:
    category = str(issue.get("category", "other")).strip().lower().replace(" ", "_")
    title = str(issue.get("title", f"issue_{idx}")).strip().lower().replace(" ", "_")
    component = str(issue.get("affected_component", "")).strip().lower().replace(" ", "_")
    return f"{category}:{title}:{component}:{idx}"


def count_unresolved_governance_issues(issues: list[dict]) -> int:
    unresolved = 0
    for idx, issue in enumerate(issues or []):
        issue_id = get_governance_issue_id(issue, idx)
        status = st.session_state.governance_issue_status.get(issue_id, "open")
        if status in {"open", "needs_fix"}:
            unresolved += 1
    return unresolved


def get_gate_blockers(result: dict, gate_id: str) -> list[str]:
    blockers: list[str] = []
    architecture_plan = result.get("architecture_plan") or {}
    validation_reports = result.get("validation_reports") or {}
    compliance_flags = result.get("compliance_flags") or {}
    governance_issues = result.get("governance_issues") or []
    approved_variant = st.session_state.get("approved_variant")
    gate_status = st.session_state.get("review_gate_status", {})

    validation_failures = count_validation_failures(validation_reports)
    security_failures = count_validator_failures(validation_reports, "security")
    unresolved_compliance = count_unresolved_compliance_flags(compliance_flags)
    unresolved_governance = count_unresolved_governance_issues(governance_issues)

    if gate_id == "architecture_review":
        if not architecture_plan:
            blockers.append("Architecture plan has not been generated.")
        if not architecture_plan.get("service_flow"):
            blockers.append("Service-to-service flow is missing.")
        if not architecture_plan.get("services"):
            blockers.append("Core services are not defined.")

    if gate_id == "ux_review" and not approved_variant:
        blockers.append("No variant has been approved in the Variants tab.")

    if gate_id == "validation_review":
        if validation_failures > 0:
            blockers.append(f"{validation_failures} failing validation issue(s) remain.")
        if unresolved_compliance > 0:
            blockers.append(f"{unresolved_compliance} compliance flag(s) are unresolved.")
        if unresolved_governance > 0:
            blockers.append(f"{unresolved_governance} governance issue(s) still need review.")

    if gate_id == "platform_review":
        if gate_status.get("architecture_review") != "approved":
            blockers.append("Architecture Review must be approved first.")
        if not architecture_plan.get("environment_promotion_policy"):
            blockers.append("Environment promotion policy is missing.")
        if not architecture_plan.get("rollback_strategy"):
            blockers.append("Rollback strategy is missing.")
        if not architecture_plan.get("monitoring_checklist"):
            blockers.append("Monitoring checklist is missing.")

    if gate_id == "security_review":
        if security_failures > 0:
            blockers.append(f"{security_failures} failing security issue(s) remain.")
        if not architecture_plan.get("security_controls"):
            blockers.append("Security controls are not defined in the architecture plan.")

    if gate_id == "deployment_approval":
        for prerequisite in ["architecture_review", "ux_review", "validation_review", "platform_review", "security_review"]:
            if gate_status.get(prerequisite) != "approved":
                blockers.append(f"{prerequisite.replace('_', ' ').title()} is not approved.")
        if validation_failures > 0:
            blockers.append("Deployment blocked by failing validations.")
        if unresolved_compliance > 0:
            blockers.append("Deployment blocked by unresolved compliance flags.")
        if unresolved_governance > 0:
            blockers.append("Deployment blocked by unresolved governance findings.")
        if security_failures > 0:
            blockers.append("Deployment blocked by failing security findings.")

    return blockers


def render_architecture_plan(plan: dict):
    st.subheader("🏗️ Architecture Plan")
    st.markdown(
        '<div class="section-caption">Large-scale system view covering services, deployment model, and release controls.</div>',
        unsafe_allow_html=True,
    )

    if not plan:
        st.info("Architecture plan will appear here after blueprint generation.")
        return

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Domain", str(plan.get("domain", "general")).title())
    metric_col2.metric("Market", plan.get("market", "global"))
    metric_col3.metric("Core Services", len(plan.get("services", [])))

    st.markdown(f"**Architecture Style:** {plan.get('architecture_style', 'N/A')}")
    st.write(plan.get("system_summary", ""))

    if plan.get("frontend_pattern"):
        st.markdown(f"**Frontend Pattern:** {plan.get('frontend_pattern')}")

    if plan.get("services"):
        st.markdown("**Core Services**")
        for service in plan.get("services", []):
            with st.expander(service.get("name", "Service")):
                st.write(service.get("responsibility", ""))
                st.caption(service.get("scale_note", ""))

    if plan.get("service_flow"):
        st.markdown("**Service-to-Service Flow**")
        for flow in plan.get("service_flow", []):
            with st.expander(flow.get("step", "Flow Step")):
                st.write(flow.get("summary", ""))

    if plan.get("data_stores"):
        st.markdown("**Data Stores**")
        for item in plan.get("data_stores", []):
            st.write(f"- {item}")

    if plan.get("deployment_model"):
        st.markdown("**Deployment Model**")
        for item in plan.get("deployment_model", []):
            st.write(f"- {item}")

    if plan.get("environment_promotion_policy"):
        st.markdown("**Environment Promotion Policy**")
        for item in plan.get("environment_promotion_policy", []):
            st.write(f"- {item}")

    if plan.get("rollback_strategy"):
        st.markdown("**Rollback Strategy**")
        for item in plan.get("rollback_strategy", []):
            st.write(f"- {item}")

    if plan.get("monitoring_checklist"):
        st.markdown("**Monitoring Checklist**")
        for item in plan.get("monitoring_checklist", []):
            st.write(f"- {item}")

    controls_col1, controls_col2 = st.columns(2)
    with controls_col1:
        if plan.get("platform_controls"):
            st.markdown("**Platform Controls**")
            for item in plan.get("platform_controls", []):
                st.write(f"- {item}")
    with controls_col2:
        if plan.get("security_controls"):
            st.markdown("**Security Controls**")
            for item in plan.get("security_controls", []):
                st.write(f"- {item}")

    if plan.get("non_functional_requirements"):
        st.markdown("**Non-Functional Requirements**")
        for item in plan.get("non_functional_requirements", []):
            st.write(f"- {item}")


def render_review_checkpoints(result: dict):
    st.subheader("✅ Review Checkpoints")
    st.markdown(
        '<div class="section-caption">Explicit approval gates for architecture, UX, validation, and deployment.</div>',
        unsafe_allow_html=True,
    )

    plan = result.get("architecture_plan") or {}
    checkpoints = plan.get("approval_checkpoints", [])
    if not checkpoints:
        st.info("Approval checkpoints will appear here after architecture generation.")
        return

    gate_status = st.session_state.review_gate_status
    approved_count = sum(1 for gate in checkpoints if gate_status.get(gate.get("id")) == "approved")
    pending_count = len(checkpoints) - approved_count
    deployment_ready = not get_gate_blockers(result, "deployment_approval")

    c1, c2, c3 = st.columns(3)
    c1.metric("Approved Gates", approved_count)
    c2.metric("Pending Gates", pending_count)
    c3.metric("Deployment Ready", "Yes" if deployment_ready else "No")

    for gate in checkpoints:
        gate_id = gate.get("id")
        status = gate_status.get(gate_id, "pending")
        blockers = get_gate_blockers(result, gate_id)

        with st.container(border=True):
            header_col1, header_col2 = st.columns([4, 1])
            with header_col1:
                st.markdown(f"### {gate.get('label', gate_id)}")
                st.caption(f"Owner: {gate.get('owner', 'Review Team')}")
            with header_col2:
                st.metric("Status", status.replace("_", " ").title())

            st.write(gate.get("description", ""))

            if blockers:
                st.markdown("**Blocking Signals**")
                for blocker in blockers:
                    st.write(f"- {blocker}")
            else:
                st.success("No active blockers detected for this checkpoint.")

            action_col1, action_col2, action_col3 = st.columns(3)
            with action_col1:
                if st.button("Approve", key=f"gate_approve_{gate_id}", disabled=bool(blockers), use_container_width=True):
                    st.session_state.review_gate_status[gate_id] = "approved"
                    st.rerun()
            with action_col2:
                if st.button("Needs Changes", key=f"gate_changes_{gate_id}", use_container_width=True):
                    st.session_state.review_gate_status[gate_id] = "needs_changes"
                    st.rerun()
            with action_col3:
                if st.button("Reset", key=f"gate_reset_{gate_id}", use_container_width=True):
                    st.session_state.review_gate_status[gate_id] = "pending"
                    st.rerun()



def render_human_review(review_items):

    st.subheader("👥 Human Review Required")

    if not review_items:
        st.success("No additional review steps required.")
        return

    cols = st.columns(len(review_items))

    for col, item in zip(cols, review_items):

        with col:
            st.info(item)

def get_best_variant_index(variants: list[dict]) -> int | None:
    if not variants:
        return None

    scored = [
        (idx, v.get("fit_score", 0))
        for idx, v in enumerate(variants)
        if isinstance(v.get("fit_score", 0), (int, float))
    ]

    if not scored:
        return None

    return max(scored, key=lambda x: x[1])[0]


def render_variant_fit_score(variant: dict, is_best: bool = False):
    score = variant.get("fit_score", 0)

    if not isinstance(score, (int, float)):
        st.caption("Fit score unavailable")
        return

    score = max(0.0, min(float(score), 1.0))
    percent = int(score * 100)

    st.markdown(f"**Fit Score — {percent}%**")
    st.progress(score)
    st.caption("Heuristic fit to your brief, not a predicted conversion rate.")

    breakdown = variant.get("fit_score_breakdown", {})
    if isinstance(breakdown, dict) and breakdown:
        evidence = breakdown.get("evidence_match", 0)
        coverage = breakdown.get("structure_coverage", 0)
        alignment = breakdown.get("brief_alignment", 0)

        if isinstance(evidence, (int, float)) and isinstance(coverage, (int, float)) and isinstance(alignment, (int, float)):
            st.caption(
                "Breakdown: "
                f"evidence match {int(max(0.0, min(1.0, float(evidence))) * 100)}%, "
                f"structure coverage {int(max(0.0, min(1.0, float(coverage))) * 100)}%, "
                f"brief alignment {int(max(0.0, min(1.0, float(alignment))) * 100)}%."
            )

    if is_best:
        st.markdown(
            """
            <div style="
                background-color:#163d28;
                padding:8px 14px;
                border-radius:6px;
                font-weight:600;
                color:#7ef2b3;
            ">
            ⭐ Recommended Variant
            </div>
            """,
            unsafe_allow_html=True
        )

def render_variant_ranking(variants: list[dict]):
    st.subheader("🏁 Variant Ranking")
    st.caption("How well each page structure fits the brief.")

    if not variants:
        st.info("No variants available.")
        return

    ranked = sorted(
        variants,
        key=lambda v: v.get("fit_score", 0) if isinstance(v.get("fit_score", 0), (int, float)) else 0,
        reverse=True,
    )

    for rank, variant in enumerate(ranked, start=1):
        score = variant.get("fit_score", 0)
        score = max(0.0, min(float(score), 1.0)) if isinstance(score, (int, float)) else 0.0
        percent = int(round(score * 100))

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])

            with c1:
                st.markdown(f"**#{rank} {variant.get('pattern_name', 'Untitled Variant')}**")
                st.caption(variant.get("description", ""))

            with c2:
                st.metric("Fit", f"{percent}%")

            st.progress(score)

def render_wireframe_from_variant(variant: dict):
    st.subheader("🖼 Wireframe Preview")
    st.markdown(
        '<div class="section-caption">A visual mock layout generated from the approved blueprint.</div>',
        unsafe_allow_html=True,
    )

    components = variant.get("components", [])
    if not components:
        st.info("No components available for preview.")
        return

    for idx, comp in enumerate(components):
        name = comp.get("component_name", "Unknown Component")
        summary = comp.get("content_summary", "Component preview")

        if name == "Hero":
            with st.container(border=True):
                st.markdown('<div class="wireframe-label">HERO</div>', unsafe_allow_html=True)
                st.markdown("### Headline Placeholder")
                st.write("Supporting subheadline for the treatment or page purpose.")
                btn1, btn2 = st.columns([1, 4])
                with btn1:
                    st.button("CTA", key=f"hero_cta_{idx}_{name}")
                with btn2:
                    st.caption(summary)

        elif name == "Treatment Overview Cards":
            with st.container(border=True):
                st.markdown('<div class="wireframe-label">TREATMENT OVERVIEW CARDS</div>', unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                c1.info("Card 1")
                c2.info("Card 2")
                c3.info("Card 3")
                st.caption(summary)

        elif name == "Safety Accordion":
            with st.container(border=True):
                st.markdown('<div class="wireframe-label">SAFETY ACCORDION</div>', unsafe_allow_html=True)
                with st.expander("Possible side effects"):
                    st.write("Safety content preview")
                with st.expander("Warnings and precautions"):
                    st.write("Safety content preview")
                st.caption(summary)

        elif name == "FAQ":
            with st.container(border=True):
                st.markdown('<div class="wireframe-label">FAQ</div>', unsafe_allow_html=True)
                with st.expander("Common question 1"):
                    st.write("Answer preview")
                with st.expander("Common question 2"):
                    st.write("Answer preview")
                st.caption(summary)

        elif name == "CTA Block":
            with st.container(border=True):
                st.markdown('<div class="wireframe-label">CTA BLOCK</div>', unsafe_allow_html=True)
                st.write("Next-step guidance or conversion action.")
                st.button("Talk to a doctor", key=f"cta_{idx}_{name}")
                st.caption(summary)

        elif name == "Disclaimer Footer":
            with st.container(border=True):
                st.markdown('<div class="wireframe-label">DISCLAIMER FOOTER</div>', unsafe_allow_html=True)
                st.caption("Regulatory and legal disclaimer preview")
                st.caption(summary)

        else:
            with st.container(border=True):
                st.markdown(f'<div class="wireframe-label">{name.upper()}</div>', unsafe_allow_html=True)
                st.write(summary)


# Top action bar
title_col, action_col1 = st.columns([4, 1.2])

with title_col:
    st.title("🧠 BlueprintAI")
    st.markdown(
        '<div class="app-subtitle">AI-assisted page blueprint and compliance recommender</div>',
        unsafe_allow_html=True,
    )

with action_col1:
    st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
    generate_clicked = st.button("Generate Blueprint", type="primary", use_container_width=True)

# Global brief input
st.subheader("Describe the webpage you want to generate")
st.caption("Provide the audience, purpose and compliance sensitivity.")

brief = st.text_area(
    "Project brief",
    height=180,
    placeholder="Create a patient-facing webpage for a new migraine treatment in the UK...",
    value=st.session_state.brief,
)

if generate_clicked:
    if not brief.strip():
        st.warning("Please enter a brief.")
    else:
        st.session_state.brief = brief
        st.session_state.approved_variant = None
        st.session_state.flag_status = {}
        st.session_state.governance_issue_status = {}
        st.session_state.review_gate_status = {}

        with st.spinner("Generating blueprint..."):
            st.session_state.result = create_blueprint(brief)

        st.success("Blueprint generated. Open the tabs below to explore the output.")

if st.session_state.approved_variant:
    st.markdown(
        f"""
        <div class="approved-banner">
            Approved Variant: {st.session_state.approved_variant.get('pattern_name', 'Selected Variant')}
        </div>
        """,
        unsafe_allow_html=True,
    )

main_tabs = st.tabs(
    [
        "1️⃣ Blueprint",
        "2️⃣ Show Variants",
        "3️⃣ Compliance & Review",
        "4️⃣ Evidence",
        "5️⃣ Architecture & Handoff",
        "6️⃣ Wireframe Preview",
        "7️⃣ Knowledge Graph",
        "8️⃣ Governance",
        "9️⃣ Explainability",
    ]
)

with main_tabs[0]:
    if not st.session_state.result:
        st.info("Generate a blueprint to see extracted requirements and summary.")
    else:
        render_requirements(st.session_state.result.get("requirements", {}))
        st.divider()
        render_summary(st.session_state.result)

with main_tabs[1]:
    if not st.session_state.result:
        st.info("Generate a blueprint first.")
    else:
        st.subheader("📐 Blueprint Variants")

        render_pattern_reasoning(st.session_state.result)
        st.divider()
        st.markdown(
            '<div class="section-caption">Review the options and approve the best page structure.</div>',
            unsafe_allow_html=True,
        )

        variants = st.session_state.result.get("variants", [])

        # Sort variants by fit score (highest first)
        variants_sorted = sorted(
            variants,
            key=lambda v: v.get("fit_score", 0),
            reverse=True,
        )
        best_idx = get_best_variant_index(variants_sorted)

        variant_tabs = st.tabs(
            [v.get("pattern_name", f"Variant {i + 1}") for i, v in enumerate(variants_sorted)]
        )

        for i, (tab, variant) in enumerate(zip(variant_tabs, variants_sorted), start=1):
            with tab:
                render_variant_card(variant, i)

with main_tabs[2]:
    if not st.session_state.result:
        st.info("Generate a blueprint first.")
    else:
        flags = st.session_state.result.get("compliance_flags", {})
        review = st.session_state.result.get("human_review_required", [])

        render_compliance_summary(flags)

        st.divider()

        # Validation summary (Accessibility, Brand, Compliance, Security)
        validation_reports = st.session_state.result.get("validation_reports", {})
        render_validation_summary(validation_reports)

        st.divider()

        # Dedicated composition validation panel
        composition_report = validation_reports.get("composition", {})
        component_compositions = st.session_state.result.get("component_compositions", [])
        render_composition_report(composition_report, component_compositions)

        st.divider()

        render_compliance_flags(flags)

        st.divider()

        render_human_review(review)

        st.divider()

        render_compliance_status(flags)

with main_tabs[3]:
    if not st.session_state.result:
        st.info("Generate a blueprint first.")
    else:
        render_evidence(st.session_state.result.get("retrieved_evidence", []))

        with st.expander("Show full raw JSON"):
            st.json(st.session_state.result)

with main_tabs[4]:
    if not st.session_state.result:
        st.info("Generate a blueprint first.")
    else:
        render_architecture_plan(st.session_state.result.get("architecture_plan", {}))
        st.divider()
        render_review_checkpoints(st.session_state.result)
        st.divider()
        render_page_blueprints(st.session_state.result.get("page_blueprints", []))
        st.divider()
        render_component_compositions(st.session_state.result.get("component_compositions", []))
        st.divider()
        render_code_templates(st.session_state.result.get("code_templates", {}))
        st.divider()

        approved = st.session_state.get("approved_variant")

        if not approved:
            st.info("Approve a variant in the Variants tab to move toward developer handoff.")
        else:
            st.success(f"Using approved variant: {approved.get('pattern_name', 'Selected Variant')}")
            render_page_spec(st.session_state.result.get("page_specification", {}))
            st.caption("Ideally, developer handoff should be generated after blueprint approval.")
            # Ticket draft generation (Phase 7 starter)
            try:
                # prefer package-style import
                from src.ticket_generator import generate_ticket_drafts, tickets_to_markdown
            except Exception:
                # fallback: load module by path
                import importlib.util
                from pathlib import Path

                spec = importlib.util.spec_from_file_location(
                    "ticket_generator", Path.cwd() / "src" / "ticket_generator.py"
                )
                ticket_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ticket_mod)
                generate_ticket_drafts = ticket_mod.generate_ticket_drafts
                tickets_to_markdown = ticket_mod.tickets_to_markdown

            tickets = []
            try:
                tickets = generate_ticket_drafts(st.session_state.result or {})
            except Exception as e:
                st.warning(f"Ticket generation failed: {e}")

            if tickets:
                st.divider()
                st.subheader("🔧 Suggested Fixes & Ticket Drafts")
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.download_button("Download Tickets JSON", data=safe_serialize_for_download(tickets), file_name="tickets.json", mime="application/json")
                with col2:
                    md = tickets_to_markdown(tickets)
                    st.download_button("Download Tickets MD", data=safe_serialize_for_download(md), file_name="tickets.md", mime="text/markdown")

                # Phase 7: GitHub issue creation UI
                st.markdown("---")
                st.markdown("**Create GitHub issues from these ticket drafts**")
                gh_repo = st.text_input("GitHub repo (owner/repo)", key="gh_repo", value="")
                gh_token = st.text_input("GitHub token (optional — leave blank to use GITHUB_TOKEN env)", type="password", key="gh_token")
                dry_run = st.checkbox("Dry run — show payloads instead of creating issues", value=True, key="gh_dry_run")
                st.markdown("_Optional: map ticket category and severity to existing repo labels (provide JSON)_")
                col_map1, col_map2 = st.columns(2)
                with col_map1:
                    cat_map_text = st.text_area("Category -> Label mapping (JSON)", value=st.session_state.get("gh_cat_map", "{}"), key="gh_cat_map")
                with col_map2:
                    sev_map_text = st.text_area("Severity -> Label mapping (JSON)", value=st.session_state.get("gh_sev_map", "{}"), key="gh_sev_map")

                # Persistence controls for label mappings
                st.markdown("**Persist label mappings for this project**")
                save_col, load_col = st.columns(2)
                label_map_path = ".blueprintai/label_mappings.json"
                import os
                import pathlib
                project_root = pathlib.Path.cwd()
                abs_label_map_path = project_root / label_map_path

                with save_col:
                    if st.button("Save mappings", key="save_label_mappings"):
                        try:
                            to_save = {
                                "category": cat_map_text,
                                "severity": sev_map_text
                            }
                            os.makedirs(abs_label_map_path.parent, exist_ok=True)
                            with open(abs_label_map_path, "w") as f:
                                json.dump(to_save, f, indent=2)
                            st.success(f"Mappings saved to {label_map_path}")
                        except Exception as e:
                            st.error(f"Failed to save mappings: {e}")

                with load_col:
                    if st.button("Load mappings", key="load_label_mappings"):
                        try:
                            if abs_label_map_path.exists():
                                with open(abs_label_map_path, "r") as f:
                                    loaded = json.load(f)
                                st.session_state["gh_cat_map"] = loaded.get("category", "{}")
                                st.session_state["gh_sev_map"] = loaded.get("severity", "{}")
                                st.success(f"Mappings loaded from {label_map_path}")
                            else:
                                st.warning(f"No mappings file found at {label_map_path}")
                        except Exception as e:
                            st.error(f"Failed to load mappings: {e}")

                confirm = st.checkbox("I confirm I want to create GitHub issues for these tickets", key="gh_confirm")
                create_btn = st.button("Create GitHub Issues", disabled=not confirm or not gh_repo)

                if create_btn:
                    try:
                        # dynamic import to avoid hard dependency at app import time
                        try:
                            from src.ticket_generator import create_github_issues_from_tickets
                        except Exception:
                            import importlib.util
                            from pathlib import Path
                            spec = importlib.util.spec_from_file_location(
                                "ticket_generator", Path.cwd() / "src" / "ticket_generator.py"
                            )
                            ticket_mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(ticket_mod)
                            create_github_issues_from_tickets = ticket_mod.create_github_issues_from_tickets

                        token_env = "GITHUB_TOKEN"
                        # If user provided a token in the widget, set it temporarily for the helper to pick up
                        if gh_token:
                            import os
                            os.environ[token_env] = gh_token

                        # parse mapping JSON
                        try:
                            cat_map = json.loads(cat_map_text) if cat_map_text else {}
                        except Exception as e:
                            st.error(f"Category mapping JSON parse error: {e}")
                            cat_map = {}
                        try:
                            sev_map = json.loads(sev_map_text) if sev_map_text else {}
                        except Exception as e:
                            st.error(f"Severity mapping JSON parse error: {e}")
                            sev_map = {}

                        if dry_run:
                            # show payloads instead of creating
                            st.info("Dry run: showing issue payloads — no issues will be created")
                            for t in tickets:
                                title = t.get("title")
                                body = '---\n' + (t.get('description') or '') + "\n\nSuggested fix:\n" + (t.get('suggested_fix') or '')
                                labels = []
                                cat = t.get("category")
                                sev = t.get("severity")
                                if cat:
                                    labels.append(cat_map.get(cat, cat))
                                if sev:
                                    labels.append(sev_map.get(sev, sev))
                                st.markdown(f"**{title}**")
                                st.json({"title": title, "body": body, "labels": labels})
                        else:
                            # If mappings provided, create issues per-ticket with mapped labels
                            use_custom_mapping = bool(cat_map) or bool(sev_map)
                            created = []
                            if use_custom_mapping:
                                try:
                                    try:
                                        from src.ticket_generator import create_github_issue
                                    except Exception:
                                        import importlib.util
                                        from pathlib import Path
                                        spec = importlib.util.spec_from_file_location(
                                            "ticket_generator", Path.cwd() / "src" / "ticket_generator.py"
                                        )
                                        ticket_mod = importlib.util.module_from_spec(spec)
                                        spec.loader.exec_module(ticket_mod)
                                        create_github_issue = ticket_mod.create_github_issue
                                    for t in tickets:
                                        title = t.get("title")
                                        try:
                                            body = ticket_mod._ticket_to_issue_body(t)
                                        except Exception:
                                            body = '---\n' + (t.get('description') or '') + "\n\nSuggested fix:\n" + (t.get('suggested_fix') or '')
                                        labels = []
                                        cat = t.get("category")
                                        sev = t.get("severity")
                                        if cat:
                                            mapped = cat_map.get(cat)
                                            labels.append(mapped if mapped is not None else cat)
                                        if sev:
                                            mapped = sev_map.get(sev)
                                            labels.append(mapped if mapped is not None else sev)
                                        try:
                                            issue = create_github_issue(gh_repo, title, body, labels=labels or None, token_env=token_env)
                                            created.append({"url": issue.get("html_url"), "number": issue.get("number"), "title": issue.get("title")})
                                        except Exception as e:
                                            created.append({"error": str(e), "title": title})
                                except Exception as e:
                                    st.error(f"Failed to create issues with mapping: {e}")
                            else:
                                with st.spinner("Creating GitHub issues..."):
                                    created = create_github_issues_from_tickets(tickets, gh_repo, token_env=token_env)

                            success_count = sum(1 for c in created if c.get("url"))
                            st.success(f"Created {success_count} issues ({len(created)-success_count} errors)")
                            for c in created:
                                if c.get("url"):
                                    st.markdown(f"- [{c.get('title')}]({c.get('url')})")
                                else:
                                    st.markdown(f"- Error creating '{c.get('title')}': {c.get('error')}")

                    except Exception as e:
                        st.error(f"Failed to create issues: {e}")

                for i, t in enumerate(tickets, start=1):
                    with st.expander(f"{i}. {t.get('title')}"):
                        st.markdown(f"**Category**: {t.get('category')}  —  **Severity**: {t.get('severity')}")
                        st.markdown("**Affected Component**: " + str(t.get("affected_component")))
                        st.markdown("**Description**")
                        st.write(t.get("description"))
                        st.markdown("**Suggested Fix**")
                        st.write(t.get("suggested_fix"))
                        if t.get("rationale"):
                            st.markdown("**Rationale / Evidence**")
                            for r in t.get("rationale"):
                                st.write(f"- {r}")
                        st.markdown(f"**Owner hint**: {t.get('owner_hint')}")
                        st.button("Copy ticket to clipboard", key=f"ticket_copy_{i}")

with main_tabs[5]:
    if not st.session_state.result:
        st.info("Generate a blueprint first.")
    else:
        approved = st.session_state.get("approved_variant")

        if not approved:
            st.info("Approve a variant in the Variants tab to preview the generated page layout.")
        else:
            render_wireframe_from_variant(approved)

with main_tabs[6]:
    st.subheader("🧭 Knowledge Graph")
    st.markdown(
        '<div class="section-caption">Structured traceability graph connecting requirements, pages, components, and policies.</div>',
        unsafe_allow_html=True,
    )

    kg = st.session_state.result.get("knowledge_graph") if st.session_state.result else None

    if st.session_state.result and (not kg or not kg.get("nodes")):
        st.warning("Knowledge graph not present or empty — attempting to rebuild from current blueprint data.")
        try:
            from knowledge.graph_builder import build_graph, serialize_graph

            requirements = st.session_state.result.get("requirements", {})
            variants = st.session_state.result.get("variants", [])
            retrieved = st.session_state.result.get("retrieved_evidence", [])

            G = build_graph(requirements, variants, retrieved)
            kg = serialize_graph(G)
            st.session_state.result["knowledge_graph"] = kg
            st.success("Knowledge graph rebuilt from current blueprint data.")
        except Exception as e:
            st.error(f"Failed to rebuild knowledge graph: {e}")
            kg = None

    if not kg or not kg.get("nodes"):
        st.info("Knowledge graph will appear here after blueprint generation.")
    else:
        nodes = kg.get("nodes", [])
        edges = kg.get("edges", [])

        # Summary cards
        c1, c2, c3 = st.columns(3)
        c1.metric("Nodes", len(nodes))
        c2.metric("Edges", len(edges))
        c3.metric(
            "Node types",
            len(set((n.get("attrs") or {}).get("type", "unknown") for n in nodes))
        )

        st.markdown("### Graph Summary")

        node_type_counts = {}
        for n in nodes:
            ntype = (n.get("attrs") or {}).get("type", "unknown")
            node_type_counts[ntype] = node_type_counts.get(ntype, 0) + 1

        st.json({
            "node_type_counts": node_type_counts,
            "sample_node_ids": [n.get("id") for n in nodes[:5]],
            "sample_edges": edges[:5],
        })

        st.markdown("### Nodes")
        node_rows = []
        for n in nodes:
            attrs = n.get("attrs") or {}
            node_rows.append({
                "id": n.get("id"),
                "name": attrs.get("name", ""),
                "type": attrs.get("type", "unknown"),
            })
        st.dataframe(node_rows, use_container_width=True)

        st.markdown("### Edges")
        edge_rows = []
        for e in edges:
            attrs = e.get("attrs") or {}
            edge_rows.append({
                "source": e.get("source"),
                "target": e.get("target"),
                "relation": attrs.get("relation", str(attrs) if attrs else ""),
            })
        st.dataframe(edge_rows, use_container_width=True)

        with st.expander("Show raw graph JSON"):
            st.json(kg)

with main_tabs[7]:
    st.subheader("🏛️ Governance Findings")
    st.markdown(
        '<div class="section-caption">Deprecated component usage, design token drift, off-system patterns, and access-control violations across all generated artefacts.</div>',
        unsafe_allow_html=True,
    )

    g_issues = st.session_state.result.get("governance_issues") if st.session_state.result else None

    if not g_issues:
        st.success("No governance issues detected.")
    else:
        _CATEGORY_META = {
            "deprecated":  {"icon": "🚫", "label": "Deprecated Components",        "color": "error"},
            "token_drift": {"icon": "🎨", "label": "Design Token Drift",           "color": "warning"},
            "off_system":  {"icon": "⚠️", "label": "Off-System Patterns",          "color": "warning"},
            "restricted":  {"icon": "🔒", "label": "Restricted Components",        "color": "error"},
            "unapproved":  {"icon": "🔶", "label": "Unapproved Components",        "color": "info"},
        }
        CATEGORY_ORDER = ["deprecated", "token_drift", "off_system", "restricted", "unapproved"]

        by_category: dict = {}
        for gi in g_issues:
            cat = gi.get("category", "other")
            by_category.setdefault(cat, []).append(gi)

        # Summary row
        summary_cols = st.columns(len(_CATEGORY_META))
        for col, cat in zip(summary_cols, CATEGORY_ORDER):
            count = len(by_category.get(cat, []))
            meta = _CATEGORY_META[cat]
            col.metric(f"{meta['icon']} {meta['label']}", count)

        st.divider()

        for cat in CATEGORY_ORDER:
            cat_issues = by_category.get(cat, [])
            if not cat_issues:
                continue
            meta = _CATEGORY_META[cat]
            st.markdown(f"### {meta['icon']} {meta['label']}")
            for local_idx, gi in enumerate(cat_issues):
                global_idx = g_issues.index(gi)
                issue_id = get_governance_issue_id(gi, global_idx)
                status = st.session_state.governance_issue_status.get(issue_id, "open")
                severity = gi.get("severity", "medium")
                sev_icon = "🔴" if severity == "high" else ("🟡" if severity == "medium" else "🔵")
                with st.expander(f"{sev_icon} **{gi.get('title')}**"):
                    st.write(gi.get("description"))
                    cols = st.columns(3)
                    if gi.get("affected_component"):
                        cols[0].markdown(f"**Component:** `{gi.get('affected_component')}`")
                    if gi.get("artefact_sources"):
                        cols[1].markdown(f"**Found in:** {gi.get('artefact_sources')}")
                    cols[2].markdown(f"**Status:** {status.replace('_', ' ').title()}")
                    st.markdown("**Recommendation**")
                    st.info(gi.get("recommendation"))

                    action_col1, action_col2, action_col3 = st.columns(3)
                    with action_col1:
                        if st.button("Mark Reviewed", key=f"gov_review_{issue_id}", use_container_width=True):
                            st.session_state.governance_issue_status[issue_id] = "reviewed"
                            st.rerun()
                    with action_col2:
                        if st.button("Waive", key=f"gov_waive_{issue_id}", use_container_width=True):
                            st.session_state.governance_issue_status[issue_id] = "waived"
                            st.rerun()
                    with action_col3:
                        if st.button("Needs Fix", key=f"gov_fix_{issue_id}", use_container_width=True):
                            st.session_state.governance_issue_status[issue_id] = "needs_fix"
                            st.rerun()

        # Any issues from unknown categories (future-proofing)
        other = [gi for cat, lst in by_category.items() if cat not in _CATEGORY_META for gi in lst]
        if other:
            st.markdown("### 🔍 Other Findings")
            for gi in other:
                global_idx = g_issues.index(gi)
                issue_id = get_governance_issue_id(gi, global_idx)
                status = st.session_state.governance_issue_status.get(issue_id, "open")
                with st.expander(f"**{gi.get('title')}**"):
                    st.write(gi.get("description"))
                    if gi.get("affected_component"):
                        st.markdown(f"**Component:** `{gi.get('affected_component')}`")
                    st.caption(f"Status: {status.replace('_', ' ').title()}")
                    st.info(gi.get("recommendation"))

with main_tabs[8]:
    st.subheader("🧾 Explainability")
    st.markdown(
        '<div class="section-caption">Decision traces, rationale and evidence for major decisions.</div>',
        unsafe_allow_html=True,
    )

    expl = st.session_state.result.get("explainability") if st.session_state.result else None

    if not expl or not expl.get("records"):
        st.info("Explainability records will appear here after blueprint generation.")
    else:
        st.markdown(f"**Total decisions:** {len(expl.get('records', []))}")

        # Export buttons
        col_export_1, col_export_2 = st.columns([1, 1])
        with col_export_1:
            st.download_button("Download Explainability JSON", data=safe_serialize_for_download(st.session_state.result.get("explainability")), file_name="explainability.json", mime="application/json")
        with col_export_2:
            md = explainability_to_markdown(expl)
            st.download_button("Download Explainability MD", data=safe_serialize_for_download(md), file_name="explainability.md", mime="text/markdown")

        for rec in expl.get("records", []):
            title = rec.get("decision")
            cid = rec.get("id")
            with st.expander(f"{title}  —  {cid}"):
                conf = rec.get("confidence", 0.0)
                st.markdown("**Confidence**")
                st.progress(min(max(float(conf), 0.0), 1.0))

                if rec.get("rationale"):
                    st.markdown("**Rationale**")
                    st.write(rec.get("rationale"))

                evs = rec.get("evidence", [])
                if evs:
                    st.markdown("**Evidence**")
                    for e in evs:
                        st.write(f"- {e}")

                rules = rec.get("rules_applied", [])
                if rules:
                    st.markdown("**Rules Applied**")
                    for r in rules:
                        st.write(f"- {r}")

                linked = rec.get("linked_components", [])
                if linked:
                    st.markdown("**Linked Components**")
                    st.write(", ".join([str(x) for x in linked]))
                    if st.button(f"Jump to graph: {linked[0]}", key=f"jump_expl_{cid}"):
                        node_val = linked[0]
                        if isinstance(node_val, str) and "::" in node_val:
                            node_id = node_val
                        else:
                            node_id = f"component::{node_val}"
                        st.session_state["kg_selected_node"] = node_id
                        st.info("Selected node stored. Open the Knowledge Graph tab to view the node.")

                if rec.get("human_review"):
                    st.markdown(f"**Human Review:** {rec.get('human_review')}")

            with st.expander("Show decision traces (raw)"):
                st.json(expl.get("decision_traces", []))

st.markdown("---")
st.caption("BlueprintAI — AI-assisted design-to-delivery acceleration")
