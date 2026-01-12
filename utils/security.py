# utils/security.py

from functools import wraps

class SecurityError(Exception):
    pass

def input_validator(schema):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This is a mock validator. A real one would check input against the schema.
            # print(f"[Security] Input validation passed for {func.__name__}.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_input(schema):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This is a mock validator.
            return func(*args, **kwargs)
        return wrapper
    return decorator
