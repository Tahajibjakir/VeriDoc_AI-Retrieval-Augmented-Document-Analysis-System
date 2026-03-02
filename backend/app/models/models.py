from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, Text, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base_class import Base

class ProjectScope(str, enum.Enum):
    SINGLE_SOURCE = "SINGLE_SOURCE"
    ALL_DOCS = "ALL_DOCS"

class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    INDEXING = "INDEXING"
    READY = "READY"
    GENERATING = "GENERATING"
    REVIEW = "REVIEW"
    OUTDATED = "OUTDATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ChunkType(str, enum.Enum):
    PARENT = "PARENT"
    CHILD = "CHILD"

class JobType(str, enum.Enum):
    INGEST = "INGEST"
    GENERATE = "GENERATE"
    PARSE_QUESTIONNAIRE = "PARSE_QUESTIONNAIRE"
    EVALUATE = "EVALUATE"

class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    job_title = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    is_active = Column(Boolean(), default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner")

class Project(Base):
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=True) # Nullable for migration
    name = Column(String, index=True)
    client_name = Column(String)
    due_date = Column(DateTime, nullable=True)
    scope_type = Column(Enum(ProjectScope), default=ProjectScope.SINGLE_SOURCE)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    config_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    questionnaires = relationship("Questionnaire", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="projects")

class Document(Base):
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=True) # Nullable for global docs
    job_id = Column(Integer, ForeignKey("job.id"), nullable=True)
    filename = Column(String)
    file_path = Column(String)
    md5_hash = Column(String, index=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    version = Column(Integer, default=1)
    is_global = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    job = relationship("Job", foreign_keys=[job_id])

class DocumentChunk(Base):
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document.id"))
    parent_section_id = Column(Integer, ForeignKey("documentchunk.id"), nullable=True)
    chunk_text = Column(Text)
    chunk_type = Column(Enum(ChunkType))
    embedding_id = Column(String, nullable=True) # ID in ChromaDB
    page_number = Column(Integer)
    bbox_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")
    children = relationship("DocumentChunk", backref="parent", remote_side=[id])

class Questionnaire(Base):
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id"))
    filename = Column(String)
    parsing_status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="questionnaires")
    questions = relationship("Question", back_populates="questionnaire", cascade="all, delete-orphan")

class Job(Base):
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(Enum(JobType))
    project_id = Column(Integer, ForeignKey("project.id"), nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED)
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="jobs")

class Question(Base):
    id = Column(Integer, primary_key=True, index=True)
    questionnaire_id = Column(Integer, ForeignKey("questionnaire.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    section_header = Column(String, nullable=True)
    question_number = Column(String)
    question_text = Column(Text)
    instructions = Column(Text, nullable=True)
    order_index = Column(Integer)
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    questionnaire = relationship("Questionnaire", back_populates="questions")
    answers = relationship("Answer", back_populates="question", cascade="all, delete-orphan")

class Answer(Base):
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("question.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    current_version_id = Column(Integer, ForeignKey("answerversion.id"), nullable=True)
    status = Column(String, default="DRAFT") # Simplify Enum here or use Enum
    last_generated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="answers")
    versions = relationship("AnswerVersion", back_populates="answer", foreign_keys="[AnswerVersion.answer_id]")
    current_version = relationship("AnswerVersion", foreign_keys=[current_version_id], post_update=True)

class AnswerVersion(Base):
    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answer.id"))
    source_type = Column(String) # AI | HUMAN
    answer_text = Column(Text)
    answerability = Column(String)
    confidence_score = Column(Integer, nullable=True)
    generation_config_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    answer = relationship("Answer", back_populates="versions", foreign_keys=[answer_id])
    citations = relationship("Citation", back_populates="version")

class Citation(Base):
    id = Column(Integer, primary_key=True, index=True)
    answer_version_id = Column(Integer, ForeignKey("answerversion.id"))
    document_chunk_id = Column(Integer, ForeignKey("documentchunk.id"))
    citation_text = Column(Text)
    relevance_score = Column(Float)
    page_number = Column(Integer)
    bbox_json = Column(JSON, nullable=True)

    version = relationship("AnswerVersion", back_populates="citations")
