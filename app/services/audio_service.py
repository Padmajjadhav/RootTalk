import json
import random
from typing import List, Dict

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
