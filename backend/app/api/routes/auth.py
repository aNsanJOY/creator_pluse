from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from supabase import Client
from datetime import timedelta
from typing import Optional
import logging

from app.core.database import get_supabase

logger = logging.getLogger(__name__)

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)
from app.core.config import settings
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.api.dependencies import get_current_user

router = APIRouter()
security = HTTPBearer()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    supabase: Client = Depends(get_supabase)
):
    """
    Register a new user without email verification.
    Creates user in database and returns JWT token.
    """
    try:
        # Check if user already exists
        existing_user = supabase.table("users").select("*").eq("email", user_data.email).execute()
        
        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user in database
        new_user = {
            "email": user_data.email,
            "full_name": user_data.full_name,
            "password_hash": hashed_password,
            "is_active": True
        }
        
        result = supabase.table("users").insert(new_user).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        created_user = result.data[0]
        
        # Generate JWT token
        access_token = create_access_token(
            data={"sub": created_user["id"], "email": created_user["email"]}
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during signup: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    supabase: Client = Depends(get_supabase)
):
    """
    Authenticate user and return JWT token.
    """
    try:
        logger.info(f"Login attempt for email: {credentials.email}")
        
        # Fetch user from database
        logger.info("Querying database for user...")
        user_result = supabase.table("users").select("*").eq("email", credentials.email).execute()
        logger.info(f"Database query completed. Found user: {bool(user_result.data)}")
        
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        user = user_result.data[0]
        
        # Verify password
        logger.info("Verifying password...")
        if not verify_password(credentials.password, user["password_hash"]):
            logger.warning("Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        logger.info("Password verified successfully")
        
        # Check if user is active
        if not user.get("is_active", True):
            logger.warning("User account is inactive")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Generate JWT token
        logger.info("Generating JWT token...")
        access_token = create_access_token(
            data={"sub": user["id"], "email": user["email"]}
        )
        
        logger.info("Login successful")
        return Token(access_token=access_token, token_type="bearer")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during login: {str(e)}"
        )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint. Since we're using JWT, actual logout is handled client-side
    by removing the token. This endpoint can be used for logging/analytics.
    """
    return {
        "message": "Successfully logged out",
        "detail": "Please remove the token from client storage"
    }


@router.post("/reset-password")
async def reset_password(
    email: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Initiate password reset process.
    For MVP, this generates a reset token and stores it in the database.
    In production, this would send an email with a reset link.
    """
    try:
        # Check if user exists
        user_result = supabase.table("users").select("*").eq("email", email).execute()
        
        if not user_result.data:
            # Don't reveal if email exists or not for security
            return {
                "message": "If the email exists, a password reset link has been sent"
            }
        
        user = user_result.data[0]
        
        # Generate reset token (valid for 1 hour)
        reset_token = create_access_token(
            data={"sub": user["id"], "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # Store reset token in database
        supabase.table("users").update({
            "reset_token": reset_token
        }).eq("id", user["id"]).execute()
        
        # TODO: Send email with reset link containing the token
        # For now, return the token (only for development)
        if settings.ENVIRONMENT == "development":
            return {
                "message": "Password reset token generated",
                "reset_token": reset_token,
                "note": "In production, this would be sent via email"
            }
        
        return {
            "message": "If the email exists, a password reset link has been sent"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during password reset: {str(e)}"
        )


@router.post("/reset-password/confirm")
async def confirm_reset_password(
    reset_token: str,
    new_password: str,
    supabase: Client = Depends(get_supabase)
):
    """
    Confirm password reset with token and set new password.
    """
    try:
        # Decode and validate reset token
        payload = decode_access_token(reset_token)
        
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        user_id = payload.get("sub")
        
        # Verify token matches the one in database
        user_result = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_result.data[0]
        
        if user.get("reset_token") != reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Hash new password
        hashed_password = get_password_hash(new_password)
        
        # Update password and clear reset token
        supabase.table("users").update({
            "password_hash": hashed_password,
            "reset_token": None
        }).eq("id", user_id).execute()
        
        return {
            "message": "Password successfully reset"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during password reset confirmation: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information.
    """
    return UserResponse(**current_user)