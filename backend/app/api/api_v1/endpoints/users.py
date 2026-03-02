from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.core import security
from app.models import models
from app.schemas import user as user_schema

router = APIRouter()

@router.get("/me", response_model=user_schema.User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.patch("/me", response_model=user_schema.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: user_schema.UserUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update own user.
    """
    if user_in.email is not None:
        existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = user_in.email
    
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.job_title is not None:
        current_user.job_title = user_in.job_title
    if user_in.organization is not None:
        current_user.organization = user_in.organization
    if user_in.industry is not None:
        current_user.industry = user_in.industry
        
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/change-password")
def change_password_me(
    *,
    db: Session = Depends(deps.get_db),
    old_password: str = Body(...),
    new_password: str = Body(...),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Change own password.
    """
    if not security.verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.hashed_password = security.get_password_hash(new_password)
    db.add(current_user)
    db.commit()
    return {"msg": "Password updated successfully"}

@router.get("/me/stats")
def read_user_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get user statistics.
    """
    project_count = db.query(func.count(models.Project.id)).filter(models.Project.owner_id == current_user.id).scalar()
    
    # Docs processed can be counted as total documents in projects owned by the user
    doc_count = db.query(func.count(models.Document.id))\
        .join(models.Project)\
        .filter(models.Project.owner_id == current_user.id)\
        .scalar()
        
    return {
        "active_projects": project_count or 0,
        "docs_processed": doc_count or 0
    }
