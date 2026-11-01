import os
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.models import VoiceRecording, Entry
from app.schemas.schemas import VoiceRecordingResponse
from app.config import settings
from app.services.audio_service import validate_audio_file
from app.services.rate_limiter import rate_limiter
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["Voices & Fieldwork Audio"])

@router.get("/voices", response_model=List[VoiceRecordingResponse])
def get_voices(
    variety: Optional[str] = None,
    entry_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(VoiceRecording)
    if variety:
        query = query.filter(VoiceRecording.variety.ilike(f"%{variety}%"))
    if entry_id:
        query = query.filter(VoiceRecording.entry_id == entry_id)
    return query.all()

@router.get("/voices/{voice_id}", response_model=VoiceRecordingResponse)
def get_voice(voice_id: int, db: Session = Depends(get_db)):
    voice = db.query(VoiceRecording).filter(VoiceRecording.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice recording not found")
    return voice

@router.post("/voices", response_model=VoiceRecordingResponse, status_code=status.HTTP_201_CREATED)
async def upload_voice(
    request: Request,
    file: UploadFile = File(...),
    entry_id: Optional[int] = Form(None),
    contributor_id: Optional[int] = Form(None),
    language: str = Form("Marathi"),
    variety: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    transcript: Optional[str] = Form(None),
    duration: float = Form(0.0),
    db: Session = Depends(get_db)
):
    # Public abuse protection
    rate_limiter.check(request, endpoint_key="voice_contribute")

    # Read content and validate extension, size, and genuine audio header magic bytes
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    content = await file.read()

    validate_audio_file(
        content=content,
        filename=file.filename or "recording.mp3",
        max_size_bytes=settings.MAX_AUDIO_SIZE_BYTES,
        allowed_extensions=settings.ALLOWED_AUDIO_EXTENSIONS
    )

    # Ensure upload directory exists
    os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(settings.AUDIO_UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    rel_audio_url = f"/uploads/audio/{unique_filename}"
    display_title = transcript[:60] if transcript else f"{variety or 'Regional'} Voice Recording"

    recording = VoiceRecording(
        entry_id=entry_id,
        contributor_id=contributor_id,
        title=display_title,
        audio_file=rel_audio_url,
        duration=duration,
        language=language,
        variety=variety,
        region=region,
        transcript=transcript,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)

    # Link audio_url to Entry if provided
    if entry_id:
        entry = db.query(Entry).filter(Entry.id == entry_id).first()
        if entry and not entry.audio_url:
            entry.audio_url = rel_audio_url
            db.commit()

    # Broadcast standardized WebSocket notification
    await ws_manager.broadcast_activity({
        "event": "AUDIO_RECORDING_UPLOADED",
        "type": "AUDIO_RECORDING_UPLOADED",
        "audio_id": recording.id,
        "title": display_title,
        "dialect_name": variety or "Regional Marathi",
        "submitted_by": "Community Preserver",
        "data": {
            "id": recording.id,
            "title": display_title,
            "dialect": variety
        }
    })

    return recording
