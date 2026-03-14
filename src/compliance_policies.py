from dataclasses import dataclass, field
from typing import List


@dataclass
class CompliancePolicy:
    policy_id: str
    label: str
    description: str
    severity: str  # "low" | "medium" | "high"
    review_type: str
    keywords: List[str] = field(default_factory=list)
    example_phrases: List[str] = field(default_factory=list)
    negative_examples: List[str] = field(default_factory=list)


POLICIES = [
    CompliancePolicy(
        policy_id="patient_content_review",
        label="Patient-facing content review",
        description=(
            "Content aimed at patients, caregivers, or the general public "
            "should be reviewed for clarity and appropriateness."
        ),
        severity="medium",
        review_type="content_review",
        keywords=["patient", "patients", "caregiver", "public-facing", "public"],
        example_phrases=[
            "written for patients",
            "for people living with the condition",
            "easy for patients to understand",
            "support for people managing symptoms",
            "public-facing health information",
        ],
        negative_examples=[
            "internal clinical dashboard",
            "clinician-only admin panel",
            "backend operational interface",
        ],
    ),
    CompliancePolicy(
        policy_id="medical_claim_review",
        label="Medical claim review",
        description=(
            "Claims about treatment effect, efficacy, benefit, symptom relief, "
            "or clinical improvement require medical and legal review."
        ),
        severity="high",
        review_type="medical_legal_review",
        keywords=["treatment", "clinical", "effective", "benefit", "outcomes", "therapy"],
        example_phrases=[
            "improves outcomes",
            "reduces symptoms",
            "clinically proven benefit",
            "effective treatment option",
            "works better than standard care",
            "helps patients recover faster",
        ],
        negative_examples=[
            "visual redesign only",
            "layout exploration",
            "component styling only",
        ],
    ),
    CompliancePolicy(
        policy_id="safety_information_review",
        label="Safety information review",
        description=(
            "Statements related to side effects, adverse events, tolerability, "
            "risk, or safety profile require validation."
        ),
        severity="high",
        review_type="safety_review",
        keywords=["safety", "side effects", "adverse", "risk", "tolerability"],
        example_phrases=[
            "well tolerated",
            "low risk of side effects",
            "safe to use",
            "minimal adverse events",
            "favourable safety profile",
        ],
        negative_examples=[
            "security risk review",
            "technical system safety only",
        ],
    ),
    CompliancePolicy(
        policy_id="market_specific_review",
        label="Market-specific review",
        description=(
            "Region-specific content may require legal or regulatory checks "
            "for that target market."
        ),
        severity="medium",
        review_type="regional_review",
        keywords=["uk", "united kingdom", "nhs", "ema", "eu", "usa", "fda"],
        example_phrases=[
            "for the UK market",
            "tailored for NHS audiences",
            "localized regulatory content",
            "region-specific healthcare messaging",
        ],
        negative_examples=[],
    ),
    CompliancePolicy(
        policy_id="accessibility_review",
        label="Accessibility review",
        description=(
            "Content or UI requirements mentioning accessibility should be reviewed "
            "for accessibility coverage and implementation quality."
        ),
        severity="medium",
        review_type="accessibility_review",
        keywords=["accessibility", "accessible", "screen reader", "wcag", "contrast"],
        example_phrases=[
            "must be accessible",
            "designed for screen readers",
            "meet WCAG expectations",
            "improve readability for all users",
        ],
        negative_examples=[],
    ),
]