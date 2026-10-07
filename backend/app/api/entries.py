from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Entry, Contributor, VoiceRecording, LanguageVariety
from app.schemas.schemas import EntryResponse, EntryCreate

router = APIRouter(tags=["Entries & Dictionary Repository"])

@router.get("/entries", response_model=List[EntryResponse])
def get_entries(
    search: Optional[str] = Query(None, description="Search word, transliteration, meaning, region"),
    category: Optional[str] = Query(None, description="Category filter"),
    variety: Optional[str] = Query(None, description="Dialect/Variety filter"),
    region: Optional[str] = Query(None, description="Region filter"),
    district: Optional[str] = Query(None, description="District filter"),
    contributor: Optional[str] = Query(None, description="Contributor name or ID"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Entry)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Entry.word.ilike(search_pattern)) |
            (Entry.transliteration.ilike(search_pattern)) |
            (Entry.meaning.ilike(search_pattern)) |
            (Entry.category.ilike(search_pattern)) |
            (Entry.variety.ilike(search_pattern)) |
            (Entry.region.ilike(search_pattern)) |
            (Entry.district.ilike(search_pattern))
        )
    if category and category.lower() != "all":
        query = query.filter(Entry.category.ilike(category))
    if variety and variety.lower() != "all":
        query = query.filter(Entry.variety.ilike(variety))
    if region:
        query = query.filter(Entry.region.ilike(f"%{region}%"))
    if district:
        query = query.filter(Entry.district.ilike(f"%{district}%"))
    if contributor:
        if contributor.isdigit():
            query = query.filter(Entry.contributor_id == int(contributor))
        else:
            query = query.join(Contributor, isouter=True).filter(Contributor.name.ilike(f"%{contributor}%"))

    offset = (page - 1) * limit
    entries = query.offset(offset).limit(limit).all()
    return entries

@router.get("/entries/{entry_id}")
def get_entry_by_id(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    contributor = db.query(Contributor).filter(Contributor.id == entry.contributor_id).first() if entry.contributor_id else None
    voices = db.query(VoiceRecording).filter(VoiceRecording.entry_id == entry.id).all()

    return {
        "id": entry.id,
        "word": entry.word,
        "term": entry.word,
        "transliteration": entry.transliteration,
        "script": entry.transliteration or "Devanagari",
        "meaning": entry.meaning,
        "meaning_en": entry.meaning,
        "meaning_standard_lang": entry.meaning_standard_lang,
        "language": entry.language,
        "variety": entry.variety,
        "dialect_name": entry.variety,
        "category": entry.category,
        "semantic_category": entry.category,
        "region": entry.region,
        "district": entry.district,
        "taluka": entry.taluka,
        "example_sentence": entry.example_sentence,
        "example_sentence_dialect": entry.example_sentence,
        "example_sentence_translation": entry.example_sentence_translation,
        "pronunciation": entry.pronunciation,
        "ipa_transcription": entry.ipa_transcription,
        "audio_url": entry.audio_url,
        "contributor_id": entry.contributor_id,
        "contributor_name": contributor.name if contributor else "Community Contributor",
        "source": entry.source,
        "status": entry.status,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
        "voice_recordings": [
            {
                "id": v.id,
                "audio_file": v.audio_file,
                "duration": v.duration,
                "transcript": v.transcript
            } for v in voices
        ]
    }

@router.post("/entries", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(entry_in: EntryCreate, db: Session = Depends(get_db)):
    contributor = None
    if entry_in.contributor_name:
        contributor = db.query(Contributor).filter(Contributor.name.ilike(entry_in.contributor_name)).first()
        if not contributor:
            contributor = Contributor(name=entry_in.contributor_name, role="Community Preserver")
            db.add(contributor)
            db.commit()
            db.refresh(contributor)

    entry = Entry(
        word=entry_in.word,
        transliteration=entry_in.transliteration,
        meaning=entry_in.meaning,
        variety=entry_in.variety or "Standard Marathi",
        category=entry_in.category,
        region=entry_in.region,
        district=entry_in.district,
        taluka=entry_in.taluka,
        example_sentence=entry_in.example_sentence,
        pronunciation=entry_in.pronunciation,
        contributor_id=contributor.id if contributor else None,
        source="User Contribution",
        status="published"
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
