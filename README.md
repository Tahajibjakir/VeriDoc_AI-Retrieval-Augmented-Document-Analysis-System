# Questionnaire Agent - Veridoc AI

A full-stack RAG system for automating due diligence questionnaires.

## Architecture

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Shadcn/UI.
- **Backend**: FastAPI, Python 3.10+, SQLAlchemy, Pydantic v2.
- **Database**: SQLite (default) or PostgreSQL.
- **Vector Store**: ChromaDB (local persistence).
- **AI Engine**: Groq API (LLM) + OpenAI/HuggingFace (Embeddings) + PyMuPDF (PDF Parser).

## Prerequisites

- Node.js 18+
- Python 3.10+
- Groq API Key (and optional OpenAI API Key if using OpenAI embeddings)

## Setup Instructions

### 1. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```

Create a virtual environment and activate it:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Configure Environment Variables:
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY
```

Run the Backend Server:
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.
API Documentation: `http://localhost:8000/docs`.

### 2. Frontend Setup

Navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies (if not already installed):
```bash
npm install
```

Configure Environment Variables:
Create `.env.local` (already created by setup script):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Run the Frontend Development Server:
```bash
npm run dev
```
The application will be available at `http://localhost:3000`.

## Usage

1.  Open the Dashboard (`http://localhost:3000`).
2.  Click **New Project** to create a due diligence engagement.
3.  Upload PDF documents in the Project Detail view.
4.  (Coming Soon) Upload a Questionnaire and generate answers.

## Project Structure

- `backend/`: FastAPI application
    - `app/models`: Database models
    - `app/schemas`: Pydantic schemas
    - `app/api`: API endpoints
    - `app/services`: Business logic (Ingestion, RAG, Jobs)
- `frontend/`: Next.js application
    - `src/app`: Pages and Layouts
    - `src/components`: UI Components
    - `src/lib`: Utilities and API client
