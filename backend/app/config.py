import os

class Settings:
    PROJECT_NAME: str = "Digital Preservation of Regional Languages & Dialects API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    MAX_AUDIO_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    ALLOWED_AUDIO_EXTENSIONS: tuple = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".aac")

    def __init__(self):
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
        
        # In production, require a secure and explicit SECRET_KEY
        insecure_default = "preservation_secret_key_super_secure_2026_regional_linguistics"
        secret = os.getenv("SECRET_KEY")
        if self.ENVIRONMENT == "production":
            if not secret or secret == insecure_default:
                raise RuntimeError(
                    "FATAL: In production environment, a secure SECRET_KEY environment variable must be configured! "
                    "Do not use the insecure default secret key."
                )
            self.SECRET_KEY: str = secret
        else:
            self.SECRET_KEY: str = secret or "preservation_dev_secret_key_2026_regional_linguistics"

        # Upload Storage Configuration (supports persistent disk mount in production)
        self.UPLOAD_DIR: str = os.getenv(
            "UPLOAD_DIR",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        )
        self.AUDIO_UPLOAD_DIR: str = os.path.join(self.UPLOAD_DIR, "audio")
        self.TRANSCRIPTION_UPLOAD_DIR: str = os.path.join(self.UPLOAD_DIR, "transcriptions")

        # Database Configuration (supports PostgreSQL on Render and local SQLite)
        raw_db_url = os.getenv("DATABASE_URL")
        if raw_db_url:
            # Render provides postgres:// which SQLAlchemy requires as postgresql://
            if raw_db_url.startswith("postgres://"):
                self.DATABASE_URL: str = raw_db_url.replace("postgres://", "postgresql://", 1)
            else:
                self.DATABASE_URL: str = raw_db_url
        else:
            default_db: str = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "preservation.db"
            ).replace("\\", "/")
            self.DATABASE_URL: str = f"sqlite:///{default_db}"

        # CORS Allowed Origins
        raw_origins = os.getenv("ALLOWED_ORIGINS")
        if raw_origins:
            self.ALLOWED_ORIGINS: list = [o.strip() for o in raw_origins.split(",") if o.strip()]
        elif self.ENVIRONMENT == "production":
            self.ALLOWED_ORIGINS: list = ["https://roottalk-frontend.onrender.com"]
        else:
            self.ALLOWED_ORIGINS: list = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
                "http://localhost:5500",
                "http://127.0.0.1:5500",
                "https://roottalk-frontend.onrender.com"
            ]

settings = Settings()

try:
    os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TRANSCRIPTION_UPLOAD_DIR, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create upload directories during initialization: {e}")
