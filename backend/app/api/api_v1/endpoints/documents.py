from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.document import Document, DocumentCreate
from app.models.models import Document as DocumentModel, Project as ProjectModel, DocumentStatus, User
from app.db.session import SessionLocal
import shutil
import os
import hashlib

router = APIRouter()

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

@router.post("/", response_model=Document)
def upload_document(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Upload a document to a project.
    """
    # Verify project exists and belongs to user
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate safe filename and path
    file_location = f"{UPLOAD_DIR}/{project_id}_{file.filename}"
    
    # Save file
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Calculate MD5
    hash_md5 = hashlib.md5()
    with open(file_location, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    file_hash = hash_md5.hexdigest()
    
    # Check duplicate (optional, skipped for now or simple check)
    
    # Create DB record
    document = DocumentModel(
        project_id=project_id,
        filename=file.filename,
        file_path=file_location,
        md5_hash=file_hash,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Trigger Ingestion Job
    from app.services.jobs import create_job, run_ingestion_job, JobType
    job = create_job(db, JobType.INGEST, project_id)
    
    # Link job to document
    document.job_id = job.id
    db.commit()
    db.refresh(document)
    
    # Run in background
    background_tasks.add_task(run_ingestion_job, job.id, document.id)
    
    return document

@router.get("/", response_model=List[Document])
def read_documents(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve documents for a project.
    """
    # Verify project ownership
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    documents = db.query(DocumentModel).filter(DocumentModel.project_id == project_id).offset(skip).limit(limit).all()
    return documents

@router.delete("/{document_id}", response_model=Document)
def delete_document(
    *,
    db: Session = Depends(deps.get_db),
    document_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a Document.
    """
    document = db.query(DocumentModel).join(ProjectModel).filter(
        DocumentModel.id == document_id,
        ProjectModel.owner_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    from app.core.chroma import get_collection
    collection = get_collection()
    
    # 1. Cleanup Chroma embeddings
    try:
        collection.delete(where={"document_id": document.id})
    except Exception as e:
        print(f"Error deleting chroma embeddings for doc {document.id}: {e}")
            
    # 2. Physical File
    if document.file_path and os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
        except Exception as e:
            print(f"Error deleting physical file {document.file_path}: {e}")

    # 3. Database cleanup (cascades handle chunks)
    db.delete(document)
    db.commit()
    
    return document
