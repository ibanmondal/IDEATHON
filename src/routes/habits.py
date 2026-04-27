from fastapi import APIRouter, HTTPException, Request, Path
from typing import List, Dict, Any

from src.models.schemas import HabitSummary
from src.services.firestore import get_meal_history, get_habit_summary
from src.utils.limiter import limiter
from src.utils.logger import logger

router = APIRouter(prefix="/api", tags=["habits"])

@router.get("/history/{user_id}", response_model=List[Dict[str, Any]])
@limiter.limit("30/minute")
async def user_history(
    request: Request, 
    user_id: str = Path(..., description="The ID of the user")
) -> List[Dict[str, Any]]:
    """Get the recent meal history for a user."""
    if len(user_id) > 100:
        raise HTTPException(status_code=400, detail="User ID too long")
    try:
        history = await get_meal_history(user_id=user_id)
        return history
    except Exception as e:
        logger.error(f"Failed to fetch history for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/summary/{user_id}", response_model=HabitSummary)
@limiter.limit("30/minute")
async def user_summary(
    request: Request,
    user_id: str = Path(..., description="The ID of the user")
) -> HabitSummary:
    """Get the habit summary and trend for a user."""
    if len(user_id) > 100:
        raise HTTPException(status_code=400, detail="User ID too long")
    try:
        summary = await get_habit_summary(user_id=user_id)
        return summary
    except Exception as e:
        logger.error(f"Failed to fetch summary for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
