from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Dialect, LexiconEntry, AudioArchive, User, UserRole
from app.schemas.schemas import DialectCreate, DialectResponse, DialectUpdate
from app.services.auth_service import get_current_user, get_optional_user

router = APIRouter(prefix="/dialects", tags=["Dialects & Regional Languages"])

@router.get("/", response_model=List[DialectResponse])
def list_dialects(
    state: Optional[str] = Query(None, description="Filter by state (e.g. Maharashtra)"),
    parent_language: Optional[str] = Query(None, description="Filter by main language (e.g. Marathi, Hindi)"),
    endangerment_status: Optional[str] = Query(None, description="Filter by endangerment status"),
    search: Optional[str] = Query(None, description="Search dialect name or region"),
    db: Session = Depends(get_db)
):
    query = db.query(Dialect)
    if state:
        query = query.filter(Dialect.state.ilike(f"%{state}%"))
    if parent_language:
        query = query.filter(Dialect.parent_language.ilike(f"%{parent_language}%"))
    if endangerment_status:
        query = query.filter(Dialect.endangerment_status == endangerment_status)
    if search:
        query = query.filter(
            (Dialect.name.ilike(f"%{search}%")) |
            (Dialect.region_name.ilike(f"%{search}%")) |
            (Dialect.description.ilike(f"%{search}%"))
        )
    
    dialects = query.all()
    results = []
    for d in dialects:
        lexicon_count = db.query(LexiconEntry).filter(LexiconEntry.dialect_id == d.id).count()
        audio_count = db.query(AudioArchive).filter(AudioArchive.dialect_id == d.id).count()
        
        # Preservation score calculation (0 to 100)
        score = min(100.0, round((lexicon_count * 2.5 + audio_count * 10.0), 1))
        
        d_res = DialectResponse.model_validate(d)
        d_res.lexicon_count = lexicon_count
        d_res.audio_count = audio_count
        d_res.preservation_score = score
        results.append(d_res)

    return results

@router.post("/", response_model=DialectResponse, status_code=status.HTTP_201_CREATED)
def create_dialect(
    dialect_in: DialectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Dialect).filter(Dialect.code == dialect_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Dialect with code '{dialect_in.code}' already exists.")

    dialect = Dialect(**dialect_in.dict())
    db.add(dialect)
    db.commit()
    db.refresh(dialect)

    d_res = DialectResponse.model_validate(dialect)
    d_res.lexicon_count = 0
    d_res.audio_count = 0
    d_res.preservation_score = 0.0
    return d_res

@router.get("/{dialect_id}", response_model=DialectResponse)
def get_dialect(dialect_id: int, db: Session = Depends(get_db)):
    dialect = db.query(Dialect).filter(Dialect.id == dialect_id).first()
    if not dialect:
        raise HTTPException(status_code=404, detail="Dialect not found")

    lexicon_count = db.query(LexiconEntry).filter(LexiconEntry.dialect_id == dialect.id).count()
    audio_count = db.query(AudioArchive).filter(AudioArchive.dialect_id == dialect.id).count()
    score = min(100.0, round((lexicon_count * 2.5 + audio_count * 10.0), 1))

    d_res = DialectResponse.model_validate(dialect)
    d_res.lexicon_count = lexicon_count
    d_res.audio_count = audio_count
    d_res.preservation_score = score
    return d_res

@router.put("/{dialect_id}", response_model=DialectResponse)
def update_dialect(
    dialect_id: int,
    dialect_in: DialectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dialect = db.query(Dialect).filter(Dialect.id == dialect_id).first()
    if not dialect:
        raise HTTPException(status_code=404, detail="Dialect not found")

    for field, val in dialect_in.dict(exclude_unset=True).items():
        setattr(dialect, field, val)

    db.commit()
    db.refresh(dialect)
    return get_dialect(dialect_id, db)

@router.delete("/{dialect_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dialect(
    dialect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only Admins can delete dialect records")
    dialect = db.query(Dialect).filter(Dialect.id == dialect_id).first()
    if not dialect:
        raise HTTPException(status_code=404, detail="Dialect not found")
    db.delete(dialect)
    db.commit()
    return None

@router.get("/{dialect_id}/map-data")
def get_dialect_map_data(dialect_id: int, db: Session = Depends(get_db)):
    dialect = db.query(Dialect).filter(Dialect.id == dialect_id).first()
    if not dialect:
        raise HTTPException(status_code=404, detail="Dialect not found")

    return {
        "id": dialect.id,
        "name": dialect.name,
        "parent_language": dialect.parent_language,
        "code": dialect.code,
        "region_name": dialect.region_name,
        "state": dialect.state,
        "districts": dialect.districts.split(",") if dialect.districts else [],
        "coordinates": {
            "latitude": dialect.latitude,
            "longitude": dialect.longitude
        },
        "endangerment_status": dialect.endangerment_status,
        "estimated_speakers": dialect.estimated_speakers
    }
