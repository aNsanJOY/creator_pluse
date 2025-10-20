from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from datetime import timedelta
import logging

from app.core.database import get_supabase
from app.api.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse, UserUpdate, PasswordResetRequest, PasswordReset
from app.core.security import create_access_token, decode_access_token, get_password_hash
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get the current user's profile information.
    """
    return UserResponse(**current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update the current user's profile information.
    Allows updating full_name and email.
    """
    try:
        user_id = current_user["id"]
        
        # Prepare update data (only include fields that are provided)
        update_data = {}
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        if user_update.email is not None:
            # Check if email is already taken by another user
            existing_user = supabase.table("users").select("id").eq("email", user_update.email).neq("id", user_id).execute()
            if existing_user.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use by another account"
                )
            update_data["email"] = user_update.email
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update user in database
        result = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        updated_user = result.data[0]
        logger.info(f"User {user_id} profile updated successfully")
        
        return UserResponse(**updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating profile: {str(e)}"
        )


@router.delete("/account")
async def delete_user_account(
    current_user: dict = Depends(get_current_active_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete the current user's account and all associated data.
    This is a destructive operation and cannot be undone.
    """
    try:
        user_id = current_user["id"]
        
        # Delete user from database
        # Note: Related data should be handled by database CASCADE rules
        # or you can explicitly delete related data here
        result = supabase.table("users").delete().eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
        
        logger.info(f"User {user_id} account deleted successfully")
        
        return {
            "message": "Account deleted successfully",
            "detail": "Your account and all associated data have been permanently deleted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting account: {str(e)}"
        )


@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    supabase: Client = Depends(get_supabase)
):
    """
    Initiate password reset process.
    Generates a reset token and stores it in the database.
    In production, this would send an email with a reset link.
    """
    try:
        # Check if user exists
        user_result = supabase.table("users").select("*").eq("email", request.email).execute()
        
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
        
        logger.info(f"Password reset token generated for user {user['id']}")
        
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
        logger.error(f"Error in forgot password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during password reset: {str(e)}"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    supabase: Client = Depends(get_supabase)
):
    """
    Confirm password reset with token and set new password.
    """
    try:
        # Decode and validate reset token
        payload = decode_access_token(reset_data.token)
        
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
        
        if user.get("reset_token") != reset_data.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Hash new password
        hashed_password = get_password_hash(reset_data.new_password)
        
        # Update password and clear reset token
        supabase.table("users").update({
            "password_hash": hashed_password,
            "reset_token": None
        }).eq("id", user_id).execute()
        
        logger.info(f"Password reset successful for user {user_id}")
        
        return {
            "message": "Password successfully reset"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reset password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during password reset confirmation: {str(e)}"
        )