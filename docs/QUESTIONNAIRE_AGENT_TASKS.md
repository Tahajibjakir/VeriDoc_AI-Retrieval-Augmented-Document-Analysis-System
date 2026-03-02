Questionnaire Agent — Task Description & Acceptance Criteria

Background
You are implementing a full-stack solution for the Questionnaire Agent. The
system ingests and indexes documents, parses questionnaire files, auto-generates
answers with citations, and supports review workflows plus evaluation against
human ground-truth.

This is a take-home exercise: do not build any code framework. Provide task
descriptions only, with clear acceptance criteria.

Scope of Work (Task Descriptions)

1) Product & Data Model Alignment
- Define end-to-end data flow for questionnaire projects, documents, questions,
  answers, references, and evaluation results.
- Map API request/response models to database entities and storage layout.
- Ensure enumerations and status transitions are captured (Project, Answer,
  Request).

2) Document Ingestion & Indexing
- Describe how multiple formats (PDF, DOCX, XLSX, PPTX) are ingested and parsed.
- Propose a multi-layer index:
  - Layer 1: answer retrieval (section or semantic retrieval)
  - Layer 2: citation chunks with bounding box references
- Define how new documents mark ALL_DOCS projects as OUTDATED.

3) Questionnaire Parsing & Project Lifecycle
- Describe how questionnaires are parsed into sections and questions, with
  ordering.
- Define lifecycle behavior for creating and updating projects (async).
- Explain how automatic regeneration is triggered when configuration changes.

4) Answer Generation with Citations & Confidence
- Describe answer generation behavior:
  - Must indicate if answer is possible
  - Must include citations at chunk level
  - Must include confidence score
- Define fallback behavior when no documents are relevant.

5) Review & Manual Overrides
- Describe review workflow: CONFIRMED / REJECTED / MANUAL_UPDATED / MISSING_DATA.
- Explain how manual answers are stored alongside AI results for comparison.

6) Evaluation Framework
- Define how generated answers are compared to human ground truth.
- Specify similarity metrics or approach (semantic similarity + keyword overlap).
- Describe evaluation outputs and reporting.

7) Optional Chat Extension
- Describe how chat uses the same indexed document corpus and citations.
- Define constraints to avoid conflicting with questionnaire flows.

8) Frontend Experience (High-Level)
- Describe UI screens: project list, project detail, question review, document
  management, evaluation report.
- Specify user interactions required for project creation, status tracking, and
  review workflow.

Acceptance Criteria

A. Documentation Completeness
- Document includes all 8 scope areas above.
- Every API endpoint listed is explained in context (create, update, answer,
  index, status).
- Data structures in the spec are mapped to the system design.

B. Functional Accuracy
- Workflow shows: upload -> index -> create project -> generate answers -> review
  -> evaluation.
- Answers always include: answerability statement + citations + confidence score.
- Projects with ALL_DOCS become OUTDATED when new docs are indexed.

C. Review & Auditability
- Manual edits are preserved alongside AI results.
- Answer status transitions are explicitly described.

D. Evaluation Framework
- Clear method for comparing AI vs. human answers.
- Output includes a numeric score and qualitative explanation.

E. Non-Functional Requirements
- Async processing and status tracking are described.
- Error handling, missing data, and regeneration logic are described.

F. Frontend UX
- All core user workflows are described:
  - Create/update project
  - Review answers
  - Track background status
  - Compare AI vs. human
