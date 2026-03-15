# Blueprint AI

> **A research prototype for AI-assisted orchestration of the web design and development lifecycle — from client brief to deployable web experience — with built-in validation, governance, and explainable decision making.**

---

# Overview

The **Blueprint AI** is a research prototype that explores how artificial intelligence can accelerate the **entire web design and delivery lifecycle**, rather than simply generating UI or code from prompts.

Most current AI web tools focus on a simplified pipeline:

```
Prompt → UI → Code
```

While useful for prototyping, this approach does not address the broader workflow required in real-world web development, where teams must manage:

* requirement interpretation
* architecture planning
* UX design
* design-system integration
* accessibility validation
* regulatory compliance
* security checks
* deployment and maintenance

The goal of this project is to design a system where **AI coordinates the workflow across these stages**, while humans retain control over key decisions.

This repository contains a **prototype implementation** demonstrating how AI can assist with:

* interpreting web project briefs
* recommending design-system components
* generating page blueprints
* validating accessibility and compliance
* detecting design-system drift
* producing explainable reports and suggested fixes

---

# Key Objectives

The system is designed to address several challenges faced by organisations delivering web experiences at scale.

### Lifecycle Fragmentation

Modern web development involves multiple stages handled by different teams:

```
Client Brief
→ Requirement Analysis
→ Architecture Planning
→ UX Design
→ Component Integration
→ Code Development
→ Testing & QA
→ Compliance Checks
→ Deployment
```

These stages often lack automation and coordination.

---

### Design System Drift

Over time, teams may:

* create custom components outside the design system
* use deprecated UI patterns
* introduce inconsistent tokens or styles

This leads to **design-system drift** across projects.

---

### Compliance and Accessibility Risks

Web applications must comply with regulations and standards such as:

* GDPR (data privacy)
* WCAG accessibility guidelines
* cookie consent requirements
* market-specific regulations

These checks are frequently performed **late in the development lifecycle**, increasing risk.

---

# Proposed Solution

The **AI Web Design Lifecycle Orchestrator** coordinates the entire web delivery pipeline using:

* **multi-agent AI workflows**
* **retrieval augmented generation (RAG)**
* **knowledge graphs**
* **rule-based policy enforcement**
* **automated validation systems**
* **human review checkpoints**

Rather than replacing developers and designers, the system **assists teams by orchestrating lifecycle stages and providing explainable recommendations.**

---

# Architecture Overview

The system follows a **layered architecture**, separating generation, validation, governance, and human oversight.

```
Input & Context Layer
        ↓
Knowledge & Retrieval Layer
        ↓
Intelligence & Multi-Agent Orchestration
        ↓
Delivery / Generation Layer
        ↓
Validation Layer
        ↓
Governance Layer
        ↓
Explainability & Audit Layer
        ↓
Human Review Layer
```

This separation ensures that generated outputs are **independently validated before deployment**, improving reliability and trust.

---

# Architecture Layers

## 1. Input and Context Layer

This layer collects all information required to initiate the web delivery workflow.

Typical inputs include:

* client briefs
* stakeholder notes
* brand guidelines
* design-system documentation
* accessibility standards
* regulatory policies
* architecture templates
* localisation requirements
* previously approved UI patterns

### Responsibilities

* document ingestion
* requirement parsing
* metadata extraction
* creation of structured project context

---

## 2. Knowledge and Retrieval Layer

This layer provides contextual knowledge required for grounded AI reasoning.

### Vector Database

Stores embeddings of documents including:

* brand guidelines
* design-system documentation
* compliance rules
* accessibility standards
* architecture templates

Supports **retrieval augmented generation (RAG)**.

---

### Knowledge Graph

Represents relationships between:

* requirements
* pages
* components
* APIs
* compliance policies
* localisation variants

This enables traceability across the system.

---

### Rule / Policy Engine

Enforces deterministic constraints such as:

* approved component variants
* required consent flows
* typography and colour tokens
* regulatory constraints

---

## 3. Intelligence and Orchestration Layer

This layer coordinates the workflow using a **multi-agent architecture**.

A central **Orchestrator Agent** assigns tasks to specialised agents.

### Core Agents

**Brief Understanding Agent**

Extracts structured requirements from client briefs.

---

**Requirements & Knowledge Graph Agent**

Constructs structured project representations within the knowledge graph.

---

**Architecture and Planning Agent**

Generates:

* sitemap structures
* page hierarchies
* integration architecture
* localisation strategies

---

**UX and Journey Agent**

Produces:

* user journeys
* layout suggestions
* CTA placement logic
* usability recommendations

---

**Design-System Retrieval Agent**

Retrieves approved UI components using semantic search.

---

**Code Generation Agent**

Generates page templates and component scaffolds.

---

**Content and Tone Agent**

Ensures generated content aligns with brand voice.

---

**Explainability Agent**

Provides explanations for system decisions.

---

# Delivery Layer

The Delivery Layer generates **structured artefacts used throughout the web development lifecycle.**

Examples include:

* requirement documents
* sitemap structures
* wireframes
* page blueprints
* component composition plans
* code templates
* deployment manifests

