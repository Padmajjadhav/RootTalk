import os
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import VoiceRecording, Entry, Contributor
from app.schemas.schemas import VoiceRecordingResponse

router = APIRouter(tags=["Voice Notes & Audio Preservation"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "audio")
os.makedirs(UPLOAD_DIR, exist_ok=True)

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
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1] or ".wav"
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    rel_audio_url = f"/uploads/audio/{unique_filename}"

    recording = VoiceRecording(
        entry_id=entry_id,
        contributor_id=contributor_id,
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
