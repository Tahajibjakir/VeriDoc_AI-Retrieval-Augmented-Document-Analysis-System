from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class QuestionnaireStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class QuestionBase(BaseModel):
    section_header: Optional[str] = None
    question_number: str
    question_text: str
    order_index: int
    assigned_to: Optional[str] = None

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    questionnaire_id: int
    project_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class QuestionnaireBase(BaseModel):
    filename: str

class QuestionnaireCreate(QuestionnaireBase):
    project_id: int

class Questionnaire(QuestionnaireBase):
    id: int
    project_id: int
    parsing_status: QuestionnaireStatus
    version: int
    created_at: datetime
    questions: List[Question] = []
    
    model_config = ConfigDict(from_attributes=True)
