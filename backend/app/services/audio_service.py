import json
import random
import os
from typing import List, Dict, Optional
from fastapi import HTTPException, status

def generate_waveform_peaks(num_points: int = 50) -> List[float]:
    """Generates normalized amplitude peak values (0.0 to 1.0) for audio visualization."""
    random.seed(42) # Consistent synthetic profile for test uploads
    return [round(random.uniform(0.1, 0.95), 2) for _ in range(num_points)]

def generate_srt_subtitles(transcript_text: str, duration_seconds: float = 60.0) -> str:
    """Generates standard SRT subtitle file content from transcript text."""
    if not transcript_text:
        return ""
    
    sentences = [s.strip() for s in transcript_text.split('.') if s.strip()]
    if not sentences:
        sentences = [transcript_text]
        
    num_sentences = len(sentences)
    time_per_sentence = max(2.0, duration_seconds / num_sentences)
    
    srt_output = []
    current_time = 0.0
    
    for idx, sentence in enumerate(sentences, start=1):
        start_time = current_time
        end_time = min(duration_seconds, current_time + time_per_sentence)
        
        start_fmt = format_srt_timestamp(start_time)
        end_fmt = format_srt_timestamp(end_time)
        
        srt_output.append(f"{idx}\n{start_fmt} --> {end_fmt}\n{sentence}\n")
        current_time = end_time
        
    return "\n".join(srt_output)

def format_srt_timestamp(seconds: float) -> str:
    """Formats float seconds into HH:MM:SS,mmm format for SRT subtitles."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def validate_audio_file(
    content: bytes,
    filename: str,
    max_size_bytes: int = 25 * 1024 * 1024,
    allowed_extensions: Optional[tuple] = None
) -> None:
    """
    Validates audio file size, extension, and genuine content magic byte signatures.
    Rejects spoofed, truncated, or unsupported files.
    """
    if not content or len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file cannot be empty."
        )

    if len(content) > max_size_bytes:
        max_mb = max_size_bytes // (1024 * 1024)
        status_413 = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
        raise HTTPException(
            status_code=status_413,
            detail=f"Audio file exceeds maximum allowed limit of {max_mb}MB."
        )

    if allowed_extensions is None:
        allowed_extensions = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm", ".aac")

    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audio file type '{ext}'. Allowed formats: {', '.join(allowed_extensions)}"
        )

    # Magic byte verification across all supported formats
    is_valid = False
    if ext == ".wav":
        is_valid = len(content) >= 12 and (content[:4] in (b"RIFF", b"RIFX")) and content[8:12] == b"WAVE"
    elif ext == ".mp3":
        is_valid = (
            content.startswith(b"ID3") or
            (len(content) >= 2 and content[0] == 0xFF and (content[1] & 0xE0) == 0xE0)
        )
    elif ext == ".ogg":
        is_valid = content.startswith(b"OggS")
    elif ext == ".flac":
        is_valid = content.startswith(b"fLaC")
    elif ext == ".webm":
        is_valid = content.startswith(b"\x1a\x45\xdf\xa3")
    elif ext == ".m4a":
        is_valid = (
            (len(content) >= 8 and content[4:8] == b"ftyp") or
            (len(content) >= 2 and content[0] == 0xFF and (content[1] & 0xF0) == 0xF0)
        )
    elif ext == ".aac":
        is_valid = (
            content.startswith(b"ID3") or
            (len(content) >= 2 and content[0] == 0xFF and (content[1] & 0xF0) == 0xF0) or
            (len(content) >= 8 and content[4:8] == b"ftyp")
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio content validation failed: The uploaded file does not contain valid audio header signatures for '{ext}'."
        )
