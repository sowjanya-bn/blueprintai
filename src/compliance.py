def check_compliance(brief: str) -> list[dict]:
    text = brief.lower()
    flags = []

    if "patient" in text:
        flags.append({
            "type": "patient_content_review",
            "description": "Patient-facing content should be reviewed for clarity and appropriateness."
        })

    if "treatment" in text or "medical" in text or "side effects" in text:
        flags.append({
            "type": "medical_claim_review",
            "description": "Treatment benefits and medical statements require medical/legal review."
        })

    if "safety" in text or "side effects" in text:
        flags.append({
            "type": "safety_information_review",
            "description": "Safety information must be validated for regulatory accuracy."
        })

    if "uk" in text:
        flags.append({
            "type": "market_specific_review",
            "description": "Check market-specific regulatory and legal requirements for the UK."
        })

    if "accessibility" in text:
        flags.append({
            "type": "accessibility_audit",
            "description": "Final page should undergo accessibility QA."
        })

    return flags