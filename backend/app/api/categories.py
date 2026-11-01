from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import Category, LexiconEntry, Entry
from app.schemas.schemas import CategoryResponse

router = APIRouter(tags=["Categories"])

@router.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    lex_counts = dict(db.query(LexiconEntry.semantic_category, func.count(LexiconEntry.id)).group_by(LexiconEntry.semantic_category).all())
    entry_counts = dict(db.query(Entry.category, func.count(Entry.id)).group_by(Entry.category).all())

    result = []
    for c in categories:
        cnt = max(lex_counts.get(c.name, 0), entry_counts.get(c.name, 0))
        result.append(CategoryResponse(id=c.id, name=c.name, description=c.description, count=cnt))
    return result
