from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from beaverhabits.app.auth import user_authenticate, user_create_token, user_create
from beaverhabits.app.db import User
from beaverhabits.app.schemas import UserRead
from beaverhabits.logging import logger
from beaverhabits.configs import settings

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response with access token and user info."""
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class RegisterRequest(BaseModel):
    """Register request model."""
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    """Register response model."""
    message: str
    user: UserRead
    verification_required: bool


@router.post("/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Authenticate user and return JWT access token.

    The token should be used in subsequent requests in the Authorization header:
    `Authorization: Bearer <token>`
    """
    # Authenticate user
    user = await user_authenticate(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is verified (if verification is required)
    if settings.REQUIRE_VERIFICATION and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your email for verification link.",
        )

    # Generate JWT token
    token = await user_create_token(user)

    if not token:
        logger.error(f"Failed to create token for user {user.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate access token"
        )

    logger.info(f"User {user.email} logged in successfully via API")

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead.model_validate(user)
    )


@router.post("/auth/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(registration: RegisterRequest):
    """
    Register a new user account.

    If email verification is enabled (REQUIRE_VERIFICATION=true in settings),
    a verification email will be sent to the provided email address.
    The user must verify their email before being able to login.
    """
    try:
        # Create the user
        user = await user_create(
            email=registration.email,
            password=registration.password,
            is_superuser=False
        )

        logger.info(f"User {user.email} registered successfully via API")

        message = "User registered successfully."
        if settings.REQUIRE_VERIFICATION:
            message += " Please check your email to verify your account before logging in."

        return RegisterResponse(
            message=message,
            user=UserRead.model_validate(user),
            verification_required=settings.REQUIRE_VERIFICATION
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Registration failed for {registration.email}: {error_msg}")

        # Check if it's a "user already exists" error
        if "already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists"
            )

        # Generic error for other cases
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {error_msg}"
        )
