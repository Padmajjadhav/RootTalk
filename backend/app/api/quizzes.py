from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import QuizDeck, QuizQuestion, Dialect, User, UserRole
from app.schemas.schemas import QuizDeckResponse, QuizSubmitRequest, QuizResultResponse
from app.services.auth_service import get_current_user, get_optional_user

router = APIRouter(prefix="/quizzes", tags=["Interactive Quizzes & Learning Decks"])

@router.get("/decks", response_model=List[QuizDeckResponse])
def list_quiz_decks(
    dialect_id: Optional[int] = Query(None, description="Filter by dialect ID"),
    difficulty: Optional[str] = Query(None, description="Beginner, Intermediate, Expert"),
    db: Session = Depends(get_db)
):
    query = db.query(QuizDeck)
    if dialect_id:
        query = query.filter(QuizDeck.dialect_id == dialect_id)
    if difficulty:
        query = query.filter(QuizDeck.difficulty == difficulty)
    return query.all()

@router.get("/decks/{deck_id}", response_model=QuizDeckResponse)
def get_quiz_deck(deck_id: int, db: Session = Depends(get_db)):
    deck = db.query(QuizDeck).filter(QuizDeck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Quiz deck not found")
    return deck

@router.post("/submit", response_model=QuizResultResponse)
def submit_quiz_answers(
    req: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    deck = db.query(QuizDeck).filter(QuizDeck.id == req.deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Quiz deck not found")

    questions_map = {q.id: q for q in deck.questions}
    correct_count = 0
    total_questions = len(deck.questions)

    for ans in req.answers:
        q = questions_map.get(ans.question_id)
        if q and q.correct_option.upper() == ans.selected_option.upper():
            correct_count += 1

    percentage = round((correct_count / max(1, total_questions)) * 100.0, 1)
    reputation_earned = 0

    if percentage >= 80 and current_user:
        reputation_earned = 15
        current_user.reputation_points += reputation_earned
        db.commit()

    feedback = f"Great work! You scored {percentage}% on {deck.title}."
    if percentage == 100:
        feedback = "Outstanding! Perfect score on dialect preservation trivia!"

    return QuizResultResponse(
        deck_id=deck.id,
        total_questions=total_questions,
        correct_count=correct_count,
        score_percentage=percentage,
        reputation_earned=reputation_earned,
        feedback=feedback
    )
