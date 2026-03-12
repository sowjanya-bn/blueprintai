import json
from sentence_transformers import SentenceTransformer, util

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def load_components():
    with open("data/components.json", "r", encoding="utf-8") as f:
        return json.load(f)


def build_component_text(component: dict) -> str:
    return f"""
Component: {component['name']}
Purpose: {component.get('purpose', '')}
Use when: {', '.join(component.get('use_when', []))}
Avoid when: {', '.join(component.get('avoid_when', []))}
Accessibility notes: {', '.join(component.get('accessibility_notes', []))}
""".strip()


def retrieve_components(query: str, top_k: int = 5):
    components = load_components()
    texts = [build_component_text(c) for c in components]

    model = get_model()
    embeddings = model.encode(texts, convert_to_tensor=True)
    query_embedding = model.encode(query, convert_to_tensor=True)

    scores = util.cos_sim(query_embedding, embeddings)[0]

    ranked = sorted(
        [
            {
                "component": component,
                "evidence": text,
                "score": float(score)
            }
            for component, text, score in zip(components, texts, scores)
        ],
        key=lambda x: x["score"],
        reverse=True
    )

    return ranked[:top_k]