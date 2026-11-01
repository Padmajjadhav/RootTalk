from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserRole
from app.schemas.schemas import UserCreate, UserResponse, Token, UserLogin, UserRoleUpdate
from app.services.auth_service import (
    verify_password, get_password_hash, create_access_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_email = db.query(User).filter(User.email == user_in.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Security requirement: Public registration must always assign Contributor role.
    # Self-selection of Linguist or Admin roles is strictly disallowed.
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=UserRole.CONTRIBUTOR,
        reputation_points=10,
        badge_title="Linguistic Enthusiast"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_in: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin-only endpoint to promote users to Linguist or manage user roles."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only administrators can promote users or modify user roles."
        )

    valid_roles = [UserRole.CONTRIBUTOR, UserRole.LINGUIST, UserRole.ADMIN]
    if role_in.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role_in.role}'. Allowed roles are: {valid_roles}"
        )

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    target_user.role = role_in.role
    if role_in.role == UserRole.LINGUIST and target_user.badge_title == "Linguistic Enthusiast":
        target_user.badge_title = "Field Linguist"
    db.commit()
    db.refresh(target_user)
    return target_user
