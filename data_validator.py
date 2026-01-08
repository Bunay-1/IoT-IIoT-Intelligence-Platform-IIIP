"""
Data validation and sanitization utilities
"""

import ipaddress
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class DataValidator:
    """Comprehensive data validation and sanitization."""

    # Common validation patterns
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{10,}$")
    IP_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
    )

    @staticmethod
    def sanitize_string(
        value: str,
        max_length: Optional[int] = None,
        allowed_chars: Optional[str] = None,
    ) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")

        # Remove null bytes and control characters
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", value)

        # Trim whitespace
        sanitized = sanitized.strip()

        # Apply length limit
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        # Filter allowed characters if specified
        if allowed_chars:
            sanitized = "".join(c for c in sanitized if c in allowed_chars)

        return sanitized

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not isinstance(email, str):
            return False
        return bool(DataValidator.EMAIL_PATTERN.match(email.strip()))

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        if not isinstance(phone, str):
            return False
        return bool(DataValidator.PHONE_PATTERN.match(phone.strip()))

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format."""
        if not isinstance(uuid_str, str):
            return False
        return bool(DataValidator.UUID_PATTERN.match(uuid_str.strip()))

    @staticmethod
    def validate_numeric_range(
        value: Union[int, float],
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> bool:
        """Validate numeric value is within range."""
        try:
            num_value = float(value)
            if min_val is not None and num_value < min_val:
                return False
            if max_val is not None and num_value > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_machine_id(machine_id: str) -> bool:
        """Validate machine ID format."""
        if not isinstance(machine_id, str):
            return False

        # Machine ID should be alphanumeric with dashes/underscores, 3-50 chars
        if not re.match(r"^[a-zA-Z0-9_-]{3,50}$", machine_id):
            return False

        return True

    @staticmethod
    def validate_sensor_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize sensor data."""
        validated = {}

        # Required fields
        required_fields = ["machine_id", "timestamp"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate machine_id
        if not DataValidator.validate_machine_id(data["machine_id"]):
            raise ValueError("Invalid machine_id format")

        # Validate timestamp
        try:
            if isinstance(data["timestamp"], str):
                datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            elif isinstance(data["timestamp"], (int, float)):
                datetime.fromtimestamp(data["timestamp"])
            validated["timestamp"] = data["timestamp"]
        except (ValueError, TypeError):
            raise ValueError("Invalid timestamp format")

        # Validate numeric sensor readings
        sensor_fields = [
            "temperature",
            "pressure",
            "vibration",
            "current",
            "voltage",
            "speed",
            "torque",
        ]
        for field in sensor_fields:
            if field in data:
                if not DataValidator.validate_numeric_range(data[field], -1000, 10000):
                    logger.warning(f"Out of range value for {field}: {data[field]}")
                    # Could set to None or clamp the value
                validated[field] = data[field]

        # Validate anomaly scores
        if "anomaly_score" in data:
            if not DataValidator.validate_numeric_range(data["anomaly_score"], 0, 1):
                raise ValueError("Anomaly score must be between 0 and 1")
            validated["anomaly_score"] = data["anomaly_score"]

        validated["machine_id"] = data["machine_id"]
        return validated

    @staticmethod
    def validate_user_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize user input data."""
        validated = {}

        # Username validation
        if "username" in data:
            username = DataValidator.sanitize_string(data["username"], 50)
            if not re.match(r"^[a-zA-Z0-9_-]{3,50}$", username):
                raise ValueError("Invalid username format")
            validated["username"] = username

        # Email validation
        if "email" in data:
            email = DataValidator.sanitize_string(data["email"], 100)
            if not DataValidator.validate_email(email):
                raise ValueError("Invalid email format")
            validated["email"] = email

        # Role validation
        if "role" in data:
            allowed_roles = ["admin", "operator", "viewer"]
            if data["role"] not in allowed_roles:
                raise ValueError(f"Invalid role. Must be one of: {allowed_roles}")
            validated["role"] = data["role"]

        return validated

    @staticmethod
    def detect_sql_injection(value: str) -> bool:
        """Basic SQL injection detection."""
        if not isinstance(value, str):
            return False

        # Common SQL injection patterns
        patterns = [
            r";\s*(drop|delete|update|insert|alter|create|truncate)\s",
            r"union\s+select",
            r"--",
            r"/\*.*\*/",
            r"xp_cmdshell",
            r"exec\s*\(",
        ]

        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def detect_xss(value: str) -> bool:
        """Basic XSS detection."""
        if not isinstance(value, str):
            return False

        # Common XSS patterns
        patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
        ]

        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True

        return False

    @classmethod
    def comprehensive_validate(
        cls, data: Dict[str, Any], data_type: str
    ) -> Dict[str, Any]:
        """Comprehensive validation based on data type."""
        try:
            if data_type == "sensor_data":
                return cls.validate_sensor_data(data)
            elif data_type == "user_input":
                return cls.validate_user_input(data)
            else:
                # Generic sanitization
                validated = {}
                for key, value in data.items():
                    if isinstance(value, str):
                        validated[key] = cls.sanitize_string(value, 1000)
                    else:
                        validated[key] = value
                return validated

        except Exception as e:
            logger.error(f"Validation error for {data_type}: {e}")
            raise ValueError(f"Data validation failed: {e}")


# Global validator instance
validator = DataValidator()
