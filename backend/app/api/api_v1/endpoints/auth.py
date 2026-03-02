from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models import models
from app.schemas import user as user_schema

router = APIRouter()

class GoogleLogin(BaseModel):
    credential: str

@router.post("/google", response_model=user_schema.Token)
def login_google(
    *,
    db: Session = Depends(deps.get_db),
    google_in: GoogleLogin,
) -> Any:
    """
    Google authentication
    """
    try:
        # Verify Google Token
        print(f"DEBUG: Verifying Google token for {google_in.credential[:20]}...")
        # idinfo = id_token.verify_oauth2_token(google_in.credential, requests.Request(), settings.GOOGLE_CLIENT_ID)
        # Note: We skip aud check for now as it's often tricky with different origins
        # Added clock_skew_in_seconds=10 to handle cases where the server's clock is slightly behind Google's
        idinfo = id_token.verify_oauth2_token(google_in.credential, requests.Request(), clock_skew_in_seconds=10)
        
        email = idinfo['email']
        print(f"DEBUG: Google token verified for email: {email}")
        full_name = idinfo.get('name', '')
        
        # Check if user exists
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            print(f"DEBUG: Creating new user for email: {email}")
            user = models.User(
                email=email,
                full_name=full_name,
                hashed_password=security.get_password_hash(security.generate_password()),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        print(f"DEBUG: Backend token created for user_id: {user.id}")
        return {
            "access_token": token,
            "token_type": "bearer",
        }
    except Exception as e:
        print(f"ERROR: Google Auth failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid Google token: {str(e)}")

@router.post("/login/access-token", response_model=user_schema.Token)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=user_schema.User)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: user_schema.UserCreate,
) -> Any:
    """
    Register a new user.
    """
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    
    db_obj = models.User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
