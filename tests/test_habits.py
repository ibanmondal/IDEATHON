import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from src.models.schemas import HabitSummary

client = TestClient(app)

@patch("src.routes.habits.get_meal_history")
def test_history_success(mock_get_history):
    """Test successful history retrieval."""
    mock_get_history.return_value = [
        {"id": "1", "meal_description": "Apple", "meal_type": "snack", "analysis": {"health_score": 90}}
    ]
    
    response = client.get("/api/history/user123")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["meal_description"] == "Apple"

def test_history_invalid_user_id_too_long():
    """Test history with too long user_id expects 400."""
    long_id = "U" * 101
    response = client.get(f"/api/history/{long_id}")
    assert response.status_code == 400

@patch("src.routes.habits.get_habit_summary")
def test_summary_success(mock_get_summary):
    """Test successful summary retrieval."""
    mock_get_summary.return_value = HabitSummary(
        avg_score=85.5,
        best_meal="Oatmeal",
        worst_meal="Donut",
        trend="improving"
    )
    
    response = client.get("/api/summary/user123")
    assert response.status_code == 200
    data = response.json()
    assert data["trend"] == "improving"
    assert data["avg_score"] == 85.5

@patch("src.routes.habits.get_meal_history")
def test_history_exception(mock_get_history):
    mock_get_history.side_effect = Exception("DB Error")
    response = client.get("/api/history/user123")
    assert response.status_code == 500

@patch("src.routes.habits.get_habit_summary")
def test_summary_exception(mock_get_summary):
    mock_get_summary.side_effect = Exception("DB Error")
    response = client.get("/api/summary/user123")
    assert response.status_code == 500
