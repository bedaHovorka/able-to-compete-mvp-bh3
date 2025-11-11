from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from app.utils.auth import demo_login, create_access_token
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Login endpoint - simplified for MVP
    In production, verify credentials against database
    """
    access_token = demo_login(credentials.email, credentials.password)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=access_token)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest):
    """
    Register new user - simplified for MVP
    In production, save to database and verify email
    """
    # For MVP, auto-login after registration
    access_token = demo_login(user_data.email, user_data.password)

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    # For MVP, just create new token
    # In production, verify refresh token and generate new access token
    import uuid
    access_token = create_access_token(data={"sub": str(uuid.uuid4())})

    return TokenResponse(access_token=access_token)
