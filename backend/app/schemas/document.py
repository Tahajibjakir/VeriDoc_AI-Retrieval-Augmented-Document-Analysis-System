from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentBase(BaseModel):
    filename: str
    is_global: bool = False

class DocumentCreate(DocumentBase):
    pass

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Job(BaseModel):
    id: int
    job_type: str
    status: JobStatus
    progress_percent: int
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)

class DocumentInDBBase(DocumentBase):
    id: int
    project_id: Optional[int]
    job_id: Optional[int] = None
    status: DocumentStatus
    md5_hash: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class Document(DocumentInDBBase):
    job: Optional[Job] = None
