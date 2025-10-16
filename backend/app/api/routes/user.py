from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.core.database import get_supabase
from app.schemas.user import UserResponse, UserUpdate
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get the current user's profile information.
    """
    return UserResponse(**current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Update the current user's profile information.
    """
    try:
        # Prepare update data (only include fields that are provided)
        update_data = {}
        if user_update.full_name is not None:
            update_data["full_name"] = user_update.full_name
        if user_update.email is not None:
            # Check if new email is already taken by another user
            existing_user = supabase.table("users").select("*").eq("email", user_update.email).execute()
            if existing_user.data and existing_user.data[0]["id"] != current_user["id"]:
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
        result = supabase.table("users").update(update_data).eq("id", current_user["id"]).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user profile"
            )
        
        return UserResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating profile: {str(e)}"
        )


@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_user_account(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Delete the current user's account and all associated data.
    This is a permanent action and cannot be undone.
    """
    try:
        user_id = current_user["id"]
        
        # Delete user's associated data in order (respecting foreign key constraints)
        # 1. Delete feedback
        supabase.table("feedback").delete().eq("user_id", user_id).execute()
        
        # 2. Delete newsletter drafts
        supabase.table("newsletter_drafts").delete().eq("user_id", user_id).execute()
        
        # 3. Delete newsletter samples
        supabase.table("newsletter_samples").delete().eq("user_id", user_id).execute()
        
        # 4. Delete source content cache
        supabase.table("source_content_cache").delete().eq("user_id", user_id).execute()
        
        # 5. Delete sources
        supabase.table("sources").delete().eq("user_id", user_id).execute()
        
        # 6. Finally, delete the user
        result = supabase.table("users").delete().eq("id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user account"
            )
        
        return {
            "message": "Account successfully deleted",
            "detail": "All your data has been permanently removed"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting account: {str(e)}"
        )
