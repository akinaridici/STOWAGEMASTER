"""Validation utilities for user input"""


def validate_positive_number(value: str) -> tuple[bool, float]:
    """Validate that a string represents a positive number
    
    Returns:
        (is_valid, numeric_value)
    """
    try:
        num = float(value)
        if num <= 0:
            return False, 0.0
        return True, num
    except (ValueError, TypeError):
        return False, 0.0


def validate_non_empty_string(value: str) -> bool:
    """Validate that a string is not empty"""
    return bool(value and value.strip())


def validate_tank_name(name: str, existing_names: list) -> tuple[bool, str]:
    """Validate tank name
    
    Args:
        name: Tank name to validate
        existing_names: List of existing tank names to check for duplicates
    
    Returns:
        (is_valid, error_message)
    """
    if not validate_non_empty_string(name):
        return False, "Tank adı boş olamaz"
    
    if name in existing_names:
        return False, "Bu isimde bir tank zaten var"
    
    return True, ""


def validate_cargo_quantity(quantity: str) -> tuple[bool, float, str]:
    """Validate cargo quantity
    
    Returns:
        (is_valid, numeric_value, error_message)
    """
    is_valid, value = validate_positive_number(quantity)
    if not is_valid:
        return False, 0.0, "Miktar pozitif bir sayı olmalıdır"
    return True, value, ""

