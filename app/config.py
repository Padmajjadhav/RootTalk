import os

class Settings:
    PROJECT_NAME: str = "Digital Preservation of Regional Languages & Dialects API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "preservation_secret_key_super_secure_2026_regional_linguistics")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # SQLite Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./preservation.db")
    
    # Upload Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    AUDIO_UPLOAD_DIR: str = os.path.join(UPLOAD_DIR, "audio")
    TRANSCRIPTION_UPLOAD_DIR: str = os.path.join(UPLOAD_DIR, "transcriptions")

settings = Settings()

os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.TRANSCRIPTION_UPLOAD_DIR, exist_ok=True)
