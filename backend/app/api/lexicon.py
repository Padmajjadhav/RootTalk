import math
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import LexiconEntry, Dialect, User, LexiconVote, VerificationStatus
from app.schemas.schemas import (
    LexiconCreate, LexiconResponse, LexiconUpdate,
    PhoneticSearchRequest
)
from app.services.auth_service import get_current_user, get_optional_user
from app.services.phonetic import (
    devanagari_to_ipa, generate_indic_soundex,
    levenshtein_distance, devanagari_to_transliteration
)
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/lexicon", tags=["Lexicon & Dictionary Preserver"])

@router.get("/", response_model=List[LexiconResponse])
def list_lexicon_entries(
    response: Response,
    dialect_id: Optional[int] = Query(None, description="Filter by dialect ID"),
    semantic_category: Optional[str] = Query(None, description="Filter by category (e.g. Agriculture, Food)"),
    part_of_speech: Optional[str] = Query(None, description="Filter by Part of Speech"),
    search: Optional[str] = Query(None, description="Search term, transliteration, or translation"),
    verification_status: Optional[str] = Query(None, description="Pending, Verified, Rejected"),
    page: Optional[int] = Query(None, ge=1, description="Page number for pagination"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Items per page"),
    skip: int = Query(0, ge=0, description="Items to skip"),
    db: Session = Depends(get_db)
):
    query = db.query(LexiconEntry)
    if dialect_id:
        query = query.filter(LexiconEntry.dialect_id == dialect_id)
    if semantic_category and semantic_category.lower() != "all":
        query = query.filter(LexiconEntry.category.ilike(semantic_category))
    if part_of_speech and part_of_speech.lower() != "all":
        query = query.filter(LexiconEntry.part_of_speech == part_of_speech)
    if verification_status and verification_status.lower() != "all":
        query = query.filter(LexiconEntry.verification_status.ilike(verification_status))
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (LexiconEntry.word.ilike(search_pattern)) |
            (LexiconEntry.transliteration.ilike(search_pattern)) |
            (LexiconEntry.meaning.ilike(search_pattern)) |
            (LexiconEntry.meaning_standard_lang.ilike(search_pattern)) |
            (LexiconEntry.example_sentence.ilike(search_pattern))
        )

    total_count = query.count()
    response.headers["X-Total-Count"] = str(total_count)

    if page is not None and limit is not None:
        effective_skip = (page - 1) * limit
        total_pages = max(1, math.ceil(total_count / limit))
        response.headers["X-Total-Pages"] = str(total_pages)
        response.headers["X-Current-Page"] = str(page)
        return query.offset(effective_skip).limit(limit).all()
    elif limit is not None:
        return query.offset(skip).limit(limit).all()

    return query.all()

