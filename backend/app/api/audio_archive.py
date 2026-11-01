import os
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request, Response, status
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config import settings
from app.database import get_db
from app.models import AudioArchive, Dialect, User, VerificationStatus
from app.schemas.schemas import AudioArchiveResponse
from app.services.auth_service import get_current_user, get_optional_user
from app.services.audio_service import generate_waveform_peaks, generate_srt_subtitles, validate_audio_file
from app.services.websocket_manager import ws_manager
from app.services.rate_limiter import rate_limiter

router = APIRouter(prefix="/audio-archive", tags=["Audio & Oral History Archive"])

@router.get("/", response_model=List[AudioArchiveResponse])
def list_audio_archives(
    dialect_id: Optional[int] = Query(None, description="Filter by dialect"),
    genre: Optional[str] = Query(None, description="Folk Tale, Folk Song / Ovi, Oral History Interview"),
    speaker_gender: Optional[str] = Query(None, description="Male / Female"),
    verification_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(AudioArchive)
    if dialect_id:
        query = query.filter(AudioArchive.dialect_id == dialect_id)
    if genre:
        query = query.filter(AudioArchive.genre == genre)
    if speaker_gender:
        query = query.filter(AudioArchive.speaker_gender == speaker_gender)
    if verification_status:
        query = query.filter(AudioArchive.verification_status == verification_status)
    if search:
        query = query.filter(
            (AudioArchive.title.ilike(f"%{search}%")) |
            (AudioArchive.transcript_text.ilike(f"%{search}%")) |
            (AudioArchive.speaker_name.ilike(f"%{search}%"))
        )
    return query.all()

@router.post("/upload", response_model=AudioArchiveResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio_recording(
    request: Request,
    dialect_id: int = Form(...),
    title: str = Form(...),
    genre: str = Form(...),
    speaker_name: Optional[str] = Form(None),
    speaker_age: Optional[int] = Form(None),
    speaker_gender: Optional[str] = Form(None),
    locality: Optional[str] = Form(None),
    transcript_text: Optional[str] = Form(None),
    transcript_translation_en: Optional[str] = Form(None),
    transcript_translation_standard: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    # Public abuse protection: rate limit unauthenticated uploads
    if not current_user:
        rate_limiter.check(request, endpoint_key="audio_contribute")

    dialect = db.query(Dialect).filter(Dialect.id == dialect_id).first()
    if not dialect:
        raise HTTPException(status_code=404, detail="Dialect not found")

    file_ext = os.path.splitext(file.filename or "")[1].lower()
    contents = await file.read()

    # Deep audio file validation (extension, size, and genuine header magic bytes)
    validate_audio_file(
        content=contents,
        filename=file.filename or "recording.mp3",
        max_size_bytes=settings.MAX_AUDIO_SIZE_BYTES,
        allowed_extensions=settings.ALLOWED_AUDIO_EXTENSIONS
    )

    os.makedirs(settings.AUDIO_UPLOAD_DIR, exist_ok=True)
    filename = f"audio_{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(settings.AUDIO_UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    # Estimate audio duration (simplified size-based estimation for raw/compressed streams)
    estimated_duration = max(10.0, round(len(contents) / 16000.0, 1))

    # Generate waveform peaks and SRT subtitles
    waveform_data = json.dumps(generate_waveform_peaks(50))
    srt_content = generate_srt_subtitles(transcript_text, duration_seconds=estimated_duration) if transcript_text else None

    # Public anonymous users are strictly PENDING; only Linguists or Admins can verify
    is_verified = (current_user.role in ["Linguist", "Admin"]) if current_user else False

    audio_entry = AudioArchive(
        dialect_id=dialect_id,
        title=title,
        genre=genre,
        speaker_name=speaker_name,
        speaker_age=speaker_age,
        speaker_gender=speaker_gender,
        locality=locality,
        audio_file_path=os.path.join("uploads", "audio", filename),
        duration_seconds=estimated_duration,
        waveform_json=waveform_data,
        transcript_text=transcript_text,
        transcript_translation_en=transcript_translation_en,
        transcript_translation_standard=transcript_translation_standard,
        srt_subtitles=srt_content,
        submitted_by_id=current_user.id if current_user else None,
        verification_status=VerificationStatus.VERIFIED if is_verified else VerificationStatus.PENDING
    )
    db.add(audio_entry)
    db.commit()
    db.refresh(audio_entry)

    # Standardized WebSocket activity event broadcast
    await ws_manager.broadcast_activity({
        "event": "AUDIO_RECORDING_UPLOADED",
        "type": "AUDIO_RECORDING_UPLOADED",
        "audio_id": audio_entry.id,
        "title": title,
        "dialect_name": dialect.name if dialect else "Regional Marathi",
        "submitted_by": current_user.username if current_user else "Community Preserver",
        "data": {
            "id": audio_entry.id,
            "title": title,
            "dialect": dialect.name if dialect else "Regional Marathi"
        }
    })

    return audio_entry

@router.get("/{audio_id}", response_model=AudioArchiveResponse)
def get_audio_archive(audio_id: int, db: Session = Depends(get_db)):
    audio = db.query(AudioArchive).filter(AudioArchive.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio recording not found")
    
    # Increment view counter
    audio.views_count += 1
    db.commit()
    return audio

@router.get("/{audio_id}/stream")
def stream_audio(audio_id: int, db: Session = Depends(get_db)):
    audio = db.query(AudioArchive).filter(AudioArchive.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio recording not found")

    raw_path = audio.audio_file_path or ""
    filename = os.path.basename(raw_path)

    # Resolve actual file path on disk across supported storage layouts
    candidate_paths = [
        raw_path,
        os.path.join(settings.AUDIO_UPLOAD_DIR, filename),
        os.path.join(settings.UPLOAD_DIR, filename),
        os.path.join(os.path.dirname(settings.UPLOAD_DIR), raw_path),
        os.path.join(os.getcwd(), raw_path)
    ]

    resolved_path = None
    for p in candidate_paths:
        if p and os.path.isfile(p):
            resolved_path = p
            break

    if not resolved_path:
        # Strictly return HTTP 404 when file does not exist on disk
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file '{filename}' does not exist on storage disk."
        )

    ext = os.path.splitext(resolved_path)[1].lower()
    media_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(resolved_path, media_type=media_type, filename=filename)

@router.get("/{audio_id}/subtitles.srt")
def download_srt_subtitles(audio_id: int, db: Session = Depends(get_db)):
    audio = db.query(AudioArchive).filter(AudioArchive.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio recording not found")

    srt_content = audio.srt_subtitles or generate_srt_subtitles(audio.transcript_text or "Preserved dialect story", audio.duration_seconds)
    return Response(content=srt_content, media_type="application/x-subrip", headers={"Content-Disposition": f"attachment; filename=subtitle_{audio_id}.srt"})

@router.get("/{audio_id}/subtitles.vtt")
def stream_vtt_subtitles(audio_id: int, db: Session = Depends(get_db)):
    audio = db.query(AudioArchive).filter(AudioArchive.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio recording not found")

    srt_content = audio.srt_subtitles or generate_srt_subtitles(audio.transcript_text or "Preserved dialect story", audio.duration_seconds)
    vtt_content = "WEBVTT\n\n" + srt_content.replace(",", ".")
    return Response(content=vtt_content, media_type="text/vtt")
