
# BlueprintAI
AI-Assisted Page Blueprint & Compliance Recommender

## Overview
BlueprintAI is an AI-powered assistant that converts a webpage brief into a compliant page blueprint using approved design-system components, with explainable reasoning and human review checkpoints.

Modern web teams managing large digital portfolios face a major challenge: translating high-level briefs into pages that remain consistent with design systems, accessibility rules and regulatory requirements. This process is often manual and slow.

BlueprintAI accelerates this step by automatically interpreting a brief, recommending an approved page structure and highlighting areas that require human compliance review.

The system demonstrates how AI can assist web teams across the design-to-delivery workflow while maintaining transparency and human oversight.

---

## Problem

Large organisations maintain thousands of webpages across markets, audiences and regulatory environments.

The difficulty is not building pages.
The difficulty is translating a brief into a compliant page structure.

Typical workflow:

Strategy → Design → Development → QA → Legal Review → Launch

Manual interpretation between each stage creates delays and inconsistencies.

Teams must decide:
- what components should appear on the page
- what compliance elements are required
- what needs legal or medical review
- how to structure the page for accessibility and clarity

BlueprintAI focuses on the earliest bottleneck:

brief → page blueprint

---

## Solution

BlueprintAI generates a governed page blueprint grounded in design system documentation.

The system performs four main tasks:

1. Interpret a webpage brief
2. Recommend a page structure using approved components
3. Explain why each component was selected
4. Flag areas requiring compliance or human review

Instead of producing arbitrary layouts, BlueprintAI ensures the output remains aligned with an organisation’s design system and governance requirements.

---

## Example

### Input Brief

UK patient-facing page explaining migraine treatment  
Include safety information and a next-step call to action

### Extracted Requirements

Audience: Patients  
Market: UK  
Content type: Treatment explanation  
Compliance sensitivity: High

### Recommended Page Blueprint

Hero Section  
Intro Text Block  
Treatment Overview Cards  
Safety Information Accordion  
FAQ Section  
CTA Block  
Legal Disclaimer Footer

### Compliance Flags

⚠ Medical claims require regulatory review  
⚠ Safety information must be validated  
⚠ Disclaimer wording requires legal approval

---

## System Workflow

User Brief  
↓  
Requirement Extraction  
↓  
Retrieve Design System Knowledge  
↓  
Page Blueprint Generation  
↓  
Compliance Rule Layer  
↓  
Structured Output

The system combines natural language understanding, retrieval over design system documentation and rule-based governance checks.

---

## Architecture

Brief Input  
↓  
LLM Requirement Extraction  
↓  
Vector Retrieval (Design System Docs)  
↓  
Blueprint Generation  
↓  
Compliance Rules Engine  
↓  
Page Blueprint + Review Flags

---

## Key Features

### AI Brief Interpretation
Understands user intent, audience and content requirements.

### Design-System Grounded Recommendations
Components are selected from an approved component library.

### Explainable AI
Each recommendation includes a reason and supporting documentation.

### Compliance Awareness
The system flags areas requiring legal, regulatory or accessibility review.

### Human Oversight
AI suggestions are transparent and designed to support human decision-making rather than replace it.

---

## Technology Stack

Frontend  
Streamlit or lightweight React interface

Backend  
Python API

LLM  
OpenAI / Claude / Gemini

Vector Database  
Chroma or FAISS

Embeddings  
Text embedding models

Rule Engine  
Simple Python policy layer

---

## Component Knowledge Base

BlueprintAI relies on a curated design-system component library.

Example components:

- Hero
- Intro Text Block
- Feature Grid
- Treatment Overview Cards
- Safety Accordion
- FAQ Section
- CTA Banner
- Testimonial Strip
- Disclaimer Footer

Each component includes metadata such as:

- Purpose
- Use Cases
- Avoid Cases
- Accessibility Notes
- Related Components

This information is embedded and indexed to support retrieval.

---

## Structured Output Example

{
  "page_type": "patient_treatment_page",
  "components": [
    "hero",
    "intro_text",
    "treatment_cards",
    "safety_accordion",
    "faq",
    "cta_block",
    "disclaimer_footer"
  ],
  "review_flags": [
    "medical_claim_review",
    "legal_disclaimer_review"
  ]
}

---

## Demo Flow

1. User enters a webpage brief
2. AI extracts structured requirements
3. System retrieves relevant design-system knowledge
4. Page blueprint is generated
5. Compliance review flags are displayed

The interface shows:
- what the AI understood
- what it recommended
- why it recommended it
- what requires human approval

---

## Future Extensions

Possible extensions beyond the hackathon include:

- HTML component scaffold generation
- Figma design token integration
- automated accessibility validation
- Jira ticket generation for compliance issues
- design system drift detection

---

## Why This Matters

BlueprintAI demonstrates how AI can support web teams by turning briefs into structured, compliant page blueprints. The system improves delivery speed while maintaining consistency, transparency and human oversight.
