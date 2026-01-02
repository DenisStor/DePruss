"""
Helper utilities for data exchange operations.
"""
from typing import Any, Optional


def bool_to_str(value: bool) -> str:
    """Convert boolean to Russian Yes/No."""
    return 'Да' if value else 'Нет'


def str_to_bool(value: str) -> bool:
    """Convert string to boolean."""
    return str(value).strip().lower() in ('да', 'yes', 'true', '1')


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Safely parse integer."""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely parse float."""
    if value is None or value == '':
        return default
    try:
        return float(str(value).replace(',', '.'))
    except (ValueError, TypeError):
        return default
