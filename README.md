# Veridoc AI - Due Diligence Assistant

Veridoc AI is a full-stack, AI-powered system designed to automate due diligence and answer complex questionnaires based on uploaded reference documents. It utilizes Retrieval-Augmented Generation (RAG) to accurately parse large documents, understand context, and generate precise answers to user-provided questionnaires.

---


<h1 align="center">Project Output (UI)</h1>

<p align="center">
  <img src="https://github.com/user-attachments/assets/893b83b3-7d38-459a-9fc2-f02b99358b5f" width="100%" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/961a9818-a3ca-4454-bb8b-91188d86c152" width="100%" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/dd630353-6800-4bb8-bd24-7604b6eaf9d8" width="100%" />
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/f1cdcf29-3bdd-4c18-b6e8-3b04596875d0" width="100%" />
</p>

## 🏗 Detailed Architecture

Veridoc AI follows a modern decoupled architecture, separating the client-side presentation from the server-side AI processing and data persistence.

### 1. Frontend Architecture (Client Layer)
The frontend is built for performance, responsiveness, and a smooth user experience.
- **Framework:** Next.js 14+ (App Router) with React 19.
- **Language:** TypeScript for type safety.
- **Styling:** Tailwind CSS with a custom global theme supporting both Light and Dark modes.
- **Authentication:** Google OAuth via `@react-oauth/google`, managing JWT tokens securely in local context.
- **State Management:** React Context API (`AuthProvider` and `ThemeProvider`) wrapped around the root layout.
- **Routing Structure:**
  - `/` - Landing Page highlighting system features and workflow.
  - `/projects` - Dashboard rendering the list of active due diligence projects.
  - `/projects/new` - Interface to create a new project.
  - `/projects/[id]` - Detailed project view supporting document uploads and questionnaire generation.
  - `/profile` - User profile and settings.
  - `/documentation` - System documentation and API reference.

### 2. Backend Architecture (API & Application Layer)
The backend is a high-performance RESTful API responsible for orchestration, business logic, asynchronous processing, and AI integration.
- **Framework:** FastAPI (Python 3.10+).
- **ORM & Data Validation:** SQLAlchemy (for database interactions) and Pydantic v2 (for schema validation and serialization).
- **Core Modules:**
  - `api/` - HTTP route handlers (Routers: Auth, Users, Projects, Documents, Questionnaires).
  - `services/ingestion.py` - Manages text extraction, chunking, and embedding generation for newly uploaded documents.
  - `services/generation.py` - Orchestrates the LLM prompt building and context retrieval to answer specific questions.
  - `services/parser.py` - Utilizes PyMuPDF to extract clean text from complex PDF documents.
  - `services/jobs.py` - Handles asynchronous execution of long-running tasks like document ingestion and bulk generation to avoid blocking the API.
- **Authentication:** JWT-based authentication via `python-jose` and `passlib`.

### 3. Data Storage Layer
Data is bifurcated into standard relational data and high-dimensional vector data.
- **Relational Database:** SQLite (`sql_app.db`) used as the default datastore via SQLAlchemy. It stores Users, Projects, Document Metadata, Questionnaires, and generated Answers.
- **Vector Database:** ChromaDB (`chroma_db/`) used for local persistence of document embeddings. It enables rapid semantic search during the retrieval phase of the RAG pipeline.

### 4. AI & Processing Engine (The RAG Pipeline)
- **Document Parsing:** PDF parsing using `PyMuPDF` to extract textual content.
- **Embeddings:** Text is chunked and embedded using OpenAI or HuggingFace embeddings (configurable via environment variables). Embedded chunks are stored in ChromaDB.
- **LLM Inference:** The system leverages the Groq API (or Google Gemini) for blitz-fast language model inference. Upon receiving a questionnaire, the system retrieves the most relevant document chunks from ChromaDB and passes them to the LLM as verified context to generate accurate answers.

---

## 📋 Prerequisites

To run this project locally, you will need:
- **Node.js:** v18 or highly recommended v20+
- **Python:** v3.10+
- **API Keys:** 
  - Groq API Key (for LLM generation)
  - Google Client ID (for OAuth)

---

## 🚀 Setup & Installation

### Step 1: Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a Python virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Duplicate `.env.example` and rename it to `.env`:
   ```bash
   cp .env.example .env
   ```
   *Make sure to populate your `.env` file with the required `GROQ_API_KEY` and secret keys.*

5. **Run the Backend Server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   - The API will be available at: `http://localhost:8000`
   - Interactive Swagger API Docs: `http://localhost:8000/docs`

### Step 2: Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Environment Variables:**
   Create a `.env.local` file in the `frontend` directory and add the necessary variables:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here
   ```

4. **Run the Frontend Development Server:**
   ```bash
   npm run dev
   ```
   - The web app will be accessible at: `http://localhost:3000`

---

## 💡 Usage Workflow

1. **Authenticate:** Open the frontend (`http://localhost:3000`) and log in using Google OAuth.
2. **Create Project:** Navigate to your Dashboard and click "New Project" to define a due diligence engagement.
3. **Ingest Knowledge:** Open the newly created project and upload reference documents (PDFs). The backend will automatically parse, chunk, embed, and index these documents into ChromaDB.
4. **Generate Answers:** Upload a Questionnaire or type questions manually. The application will use RAG against your indexed documents to generate precise, context-aware answers.

---

## 🛡️ Best Practices & Git
- The backend virtual environment (`venv/`), Python cache (`__pycache__/`), and database files (`sql_app.db`, `chroma_db/`) should not be committed.
- The frontend `node_modules` and Next.js build output (`.next/`) are ignored via `.gitignore`.
- Ensure `.env` and `.env.local` files remain strictly local and untracked to protect secrets.
