"""
Helper utilities for audit operations.
"""
from typing import Optional, Any, Dict, List
from decimal import Decimal


def model_to_dict(model, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convert SQLAlchemy model to dictionary.

    Args:
        model: SQLAlchemy model instance
        exclude: List of field names to exclude

    Returns:
        Dictionary with model data
    """
    exclude = exclude or []
    # Add standard exclusions
    exclude.extend(['password_hash', '_sa_instance_state'])

    data = {}
    for column in model.__table__.columns:
        if column.name not in exclude:
            value = getattr(model, column.name)
            # Convert datetime to string
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            # Convert Decimal to float for JSON serialization
            elif isinstance(value, Decimal):
                value = float(value)
            data[column.name] = value

    return data


def compute_changes(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute changes between old and new data.

    Args:
        old_data: Original data dictionary
        new_data: New data dictionary

    Returns:
        Dictionary with only changed fields: {field: {'old': ..., 'new': ...}}
    """
    changes = {}
    for key, new_value in new_data.items():
        old_value = old_data.get(key)
        if old_value != new_value:
            changes[key] = {'old': old_value, 'new': new_value}
    return changes
