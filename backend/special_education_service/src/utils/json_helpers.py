"""JSON serialization helpers"""

from typing import Any
from datetime import datetime, date
from uuid import UUID
import json


def ensure_json_serializable(obj: Any) -> Any:
    """Recursively ensure all objects are JSON serializable"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: ensure_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [ensure_json_serializable(item) for item in obj]
    elif hasattr(obj, 'model_dump'):  # Pydantic model
        return ensure_json_serializable(obj.model_dump())
    elif hasattr(obj, '__dict__'):
        return ensure_json_serializable(obj.__dict__)
    else:
        return str(obj)