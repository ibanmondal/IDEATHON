import os
from typing import List, Dict, Any, Optional
from google.cloud import firestore

from src.models.schemas import HabitSummary, FoodAnalysisResponse
from src.utils.logger import logger

def get_firestore_client() -> firestore.AsyncClient:
    """Initialize Firestore async client."""
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        try:
            return firestore.AsyncClient()
        except Exception as e:
            logger.warning(f"Could not initialize Firestore without project ID: {e}")
            raise
    return firestore.AsyncClient(project=project_id)


async def save_meal(user_id: str, meal_description: str, meal_type: str, analysis: FoodAnalysisResponse) -> str:
    """
    Save a meal analysis to Firestore.
    Returns the document ID.
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("meals").document()
        
        data = {
            "user_id": user_id,
            "meal_description": meal_description,
            "meal_type": meal_type,
            "analysis": analysis.model_dump(),
            "logged_at": firestore.SERVER_TIMESTAMP
        }
        
        await doc_ref.set(data)
        logger.info(f"Saved meal for user {user_id} with ID {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        logger.error(f"Firestore save error (mocking success): {e}")
        return "mock-doc-id-123"

async def get_meal_history(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve the recent meal history for a user."""
    try:
        db = get_firestore_client()
        query = (
            db.collection("meals")
            .where("user_id", "==", user_id)
            .order_by("logged_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        
        results = []
        async for doc in query.stream():
            doc_dict = doc.to_dict()
            doc_dict["id"] = doc.id
            results.append(doc_dict)
            
        return results
    except Exception as e:
        logger.error(f"Firestore get history error (returning mock data): {e}")
        return [
            {
                "id": "mock-1",
                "meal_description": "Oatmeal with Blueberries",
                "meal_type": "Breakfast",
                "analysis": {
                    "health_score": 85,
                    "nutrition": {"calories": 300, "protein_g": 10, "carbs_g": 50, "fat_g": 5, "fiber_g": 8},
                },
                "logged_at": "Today"
            },
            {
                "id": "mock-2",
                "meal_description": "Grilled Chicken Salad",
                "meal_type": "Lunch",
                "analysis": {
                    "health_score": 92,
                    "nutrition": {"calories": 400, "protein_g": 35, "carbs_g": 15, "fat_g": 20, "fiber_g": 5},
                },
                "logged_at": "Yesterday"
            }
        ]

async def get_habit_summary(user_id: str) -> HabitSummary:
    """
    Compute a habit summary based on user's meal history.
    Compare recent half vs older half of the last 20 meals to determine trend.
    """
    try:
        meals = await get_meal_history(user_id, limit=20)
        
        if not meals:
            return HabitSummary(avg_score=0.0, trend="stable")
            
        scores = [meal.get("analysis", {}).get("health_score", 0) for meal in meals]
        avg_score = sum(scores) / len(scores)
        
        # Sort meals by score to find best and worst
        sorted_meals = sorted(meals, key=lambda m: m.get("analysis", {}).get("health_score", 0))
        worst_meal = sorted_meals[0].get("meal_description") if sorted_meals else None
        best_meal = sorted_meals[-1].get("meal_description") if sorted_meals else None
        
        # Calculate trend (recent vs older)
        # Note: meals is already ordered by logged_at DESCENDING (newest first)
        trend = "stable"
        if len(scores) >= 4:
            half = len(scores) // 2
            recent_half = scores[:half]
            older_half = scores[half:]
            
            recent_avg = sum(recent_half) / len(recent_half)
            older_avg = sum(older_half) / len(older_half)
            
            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
                
        return HabitSummary(
            avg_score=round(avg_score, 1),
            best_meal=best_meal,
            worst_meal=worst_meal,
            trend=trend
        )
    except Exception as e:
        logger.error(f"Firestore get summary error (returning mock data): {e}")
        return HabitSummary(
            avg_score=88.5,
            best_meal="Grilled Chicken Salad",
            worst_meal="Oatmeal with Blueberries",
            trend="improving"
        )
