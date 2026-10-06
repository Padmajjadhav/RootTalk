from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.seed_data import seed_database
from app.api import (
    auth, dialects, lexicon, audio_archive,
    contributions, quizzes, analytics, websockets
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Initializing Database Tables & Preservation Data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Shutdown logic
    print("Shutting down Regional Language Preservation Backend API.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
# 🎙️ Digital Preservation of Regional Languages & Dialects API Backend

A high-performance, interactive backend engine for preserving endangered regional languages, dialects, oral folklore, and phonetic heritage.

### 🌟 Core Capabilities & Interactive Features:
1. **Dialect Cartography & Registry**: Metadata, endangerment status tracking (Safe to Extinct), geo-coordinates mapping.
2. **Linguistic Dictionary Vault**: Vocabulary entries with Devanagari/regional script, International Phonetic Alphabet (IPA) transcriptions, standard translations, etymology, and semantic categories.
3. **Phonetic Search Engine**: Indic Soundex phonetic algorithm + Levenshtein distance fuzzy matching for regional pronunciations.
4. **Audio & Oral History Archive**: Audio file upload, amplitude waveform generation, range-request audio streaming playback, and auto-generated SRT/WebVTT subtitles.
5. **Interactive Peer Verification & Gamification**: Linguist verification workflow, voting system, reputation points, and contributor leaderboards.
6. **Interactive Learning & Quizzes**: Multiple choice trivia decks, flashcard scoring, and reputation rewards.
7. **Real-time WebSockets**: Live collaborative dictation rooms, multiplayer quiz trivia rooms, and live preservation activity broadcasting.
8. **Data Export & Preservation Index**: Quantitative preservation scoring + full JSON and CSV export endpoints.

---
📘 **Interactive Swagger Docs**: [/docs](/docs)  
📕 **ReDoc API Documentation**: [/redoc](/redoc)  
    """,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(dialects.router, prefix=settings.API_V1_STR)
app.include_router(lexicon.router, prefix=settings.API_V1_STR)
app.include_router(audio_archive.router, prefix=settings.API_V1_STR)
app.include_router(contributions.router, prefix=settings.API_V1_STR)
app.include_router(quizzes.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(websockets.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health & Root"])
def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "interactive_docs": "/docs",
        "redoc_docs": "/redoc",
        "api_v1_endpoint": settings.API_V1_STR,
        "message": "Welcome to the Digital Preservation of Regional Languages and Dialects API Backend Engine!"
    }
