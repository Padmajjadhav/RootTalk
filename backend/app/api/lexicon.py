import math
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request, status
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
    levenshtein_distance, devanagari_to_transliteration,
    normalize_marathi_text
)
from app.services.websocket_manager import ws_manager
from app.services.rate_limiter import rate_limiter

router = APIRouter(prefix="/lexicon", tags=["Lexicon & Dictionary Preserver"])

@router.get("/", response_model=List[LexiconResponse])
def list_lexicon_entries(
    response: Response,
    dialect_id: Optional[int] = Query(None, description="Filter by dialect ID"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. Agriculture, Food)"),
    semantic_category: Optional[str] = Query(None, description="Filter by category alias"),
    part_of_speech: Optional[str] = Query(None, description="Filter by Part of Speech"),
    search: Optional[str] = Query(None, description="Search term, transliteration, or translation"),
    verification_status: Optional[str] = Query(None, description="Pending, Verified, Rejected"),
    page: Optional[int] = Query(None, ge=1, description="Page number for pagination"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Items per page"),
    skip: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(LexiconEntry)

    if dialect_id:
        query = query.filter(LexiconEntry.dialect_id == dialect_id)
    cat_filter = category or semantic_category
    if cat_filter and cat_filter.strip().lower() != "all":
        query = query.filter(LexiconEntry.category.ilike(f"%{cat_filter.strip()}%"))
    if part_of_speech and part_of_speech.strip().lower() != "all":
        query = query.filter(LexiconEntry.part_of_speech.ilike(f"%{part_of_speech.strip()}%"))
    if verification_status and verification_status.strip().lower() != "all":
        query = query.filter(LexiconEntry.verification_status.ilike(f"%{verification_status.strip()}%"))

    if search:
        search_filter = (
            LexiconEntry.word.ilike(f"%{search}%") |
            LexiconEntry.transliteration.ilike(f"%{search}%") |
            LexiconEntry.meaning.ilike(f"%{search}%") |
            LexiconEntry.meaning_standard_lang.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

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
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    # Public abuse protection: rate limit unauthenticated submissions
    if not current_user:
        rate_limiter.check(request, endpoint_key="lexicon_contribute")

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

    # Standardized WebSocket activity event broadcast
    await ws_manager.broadcast_activity({
        "event": "NEW_LEXICON_ENTRY",
        "type": "NEW_LEXICON_ENTRY",
        "entry_id": entry.id,
        "term": entry.term,
        "word": entry.word,
        "dialect_name": dialect.name if dialect else "Regional Marathi",
        "submitted_by": username,
        "data": {
            "id": entry.id,
            "term": entry.term,
            "meaning": entry.meaning,
            "dialect": dialect.name if dialect else "Regional Marathi"
        }
    })

    return entry

@router.get("/{entry_id}", response_model=LexiconResponse)
def get_lexicon_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(LexiconEntry).filter(LexiconEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Lexicon entry not found")
    return entry

@router.post("/ipa-generate")
def generate_ipa_for_term(term: str = Query(..., description="Devanagari regional term")):
    """Converts a Devanagari text term into standard International Phonetic Alphabet (IPA)."""
    ipa = devanagari_to_ipa(term)
    soundex = generate_indic_soundex(term)
    transliteration = devanagari_to_transliteration(term)
    return {
        "term": term,
        "ipa": ipa,
        "soundex_code": soundex,
        "transliteration": transliteration
    }

@router.post("/phonetic-search", response_model=List[LexiconResponse])
def phonetic_lexicon_search(
    req: PhoneticSearchRequest,
    db: Session = Depends(get_db)
):
    q_clean = req.query_term.strip() if req.query_term else ""
    if not q_clean:
        return []

    query = db.query(LexiconEntry)
    if req.dialect_id:
        query = query.filter(LexiconEntry.dialect_id == req.dialect_id)
    cat = req.category or req.semantic_category
    if cat and cat.strip().lower() != "all":
        query = query.filter(LexiconEntry.category.ilike(f"%{cat.strip()}%"))

    all_entries = query.all()

    q_lower = q_clean.lower()
    q_norm = normalize_marathi_text(q_clean)
    q_trans = devanagari_to_transliteration(q_clean).lower()
    q_soundex = generate_indic_soundex(q_clean)
    is_dev = any('\u0900' <= c <= '\u097f' for c in q_clean)

    results = []
    for entry in all_entries:
        e_term = (entry.term or entry.word or "").strip()
        e_norm = normalize_marathi_text(e_term)
        e_trans = (entry.transliteration or "").strip().lower()
        e_term_trans = devanagari_to_transliteration(e_term).lower()
        e_meaning = (entry.meaning or "").lower()
        e_std = (entry.meaning_standard_lang or "").lower()
        e_soundex = entry.phonetic_code or generate_indic_soundex(e_term)

        e_tokens = set([t.strip('?!.,:;"\'') for t in (e_term_trans + " " + e_trans).split() if t])
        e_dev_tokens = set([t.strip('?!.,:;"\'') for t in e_norm.split() if t])

        rank = None
        best_dist = 99

        # 1. Exact match (Rank 0)
        if q_norm == e_norm or q_lower == e_trans or q_trans == e_term_trans or q_lower == e_term_trans:
            rank = 0
            best_dist = 0
        # 2. Token exact match (Rank 1)
        elif (is_dev and q_norm in e_dev_tokens) or (q_lower in e_tokens) or (q_trans in e_tokens):
            rank = 1
            best_dist = 0
        # 3. Prefix match (Rank 2)
        elif e_trans.startswith(q_lower) or e_term_trans.startswith(q_trans) or (is_dev and e_norm.startswith(q_norm)):
            rank = 2
            best_dist = 1
        # 4. Substring match (Rank 3)
        elif (q_lower in e_trans) or (q_trans in e_term_trans) or (is_dev and q_norm in e_norm):
            rank = 3
            best_dist = 1
        else:
            # 5. Fuzzy match on transliteration or Devanagari
            dist_trans = min(
                levenshtein_distance(q_trans, e_term_trans),
                levenshtein_distance(q_trans, e_trans) if e_trans else 99
            )
            token_dists = [levenshtein_distance(q_trans, tok) for tok in e_tokens if tok]
            if token_dists:
                dist_trans = min(dist_trans, min(token_dists))

            if is_dev:
                dist_dev = min([levenshtein_distance(q_norm, tok) for tok in e_dev_tokens if tok] + [levenshtein_distance(q_norm, e_norm)])
                best_dist = min(dist_trans, dist_dev)
            else:
                best_dist = dist_trans

            soundex_match = bool(q_soundex and e_soundex and q_soundex == e_soundex)

            if soundex_match and best_dist <= (req.max_distance + 1):
                rank = 4 + min(best_dist, 3)
            elif best_dist <= req.max_distance:
                rank = 5 + best_dist
            elif q_lower in e_meaning or q_lower in e_std:
                rank = 12
                best_dist = 10

        if rank is not None:
            results.append((rank, best_dist, entry))

    results.sort(key=lambda x: (x[0], x[1], x[2].id))
    return [item[2] for item in results[:50]]

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
