from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class AnswerStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    MANUAL_UPDATED = "MANUAL_UPDATED"
    MISSING_DATA = "MISSING_DATA"

class SourceType(str, Enum):
    AI = "AI"
    HUMAN = "HUMAN"

class Answerability(str, Enum):
    ANSWERABLE = "ANSWERABLE"
    NO_DATA_FOUND = "NO_DATA_FOUND"

class CitationBase(BaseModel):
    citation_text: str
    relevance_score: float
    page_number: int
    bbox_json: Optional[Any] = None
    document_chunk_id: int

class Citation(CitationBase):
    id: int
    answer_version_id: int
    
    model_config = ConfigDict(from_attributes=True)

class AnswerVersionBase(BaseModel):
    source_type: SourceType
    answer_text: str
    answerability: Answerability
    confidence_score: Optional[int] = None

class AnswerVersion(AnswerVersionBase):
    id: int
    answer_id: int
    created_at: datetime
    citations: List[Citation] = []
    
    model_config = ConfigDict(from_attributes=True)

class AnswerBase(BaseModel):
    status: AnswerStatus

class Answer(AnswerBase):
    id: int
    question_id: int
    project_id: int
    current_version_id: Optional[int] = None
    last_generated_at: Optional[datetime] = None
    created_at: datetime
    current_version: Optional[AnswerVersion] = None
    
    model_config = ConfigDict(from_attributes=True)
