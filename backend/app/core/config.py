from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Questionnaire Agent"
    API_V1_STR: str = "/api/v1"
    GROQ_API_KEY: str
    OPENAI_API_KEY: str
    GEMINI_API_KEY: str
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    SECRET_KEY: str = "72ec7e94e9ed11846b9a896d83cf98587d6118d5386901869e578da37ca62391" # Placeholder
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days

    class Config:
        env_file = ".env"

settings = Settings()
