import time
from typing import Any, Dict, Optional

# Simple in-memory cache
# Format: { "key": {"value": Any, "expires_at": float} }
_cache: Dict[str, Dict[str, Any]] = {}

TTL_SECONDS = 30 * 60  # 30 minutes

def make_cache_key(meal_description: str, meal_type: str) -> str:
    """Generate a unique cache key based on meal content."""
    return f"{meal_type}:{meal_description.strip().lower()}"

def get_cached(key: str) -> Optional[Any]:
    """Retrieve an item from cache if it exists and is not expired."""
    item = _cache.get(key)
    if not item:
        return None
    
    if time.time() > item["expires_at"]:
        del _cache[key]
        return None
        
    return item["value"]

def set_cache(key: str, value: Any) -> None:
    """Store an item in the cache with the default TTL."""
    _cache[key] = {
        "value": value,
        "expires_at": time.time() + TTL_SECONDS
    }

def clear_cache() -> None:
    """Clear all items from cache (useful for testing)."""
    _cache.clear()
