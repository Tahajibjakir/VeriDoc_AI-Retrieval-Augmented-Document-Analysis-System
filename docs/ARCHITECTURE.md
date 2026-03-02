Questionnaire Agent – Final Production Architecture (Single Document)
1. System Overview

The Questionnaire Agent is a full-stack system designed to automate due diligence questionnaire (DDQ) completion using Retrieval-Augmented Generation (RAG). The system prioritizes:

Reliable ingestion of real-world documents

Verifiable, citation-backed answers

Human-in-the-loop validation

Auditability and regeneration safety

Async processing for scalability

Technology stack:

Backend:

FastAPI

SQLAlchemy + SQLite/PostgreSQL

ChromaDB (vector storage)

PyMuPDF (PDF parsing)

Groq API (LLM) + OpenAI/HuggingFace (Embeddings)

Pydantic v2

Frontend:

Next.js 14+ (App Router)

React 18 + TypeScript

Tailwind CSS

Axios / Fetch API

Shadcn/UI (Recommended)

All heavy operations (ingestion, parsing, generation, evaluation) are asynchronous and tracked via Job records.

2. Core Data Model (Production-Ready & Fully Normalized)

The system uses strict relational modeling with enforced foreign keys.

2.1 Project

Represents a single DDQ engagement.

Fields:

id (PK)

name

client_name

due_date

scope_type (ENUM: SINGLE_SOURCE | ALL_DOCS)

status (ENUM: DRAFT | INDEXING | READY | GENERATING | REVIEW | OUTDATED | COMPLETED | FAILED)

config_hash (detects regeneration need)

created_at

updated_at

Behavior:

SINGLE_SOURCE → scoped only to project documents

ALL_DOCS → depends on global corpus

When a new global document is indexed:
→ All ALL_DOCS projects automatically transition to OUTDATED

This enforces document freshness.

2.2 Document

Uploaded file.

Fields:

id (PK)

project_id (nullable for global corpus)

filename

file_path

md5_hash

status (ENUM: PENDING | IN_PROGRESS | COMPLETED | FAILED)

version

is_global (bool)

created_at

Behavior:

MD5 prevents duplicates

Version incremented if file changes

Global documents affect ALL_DOCS projects

2.3 DocumentChunk (Parent–Child Indexing)

Supports precise retrieval + contextual grounding.

Fields:

id (PK)

document_id (FK)

parent_section_id (nullable FK)

chunk_text

chunk_type (ENUM: PARENT | CHILD)

embedding_id (Chroma reference)

page_number

bbox_json

created_at

Design:

CHILD chunks → used for similarity search

PARENT chunks → passed to LLM for context

Citations always reference CHILD chunks

2.4 Questionnaire

Fields:

id (PK)

project_id (FK)

filename

parsing_status (ENUM: PENDING | IN_PROGRESS | COMPLETED | FAILED)

version

created_at

2.5 Question

Fields:

id (PK)

questionnaire_id (FK)

project_id (FK)

section_header

question_number

question_text

order_index

assigned_to (nullable)

created_at

Supports:

Stable numbering (1.1, 1.2, etc.)

Assignment for missing data workflow

2.6 Answer (Logical Container)

Represents answer state.

Fields:

id (PK)

question_id (FK)

project_id (FK)

current_version_id (FK → AnswerVersion)

status (ENUM: DRAFT | CONFIRMED | REJECTED | MANUAL_UPDATED | MISSING_DATA)

last_generated_at

created_at

2.7 AnswerVersion (Full Audit Trail)

Preserves AI and human outputs.

Fields:

id (PK)

answer_id (FK)

source_type (ENUM: AI | HUMAN)

answer_text

answerability (ENUM: ANSWERABLE | NO_DATA_FOUND)

confidence_score (1–10)

generation_config_hash

created_at

Rules:

AI regeneration creates new AI version

Manual edits create HUMAN version

No version is ever overwritten

current_version_id determines active answer

2.8 Citation

Fields:

id (PK)

answer_version_id (FK)

