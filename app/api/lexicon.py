from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import LexiconEntry, Dialect, User, LexiconVote, VerificationStatus
from app.schemas.schemas import (
    LexiconCreate, LexiconResponse, LexiconUpdate,
    PhoneticSearchRequest
)
from app.services.auth_service import get_current_user, get_optional_user
from app.services.phonetic import devanagari_to_ipa, generate_indic_soundex, levenshtein_distance
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/lexicon", tags=["Lexicon & Dictionary Preserver"])

@router.get("/", response_model=List[LexiconResponse])
def list_lexicon_entries(
    dialect_id: Optional[int] = Query(None, description="Filter by dialect ID"),
    semantic_category: Optional[str] = Query(None, description="Filter by category (e.g. Folklore, Maritime, Daily Life)"),
    part_of_speech: Optional[str] = Query(None, description="Filter by Part of Speech"),
    search: Optional[str] = Query(None, description="Search term or translation"),
    verification_status: Optional[str] = Query(None, description="Pending, Verified, Rejected"),
    db: Session = Depends(get_db)
):
    query = db.query(LexiconEntry)
    if dialect_id:
        query = query.filter(LexiconEntry.dialect_id == dialect_id)
    if semantic_category:
        query = query.filter(LexiconEntry.semantic_category == semantic_category)
    if part_of_speech:
        query = query.filter(LexiconEntry.part_of_speech == part_of_speech)
    if verification_status:
        query = query.filter(LexiconEntry.verification_status == verification_status)
    if search:
        query = query.filter(
            (LexiconEntry.term.ilike(f"%{search}%")) |
            (LexiconEntry.meaning_en.ilike(f"%{search}%")) |
            (LexiconEntry.meaning_standard_lang.ilike(f"%{search}%"))
        )
    return query.all()

@router.post("/", response_model=LexiconResponse, status_code=status.HTTP_201_CREATED)
async def create_lexicon_entry(
    entry_in: LexiconCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dialect = db.query(Dialect).filter(Dialect.id == entry_in.dialect_id).first()
    if not dialect:
        raise HTTPException(status_code=404, detail="Dialect not found")

    # Auto generate IPA if missing
    ipa = entry_in.ipa_transcription
    if not ipa and entry_in.script == "Devanagari":
        ipa = devanagari_to_ipa(entry_in.term)

    phonetic_code = generate_indic_soundex(entry_in.term)

    entry = LexiconEntry(
        dialect_id=entry_in.dialect_id,
        term=entry_in.term,
        script=entry_in.script,
        ipa_transcription=ipa,
        phonetic_code=phonetic_code,
        meaning_en=entry_in.meaning_en,
        meaning_standard_lang=entry_in.meaning_standard_lang,
        part_of_speech=entry_in.part_of_speech,
        example_sentence_dialect=entry_in.example_sentence_dialect,
        example_sentence_translation=entry_in.example_sentence_translation,
        etymology=entry_in.etymology,
        semantic_category=entry_in.semantic_category,
        submitted_by_id=current_user.id,
        verification_status=VerificationStatus.VERIFIED if current_user.role in ["Linguist", "Admin"] else VerificationStatus.PENDING
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Broadcast websocket activity update
    await ws_manager.broadcast_activity({
        "type": "NEW_LEXICON_ENTRY",
        "entry_id": entry.id,
        "term": entry.term,
        "dialect_name": dialect.name,
        "submitted_by": current_user.username
    })

    return entry

@router.get("/{entry_id}", response_model=LexiconResponse)
def get_lexicon_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(LexiconEntry).filter(LexiconEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Lexicon entry not found")
    return entry

@router.post("/ipa-generate")
def generate_ipa_for_text(text: str = Query(..., example="ख़य चाललोस?")):
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
    query = db.query(LexiconEntry)
    if req.dialect_id:
        query = query.filter(LexiconEntry.dialect_id == req.dialect_id)

    all_entries = query.all()
    results = []
    for entry in all_entries:
        # Match by soundex code or Levenshtein distance
        dist = levenshtein_distance(req.query_term.lower(), entry.term.lower())
        soundex_match = (entry.phonetic_code == target_code)
        
        if dist <= req.max_distance or soundex_match:
            results.append((dist, entry))

    # Sort results by closest distance
    results.sort(key=lambda x: x[0])
    return [item[1] for item in results[:20]]

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
        # Update vote
        if existing_vote.vote == 1:
            entry.upvotes -= 1
        else:
            entry.downvotes -= 1
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
        "message": "Vote recorded successfully",
        "upvotes": entry.upvotes,
        "downvotes": entry.downvotes
    }