@router.post("/", response_model=LexiconResponse, status_code=status.HTTP_201_CREATED)
async def create_lexicon_entry(
    entry_in: LexiconCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    dialect = None
    if entry_in.dialect_id:
        dialect = db.query(Dialect).filter(Dialect.id == entry_in.dialect_id).first()
    if not dialect:
        dialect = db.query(Dialect).first()

    dialect_id = dialect.id if dialect else None

    # Auto generate IPA if missing
    ipa = entry_in.ipa_transcription
    if not ipa:
        ipa = devanagari_to_ipa(entry_in.term)

    phonetic_code = generate_indic_soundex(entry_in.term)
    is_verified = (current_user.role in ["Linguist", "Admin"]) if current_user else False
    user_id = current_user.id if current_user else None
    username = current_user.username if current_user else "Community Preserver"

    entry = LexiconEntry(
        dialect_id=dialect_id,
        word=entry_in.term,
        transliteration=entry_in.script if entry_in.script != "Devanagari" else devanagari_to_transliteration(entry_in.term),
        ipa_transcription=ipa,
        phonetic_code=phonetic_code,
        meaning=entry_in.meaning_en,
        meaning_standard_lang=entry_in.meaning_standard_lang,
        part_of_speech=entry_in.part_of_speech or "Noun",
        example_sentence=entry_in.example_sentence_dialect,
        example_sentence_translation=entry_in.example_sentence_translation,
        etymology=entry_in.etymology,
        category=entry_in.semantic_category or "Daily Life",
        submitted_by_id=user_id,
        verification_status=VerificationStatus.VERIFIED if is_verified else VerificationStatus.PENDING,
        source="Community Submission" if not current_user else "Authenticated Contributor"
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Broadcast websocket activity update
    await ws_manager.broadcast_activity({
        "type": "NEW_LEXICON_ENTRY",
        "entry_id": entry.id,
        "term": entry.term,
        "dialect_name": dialect.name if dialect else "Regional Marathi",
        "submitted_by": username
    })

    return entry

@router.get("/{entry_id}", response_model=LexiconResponse)
def get_lexicon_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(LexiconEntry).filter(LexiconEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Lexicon entry not found")
    return entry

@router.post("/ipa-generate")
def generate_ipa_for_text(text: str = Query(..., description="Devanagari phrase or word to convert")):
    """Generates real-time IPA representation for given regional script text."""
    ipa = devanagari_to_ipa(text)
    return {
        "input_text": text,
        "ipa_transcription": ipa
    }

@router.post("/phonetic-search", response_model=List[LexiconResponse])
def search_phonetically(
    req: PhoneticSearchRequest,
    db: Session = Depends(get_db)
):
    """Searches lexicon entries using phonetic distance matching (Soundex + Levenshtein)."""
    target_code = generate_indic_soundex(req.query_term)
    target_norm = devanagari_to_transliteration(req.query_term).lower()

    query = db.query(LexiconEntry)
    if req.dialect_id:
        query = query.filter(LexiconEntry.dialect_id == req.dialect_id)

    all_entries = query.all()
    results = []
    for entry in all_entries:
        entry_norm = devanagari_to_transliteration(entry.word or "").lower()
        dist = levenshtein_distance(target_norm, entry_norm)
        soundex_match = (entry.phonetic_code == target_code) or (generate_indic_soundex(entry.word) == target_code)
        text_match = (req.query_term.lower() in (entry.word or "").lower()) or (req.query_term.lower() in (entry.meaning or "").lower())

        if dist <= req.max_distance or soundex_match or text_match:
            rank = 0 if soundex_match else dist
            results.append((rank, entry))

    results.sort(key=lambda x: x[0])
    return [item[1] for item in results[:50]]

@router.post("/{entry_id}/vote")
def vote_lexicon_entry(
    entry_id: int,
    vote_type: int = Query(..., description="Pass +1 for Upvote, -1 for Downvote"),
    comment: Optional[str] = Query(None, description="Optional peer review feedback comment"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    entry = db.query(LexiconEntry).filter(LexiconEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Lexicon entry not found")

    existing_vote = db.query(LexiconVote).filter(
        LexiconVote.user_id == current_user.id,
        LexiconVote.lexicon_id == entry_id
    ).first()

    if existing_vote:
        if existing_vote.vote == 1:
            entry.upvotes = max(0, entry.upvotes - 1)
        elif existing_vote.vote == -1:
            entry.downvotes = max(0, entry.downvotes - 1)

        existing_vote.vote = 1 if vote_type > 0 else -1
        existing_vote.comment = comment
    else:
        new_vote = LexiconVote(
            user_id=current_user.id,
            lexicon_id=entry_id,
            vote=1 if vote_type > 0 else -1,
            comment=comment
        )
        db.add(new_vote)

    if vote_type > 0:
        entry.upvotes += 1
    else:
        entry.downvotes += 1

    db.commit()
    db.refresh(entry)

    return {
        "entry_id": entry_id,
        "upvotes": entry.upvotes,
        "downvotes": entry.downvotes,
        "user_vote": 1 if vote_type > 0 else -1
    }
