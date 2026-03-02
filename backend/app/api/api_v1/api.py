from fastapi import APIRouter
from app.api.api_v1.endpoints import projects, documents, questionnaires, auth, users

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(questionnaires.router, prefix="/questionnaires", tags=["questionnaires"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

