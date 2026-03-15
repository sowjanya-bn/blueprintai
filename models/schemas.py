from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ProjectBrief(BaseModel):
    title: Optional[str]
    description: str
    audience: Optional[str]
    market: Optional[str]
    brand: Optional[str]


class StructuredRequirements(BaseModel):
    audience: Optional[str]
    market: Optional[str]
    content_type: Optional[str]
    compliance_sensitivity: Optional[str]
    notes: Optional[List[str]] = []


class ComponentRecommendation(BaseModel):
    component_name: str
    rationale: Optional[str]
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    evidence: Optional[str]


class PageComponent(BaseModel):
    component: str
    props: Dict[str, Any] = {}
    accessibility_notes: List[str] = []


class PageBlueprint(BaseModel):
    page_type: str
    layout: List[PageComponent] = []
    pattern_reasoning: List[str] = []


class ValidationIssue(BaseModel):
    status: str
    category: str
    title: str
    description: str
    rule_triggered: Optional[str]
    evidence: Optional[str]
    severity: Optional[str]
    suggested_fix: Optional[str]
    human_review_required: bool = False


class ValidationReport(BaseModel):
    issues: List[ValidationIssue] = []
    passed: bool = False


class GovernanceIssue(BaseModel):
    title: str
    description: str
    affected_component: Optional[str]
    recommendation: Optional[str]


class ExplainabilityRecord(BaseModel):
    decision: str
    confidence: float
    evidence: List[str] = []
    rules_applied: List[str] = []
    human_review: Optional[str]


class DecisionTrace(BaseModel):
    traces: List[ExplainabilityRecord] = []


class TicketDraft(BaseModel):
    title: str
    category: str
    severity: str
    affected_component: Optional[str]
    description: str
    suggested_fix: str
    rationale: Optional[str]
    owner_hint: Optional[str]
