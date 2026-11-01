from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import LexiconEntry, Entry, User, UserRole, VerificationStatus
from app.schemas.schemas import LexiconResponse, UserResponse
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/contributions", tags=["Peer Verification & Gamification"])

@router.get("/pending-lexicon", response_model=List[LexiconResponse])
def list_pending_lexicon_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.LINGUIST, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only Linguists or Admins can review pending submissions")
    return db.query(LexiconEntry).filter(LexiconEntry.verification_status == VerificationStatus.PENDING).all()

@router.post("/verify-lexicon/{entry_id}")
def verify_lexicon_entry(
    entry_id: int,
    approve: bool = Query(..., description="True to verify/approve, False to reject"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.LINGUIST, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only Linguists or Admins can verify submissions")

    entry = db.query(LexiconEntry).filter(LexiconEntry.id == entry_id).first()
    alt_entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if not entry and not alt_entry:
        raise HTTPException(status_code=404, detail="Lexicon entry not found")

    if entry:
        if approve:
            entry.verification_status = VerificationStatus.VERIFIED
            entry.verified_by_id = current_user.id
            if entry.submitted_by_id:
                contributor = db.query(User).filter(User.id == entry.submitted_by_id).first()
                if contributor:
                    contributor.reputation_points += 25
                    if contributor.reputation_points >= 100 and contributor.badge_title == "Linguistic Enthusiast":
                        contributor.badge_title = "Dialect Champion"
                    elif contributor.reputation_points >= 300:
                        contributor.badge_title = "Preservation Master"
        else:
            entry.verification_status = VerificationStatus.REJECTED

    if alt_entry:
        alt_entry.status = "published" if approve else "rejected"

    db.commit()
    final_status = entry.verification_status if entry else ("Verified" if approve else "Rejected")
    return {
        "entry_id": entry_id,
        "verification_status": final_status,
        "verified_by": current_user.username
    }

@router.get("/leaderboard", response_model=List[UserResponse])
def get_contributor_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    top_users = db.query(User).order_by(User.reputation_points.desc()).limit(limit).all()
    return top_users
