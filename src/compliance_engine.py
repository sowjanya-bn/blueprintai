import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from src.compliance_policies import CompliancePolicy


def load_policies():
    path = Path("data/compliance_rules.json")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    return [CompliancePolicy(**p) for p in raw]

POLICIES = load_policies()

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





    def run(self, brief: str) -> Dict[str, Any]:
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

        if any(f["review_type"] == "accessibility_review" for f in flags):
            recommendations.append("Confirm accessibility requirements are reflected in the design output.")

        return recommendations