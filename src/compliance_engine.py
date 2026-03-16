import re
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from src.compliance_policies import POLICIES, CompliancePolicy


class ComplianceEngine:
    def __init__(
        self,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        semantic_threshold_high: float = 0.80,
        semantic_threshold_medium: float = 0.70,
        semantic_threshold_borderline: float = 0.60,
        negative_weight: float = 0.40,
    ) -> None:
        self.model = SentenceTransformer(embedding_model_name)
        self.semantic_threshold_high = semantic_threshold_high
        self.semantic_threshold_medium = semantic_threshold_medium
        self.semantic_threshold_borderline = semantic_threshold_borderline
        self.negative_weight = negative_weight

    def run(self, brief: str, requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        brief = (brief or "").strip()
        if not brief:
            return {
                "flags": [],
                "summary": {
                    "total_flags": 0,
                    "high_risk_count": 0,
                    "medium_risk_count": 0,
                    "low_risk_count": 0,
                },
                "evidence": [],
                "review_recommendations": [],
            }

        chunks = self._split_into_chunks(brief)

        flags: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []

        for policy in POLICIES:
            result = self._evaluate_policy(brief=brief, chunks=chunks, policy=policy)

            if result["flagged"]:
                flags.append(result["flag"])
                evidence.extend(result["evidence"])

        context_flags, context_evidence = self._build_contextual_flags(brief, requirements or {})
        flags = self._merge_flags(flags, context_flags)
        evidence.extend(context_evidence)

        flags = self._sort_flags(flags)

        summary = self._build_summary(flags)
        recommendations = self._build_review_recommendations(flags)

        return {
            "flags": flags,
            "summary": summary,
            "evidence": evidence,
            "review_recommendations": recommendations,
        }

    def _split_into_chunks(self, text: str) -> List[str]:
        raw_chunks = re.split(r"(?:\n+|[•\-]\s+|(?<=[.!?])\s+)", text)
        chunks = [chunk.strip() for chunk in raw_chunks if chunk and chunk.strip()]
        return chunks

    def _evaluate_policy(
        self,
        brief: str,
        chunks: List[str],
        policy: CompliancePolicy,
    ) -> Dict[str, Any]:
        keyword_score, keyword_hits = self._keyword_match_score(brief, policy.keywords)

        positive_match = self._best_semantic_match(chunks, policy.example_phrases)
        negative_match = self._best_semantic_match(chunks, policy.negative_examples)

        raw_semantic_score = positive_match["score"]
        negative_score = negative_match["score"]
        adjusted_semantic_score = max(
            0.0,
            raw_semantic_score - (self.negative_weight * negative_score)
        )

        confidence = self._determine_confidence(
            keyword_score=keyword_score,
            semantic_score=adjusted_semantic_score,
        )

        flagged = confidence is not None

        flag = None
        evidence = []

        if flagged:
            rationale = self._build_rationale(
                policy=policy,
                keyword_hits=keyword_hits,
                positive_match=positive_match,
                adjusted_semantic_score=adjusted_semantic_score,
                raw_semantic_score=raw_semantic_score,
                negative_score=negative_score,
                confidence=confidence,
            )

            flag = {
                "policy_id": policy.policy_id,
                "label": policy.label,
                "description": policy.description,
                "severity": policy.severity,
                "review_type": policy.review_type,
                "confidence": confidence,
                "keyword_hits": keyword_hits,
                "keyword_score": round(keyword_score, 3),
                "semantic_score": round(adjusted_semantic_score, 3),
                "raw_semantic_score": round(raw_semantic_score, 3),
                "negative_score": round(negative_score, 3),
                "matched_brief_text": positive_match["best_chunk"],
                "matched_policy_example": positive_match["best_example"],
                "reason": rationale,
                "status": "Potential review needed",
            }

            evidence.append({
                "policy_id": policy.policy_id,
                "label": policy.label,
                "source": self._evidence_source(keyword_hits, adjusted_semantic_score),
                "matched_brief_text": positive_match["best_chunk"],
                "matched_policy_example": positive_match["best_example"],
                "semantic_score": round(adjusted_semantic_score, 3),
                "raw_semantic_score": round(raw_semantic_score, 3),
                "negative_score": round(negative_score, 3),
                "keyword_hits": keyword_hits,
            })

        return {
            "flagged": flagged,
            "flag": flag,
            "evidence": evidence,
        }

    def _keyword_match_score(self, text: str, keywords: List[str]) -> tuple[float, List[str]]:
        if not keywords:
            return 0.0, []

        text_lower = text.lower()
        hits = [kw for kw in keywords if kw.lower() in text_lower]

        score = min(1.0, len(hits) / max(2, len(keywords) * 0.5))
        return score, hits

    def _best_semantic_match(self, chunks: List[str], examples: List[str]) -> Dict[str, Any]:
        if not chunks or not examples:
            return {
                "score": 0.0,
                "best_chunk": None,
                "best_example": None,
            }

        chunk_embeddings = self.model.encode(chunks, normalize_embeddings=True)
        example_embeddings = self.model.encode(examples, normalize_embeddings=True)

        best_score = -1.0
        best_chunk: Optional[str] = None
        best_example: Optional[str] = None

        for chunk, c_emb in zip(chunks, chunk_embeddings):
            for example, e_emb in zip(examples, example_embeddings):
                score = float(np.dot(c_emb, e_emb))
                if score > best_score:
                    best_score = score
                    best_chunk = chunk
                    best_example = example

        return {
            "score": best_score if best_score > 0 else 0.0,
            "best_chunk": best_chunk,
            "best_example": best_example,
        }

    def _determine_confidence(
        self,
        keyword_score: float,
        semantic_score: float,
    ) -> Optional[str]:
        if keyword_score > 0 and semantic_score >= self.semantic_threshold_medium:
            return "high"

        if semantic_score >= self.semantic_threshold_high:
            return "high"

        if semantic_score >= self.semantic_threshold_medium:
            return "medium"

        if semantic_score >= self.semantic_threshold_borderline and keyword_score > 0:
            return "medium"

        if keyword_score >= 0.5:
            return "medium"

        return None

    def _build_rationale(
        self,
        policy: CompliancePolicy,
        keyword_hits: List[str],
        positive_match: Dict[str, Any],
        adjusted_semantic_score: float,
        raw_semantic_score: float,
        negative_score: float,
        confidence: str,
    ) -> str:
        parts = []

        if keyword_hits:
            parts.append(f"Keyword hits: {', '.join(keyword_hits)}.")

        if positive_match["best_example"] and positive_match["best_chunk"]:
            parts.append(
                f"Matched brief text '{positive_match['best_chunk']}' "
                f"to policy example '{positive_match['best_example']}'."
            )

        parts.append(
            f"Semantic score {adjusted_semantic_score:.2f} "
            f"(raw {raw_semantic_score:.2f}, negative {negative_score:.2f})."
        )

        parts.append(f"Confidence assessed as {confidence}.")

        return " ".join(parts)

    def _evidence_source(self, keyword_hits: List[str], semantic_score: float) -> str:
        has_keywords = len(keyword_hits) > 0
        has_semantic = semantic_score > 0

        if has_keywords and has_semantic:
            return "keyword+semantic"
        if has_keywords:
            return "keyword"
        if has_semantic:
            return "semantic"
        return "unknown"

    def _sort_flags(self, flags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        severity_rank = {"high": 3, "medium": 2, "low": 1}
        confidence_rank = {"high": 3, "medium": 2, "low": 1}

        return sorted(
            flags,
            key=lambda item: (
                severity_rank.get(item["severity"], 0),
                confidence_rank.get(item["confidence"], 0),
                item.get("semantic_score", 0.0),
            ),
            reverse=True,
        )

    def _build_summary(self, flags: List[Dict[str, Any]]) -> Dict[str, int]:
        high_risk = sum(1 for f in flags if f["severity"] == "high")
        medium_risk = sum(1 for f in flags if f["severity"] == "medium")
        low_risk = sum(1 for f in flags if f["severity"] == "low")

        return {
            "total_flags": len(flags),
            "high_risk_count": high_risk,
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
        }

    def _build_review_recommendations(self, flags: List[Dict[str, Any]]) -> List[str]:
        recommendations = []

        if any(f["review_type"] == "medical_legal_review" for f in flags):
            recommendations.append("Send medical benefit claims for medical/legal review.")

        if any(f["review_type"] == "safety_review" for f in flags):
            recommendations.append("Validate all safety and side-effect language before approval.")

        if any(f["review_type"] == "content_review" for f in flags):
            recommendations.append("Review patient-facing wording for clarity and audience appropriateness.")

        if any(f["review_type"] == "regional_review" for f in flags):
            recommendations.append("Check region-specific regulatory expectations for the target market.")

        if any(f["review_type"] == "privacy_review" for f in flags):
            recommendations.append("Validate privacy notice, lawful basis, and consent handling for personal data collection.")

        if any(f["review_type"] == "financial_legal_review" for f in flags):
            recommendations.append("Review financial promotions, risk disclosures, and claim wording with legal/compliance.")

        if any(f["review_type"] == "accessibility_review" for f in flags):
            recommendations.append("Confirm accessibility requirements are reflected in the design output.")

        return recommendations

    def _merge_flags(self, semantic_flags: List[Dict[str, Any]], context_flags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        severity_rank = {"high": 3, "medium": 2, "low": 1}
        confidence_rank = {"high": 3, "medium": 2, "low": 1}

        merged: Dict[str, Dict[str, Any]] = {}
        for flag in semantic_flags + context_flags:
            key = flag.get("policy_id") or f"{flag.get('label')}::{flag.get('review_type')}"
            if key not in merged:
                merged[key] = flag
                continue

            current = merged[key]
            incoming_rank = (
                severity_rank.get(flag.get("severity", "low"), 0),
                confidence_rank.get(flag.get("confidence", "low"), 0),
                float(flag.get("semantic_score", 0.0) or 0.0),
            )
            current_rank = (
                severity_rank.get(current.get("severity", "low"), 0),
                confidence_rank.get(current.get("confidence", "low"), 0),
                float(current.get("semantic_score", 0.0) or 0.0),
            )

            if incoming_rank > current_rank:
                merged[key] = flag

        return list(merged.values())

    def _build_contextual_flags(self, brief: str, requirements: Dict[str, Any]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        text = (brief or "").lower()
        market = str(requirements.get("market") or "").upper()

        industry = self._infer_industry(text)
        collects_personal_data = self._likely_collects_personal_data(text)
        is_eu = ("EU" in market) or bool(re.search(r"\beu\b|\beurope\b|european", text, re.IGNORECASE))

        flags: List[Dict[str, Any]] = []
        evidence: List[Dict[str, Any]] = []

        def add_flag(
            policy_id: str,
            label: str,
            description: str,
            severity: str,
            review_type: str,
            confidence: str,
            reason: str,
            keyword_hits: Optional[List[str]] = None,
        ) -> None:
            hits = keyword_hits or []
            flags.append(
                {
                    "policy_id": policy_id,
                    "label": label,
                    "description": description,
                    "severity": severity,
                    "review_type": review_type,
                    "confidence": confidence,
                    "keyword_hits": hits,
                    "keyword_score": round(min(1.0, len(hits) / 3.0), 3),
                    "semantic_score": 0.0,
                    "raw_semantic_score": 0.0,
                    "negative_score": 0.0,
                    "matched_brief_text": brief[:180] if brief else None,
                    "matched_policy_example": None,
                    "reason": reason,
                    "status": "Potential review needed",
                }
            )
            evidence.append(
                {
                    "policy_id": policy_id,
                    "label": label,
                    "source": "context",
                    "matched_brief_text": brief[:180] if brief else None,
                    "matched_policy_example": None,
                    "semantic_score": 0.0,
                    "raw_semantic_score": 0.0,
                    "negative_score": 0.0,
                    "keyword_hits": hits,
                }
            )

        if industry == "healthcare":
            health_hits = [k for k in ["patient", "treatment", "medical", "clinical", "therapy", "symptom"] if k in text]
            add_flag(
                policy_id="industry.healthcare_review",
                label="Healthcare content regulatory review",
                description="Healthcare-related claims and patient-facing medical content require medical/legal review.",
                severity="high",
                review_type="medical_legal_review",
                confidence="high" if health_hits else "medium",
                reason="Brief indicates healthcare context. Apply medical/legal review controls for claims and patient communication.",
                keyword_hits=health_hits,
            )

        if industry == "financial":
            fin_hits = [k for k in ["financial", "bank", "investment", "loan", "insurance", "credit", "returns", "interest"] if k in text]
            add_flag(
                policy_id="industry.financial_review",
                label="Financial promotions compliance review",
                description="Financial content should include fair, clear risk disclosures and legal/compliance review.",
                severity="high",
                review_type="financial_legal_review",
                confidence="high" if fin_hits else "medium",
                reason="Brief indicates financial domain. Enforce financial promotions and disclosure review.",
                keyword_hits=fin_hits,
            )

        if is_eu:
            eu_hits = [k for k in ["eu", "europe", "gdpr", "privacy", "consent"] if k in text]
            add_flag(
                policy_id="regional.eu_gdpr_applicability",
                label="EU GDPR applicability check",
                description="EU-targeted experiences should be reviewed for GDPR lawful basis, transparency, and data subject rights handling.",
                severity="high" if collects_personal_data else "medium",
                review_type="privacy_review",
                confidence="high" if collects_personal_data else "medium",
                reason="Target market appears to be EU/Europe. GDPR controls should be applied.",
                keyword_hits=eu_hits,
            )

            if collects_personal_data:
                data_hits = [k for k in ["signup", "sign up", "register", "form", "contact", "email", "phone", "book"] if k in text]
                add_flag(
                    policy_id="regional.eu_consent_required",
                    label="Consent and privacy notice required for EU data capture",
                    description="When collecting personal data in the EU, explicit consent and clear privacy information are required.",
                    severity="high",
                    review_type="privacy_review",
                    confidence="high",
                    reason="EU context plus likely personal-data collection detected.",
                    keyword_hits=data_hits,
                )

        return flags, evidence

    def _infer_industry(self, text: str) -> str:
        healthcare_markers = [
            "healthcare", "patient", "patients", "medical", "clinical", "treatment", "therapy", "hospital", "pharma", "side effect",
        ]
        financial_markers = [
            "financial", "finance", "bank", "banking", "loan", "credit", "insurance", "investment", "mortgage", "wealth", "fintech",
        ]

        if any(marker in text for marker in healthcare_markers):
            return "healthcare"
        if any(marker in text for marker in financial_markers):
            return "financial"
        return "general"

    def _likely_collects_personal_data(self, text: str) -> bool:
        data_collection_markers = [
            "signup", "sign up", "register", "form", "contact", "email", "phone", "book", "appointment", "apply", "lead",
        ]
        return any(marker in text for marker in data_collection_markers)