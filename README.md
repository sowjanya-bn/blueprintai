# BlueprintAI

**BlueprintAI** is an AI‑assisted **design system planning and
compliance copilot** for regulated web delivery workflows.

It converts a high‑level webpage brief into an explainable, reviewable
and governed **page blueprint** by combining:

• requirement extraction\
• semantic retrieval over design‑system components (RAG)\
• blueprint variant generation\
• semantic compliance risk detection\
• human review checkpoints\
• developer handoff generation

Instead of generating arbitrary UI or code, BlueprintAI helps teams move
from:

**brief → structured requirements → design‑system aligned blueprint →
compliance review → approved implementation**

This prototype explores how AI can support **governed web delivery** in
environments such as healthcare, pharma, finance and other
compliance‑sensitive domains.

------------------------------------------------------------------------

# Why BlueprintAI

Modern organisations maintain large **design systems** and strict
**compliance processes**.

When a team receives a webpage brief they must determine:

• which design system components to use\
• how those components should be structured\
• whether regulatory review is required\
• how the page should be implemented by developers

This process often involves many manual steps across design, product,
regulatory and engineering teams.

BlueprintAI accelerates this process while keeping **humans in control
of critical decisions**.

------------------------------------------------------------------------

# Core Workflow

The system follows a human‑centred AI workflow.

    Brief
      ↓
    Requirement Extraction
      ↓
    Design System Retrieval (RAG)
      ↓
    Blueprint Variant Generation
      ↓
    Compliance Risk Assessment
      ↓
    Human Review & Approval
      ↓
    Developer Handoff

This workflow ensures AI **assists planning without bypassing
governance**.

------------------------------------------------------------------------

# Key Features

## 1. Brief Interpretation

The user provides a natural language webpage brief such as:

    Create a patient-facing webpage for a migraine treatment in the UK.
    Explain the treatment in simple language, include safety information,
    FAQs, and a clear next step to speak with a doctor.

BlueprintAI extracts structured signals such as:

• audience\
• market\
• content type\
• compliance sensitivity

These signals guide blueprint generation and compliance checks.

------------------------------------------------------------------------

## 2. RAG over Design‑System Components

BlueprintAI retrieves relevant components from a design‑system knowledge
base using semantic similarity.

Example components:

• Hero\
• Treatment Overview Cards\
• Safety Accordion\
• FAQ Section\
• CTA Block\
• Disclaimer Footer

Embeddings are generated using SentenceTransformers and similarity
search determines which components best match the brief.

This ensures the generated blueprint remains aligned with **approved
design system components**.

------------------------------------------------------------------------

## 3. Blueprint Variant Generation

Instead of producing a single answer, the LLM generates **multiple
blueprint variants**.

Each variant includes:

• component sequence\
• content summary\
• rationale\
• fit score\
• confidence

Example:

    Variant: Educational Treatment Page

    Hero
    → Treatment Overview Cards
    → Safety Accordion
    → FAQ Section
    → CTA Block
    → Disclaimer Footer

Variants allow teams to **compare structured delivery options** rather
than accept a single AI output.

------------------------------------------------------------------------

## 4. Pattern Reasoning

For each blueprint variant the system explains **why** the structure was
chosen.

Example reasoning may include:

• hero establishes immediate context and next step\
• overview cards simplify complex medical concepts\
• accordion manages dense safety information\
• FAQs reduce patient uncertainty

This improves transparency and supports design reviews.

------------------------------------------------------------------------

## 5. Semantic Compliance Detection

BlueprintAI includes a compliance engine that combines:

• rule‑based checks\
• semantic similarity matching\
• keyword signals\
• severity scoring\
• confidence scoring

Flags may include review categories such as:

• medical claim review\
• safety information review\
• patient‑facing content review\
• market‑specific compliance review\
• accessibility review

Each flag contains:

• review category\
• severity level\
• confidence\
• semantic match evidence\
• explanation for the flag