Rather than producing a full website directly, the system generates **structured intermediate artefacts** to improve traceability.

---

# Validation Layer

All generated outputs pass through an independent validation pipeline.

### Accessibility Validation

Ensures compliance with WCAG guidelines by checking:

* colour contrast
* semantic HTML structure
* keyboard accessibility
* alternative text
* form labels

---

### Compliance Validation

Evaluates regulatory requirements such as:

* GDPR consent mechanisms
* privacy policy links
* cookie banner implementation
* personal data handling

---

### Brand Consistency Validation

Verifies alignment with brand guidelines including:

* colour tokens
* typography rules
* spacing tokens
* allowed component usage
* layout conventions

---

### Security Validation

Detects vulnerabilities such as:

* injection risks
* insecure API calls
* exposed secrets
* weak input validation

---

### Performance & SEO Validation

Checks:

* page performance metrics
* metadata structure
* search engine optimisation best practices

---

# Governance Layer

The Governance Layer monitors design-system health across projects.

### Governance checks

* deprecated component detection
* design token drift detection
* off-system UI patterns
* duplicated components
* cross-project consistency monitoring

When inconsistencies are detected, the system recommends upgrades or replacements.

---

# Explainability and Audit Layer

This layer provides transparency into system behaviour.

The system can explain:

* why a component was selected
* which rules were applied
* why validation failed
* which documents influenced decisions
* recommended remediation actions

Explainability improves trust and debugging.

---

# Human Review Layer

Human oversight is integrated throughout the workflow.

### Human checkpoints

1. requirement confirmation
2. architecture approval
3. UX approval
4. validation review
5. governance decisions
6. deployment approval

The system is designed as **AI-assisted orchestration rather than full automation.**

---

# End-to-End Workflow

The orchestrator coordinates the lifecycle through the following stages:

```
1  Brief Intake
2  Requirement Extraction
3  Knowledge Graph Construction
4  Architecture Planning
5  UX & Wireframe Generation
6  Design-System Component Retrieval
7  Blueprint / Code Template Generation
8  Automated Validation
9  Governance Checks
10 Repair & Ticket Generation
11 Deployment Preview
12 Continuous Feedback & Learning
```

---

# Prototype Scope

The research prototype focuses on demonstrating three core capabilities.

### A — Brief-to-Blueprint Generation

The system interprets client briefs and recommends design-system components.

Outputs include:

* page blueprints
* component compositions
* code templates

---

### B — Automated Validation

Generated outputs are evaluated using automated validation checks including:

* accessibility
* brand consistency
* regulatory compliance

---

### C — Design-System Governance

The system detects issues such as:

* deprecated components
* design token drift
* off-system UI patterns

---

# Prototype Interface

The prototype interface is implemented using **Streamlit**.

Streamlit enables rapid development of an interactive research demo without requiring a production frontend framework.

The interface allows users to:

* submit project briefs
* view structured requirements
* inspect generated page blueprints
* review validation reports
* explore governance findings
* inspect explainability outputs
* approve or reject system suggestions

This lightweight interface allows development effort to focus on **AI orchestration and validation logic rather than frontend engineering.**

---

# Technology Stack (Prototype)

### Frontend

* Streamlit

---

### Backend

* Python
* modular service architecture
* FastAPI (optional for API endpoints)

---

### AI / Agent Framework

* LangGraph or CrewAI
* OpenAI or other LLM APIs
* structured prompting
* tool/function calling

---

### Retrieval Layer

* pgvector / Chroma / Pinecone
* document embeddings for design-system documentation and policies

---

### Knowledge Graph

* Neo4j
  or
* relational graph representation in PostgreSQL

---

### Validation Tools

* axe-core (accessibility checks)
* Lighthouse (performance)
* ESLint
* Semgrep (security)
* custom rule engine for brand and compliance validation

---

### Deployment / CI

* GitHub Actions
* Streamlit app deployment
* optional preview environments

---

# Repository Structure (Suggested)

```
ai-web-lifecycle-orchestrator/

agents/
    orchestrator.py
    brief_agent.py
    ux_agent.py
    retrieval_agent.py
    code_agent.py
    explainability_agent.py

validation/
    accessibility_validator.py
    compliance_validator.py
    brand_validator.py
    security_validator.py

governance/
    drift_detector.py
    component_registry.py

knowledge/
    rag_pipeline.py
    knowledge_graph.py
    policy_engine.py

ui/
    streamlit_app.py

docs/
    architecture.md
    workflow.md
```

---

# Benefits

### Faster Web Delivery

AI assists with requirement analysis, component selection, and validation.

---

### Design-System Governance

The system prevents UI drift across projects.

---

### Compliance Support

Automated validation reduces regulatory risk.

---

### Explainable AI

Transparent reasoning enables trust in AI-assisted workflows.

---

### Scalable Architecture

The modular architecture allows additional agents and validation modules to be added easily.

---

# Future Work

Possible future extensions include:

* automated localisation across markets
* integration with design tools such as Figma
* reinforcement learning from human feedback
* automated A/B testing optimisation
* CI/CD pipeline integration
* enterprise design-system management tools

---

# License

This repository is intended for **academic and research purposes**.

---
