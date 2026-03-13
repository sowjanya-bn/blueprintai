import json
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
        max-width: 95%;
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

    .workflow-step-complete {
        text-align: center;
        padding: 0.7rem 0.5rem;
        border-radius: 12px;
        background: rgba(34, 197, 94, 0.10);
        border: 1px solid rgba(34, 197, 94, 0.4);
        font-weight: 600;
    }

    .workflow-step-pending {
        text-align: center;
        padding: 0.7rem 0.5rem;
        border-radius: 12px;
        background: rgba(148, 163, 184, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.18);
        font-weight: 600;
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


def get_current_stage():
    if not st.session_state.result:
        return 1
    if st.session_state.result and not st.session_state.approved_variant:
        return 4
    if st.session_state.approved_variant:
        return 5
    return 1


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

    flags = result.get("compliance_flags", [])
    if flags:
        md += "\n## Compliance Flags\n"
        for flag in flags:
            md += f"- **{flag.get('type', 'flag')}**: {flag.get('description', '')}\n"

    return md

def render_workflow_indicator():
    stages = ["Blueprint", "Variants", "Evidence", "Handoff"]
    current = st.session_state.get("workflow_stage", 0)

    cols = st.columns(len(stages))

    for i, stage in enumerate(stages):
        if i <= current:
            cols[i].success(stage)
        else:
            cols[i].info(stage)


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
    compliance_flags = result.get("compliance_flags", [])
    component_count = sum(len(v.get("components", [])) for v in variants)

    col1, col2, col3 = st.columns(3)
    col1.metric("Variants Generated", len(variants))
    col2.metric("Components Suggested", component_count)
    col3.metric("Compliance Flags", len(compliance_flags))


def render_variant_card(variant: dict, idx: int):
    with st.container(border=True):
        top_left, top_right = st.columns([5, 1])

        with top_left:
            st.markdown(f"### Variant {idx}: {variant.get('pattern_name', 'Untitled Variant')}")
            st.write(variant.get("description", ""))

        with top_right:
            if st.button("Approve", key=f"approve_{idx}", use_container_width=True):
                st.session_state.approved_variant = variant
                st.success(f"Approved: {variant.get('pattern_name', f'Variant {idx}')}")

        components = variant.get("components", [])
        if not components:
            st.info("No components returned for this variant.")
            return

        st.markdown("#### Page Flow")

        for step, comp in enumerate(components, start=1):
            confidence = comp.get("confidence", 0)
            comp_name = comp.get("component_name", "Unknown Component")

            with st.expander(f"{step}. {comp_name}", expanded=(step == 1)):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.write(comp.get("content_summary", ""))
                    st.caption(comp.get("rationale", ""))

                with col2:
                    if isinstance(confidence, (int, float)):
                        st.metric("Confidence", f"{confidence:.2f}")
                        st.progress(max(0.0, min(float(confidence), 1.0)))
                    else:
                        st.metric("Confidence", str(confidence))


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

                if notes:
                    st.markdown("**Accessibility Notes**")
                    for note in notes:
                        st.write(f"- {note}")


def render_evidence(evidence_items: list[dict]):
    st.subheader("🔍 Evidence Used")
    st.markdown(
        '<div class="section-caption">Retrieved design-system evidence used to support recommendations.</div>',
        unsafe_allow_html=True,
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


# Top action bar
title_col, action_col1, action_col2, action_col3 = st.columns([4, 1.2, 1.4, 1.4])

with title_col:
    st.title("🧠 BlueprintAI")
    st.markdown(
        '<div class="app-subtitle">AI-assisted page blueprint and compliance recommender</div>',
        unsafe_allow_html=True,
    )

with action_col1:
    st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
    generate_clicked = st.button("Generate Blueprint", type="primary", use_container_width=True)

with action_col2:
    st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
    if st.session_state.result:
        plan_json = json.dumps(st.session_state.result, indent=2)
        st.download_button(
            "Download JSON",
            data=plan_json,
            file_name="blueprint_plan.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.button("Download JSON", disabled=True, use_container_width=True)

with action_col3:
    st.markdown("<div style='height: 1.9rem;'></div>", unsafe_allow_html=True)
    if st.session_state.result:
        md_plan = blueprint_to_markdown(st.session_state.result)
        st.download_button(
            "Download MD",
            data=md_plan,
            file_name="blueprint_plan.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        st.button("Download MD", disabled=True, use_container_width=True)

# Brief input stays global
st.subheader("Describe the webpage you want to generate")
st.caption("Provide the audience, purpose and compliance sensitivity.")

brief = st.text_area(
    "",
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
        "1️⃣ Generate Blueprint",
        "2️⃣ Show Variants",
        "3️⃣ Compliance & Review",
        "4️⃣ Evidence",
        "5️⃣ Developer Handoff",
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
        st.markdown(
            '<div class="section-caption">Review the options and approve the best page structure.</div>',
            unsafe_allow_html=True,
        )

        variants = st.session_state.result.get("variants", [])
        if not variants:
            st.info("No variants returned.")
        else:
            variant_tabs = st.tabs(
                [v.get("pattern_name", f"Variant {i+1}") for i, v in enumerate(variants)]
            )
            for i, (tab, variant) in enumerate(zip(variant_tabs, variants), start=1):
                with tab:
                    render_variant_card(variant, i)

with main_tabs[2]:
    if not st.session_state.result:
        st.info("Generate a blueprint first.")
    else:
        left, right = st.columns([1, 1])

        with left:
            render_compliance_flags(st.session_state.result.get("compliance_flags", []))

        with right:
            render_human_review(st.session_state.result.get("human_review_required", []))

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
        approved = st.session_state.get("approved_variant")

        if not approved:
            st.info("Approve a variant in the Variants tab to move toward developer handoff.")
        else:
            st.success(f"Using approved variant: {approved.get('pattern_name', 'Selected Variant')}")
            render_page_spec(st.session_state.result.get("page_specification", {}))
            st.caption("Ideally, developer handoff should be generated after blueprint approval.")

st.markdown("---")
st.caption("BlueprintAI — AI-assisted design-to-delivery acceleration")
