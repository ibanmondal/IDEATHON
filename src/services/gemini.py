import json
import os
from google import genai
from pydantic import ValidationError

from src.models.schemas import FoodAnalysisResponse, RecipeSuggestionResponse
from src.services.cache import get_cached, set_cache, make_cache_key
from src.utils.logger import logger

def get_gemini_client():
    """Initialize the Gemini client using API key from env."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY environment variable not set. API calls will fail.")
        # Attempt to create client, it will use ADC if api_key is None
        return genai.Client()
    return genai.Client(api_key=api_key)

async def analyze_meal(meal_description: str, meal_type: str) -> FoodAnalysisResponse:
    """
    Analyze a meal using Gemini 2.5 Flash.
    Returns a FoodAnalysisResponse object.
    Checks cache first.
    """
    cache_key = make_cache_key(meal_description, meal_type)
    cached_response = get_cached(cache_key)
    if cached_response:
        logger.info(f"Cache hit for meal: {meal_description[:20]}...")
        return FoodAnalysisResponse.model_validate(cached_response)

    prompt = f"""
    You are a professional nutritionist API. Analyze the following meal.
    Meal: "{meal_description}"
    Type: {meal_type}
    
    Return ONLY a strict JSON object with the following structure exactly (no markdown fences, no extra text):
    {{
        "health_score": <int 0-100>,
        "nutrition": {{
            "calories": <int>,
            "protein_g": <int>,
            "carbs_g": <int>,
            "fat_g": <int>,
            "fiber_g": <int>
        }},
        "positive_aspects": ["<string>", ...],
        "improvements": ["<string>", ...],
        "recommendation": "<string>"
    }}
    """
    
    logger.info(f"Calling Gemini API for meal: {meal_description[:20]}...")
    client = get_gemini_client()
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        response_text = response.text.strip()
        
        # Strip markdown fences if Gemini still returns them
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        data = json.loads(response_text)
        validated_response = FoodAnalysisResponse(**data)
        
        # Save to cache
        set_cache(cache_key, validated_response.model_dump())
        return validated_response
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON: {response_text}")
        raise ValueError("Invalid JSON returned from AI") from e
    except ValidationError as e:
        logger.error(f"Validation error on Gemini data: {e}")
        raise ValueError("AI response did not match expected schema") from e
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise

async def suggest_recipe(ingredients: str) -> RecipeSuggestionResponse:
    """
    Suggest a healthy recipe using Gemini 2.5 Flash based on provided ingredients.
    """
    prompt = f"""
    You are a professional chef and nutritionist. The user has the following ingredients: "{ingredients}".
    Suggest ONE healthy recipe they can make. You can assume they have basic pantry staples (salt, pepper, oil, water).
    
    Return ONLY a strict JSON object with the following structure exactly (no markdown fences, no extra text):
    {{
        "recipe_name": "<string>",
        "instructions": ["<string>", ...],
        "nutrition": {{
            "calories": <int>,
            "protein_g": <int>,
            "carbs_g": <int>,
            "fat_g": <int>,
            "fiber_g": <int>
        }},
        "health_percentage": <int 0-100>,
        "why_its_healthy": "<string>"
    }}
    """
    
    logger.info(f"Calling Gemini API for recipe suggestion...")
    client = get_gemini_client()
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        response_text = response.text.strip()
        
        # Strip markdown fences if Gemini still returns them
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        data = json.loads(response_text)
        validated_response = RecipeSuggestionResponse(**data)
        
        return validated_response
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON: {response_text}")
        raise ValueError("Invalid JSON returned from AI") from e
    except ValidationError as e:
        logger.error(f"Validation error on Gemini data: {e}")
        raise ValueError("AI response did not match expected schema") from e
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise
