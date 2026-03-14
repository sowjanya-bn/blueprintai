from __future__ import annotations

import json
from pathlib import Path
from src.llm import generate_json
from src.retriever import retrieve_components
from src.compliance_engine import ComplianceEngine

compliance_engine = ComplianceEngine()


def load_prompt(name: str) -> str:
    path = Path("prompts") / name
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

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

    prompt_template = load_prompt("blueprint_generation.txt")

    prompt = (
        prompt_template
        .replace("[[BRIEF]]", brief)
        .replace("[[EVIDENCE_TEXT]]", evidence_text)
        .replace("[[ALLOWED_COMPONENT_NAMES]]", "\n".join(allowed_component_names))
    )

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