import os
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.services.seed_data import seed_database
from app.api import (
    auth, dialects, lexicon, audio_archive,
    contributions, quizzes, analytics, websockets,
    entries, categories, contributors, voices
)

# Derive FRONTEND_DIR safely across local dev and containerized deployments
CANDIDATE_FRONTEND_DIRS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend")),
    os.path.abspath(os.path.join(os.getcwd(), "..", "frontend")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")),
]
FRONTEND_DIR = next((d for d in CANDIDATE_FRONTEND_DIRS if os.path.isdir(d)), CANDIDATE_FRONTEND_DIRS[0])

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
# 🎙️ BhashaLok — Digital Preservation of Marathi Regional Language & Dialects API

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

# CORS Configuration with restricted origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Static Uploads directory (configured via settings.UPLOAD_DIR)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/api/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="api_uploads")

# Frontend static asset subdirectories
assets_dir = os.path.join(FRONTEND_DIR, "assets")
if os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend_assets")

styles_dir = os.path.join(FRONTEND_DIR, "styles")
if os.path.isdir(styles_dir):
    app.mount("/styles", StaticFiles(directory=styles_dir), name="frontend_styles")

# Register API Routers (v1 prefix)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(dialects.router, prefix=settings.API_V1_STR)
app.include_router(lexicon.router, prefix=settings.API_V1_STR)
app.include_router(audio_archive.router, prefix=settings.API_V1_STR)
app.include_router(contributions.router, prefix=settings.API_V1_STR)
app.include_router(quizzes.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(websockets.router, prefix=settings.API_V1_STR)

# Register BhashaLok Direct API Endpoints under /api and /api/v1
for prefix in ["/api", "/api/v1"]:
    app.include_router(entries.router, prefix=prefix)
    app.include_router(categories.router, prefix=prefix)
    app.include_router(contributors.router, prefix=prefix)
    app.include_router(voices.router, prefix=prefix)

# Dedicated Static File Routes
@app.get("/style.css", include_in_schema=False)
def serve_root_style():
    style_path = os.path.join(FRONTEND_DIR, "style.css")
    if not os.path.isfile(style_path):
        style_path = os.path.join(FRONTEND_DIR, "styles", "style.css")
    if os.path.isfile(style_path):
        return FileResponse(style_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="style.css not found")

@app.get("/script.js", include_in_schema=False)
def serve_root_script():
    script_path = os.path.join(FRONTEND_DIR, "script.js")
    if os.path.isfile(script_path):
        return FileResponse(script_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="script.js not found")

@app.get("/index.html", include_in_schema=False)
def serve_index_html():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/api/v1", tags=["Health & Root"])
@app.get("/api/health", tags=["Health & Root"])
def api_status():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "interactive_docs": "/docs",
        "redoc_docs": "/redoc",
        "api_v1_endpoint": settings.API_V1_STR,
        "message": "Welcome to BhashaLok — Digital Preservation of Regional Languages and Dialects API Backend Engine!"
    }

@app.get("/", tags=["Frontend & Root"])
def root(request: Request):
    """
    Root endpoint:
    - Serves the frontend homepage (index.html) to web browsers.
    - Returns JSON status metadata for programmatic/API consumers.
    """
    accept = request.headers.get("accept", "")
    format_param = request.query_params.get("format", "")

    # Programmatic API consumer requested JSON metadata
    if format_param == "json" or ("application/json" in accept and "text/html" not in accept) or accept == "*/*":
        return {
            "status": "online",
            "system": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "interactive_docs": "/docs",
            "redoc_docs": "/redoc",
            "api_v1_endpoint": settings.API_V1_STR,
            "message": "Welcome to BhashaLok — Digital Preservation of Regional Languages and Dialects API Backend Engine!"
        }

    # Browser navigation (Accept contains text/html): serve frontend homepage
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_file):
        return FileResponse(index_file, media_type="text/html")

    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "interactive_docs": "/docs",
        "redoc_docs": "/redoc",
        "api_v1_endpoint": settings.API_V1_STR
    }

# Safe fallback for frontend assets/routes (placed after all API routers)
@app.api_route("/{file_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], include_in_schema=False)
def serve_frontend_static(file_path: str, request: Request):
    # Safety guard: Never intercept API, WebSocket, Docs, or Upload paths
    reserved_prefixes = ("api/", "api", "ws/", "ws", "docs", "redoc", "openapi.json", "uploads/")
    if file_path.startswith(reserved_prefixes):
        raise HTTPException(status_code=404, detail="Resource not found")

    if request.method not in ("GET", "HEAD"):
        raise HTTPException(status_code=405, detail="Method Not Allowed")

    safe_path = os.path.abspath(os.path.join(FRONTEND_DIR, file_path))
    # Path traversal protection
    if not safe_path.startswith(FRONTEND_DIR):
        raise HTTPException(status_code=403, detail="Forbidden")

    if os.path.isfile(safe_path):
        return FileResponse(safe_path)

    raise HTTPException(status_code=404, detail="Static resource not found")
