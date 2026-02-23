from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.auth import create_access_token, hash_password, verify_password
from src.api.db import get_db
from src.api.models import AppUser
from src.api.schemas import LoginRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    summary="Sign up",
    description="Create a new user account and return an access token.",
    operation_id="auth_signup",
)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Create a user account and return JWT access token."""
    existing = db.execute(select(AppUser).where(AppUser.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = AppUser(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user_id=str(user.id), email=user.email)
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description="Authenticate with email/password and return an access token.",
    operation_id="auth_login",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate existing user and return JWT access token."""
    user = db.execute(select(AppUser).where(AppUser.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user_id=str(user.id), email=user.email)
    return TokenResponse(access_token=token)
