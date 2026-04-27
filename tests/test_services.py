import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock

from src.services.cache import make_cache_key, set_cache, get_cached, clear_cache
from src.services.firestore import get_habit_summary, save_meal, get_meal_history
from src.models.schemas import FoodAnalysisResponse, NutritionInfo
from src.services.gemini import analyze_meal
from src.utils.logger import setup_logger

def test_cache_operations():
    """Test setting, getting, and clearing cache."""
    clear_cache()
    key = make_cache_key("apple", "snack")
    assert key == "snack:apple"
    
    # Not in cache
    assert get_cached(key) is None
    
    # Set and get
    set_cache(key, {"health_score": 100})
    assert get_cached(key) == {"health_score": 100}
    
    # Clear cache
    clear_cache()
    assert get_cached(key) is None

@patch("src.services.cache.time")
def test_cache_expiration(mock_time):
    """Test cache expiration."""
    clear_cache()
    # Set current time to 100
    mock_time.time.return_value = 100
    
    key = "test_key"
    set_cache(key, "data")
    
    # Still valid (time is 100 < 100 + 1800)
    assert get_cached(key) == "data"
    
    # Move time forward past TTL (100 + 1801 = 1901)
    mock_time.time.return_value = 1901
    assert get_cached(key) is None

@pytest.mark.asyncio
@patch("src.services.firestore.get_firestore_client")
async def test_get_habit_summary_empty(mock_get_client):
    """Test habit summary when user has no meals."""
    mock_db = MagicMock()
    mock_get_client.return_value = mock_db
    
    mock_query = mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value
    async def mock_stream():
        yield None
    mock_query.stream.return_value = mock_stream()
    # But we want empty list
    async def empty_stream():
        return
        yield
    mock_query.stream.return_value = empty_stream()
    
    summary = await get_habit_summary("user123")
    assert summary.avg_score == 0.0
    assert summary.trend == "stable"

@pytest.mark.asyncio
@patch("src.services.firestore.get_firestore_client")
async def test_get_habit_summary_trend(mock_get_client):
    """Test habit summary trend calculation."""
    mock_db = MagicMock()
    mock_get_client.return_value = mock_db
    
    # Mocking stream to return 4 meals (recent 2 have higher scores)
    class MockDoc:
        def __init__(self, d, i):
            self.d = d
            self.id = i
        def to_dict(self):
            return self.d
            
    mock_query = mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value
    async def mock_stream():
        for d in [
            MockDoc({"meal_description": "Apple", "analysis": {"health_score": 90}}, "1"),
            MockDoc({"meal_description": "Salad", "analysis": {"health_score": 85}}, "2"),
            MockDoc({"meal_description": "Burger", "analysis": {"health_score": 40}}, "3"),
            MockDoc({"meal_description": "Pizza", "analysis": {"health_score": 30}}, "4"),
        ]:
            yield d
    mock_query.stream.return_value = mock_stream()
    
    summary = await get_habit_summary("user123")
    # recent avg: (90+85)/2 = 87.5. older avg: (40+30)/2 = 35. Trend should be improving.
    assert summary.trend == "improving"
    assert summary.best_meal == "Apple"
    assert summary.worst_meal == "Pizza"

@pytest.mark.asyncio
@patch("src.services.firestore.get_firestore_client")
async def test_habit_trend_declining(mock_get_client):
    """Test habit summary declining trend calculation."""
    mock_db = MagicMock()
    mock_get_client.return_value = mock_db
    class MockDoc:
        def __init__(self, d, i):
            self.d = d
            self.id = i
        def to_dict(self):
            return self.d
    mock_query = mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value
    async def mock_stream():
        for d in [
            MockDoc({"meal_description": "Donut", "analysis": {"health_score": 20}}, "1"),
            MockDoc({"meal_description": "Fries", "analysis": {"health_score": 30}}, "2"),
            MockDoc({"meal_description": "Salad", "analysis": {"health_score": 90}}, "3"),
            MockDoc({"meal_description": "Apple", "analysis": {"health_score": 95}}, "4"),
        ]:
            yield d
    mock_query.stream.return_value = mock_stream()
    summary = await get_habit_summary("user123")
    assert summary.trend == "declining"

