import csv
import io
import json
from fastapi import APIRouter, Depends, Response, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dialect, LexiconEntry, AudioArchive, User
from app.schemas.schemas import PreservationStatsResponse

router = APIRouter(prefix="/analytics", tags=["Analytics & Data Preservation Archives"])

@router.get("/stats", response_model=PreservationStatsResponse)
def get_preservation_stats(db: Session = Depends(get_db)):
    total_dialects = db.query(Dialect).count()
    total_words = db.query(LexiconEntry).count()
    total_audio = db.query(AudioArchive).count()
    total_users = db.query(User).count()

    # Coverage by status
    dialects = db.query(Dialect).all()
    status_counts = {}
    for d in dialects:
        status_counts[d.endangerment_status] = status_counts.get(d.endangerment_status, 0) + 1

    # Top dialects
    top_dialects = []
    for d in dialects:
        w_count = db.query(LexiconEntry).filter(LexiconEntry.dialect_id == d.id).count()
        top_dialects.append({"name": d.name, "code": d.code, "words_count": w_count})

    top_dialects.sort(key=lambda x: x["words_count"], reverse=True)

    return PreservationStatsResponse(
        total_dialects=total_dialects,
        total_words_preserved=total_words,
        total_audio_recordings=total_audio,
        total_active_contributors=total_users,
        preservation_coverage_by_status=status_counts,
        top_dialects_by_entries=top_dialects[:5]
    )

@router.get("/preservation-index/{dialect_id}")
def get_dialect_preservation_index(dialect_id: int, db: Session = Depends(get_db)):
    dialect = db.query(Dialect).filter(Dialect.id == dialect_id).first()
    if not dialect:
        raise HTTPException(status_code=404, detail="Dialect not found")

    lexicon_count = db.query(LexiconEntry).filter(LexiconEntry.dialect_id == dialect.id).count()
    audio_count = db.query(AudioArchive).filter(AudioArchive.dialect_id == dialect.id).count()
    ipa_count = db.query(LexiconEntry).filter(LexiconEntry.dialect_id == dialect.id, LexiconEntry.ipa_transcription.isnot(None)).count()

    # Index formula (0 - 100 scale)
    vocab_score = min(40.0, lexicon_count * 2.0)
    audio_score = min(30.0, audio_count * 15.0)
    ipa_score = min(30.0, ipa_count * 3.0)
    total_index = round(vocab_score + audio_score + ipa_score, 1)

    return {
        "dialect_id": dialect.id,
        "dialect_name": dialect.name,
        "endangerment_status": dialect.endangerment_status,
        "preservation_index_score": total_index,
        "metrics": {
            "preserved_lexicon_entries": lexicon_count,
            "preserved_audio_recordings": audio_count,
            "ipa_transcribed_terms": ipa_count
        },
        "preservation_level": "High Preservation" if total_index >= 75 else ("Moderate Preservation" if total_index >= 40 else "Needs Urgent Preservation")
    }

@router.get("/export/json")
def export_archive_json(db: Session = Depends(get_db)):
    dialects = db.query(Dialect).all()
    archive = []

    for d in dialects:
        words = db.query(LexiconEntry).filter(LexiconEntry.dialect_id == d.id).all()
        audios = db.query(AudioArchive).filter(AudioArchive.dialect_id == d.id).all()

        d_dict = {
            "dialect": {
                "name": d.name,
                "parent_language": d.parent_language,
                "code": d.code,
                "region_name": d.region_name,
                "state": d.state,
                "endangerment_status": d.endangerment_status
            },
            "dictionary": [
                {
                    "term": w.term,
                    "ipa": w.ipa_transcription,
                    "meaning_en": w.meaning_en,
                    "meaning_standard": w.meaning_standard_lang,
                    "part_of_speech": w.part_of_speech,
                    "semantic_category": w.semantic_category
                } for w in words
            ],
            "audio_recordings": [
                {
                    "title": a.title,
                    "genre": a.genre,
                    "speaker": a.speaker_name,
                    "transcript": a.transcript_text,
                    "duration_seconds": a.duration_seconds
                } for a in audios
            ]
        }
        archive.append(d_dict)

    json_str = json.dumps(archive, indent=2, ensure_ascii=False)
    return Response(content=json_str, media_type="application/json", headers={"Content-Disposition": "attachment; filename=regional_dialect_preservation_archive.json"})

@router.get("/export/csv")
def export_lexicon_csv(db: Session = Depends(get_db)):
    entries = db.query(LexiconEntry).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Dialect Code", "Term", "IPA", "English Meaning", "Standard Language Meaning", "Category", "Status"])

    for e in entries:
        dialect_code = e.dialect.code if e.dialect else ""
        writer.writerow([e.id, dialect_code, e.term, e.ipa_transcription, e.meaning_en, e.meaning_standard_lang, e.semantic_category, e.verification_status])

    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=dialect_lexicon_dictionary.csv"})