document_chunk_id (FK)

citation_text

relevance_score

page_number

bbox_json

Citations are tied to AnswerVersion to preserve audit integrity.

2.9 Job (Async Task Engine)

Fields:

id (PK)

job_type (ENUM: INGEST | GENERATE | PARSE_QUESTIONNAIRE | EVALUATE)

project_id

status (ENUM: QUEUED | RUNNING | COMPLETED | FAILED)

progress_percent

error_message

created_at

completed_at

Used for:

Document ingestion

Questionnaire parsing

Answer generation

Evaluation

2.10 Evaluation

Fields:

id (PK)

project_id

question_id

ai_version_id

human_version_id

semantic_similarity_score (0–1)

keyword_overlap_score (0–1)

citation_match_score (0–1)

final_score (0–1)

qualitative_feedback

created_at

Final score = weighted combination of metrics.

3. Document Ingestion Pipeline

Steps:

User uploads file

Document row created (PENDING)

INGEST Job created

Background worker:

Parse file (PyMuPDF / structured loader)

Extract layout + tables

Chunk into parent + child

Generate embeddings

Store in Chroma with metadata (project_id, document_id)

Store DocumentChunks in SQL

Mark Document COMPLETED

Failure:

If one document fails, it does not block other documents

Document.status = FAILED

If document is_global = true:

All ALL_DOCS projects → status = OUTDATED

4. Questionnaire Parsing & Lifecycle

Flow:

Upload questionnaire

PARSE_QUESTIONNAIRE job created

Background parsing:

Extract structured rows

Handle merged cells

Normalize numbering

Questions inserted

Project.status → READY

If:

Config changes

Scope changes

Documents updated

Then:
→ Project.status = OUTDATED

5. Answer Generation (RAG Pipeline)

Per Question:

Construct retrieval query

Retrieve top K CHILD chunks

Expand to PARENT sections

If similarity below threshold:
→ Create AI version with answerability = NO_DATA_FOUND
→ status = MISSING_DATA

Else:
→ Generate grounded answer
→ Must begin with:

“Based on the provided documents…” OR

“The documents do not contain information about…”
→ Attach citations
→ Store confidence score
→ Create new AI AnswerVersion
→ Update Answer.current_version_id

Never hallucinate beyond retrieved chunks.

6. Review Workflow

Answer.status transitions:

DRAFT → CONFIRMED

DRAFT → REJECTED

DRAFT → MANUAL_UPDATED

DRAFT → MISSING_DATA

Manual Edit:

Create new HUMAN AnswerVersion

Set as current_version_id

status = MANUAL_UPDATED

AI regeneration:

Does NOT overwrite HUMAN versions

Creates new AI version

Human must explicitly switch back if desired

7. Evaluation Framework

When triggered:

For each question:

Identify latest AI version

Identify latest HUMAN version (ground truth)

Compute:

Semantic similarity (embedding cosine)

Keyword overlap

Citation match accuracy

Generate qualitative feedback via LLM judge

Compute weighted final_score

Exportable as:

CSV

JSON

Report includes:

Question
AI Answer
Human Answer
Semantic Score
Keyword Score
Citation Score
Final Score
Feedback

8. Optional Chat Extension

Endpoint: /chat

Rules:

Uses same vector store

Same citation format

Same grounding constraints

Maintains last 3–5 turns of memory

Read-only (does not modify questionnaire data)

9. Frontend UX
Project List

Card layout

Status badge (INDEXING, READY, OUTDATED)

Regenerate button when OUTDATED

Project Detail

Document manager

Questionnaire status

Job progress

Review Interface (Split Layout)

Left:

Question list

Center:

Active answer

Confidence score

Editable textarea

Approve / Reject / Regenerate

Right:

Citation viewer

Click → opens PDF at page + bbox

Evaluation Screen

Side-by-side AI vs Human

Highlight differences

Show numeric scores

Export button

10. End-to-End Workflow

Upload → Ingest → Parse → Generate → Review → Evaluate → Export

Async status always tracked via Job table.