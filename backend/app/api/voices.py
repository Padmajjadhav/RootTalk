import os
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.config import settings
from app.database import get_db
from app.models import VoiceRecording, Entry, Contributor
from app.schemas.schemas import VoiceRecordingResponse

router = APIRouter(tags=["Voice Notes & Audio Preservation"])

@router.get("/voices", response_model=List[VoiceRecordingResponse])
def list_voices(
    entry_id: Optional[int] = None,
    contributor_id: Optional[int] = None,
    variety: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(VoiceRecording)
    if entry_id:
        query = query.filter(VoiceRecording.entry_id == entry_id)
    if contributor_id:
        query = query.filter(VoiceRecording.contributor_id == contributor_id)
    if variety:
        query = query.filter(VoiceRecording.variety.ilike(f"%{variety}%"))
    return query.all()

@router.get("/voices/{voice_id}", response_model=VoiceRecordingResponse)
def get_voice(voice_id: int, db: Session = Depends(get_db)):
    voice = db.query(VoiceRecording).filter(VoiceRecording.id == voice_id).first()
    if not voice:
        raise HTTPException(status_code=404, detail="Voice recording not found")
    return voice

@router.post("/voices", response_model=VoiceRecordingResponse, status_code=status.HTTP_201_CREATED)
async def upload_voice(
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
    # Validate file extension
    file_ext = os.path.splitext(file.filename or "")[1].lower()
    if file_ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio file type '{file_ext}'. Allowed formats: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}"
        )

    # Read and validate file content & size
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded audio file cannot be empty.")
    if len(content) > settings.MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file exceeds maximum allowed limit of {settings.MAX_AUDIO_SIZE_BYTES // (1024 * 1024)}MB."
        )

    # Ensure upload directory exists
    os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(settings.AUDIO_UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    rel_audio_url = f"/uploads/audio/{unique_filename}"

    recording = VoiceRecording(
        entry_id=entry_id,
        contributor_id=contributor_id,
        title=transcript[:60] if transcript else f"{variety or 'Regional'} Voice Recording",
        audio_file=rel_audio_url,
        duration=duration,
        language=language,
        variety=variety,
        region=region,
        transcript=transcript,
        created_at=datetime.datetime.utcnow()
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

    return recording
