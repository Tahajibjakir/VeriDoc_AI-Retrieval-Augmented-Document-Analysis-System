from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.questionnaire import Questionnaire, QuestionnaireCreate
from app.models.models import Questionnaire as QuestionnaireModel, Project as ProjectModel, DocumentStatus, User
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

@router.post("/", response_model=Questionnaire)
def upload_questionnaire(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Upload a questionnaire to a project.
    """
    # Verify project exists and belongs to user
    project = db.query(ProjectModel).filter(
        ProjectModel.id == project_id,
        ProjectModel.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Generate safe filename and path
    file_location = f"{UPLOAD_DIR}/questionnaire_{project_id}_{file.filename}"
    
    # Save file
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create DB record
    questionnaire = QuestionnaireModel(
        project_id=project_id,
        filename=file.filename,
        parsing_status=DocumentStatus.PENDING,
    )
    db.add(questionnaire)
    db.commit()
    db.refresh(questionnaire)
    
    # Trigger Job
    from app.services.jobs import create_job, JobType, run_questionnaire_parsing_job
    job = create_job(db, JobType.PARSE_QUESTIONNAIRE, project_id)
    
    # Run in background
    background_tasks.add_task(run_questionnaire_parsing_job, job.id, questionnaire.id)
    
    # For now, just return it
    return questionnaire

@router.delete("/{questionnaire_id}", response_model=Questionnaire)
def delete_questionnaire(
    *,
    db: Session = Depends(deps.get_db),
    questionnaire_id: int,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a Questionnaire.
    """
    questionnaire = db.query(QuestionnaireModel).join(ProjectModel).filter(
        QuestionnaireModel.id == questionnaire_id,
        ProjectModel.owner_id == current_user.id
    ).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")

    # TODO: Physically delete file if stored path is saved

    # Database cleanup (cascades handle questions)
    db.delete(questionnaire)
    db.commit()
    
    return questionnaire
