from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from src.models.schemas import FoodAnalysisRequest, FoodAnalysisResponse, MealLogRequest, RecipeSuggestionRequest, RecipeSuggestionResponse
from src.services.gemini import analyze_meal, suggest_recipe
from src.services.firestore import save_meal
from src.utils.limiter import limiter
from src.utils.logger import logger

router = APIRouter(prefix="/api", tags=["food"])

@router.post("/analyze", response_model=FoodAnalysisResponse)
@limiter.limit("20/minute")
async def analyze_food(request: Request, payload: FoodAnalysisRequest):
    """
    Analyze a meal using AI.
    """
    try:
        analysis = await analyze_meal(
            meal_description=payload.meal_description,
            meal_type=payload.meal_type.value
        )
        return analysis
    except ValueError as e:
        logger.error(f"Analysis error: {e}")
        # Could be an invalid response from Gemini or bad format
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in /analyze: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/log")
@limiter.limit("30/minute")
async def log_food(request: Request, payload: MealLogRequest):
    """
    Save a meal analysis to the database.
    """
    try:
        doc_id = await save_meal(
            user_id=payload.user_id,
            meal_description=payload.meal_description,
            meal_type=payload.meal_type.value,
            analysis=payload.analysis
        )
        return {"success": True, "meal_id": doc_id}
    except Exception as e:
        logger.error(f"Failed to log meal: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while logging meal")

@router.post("/suggest-recipe", response_model=RecipeSuggestionResponse)
@limiter.limit("20/minute")
async def suggest_recipe_route(request: Request, payload: RecipeSuggestionRequest):
    """
    Suggest a healthy recipe based on ingredients using AI.
    """
    try:
        suggestion = await suggest_recipe(ingredients=payload.ingredients)
        return suggestion
    except ValueError as e:
        logger.error(f"Recipe suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in /suggest-recipe: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
