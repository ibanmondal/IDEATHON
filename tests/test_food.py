import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from src.models.schemas import FoodAnalysisResponse, NutritionInfo

client = TestClient(app)

# Helper mock data
mock_analysis = FoodAnalysisResponse(
    health_score=85,
    nutrition=NutritionInfo(calories=400, protein_g=20, carbs_g=40, fat_g=15, fiber_g=8),
    positive_aspects=["High protein", "Good fiber"],
    improvements=["Lower sodium"],
    recommendation="Add more greens."
)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("src.routes.food.analyze_meal")
def test_analyze_success(mock_analyze):
    """Test successful meal analysis."""
    mock_analyze.return_value = mock_analysis
    
    response = client.post(
        "/api/analyze",
        json={
            "meal_description": "Oatmeal with berries",
            "user_id": "user123",
            "meal_type": "breakfast"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["health_score"] == 85
    assert "nutrition" in data
    assert data["positive_aspects"] == ["High protein", "Good fiber"]

def test_analyze_empty_input():
    """Test analysis with empty description expects 422."""
    response = client.post(
        "/api/analyze",
        json={
            "meal_description": "",
            "user_id": "user123",
            "meal_type": "breakfast"
        }
    )
    assert response.status_code == 422

def test_analyze_too_long():
    """Test analysis with too long description expects 422."""
    response = client.post(
        "/api/analyze",
        json={
            "meal_description": "A" * 501,
            "user_id": "user123",
            "meal_type": "breakfast"
        }
    )
    assert response.status_code == 422

def test_analyze_missing_user_id():
    """Test analysis with missing user_id expects 422."""
    response = client.post(
        "/api/analyze",
        json={
            "meal_description": "Oatmeal",
            "meal_type": "breakfast"
        }
    )
    assert response.status_code == 422

@patch("src.routes.food.save_meal")
def test_log_success(mock_save):
    """Test successful meal logging."""
    mock_save.return_value = "doc_id_123"
    
    response = client.post(
        "/api/log",
        json={
            "user_id": "user123",
            "meal_description": "Oatmeal",
            "meal_type": "breakfast",
            "analysis": mock_analysis.model_dump()
        }
    )
    
    assert response.status_code == 200
    assert response.json() == {"success": True, "meal_id": "doc_id_123"}

def test_log_invalid_score():
    """Test log with invalid health score expects 422."""
    invalid_analysis = mock_analysis.model_dump()
    invalid_analysis["health_score"] = 150  # Must be <= 100
    
    response = client.post(
        "/api/log",
        json={
            "user_id": "user123",
            "meal_description": "Oatmeal",
            "meal_type": "breakfast",
            "analysis": invalid_analysis
        }
    )
    assert response.status_code == 422

@patch("src.routes.food.analyze_meal")
def test_analyze_value_error(mock_analyze):
    mock_analyze.side_effect = ValueError("Invalid AI")
    response = client.post(
        "/api/analyze",
        json={"meal_description": "Oatmeal", "user_id": "user123", "meal_type": "breakfast"}
    )
    assert response.status_code == 500

@patch("src.routes.food.analyze_meal")
def test_analyze_exception(mock_analyze):
    mock_analyze.side_effect = Exception("Unknown")
    response = client.post(
        "/api/analyze",
        json={"meal_description": "Oatmeal", "user_id": "user123", "meal_type": "breakfast"}
    )
    assert response.status_code == 500

@patch("src.routes.food.save_meal")
def test_log_exception(mock_save):
    mock_save.side_effect = Exception("DB Error")
    response = client.post(
        "/api/log",
        json={
            "user_id": "user123",
            "meal_description": "Oatmeal",
            "meal_type": "breakfast",
            "analysis": mock_analysis.model_dump()
        }
    )
    assert response.status_code == 500
