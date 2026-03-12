import streamlit as st
from src.blueprint import create_blueprint

st.set_page_config(page_title="BlueprintAI", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.15rem;
    }
    [data-testid="stMetricLabel"] p {
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("BlueprintAI")
st.caption("AI-assisted page blueprint and compliance recommender")

brief = st.text_area(
    "Enter webpage brief",
    height=180,
    placeholder="Create a patient-facing webpage for a new migraine treatment in the UK..."
)


def render_requirements(requirements: dict):
    st.subheader("🧠 Extracted Requirements")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Audience", requirements.get("audience", "N/A"))
    col2.metric("Market", requirements.get("market", "N/A"))
    col3.metric("Content Type", requirements.get("content_type", "N/A"))
    col4.metric("Compliance", requirements.get("compliance_sensitivity", "N/A"))


def render_summary(result: dict):
    st.subheader("📊 Generation Summary")

    variants = result.get("variants", [])
    compliance_flags = result.get("compliance_flags", [])
    component_count = sum(len(v.get("components", [])) for v in variants)

    col1, col2, col3 = st.columns(3)
    col1.metric("Variants Generated", len(variants))
    col2.metric("Components Suggested", component_count)
    col3.metric("Compliance Flags", len(compliance_flags))


def render_variant_card(variant: dict, idx: int):
    st.markdown(f"### Variant {idx}: {variant.get('pattern_name', 'Untitled Variant')}")
    st.write(variant.get("description", ""))

    components = variant.get("components", [])
    if not components:
        st.info("No components returned for this variant.")
        return

    for step, comp in enumerate(components, start=1):
        confidence = comp.get("confidence", 0)

        st.markdown("---")
        c1, c2 = st.columns([4, 1])

        with c1:
            st.markdown(f"### {step}. {comp.get('component_name', 'Unknown Component')}")
            st.write(comp.get("content_summary", ""))
            st.caption(comp.get("rationale", ""))

        with c2:
            if isinstance(confidence, (int, float)):
                st.metric("Confidence", f"{confidence:.2f}")
            else:
                st.metric("Confidence", str(confidence))


def render_compliance_flags(flags: list[dict]):
    st.subheader("⚠ Compliance Flags")

    if not flags:
        st.success("No compliance flags detected.")
        return

    for flag in flags:
        st.warning(
            f"**{flag.get('type', 'flag')}**\n\n{flag.get('description', '')}"
        )


def render_human_review(review_items: list[str]):
    st.subheader("👥 Human Review Required")

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

    st.markdown(f"**Page Type:** {page_spec.get('page_type', 'N/A')}")

    layout = page_spec.get("layout", [])
    if not layout:
        st.info("No page specification returned.")
        return

    for idx, block in enumerate(layout, start=1):
        with st.container(border=True):
            st.markdown(f"**{idx}. {block.get('component', 'Unknown Component')}**")

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


if st.button("Generate Blueprint", type="primary"):
    if not brief.strip():
        st.warning("Please enter a brief.")
    else:
        with st.spinner("Generating blueprint..."):
            result = create_blueprint(brief)

        render_requirements(result.get("requirements", {}))
        st.divider()

        render_summary(result)
        st.divider()

        st.subheader("📐 Blueprint Variants")
        variants = result.get("variants", [])
        if not variants:
            st.info("No variants returned.")
        else:
            tabs = st.tabs([v.get("pattern_name", f"Variant {i+1}") for i, v in enumerate(variants)])
            for i, (tab, variant) in enumerate(zip(tabs, variants), start=1):
                with tab:
                    render_variant_card(variant, i)

        st.divider()

        left, right = st.columns([1, 1])

        with left:
            render_compliance_flags(result.get("compliance_flags", []))

        with right:
            render_human_review(result.get("human_review_required", []))

        st.divider()

        render_page_spec(result.get("page_specification", {}))
        st.divider()

        render_evidence(result.get("retrieved_evidence", []))

        with st.expander("Show full raw JSON"):
            st.json(result)

        st.markdown("---")
        st.caption("BlueprintAI — AI-assisted design-to-delivery acceleration")
