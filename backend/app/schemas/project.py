from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ProjectScope(str, Enum):
    SINGLE_SOURCE = "SINGLE_SOURCE"
    ALL_DOCS = "ALL_DOCS"

class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    INDEXING = "INDEXING"
    READY = "READY"
    GENERATING = "GENERATING"
    REVIEW = "REVIEW"
    OUTDATED = "OUTDATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ProjectBase(BaseModel):
    name: str
    client_name: str
    due_date: Optional[datetime] = None
    scope_type: ProjectScope = ProjectScope.SINGLE_SOURCE

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    due_date: Optional[datetime] = None
    scope_type: Optional[ProjectScope] = None
    status: Optional[ProjectStatus] = None

class ProjectInDBBase(ProjectBase):
    id: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

from app.schemas.questionnaire import Questionnaire
from app.schemas.document import Job

class Project(ProjectInDBBase):
    questionnaires: List[Questionnaire] = []
    jobs: List[Job] = []

class ProjectWithDetails(Project):
    # This will be populated with counts later
    document_count: int = 0
    questionnaire_count: int = 0
