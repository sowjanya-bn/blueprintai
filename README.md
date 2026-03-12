
# BlueprintAI

BlueprintAI is an AI-assisted **Design-to-Delivery Accelerator** that converts a webpage brief into an explainable, design‑system compliant page blueprint.  
The project demonstrates how AI can assist web teams in moving from **brief → design system components → governed page blueprint → developer handoff**.

This prototype was built for a hackathon focused on **AI-assisted web delivery workflows**.

---

# Core Idea

Large organisations often maintain **design systems** containing approved UI components.  
When teams receive a webpage brief, designers and developers must decide:

• Which components should be used  
• How they should be structured  
• What compliance checks apply  
• How the final page should be implemented  

BlueprintAI accelerates this process by using:

• **RAG over design-system documentation**
• **AI component recommendations**
• **Explainable reasoning**
• **Compliance flagging**
• **Human approval checkpoints**
• **Developer handoff generation**

---

# Workflow

The system follows a human‑centred AI workflow:

```
Brief
 ↓
Requirement Extraction
 ↓
Component Retrieval (RAG)
 ↓
Blueprint Variant Generation
 ↓
Human Review & Selection
 ↓
Developer Handoff Specification
```

This keeps **humans in control**, which is critical in regulated industries.

---

# Features

## 1. Brief Interpretation

The user provides a webpage brief such as:

```
Create a patient-facing webpage for a migraine treatment in the UK.
Explain the treatment in simple language and include safety information,
FAQs, and a clear next step to speak with a doctor.
```

BlueprintAI extracts:

• Audience  
• Market  
• Content type  
• Compliance sensitivity  

---

## 2. RAG over Design System Components

The system retrieves relevant components from a small design system knowledge base.

Example components:

• Hero  
• Treatment Overview Cards  
• Safety Accordion  
• FAQ Section  
• CTA Block  
• Disclaimer Footer  

Embeddings are generated using:

```
sentence-transformers/all-MiniLM-L6-v2
```

Similarity search determines which components are most relevant to the brief.

---

## 3. Blueprint Variant Generation

The LLM generates **multiple blueprint variants**.

Each variant contains:

• Component sequence  
• Content summary  
• Rationale  
• Confidence score  

Example:

```
Variant: Educational Treatment Page

1. Hero
2. Treatment Overview Cards
3. Safety Accordion
4. FAQ Section
5. CTA Block
6. Disclaimer Footer
```

This provides **explainable planning rather than direct code generation**.

---

## 4. Compliance Flagging

A lightweight rule system flags potential regulatory issues.

Examples:

• Medical claim review required  
• Patient content review required  
• Market-specific compliance review  
• Accessibility audit required  

These flags ensure **governance and oversight**.

---

## 5. Human Review

The UI highlights stakeholders who must approve the blueprint:

• Medical Affairs  
• Regulatory  
• Accessibility QA  

This enforces **human‑in‑the‑loop AI usage**.

---

## 6. Developer Handoff

After approval, the system can generate a **developer page specification**.

Example structure:

```
Page Type: Patient Treatment Page

Layout:
1. Hero
2. Treatment Overview Cards
3. Safety Accordion
4. FAQ Section
5. CTA Block
6. Disclaimer Footer
```

Each component includes:

• Props  
• Accessibility notes  
• Content guidance

This bridges **design → engineering**.

---

# User Interface

The Streamlit UI presents the workflow clearly:

1️⃣ Extracted Requirements  
2️⃣ Generation Summary  
3️⃣ Blueprint Variants  
4️⃣ Compliance Flags  
5️⃣ Human Review Requirements  
6️⃣ Developer Handoff  
7️⃣ Evidence Panel (RAG transparency)

Raw JSON is available for debugging but hidden by default.

---

# Technology Stack

Frontend

• Streamlit

AI

• Google Gemini (Flash models) for reasoning
• Sentence Transformers for embeddings

Retrieval

• Semantic similarity search over component documentation

Backend

• Python

---

# Project Structure

```
blueprintai/
│
├── app.py
│
├── src/
│   ├── blueprint.py
│   ├── retriever.py
│   ├── compliance.py
│   ├── llm.py
│
├── data/
│   └── components.json
│
└── requirements.txt
```

---

# Running the Project

Create a virtual environment

```
python -m venv blue
source blue/bin/activate
```

Install dependencies

```
pip install -r requirements.txt
```

Add environment variables

```
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.0-flash
```

Run the application

```
streamlit run app.py
```

---

# Future Improvements

Possible extensions:

• Visual wireframe generation from blueprint  
• Full Graph‑based component relationships  
• Accessibility validation engine  
• Automated QA rule checking  
• Direct Figma component mapping  
• Code generation for frontend frameworks  

---

# Why This Matters

Modern web platforms contain **thousands of pages and components**.

AI can accelerate delivery only if it:

• respects design systems  
• remains explainable  
• includes human oversight  
• enforces compliance

BlueprintAI demonstrates how **AI can assist without removing governance**.

---

# License

Prototype created for hackathon experimentation.
