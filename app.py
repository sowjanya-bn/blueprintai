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
            if st.button("Approve", key=f"approve_{idx}"):
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

def render_pattern_reasoning(result: dict):
    reasons = result.get("pattern_reasoning", [])

    if not reasons:
        return

    st.subheader("🧠 Why this page pattern?")
    st.caption("Explanation of how the system mapped the brief to a page structure.")

    for reason in reasons:
        st.write(f"• {reason}")


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
                if st.button("Mark Reviewed", key=f"review_{flag_id}", use_container_width=True):
                    st.session_state.flag_status[flag_id] = "reviewed"
                    st.rerun()
            with col2:
                if st.button("Waive", key=f"waive_{flag_id}", use_container_width=True):
                    st.session_state.flag_status[flag_id] = "waived"
                    st.rerun()
            with col3:
                if st.button("Needs Fix", key=f"fix_{flag_id}", use_container_width=True):
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

    st.markdown(
        """
        <style>
        .wf-canvas {
            max-width: 920px;
            margin: 28px auto;
            padding: 30px 28px;
            border-radius: 18px;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(148, 163, 184, 0.16);
            box-shadow: 0 8px 40px rgba(0,0,0,0.28);
        }

        .wf-page-label {
            text-align: center;
            font-size: 0.72rem;
            letter-spacing: 0.14em;
            color: #64748b;
            margin-bottom: 18px;
            font-weight: 700;
        }

        .wf-end-label {
            text-align: center;
            font-size: 0.72rem;
            letter-spacing: 0.14em;
            color: #64748b;
            margin-top: 18px;
            font-weight: 700;
        }

        .wf-block {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 18px;
            background: rgba(255, 255, 255, 0.02);
        }

        .wf-label {
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            color: #94a3b8;
            margin-bottom: 12px;
            text-transform: uppercase;
        }

        .wf-hero {
            padding: 26px 22px;
            min-height: 190px;
        }

        .wf-line-lg {
            height: 18px;
            width: 60%;
            border-radius: 999px;
            background: rgba(255,255,255,0.82);
            margin-bottom: 14px;
        }

        .wf-line-md {
            height: 12px;
            width: 72%;
            border-radius: 999px;
            background: rgba(255,255,255,0.22);
            margin-bottom: 10px;
        }

        .wf-line-sm {
            height: 12px;
            width: 48%;
            border-radius: 999px;
            background: rgba(255,255,255,0.18);
            margin-bottom: 18px;
        }

        .wf-btn {
            display: inline-block;
            height: 34px;
            width: 120px;
            border-radius: 999px;
            background: rgba(59, 130, 246, 0.85);
            margin-top: 10px;
        }

        .wf-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 8px;
        }

        .wf-card {
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            min-height: 120px;
            padding: 14px;
            background: rgba(255,255,255,0.02);
        }

        .wf-card-line-1 {
            height: 12px;
            width: 60%;
            border-radius: 999px;
            background: rgba(255,255,255,0.35);
            margin-bottom: 12px;
        }

        .wf-card-line-2 {
            height: 10px;
            width: 90%;
            border-radius: 999px;
            background: rgba(255,255,255,0.16);
            margin-bottom: 8px;
        }

        .wf-card-line-3 {
            height: 10px;
            width: 70%;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
        }

        .wf-logo-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin-top: 8px;
        }

        .wf-logo {
            height: 42px;
            border-radius: 8px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(148, 163, 184, 0.16);
        }

        .wf-accordion-item {
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.02);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .wf-accordion-line {
            height: 12px;
            width: 58%;
            border-radius: 999px;
            background: rgba(255,255,255,0.28);
        }

        .wf-accordion-icon {
            height: 14px;
            width: 14px;
            border-radius: 50%;
            background: rgba(255,255,255,0.22);
        }

        .wf-cta {
            text-align: center;
            padding: 28px 20px;
            min-height: 140px;
        }

        .wf-cta-title {
            height: 16px;
            width: 44%;
            margin: 0 auto 14px auto;
            border-radius: 999px;
            background: rgba(255,255,255,0.78);
        }

        .wf-cta-sub {
            height: 12px;
            width: 58%;
            margin: 0 auto 18px auto;
            border-radius: 999px;
            background: rgba(255,255,255,0.18);
        }

        .wf-form-wrap {
            max-width: 620px;
            margin: 0 auto;
        }

        .wf-input {
            height: 38px;
            border-radius: 8px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(148, 163, 184, 0.16);
            margin-bottom: 10px;
        }

        .wf-footer {
            min-height: 78px;
            padding: 18px;
        }

        .wf-footer-line-1 {
            height: 10px;
            width: 75%;
            border-radius: 999px;
            background: rgba(255,255,255,0.16);
            margin-bottom: 10px;
        }

        .wf-footer-line-2 {
            height: 10px;
            width: 52%;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
        }

        .wf-summary {
            color: #94a3b8;
            font-size: 0.9rem;
            margin-top: 12px;
        }

        .wf-device {
            margin-bottom: 1rem;
            padding: 0.8rem 1rem;
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            background: rgba(255,255,255,0.02);
            color: #cbd5e1;
            font-size: 0.92rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    preview_name = variant.get("pattern_name", "Approved Variant")
    st.markdown(
        f"""
        <div class="wf-device">
            <strong>Previewing Approved Blueprint</strong><br>
            Pattern: {preview_name}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="wf-canvas">', unsafe_allow_html=True)
    st.markdown('<div class="wf-page-label">DESKTOP LAYOUT PREVIEW</div>', unsafe_allow_html=True)
    st.markdown('<div class="wf-page-label" style="margin-top:-6px;">PAGE START</div>', unsafe_allow_html=True)

    for idx, comp in enumerate(components, start=1):
        name = comp.get("component_name", "Unknown Component")
        summary = comp.get("content_summary", "Component preview")
        name_lower = name.lower()

        label = f"{idx}. {name}"

        if "hero" in name_lower:
            st.markdown(
                f"""
                <div class="wf-block wf-hero">
                    <div class="wf-label">{label}</div>
                    <div class="wf-line-lg"></div>
                    <div class="wf-line-md"></div>
                    <div class="wf-line-sm"></div>
                    <div class="wf-btn"></div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif "trust" in name_lower or "logo" in name_lower:
            st.markdown(
                f"""
                <div class="wf-block">
                    <div class="wf-label">{label}</div>
                    <div class="wf-logo-grid">
                        <div class="wf-logo"></div>
                        <div class="wf-logo"></div>
                        <div class="wf-logo"></div>
                        <div class="wf-logo"></div>
                        <div class="wf-logo"></div>
                    </div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif "feature" in name_lower or "card" in name_lower or "grid" in name_lower:
            st.markdown(
                f"""
                <div class="wf-block">
                    <div class="wf-label">{label}</div>
                    <div class="wf-grid">
                        <div class="wf-card">
                            <div class="wf-card-line-1"></div>
                            <div class="wf-card-line-2"></div>
                            <div class="wf-card-line-3"></div>
                        </div>
                        <div class="wf-card">
                            <div class="wf-card-line-1"></div>
                            <div class="wf-card-line-2"></div>
                            <div class="wf-card-line-3"></div>
                        </div>
                        <div class="wf-card">
                            <div class="wf-card-line-1"></div>
                            <div class="wf-card-line-2"></div>
                            <div class="wf-card-line-3"></div>
                        </div>
                    </div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif "accordion" in name_lower or "faq" in name_lower:
            st.markdown(
                f"""
                <div class="wf-block">
                    <div class="wf-label">{label}</div>
                    <div class="wf-accordion-item">
                        <div class="wf-accordion-line"></div>
                        <div class="wf-accordion-icon"></div>
                    </div>
                    <div class="wf-accordion-item">
                        <div class="wf-accordion-line"></div>
                        <div class="wf-accordion-icon"></div>
                    </div>
                    <div class="wf-accordion-item">
                        <div class="wf-accordion-line"></div>
                        <div class="wf-accordion-icon"></div>
                    </div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif "cta" in name_lower:
            st.markdown(
                f"""
                <div class="wf-block wf-cta">
                    <div class="wf-label">{label}</div>
                    <div class="wf-cta-title"></div>
                    <div class="wf-cta-sub"></div>
                    <div class="wf-btn" style="margin: 0 auto;"></div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif "contact" in name_lower or "leadgen" in name_lower or "form" in name_lower:
            st.markdown(
                f"""
                <div class="wf-block wf-cta">
                    <div class="wf-label">{label}</div>
                    <div class="wf-form-wrap">
                        <div class="wf-input"></div>
                        <div class="wf-input"></div>
                        <div class="wf-input"></div>
                        <div class="wf-btn" style="margin: 12px auto 0 auto;"></div>
                    </div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif "footer" in name_lower or "disclaimer" in name_lower:
            st.markdown(
                f"""
                <div class="wf-block wf-footer">
                    <div class="wf-label">{label}</div>
                    <div class="wf-footer-line-1"></div>
                    <div class="wf-footer-line-2"></div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif "stat" in name_lower or "metric" in name_lower or "counter" in name_lower:
            st.markdown(
                f"""
                <div class="wf-block">
                    <div class="wf-label">{label}</div>
                    <div class="wf-grid">
                        <div class="wf-card" style="min-height: 90px;"></div>
                        <div class="wf-card" style="min-height: 90px;"></div>
                        <div class="wf-card" style="min-height: 90px;"></div>
                    </div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f"""
                <div class="wf-block">
                    <div class="wf-label">{label}</div>
                    <div class="wf-line-md" style="width: 64%;"></div>
                    <div class="wf-line-sm" style="width: 42%;"></div>
                    <div class="wf-summary">{summary}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="wf-end-label">PAGE END</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)



# Top action bar
title_col, action_col1, action_col2, action_col3 = st.columns([4, 1.2, 1.2, 1.2])

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
        "5️⃣ Developer Handoff",
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
        best_idx = get_best_variant_index(variants)
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
        flags = st.session_state.result.get("compliance_flags", {})
        review = st.session_state.result.get("human_review_required", [])

        render_compliance_summary(flags)

        st.divider()

        # Validation summary (Accessibility, Brand, Compliance, Security)
        validation_reports = st.session_state.result.get("validation_reports", {})
        render_validation_summary(validation_reports)

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
        approved = st.session_state.get("approved_variant")

        if not approved:
            st.info("Approve a variant in the Variants tab to move toward developer handoff.")
        else:
            st.success(f"Using approved variant: {approved.get('pattern_name', 'Selected Variant')}")
            render_page_spec(st.session_state.result.get("page_specification", {}))
            st.caption("Ideally, developer handoff should be generated after blueprint approval.")

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
            '<div class="section-caption">Serialized knowledge graph showing nodes and edges used for traceability.</div>',
            unsafe_allow_html=True,
        )

        kg = st.session_state.result.get("knowledge_graph") if st.session_state.result else None

        if not kg or not kg.get("nodes"):
            st.info("Knowledge graph will appear here after blueprint generation.")
        else:
            # Build NetworkX graph object from serialized KG for exploration and optional visualization
            try:
                import networkx as nx
                import matplotlib.pyplot as plt
            except Exception:
                nx = None
                plt = None

            G = None
            try:
                if nx:
                    G = nx.DiGraph()
                    for n in kg.get("nodes", []):
                        G.add_node(n.get("id"), **(n.get("attrs") or {}))

                    for e in kg.get("edges", []):
                        G.add_edge(e.get("source"), e.get("target"), **(e.get("attrs") or {}))
            except Exception:
                G = None

            # Prefer JS-based interactive pyvis visualization when available
            clicked_node = None
            # Prefer using the new lightweight Streamlit custom component if available
            clicked_node = None
            try:
                from components.streamlit_pyvis import streamlit_pyvis

                nodes = []
                edges = []
                for n in kg.get("nodes", []):
                    nid = n.get("id")
                    label = (n.get("attrs") or {}).get("name") or nid
                    title = "\n".join([f"{k}: {v}" for k, v in (n.get("attrs") or {}).items()])
                    nodes.append({"id": nid, "label": label, "title": title})

                for e in kg.get("edges", []):
                    edges.append({"source": e.get("source"), "target": e.get("target"), "title": str((e.get("attrs") or {}))})

                # This calls the component; the frontend will return {selected_node: id} when clicked
                result = streamlit_pyvis(nodes=nodes, edges=edges)
                if result and isinstance(result, dict):
                    clicked_node = result.get("selected_node")

            except Exception:
                # fallback: static matplotlib visualization
                try:
                    pos = nx.spring_layout(G, seed=42)
                    fig = plt.figure(figsize=(9, 6))
                    nx.draw_networkx_nodes(G, pos, node_size=700, node_color="#7ef2b3")
                    nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=12)
                    nx.draw_networkx_labels(G, pos, font_size=8)
                    plt.axis("off")
                    st.pyplot(fig)
                except Exception:
                    st.warning("Graph visualization unavailable (missing dependencies or rendering error).")

            # Interactive exploration: node selector, node details, neighbors
            node_options = [n.get("id") for n in kg.get("nodes", [])]

            filter_type = st.selectbox("Filter nodes by type (optional)", options=["all"] + sorted({(n.get("attrs") or {}).get("type", "unknown") for n in kg.get("nodes", [])}))

            if filter_type and filter_type != "all":
                node_options = [n for n in node_options if ((next(filter(lambda x: x.get("id") == n, kg.get("nodes", [])) or {}).get("attrs") or {}).get("type") == filter_type)]

            # allow selection from pyvis click or selector
            selected = st.selectbox("Select node to inspect", options=node_options)
            if not selected and clicked_node:
                selected = clicked_node

            if selected:
                # show node attrs
                node_obj = next(filter(lambda x: x.get("id") == selected, kg.get("nodes", [])), None)
                if node_obj:
                    st.markdown("**Node Attributes**")
                    for k, v in (node_obj.get("attrs") or {}).items():
                        st.write(f"- **{k}**: {v}")

                # show incoming and outgoing edges
                st.markdown("**Neighbors**")
                incoming = [e for e in kg.get("edges", []) if e.get("target") == selected]
                outgoing = [e for e in kg.get("edges", []) if e.get("source") == selected]

                if incoming:
                    st.markdown("**Incoming**")
                    for e in incoming:
                        st.write(f"- {e.get('source')}  →  {e.get('target')}  — {e.get('attrs', {})}")
                else:
                    st.write("No incoming edges")

                if outgoing:
                    st.markdown("**Outgoing**")
                    for e in outgoing:
                        st.write(f"- {e.get('source')}  →  {e.get('target')}  — {e.get('attrs', {})}")
                else:
                    st.write("No outgoing edges")

            with st.expander("Show raw graph JSON"):
                st.json(kg)

    with main_tabs[7]:
        st.subheader("🏛️ Governance Findings")
        st.markdown(
            '<div class="section-caption">Governance drift detection results highlighting deprecated, restricted, or off-system components.</div>',
            unsafe_allow_html=True,
        )

        g_issues = st.session_state.result.get("governance_issues") if st.session_state.result else None

        if not g_issues:
            st.success("No governance issues detected.")
        else:
            for idx, gi in enumerate(g_issues, start=1):
                with st.container():
                    st.markdown(f"**{idx}. {gi.get('title')}**")
                    st.write(gi.get("description"))
                    if gi.get("affected_component"):
                        st.markdown(f"- Affected component: **{gi.get('affected_component')}**")
                    st.markdown(f"- Recommendation: {gi.get('recommendation')}")
                    st.divider()

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
            for idx, rec in enumerate(expl.get("records", []), start=1):
                with st.expander(f"{idx}. {rec.get('decision')}"):
                    st.markdown(f"**Confidence:** {rec.get('confidence')}")
                    st.markdown("**Evidence**")
                    for e in rec.get("evidence", []):
                        st.write(f"- {e}")
                    st.markdown("**Rules Applied**")
                    for r in rec.get("rules_applied", []):
                        st.write(f"- {r}")
                    if rec.get("human_review"):
                        st.markdown(f"**Human Review:** {rec.get('human_review')}")

            with st.expander("Show decision traces (raw)"):
                st.json(expl.get("decision_traces", []))

st.markdown("---")
st.caption("BlueprintAI — AI-assisted design-to-delivery acceleration")
