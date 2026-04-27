import re
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class MealType(str, Enum):
    """Enumeration for meal types."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class FoodAnalysisRequest(BaseModel):
    """Request model for analyzing a meal."""
    meal_description: str = Field(..., min_length=3, max_length=500)
    user_id: str = Field(..., min_length=1, max_length=100)
    meal_type: MealType

    @field_validator("meal_description")
    def sanitize_description(cls, v: str) -> str:
        """Strip HTML characters < > & for basic sanitization."""
        if v:
            v = re.sub(r"[<>&]", "", v)
        return v


class NutritionInfo(BaseModel):
    """Nutritional information breakdown."""
    calories: int = Field(..., ge=0)
    protein_g: int = Field(..., ge=0)
    carbs_g: int = Field(..., ge=0)
    fat_g: int = Field(..., ge=0)
    fiber_g: int = Field(..., ge=0)


class FoodAnalysisResponse(BaseModel):
    """Response model for meal analysis from Gemini."""
    health_score: int = Field(..., ge=0, le=100)
    nutrition: NutritionInfo
    positive_aspects: List[str]
    improvements: List[str]
    recommendation: str


class MealLogRequest(BaseModel):
    """Request model for logging a meal to Firestore."""
    user_id: str = Field(..., min_length=1, max_length=100)
    meal_description: str = Field(..., min_length=3, max_length=500)
    meal_type: MealType
    analysis: FoodAnalysisResponse


class HabitSummary(BaseModel):
    """Summary of user's eating habits."""
    avg_score: float
    best_meal: Optional[str] = None
    worst_meal: Optional[str] = None
    trend: str = Field(..., description="improving, stable, or declining")


class RecipeSuggestionRequest(BaseModel):
    """Request model for recipe suggestions."""
    ingredients: str = Field(..., min_length=3, max_length=500)
    user_id: str = Field(..., min_length=1, max_length=100)

    @field_validator("ingredients")
    def sanitize_ingredients(cls, v: str) -> str:
        """Strip HTML characters < > & for basic sanitization."""
        if v:
            v = re.sub(r"[<>&]", "", v)
        return v

class RecipeSuggestionResponse(BaseModel):
    """Response model for a recipe suggestion from Gemini."""
    recipe_name: str
    instructions: List[str]
    nutrition: NutritionInfo
    health_percentage: int = Field(..., ge=0, le=100)
    why_its_healthy: str

