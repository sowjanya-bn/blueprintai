from __future__ import annotations

import json

from src.compliance import check_compliance
from src.llm import generate_json
from src.retriever import retrieve_components
from src.compliance_engine import ComplianceEngine

compliance_engine = ComplianceEngine()


def create_blueprint(brief: str) -> dict:
    retrieved = retrieve_components(brief, top_k=5)

    evidence_blocks = []
    allowed_component_names = []

    for item in retrieved:
        component = item["component"]
        evidence = item["evidence"]
        score = round(item["score"], 3)

        allowed_component_names.append(component["name"])
        evidence_blocks.append(
            f"Component: {component['name']}\n"
            f"Relevance Score: {score}\n"
            f"Evidence:\n{evidence}"
        )

    evidence_text = "\n\n---\n\n".join(evidence_blocks)

    prompt = f"""
You are BlueprintAI, an enterprise web design assistant.

Your job is to convert a webpage brief into a governed page blueprint.

Rules:
- Recommend only from the approved components listed in the retrieved evidence
- Be concise, structured, and realistic
- Prefer explainable choices
- Return valid JSON only
- Generate exactly 3 blueprint variants
- Include confidence scores between 0 and 1
- Include a short pattern_reasoning list explaining why this page structure suits the brief
- The page_specification must be developer-friendly

Webpage brief:
{brief}

Approved retrieved component evidence:
{evidence_text}

Return JSON in this schema:

{{
  "requirements": {{
    "audience": "string",
    "market": "string",
    "content_type": "string",
    "compliance_sensitivity": "Low | Medium | High"
  }},
  "pattern_reasoning": [
    "string"
  ],
  "variants": [
    {{
      "pattern_name": "string",
      "fit_score": 0.0,
      "description": "string",
      "components": [
        {{
          "component_name": "string",
          "content_summary": "string",
          "rationale": "string",
          "confidence": 0.0
        }}
      ]
    }}
  ],
  "human_review_required": ["string"],
  "page_specification": {{
    "page_type": "string",
    "layout": [
      {{
        "component": "string",
        "props": {{}},
        "accessibility_notes": ["string"]
      }}
    ]
  }}
}}

Only use these component names:
{allowed_component_names}
"""

    llm_output = generate_json(prompt)

    try:
        data = json.loads(llm_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini did not return valid JSON:\n{llm_output}") from e

    if isinstance(data, list):
        if len(data) == 1 and isinstance(data[0], dict):
            data = data[0]
        else:
            raise ValueError(
                f"Expected a JSON object or single-item list containing an object, but got list:\n{data}"
            )

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected Gemini to return a JSON object, but got {type(data).__name__}:\n{data}"
        )


    compliance = compliance_engine.run(brief)
    data["compliance_flags"] = compliance
    data["retrieved_evidence"] = retrieved
    return data