This helps teams identify governance risks **before implementation
begins**.

------------------------------------------------------------------------

## 6. Explainable Evidence

BlueprintAI surfaces the evidence behind AI decisions.

For compliance checks and component reasoning the system can display:

• matched brief text\
• matched policy examples\
• similarity scores\
• reasoning explanations

This improves trust and supports auditability.

------------------------------------------------------------------------

## 7. Human‑in‑the‑Loop Review

The interface highlights where **human approval is required**.

Typical stakeholders may include:

• medical affairs\
• regulatory teams\
• accessibility QA\
• product or design leads

This ensures AI outputs remain **reviewable and governable**.

------------------------------------------------------------------------

## 8. Variant Approval

Users can inspect multiple blueprint variants and approve the one that
best fits the brief.

This encourages **decision support rather than blind automation**.

------------------------------------------------------------------------

## 9. Developer Handoff

After approval the system produces a developer‑ready page structure.

Example output:

    Page Type: Patient Treatment Page

    Layout
    1. Hero
    2. Treatment Overview Cards
    3. Safety Accordion
    4. FAQ Section
    5. CTA Block
    6. Disclaimer Footer

Each component may include:

• content guidance\
• accessibility notes\
• implementation hints

This bridges the gap between design planning and engineering.

------------------------------------------------------------------------

## 10. Wireframe Preview

BlueprintAI includes a lightweight visual preview that approximates the
layout structure.

This allows teams to quickly validate page flow before implementation.

------------------------------------------------------------------------

# Example Output Structure

Example simplified output:

``` json
{
  "requirements": {
    "audience": "UK migraine patients",
    "market": "United Kingdom",
    "content_type": "Patient education page"
  },
  "variants": [
    {
      "pattern_name": "Educational Flow",
      "fit_score": 0.94
    }
  ],
  "compliance": {
    "flags": [
      {
        "review_type": "medical_claim_review",
        "severity": "high",
        "confidence": "medium"
      }
    ]
  }
}
```

------------------------------------------------------------------------

# User Interface

The Streamlit UI presents the workflow clearly.

Main sections include:

• Blueprint\
• Variants\
• Compliance & Review\
• Evidence\
• Developer Handoff\
• Wireframe Preview

This structure mirrors a real web delivery pipeline.

------------------------------------------------------------------------

# Technology Stack

Frontend\
• Streamlit

AI / LLM\
• Google Gemini Flash

Embeddings\
• SentenceTransformers

Retrieval\
• Semantic similarity search

Backend\
• Python

------------------------------------------------------------------------

# System Architecture

    User Brief
        ↓
    Requirement Extraction (LLM)
        ↓
    Component Retrieval (Embeddings + RAG)
        ↓
    Blueprint Variant Generation (LLM)
        ↓
    Compliance Detection (Semantic + Rules)
        ↓
    Human Governance Layer
        ↓
    Developer Handoff

------------------------------------------------------------------------

# Running the Project

Create a virtual environment

    python -m venv blue
    source blue/bin/activate

Install dependencies

    pip install -r requirements.txt

Add environment variables

    export GEMINI_API_KEY=your_api_key
    export GEMINI_MODEL=gemini-2.0-flash

Run the application

    streamlit run app.py

------------------------------------------------------------------------

# Future Improvements

Possible extensions include:

• stronger compliance policy libraries\
• accessibility validation engine\
• richer component knowledge graphs\
• design token mapping\
• Figma integration\
• frontend code scaffolding\
• workflow persistence and reviewer attribution\
• evaluation metrics for blueprint quality

------------------------------------------------------------------------

# Why This Matters

AI can accelerate web delivery only if it respects real organisational
constraints.

BlueprintAI demonstrates how AI can assist while maintaining:

• design‑system alignment\
• explainability\
• governance oversight\
• human decision control

This approach enables **AI‑assisted delivery without sacrificing
compliance or trust**.

------------------------------------------------------------------------

# License

Prototype created for hackathon experimentation.