@pytest.mark.asyncio
@patch("src.services.firestore.get_firestore_client")
async def test_save_meal(mock_get_client):
    mock_db = MagicMock()
    mock_get_client.return_value = mock_db
    mock_doc_ref = MagicMock()
    mock_doc_ref.id = "new_doc_123"
    mock_doc_ref.set = AsyncMock()
    mock_db.collection.return_value.document.return_value = mock_doc_ref
    
    analysis = FoodAnalysisResponse(
        health_score=100,
        nutrition=NutritionInfo(calories=100, protein_g=1, carbs_g=1, fat_g=1, fiber_g=1),
        positive_aspects=[],
        improvements=[],
        recommendation="Good"
    )
    
    doc_id = await save_meal("user1", "Apple", "snack", analysis)
    assert doc_id == "new_doc_123"
    mock_doc_ref.set.assert_called_once()

@pytest.mark.asyncio
@patch("src.services.firestore.get_firestore_client")
async def test_get_meal_history(mock_get_client):
    mock_db = MagicMock()
    mock_get_client.return_value = mock_db
    
    class MockDoc:
        def __init__(self, d, i):
            self.d = d
            self.id = i
        def to_dict(self):
            return self.d
            
    mock_query = mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value
    async def mock_stream():
        yield MockDoc({"meal_description": "Apple"}, "1")
        
    mock_query.stream.return_value = mock_stream()
    
    history = await get_meal_history("user1")
    assert len(history) == 1
    assert history[0]["id"] == "1"

@patch("src.utils.logger.os.environ.get")
@patch("src.utils.logger.google.cloud.logging.Client")
def test_setup_logger_with_gcp(mock_client, mock_env_get):
    """Test logger setup with GCP_PROJECT_ID."""
    mock_env_get.return_value = "test-project"
    logger = setup_logger("test-logger")
    assert logger.name == "test-logger"
    # Note: testing handlers might be flaky depending on environment, but this runs the code path

@patch("src.utils.logger.os.environ.get")
def test_setup_logger_no_gcp(mock_env_get):
    """Test logger setup without GCP_PROJECT_ID."""
    mock_env_get.return_value = None
    logger = setup_logger("test-logger-2")
    assert logger.name == "test-logger-2"

@pytest.mark.asyncio
@patch("src.services.gemini.get_gemini_client")
async def test_analyze_meal_gemini(mock_get_client):
    """Test gemini analysis parsing."""
    clear_cache()
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # Mock valid JSON response inside markdown fences
    mock_client.models.generate_content.return_value.text = '''```json
    {
        "health_score": 80,
        "nutrition": {"calories": 300, "protein_g": 10, "carbs_g": 20, "fat_g": 5, "fiber_g": 3},
        "positive_aspects": ["Good"],
        "improvements": ["None"],
        "recommendation": "Keep it up"
    }
    ```'''
    
    result = await analyze_meal("toast", "breakfast")
    assert result.health_score == 80
    assert result.recommendation == "Keep it up"

@pytest.mark.asyncio
@patch("src.services.gemini.get_gemini_client")
async def test_cache_hit(mock_get_client):
    """Test cache hit avoids API call."""
    clear_cache()
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.generate_content.return_value.text = '''```json
    {
        "health_score": 100,
        "nutrition": {"calories": 1, "protein_g": 1, "carbs_g": 1, "fat_g": 1, "fiber_g": 1},
        "positive_aspects": ["Good"],
        "improvements": ["None"],
        "recommendation": "Great"
    }
    ```'''
    
    # First call sets cache
    await analyze_meal("cache_test", "snack")
    assert mock_client.models.generate_content.call_count == 1
    
    # Second call should use cache
    res = await analyze_meal("cache_test", "snack")
    assert mock_client.models.generate_content.call_count == 1
    assert res.health_score == 100

@pytest.mark.asyncio
@patch("src.services.gemini.get_gemini_client")
async def test_analyze_meal_gemini_invalid_json(mock_get_client):
    """Test gemini analysis parsing with bad json."""
    clear_cache()
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.models.generate_content.return_value.text = "This is not JSON"
    
    with pytest.raises(ValueError, match="Invalid JSON"):
        await analyze_meal("toast", "breakfast")
