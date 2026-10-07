from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Contributor
from app.schemas.schemas import ContributorResponse

router = APIRouter(tags=["Contributors"])

@router.get("/contributors", response_model=List[ContributorResponse])
def list_contributors(db: Session = Depends(get_db)):
    return db.query(Contributor).all()

@router.get("/contributors/{contributor_id}", response_model=ContributorResponse)
def get_contributor(contributor_id: int, db: Session = Depends(get_db)):
    contributor = db.query(Contributor).filter(Contributor.id == contributor_id).first()
    if not contributor:
        raise HTTPException(status_code=404, detail="Contributor not found")
    return contributor
