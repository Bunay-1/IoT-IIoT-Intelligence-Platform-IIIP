# utils/security.py

import re
from functools import wraps
from typing import Any, Callable, Dict

class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass

class ValidationError(ValueError, SecurityError):
    """Raised when input validation fails."""
    pass

def _get_arg_value(arg_name: str, func: Callable, args: tuple, kwargs: dict) -> Any:
    """Helper to get argument value from either args or kwargs."""
    try:
        # Get from kwargs first
        if arg_name in kwargs:
            return kwargs[arg_name]
        # Get from args by position
        arg_index = func.__code__.co_varnames.index(arg_name)
        if arg_index < len(args):
            return args[arg_index]
        return None # Not found
    except (ValueError, IndexError):
        return None

def validate_input(schema: Dict[str, Dict[str, Any]]) -> Callable:
    """
    A decorator to validate function arguments against a schema.

    The schema supports checks for:
    - required: bool
    - type: 'string', 'integer', 'float', 'boolean'
    - max_length: int (for strings)
    - pattern: regex string (for strings)
    - custom: 'loop_exists', 'loop_exists_if_provided' for this project
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            instance = args[0] if args and hasattr(args[0], '__class__') else None

            for arg_name, rules in schema.items():
                value = _get_arg_value(arg_name, func, args, kwargs)

                # --- Custom validation logic ---
                custom_rule = rules.get("custom")
                if custom_rule == "loop_exists":
                    if not instance or not hasattr(instance, 'control_loops') or value not in instance.control_loops:
                        raise ValidationError(f"Validation failed for '{arg_name}': Control loop '{value}' not found.")
                    continue # Custom rule handles all checks for this arg

                if custom_rule == "loop_exists_if_provided":
                    if value is not None:
                        if not instance or not hasattr(instance, 'control_loops') or value not in instance.control_loops:
                            raise ValidationError(f"Validation failed for '{arg_name}': Control loop '{value}' not found.")
                    continue # Custom rule handles all checks for this arg

                # --- Standard validation logic ---
                is_required = rules.get("required", False)
                if is_required and value is None:
                    raise ValidationError(f"Validation failed: Required argument '{arg_name}' is missing.")

                if value is None: # Skip other checks if not required and not present
                    continue

                # Type checking
                arg_type = rules.get("type")
                if arg_type:
                    if arg_type == "string" and not isinstance(value, str):
                        raise ValidationError(f"'{arg_name}' must be a string.")
                    if arg_type == "integer" and not isinstance(value, int):
                         raise ValidationError(f"'{arg_name}' must be an integer.")
                    if arg_type == "float" and not isinstance(value, (int, float)):
                         raise ValidationError(f"'{arg_name}' must be a float.")
                    if arg_type == "boolean" and not isinstance(value, bool):
                         raise ValidationError(f"'{arg_name}' must be a boolean.")

                # String-specific checks
                if isinstance(value, str):
                    max_len = rules.get("max_length")
                    if max_len and len(value) > max_len:
                        raise ValidationError(f"'{arg_name}' exceeds max length of {max_len}.")

                    pattern = rules.get("pattern")
                    if pattern and not re.match(pattern, value):
                        raise ValidationError(f"'{arg_name}' does not match pattern '{pattern}'.")

            return func(*args, **kwargs)
        return wrapper
    return decorator

# Kept for compatibility if used elsewhere
input_validator = validate_input
