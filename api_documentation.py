"""
Enhanced API documentation with OpenAPI extensions
"""

import json
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def customize_openapi(app: FastAPI) -> Dict[str, Any]:
    """Customize OpenAPI schema with additional information."""

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=get_api_description(),
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Authorization header using the Bearer scheme.",
        }
    }

    # Apply security globally
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Add custom tags
    openapi_schema["tags"] = get_api_tags()

    # Add custom examples
    add_request_examples(openapi_schema)

    # Add response examples
    add_response_examples(openapi_schema)

    # Add custom extensions
    openapi_schema["x-api-version"] = app.version
    openapi_schema["x-rate-limit"] = "10 requests per second"
    openapi_schema["x-contact"] = {
        "name": "IoT Platform Support",
        "email": "support@iot-platform.com",
        "url": "https://iot-platform.com/support",
    }

    app.openapi_schema = openapi_schema
    return openapi_schema


def get_api_description() -> str:
    """Get comprehensive API description."""
    return """
# IoT IIoT Intelligence Platform API

A comprehensive REST API for IoT and IIoT applications providing real-time monitoring, predictive analytics, and intelligent automation.

## Features

- **Real-time Monitoring**: WebSocket connections for live data streaming
- **Predictive Analytics**: AI-powered anomaly detection and forecasting
- **Authentication**: JWT-based secure authentication with role-based access
- **Rate Limiting**: Built-in protection against abuse
- **Comprehensive Monitoring**: Prometheus metrics and health checks
- **Multi-tenancy**: Support for multiple organizations and users

## Authentication

All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Rate Limits

- General API: 10 requests/second
- Authentication endpoints: 5 requests/second
- WebSocket connections: 1000 messages/minute

## Response Format

All responses follow a consistent format:

```json
{
  "data": {},
  "meta": {
    "timestamp": "2025-12-12T12:00:00Z",
    "request_id": "req-123"
  }
}
```

## Error Handling

Errors are returned with appropriate HTTP status codes and detailed messages:

```json
{
  "detail": "Error description",
  "type": "error_type",
  "code": "ERROR_CODE"
}
```
"""


def get_api_tags() -> list:
    """Get API tags for organization."""
    return [
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.iot-platform.com/auth",
            },
        },
        {
            "name": "Machines",
            "description": "Machine management and monitoring",
            "externalDocs": {
                "description": "Machine Management",
                "url": "https://docs.iot-platform.com/machines",
            },
        },
        {
            "name": "Analytics",
            "description": "Data analytics and reporting",
            "externalDocs": {
                "description": "Analytics Guide",
                "url": "https://docs.iot-platform.com/analytics",
            },
        },
        {
            "name": "Alerts",
            "description": "Alert management and notifications",
            "externalDocs": {
                "description": "Alert System",
                "url": "https://docs.iot-platform.com/alerts",
            },
        },
        {
            "name": "WebSocket",
            "description": "Real-time data streaming",
            "externalDocs": {
                "description": "WebSocket API",
                "url": "https://docs.iot-platform.com/websocket",
            },
        },
    ]


def add_request_examples(openapi_schema: Dict[str, Any]):
    """Add request examples to OpenAPI schema."""
    if "paths" not in openapi_schema:
        return

    # Add examples for machine creation
    if "/api/v1/machines" in openapi_schema["paths"]:
        machine_example = {
            "machine_id": "CNC-001",
            "name": "CNC Milling Machine Alpha",
            "location": "Factory Floor A",
            "model": "DMG Mori DMU 50",
            "installation_date": "2023-01-15T00:00:00Z",
            "status": "active",
            "metadata": {
                "manufacturer": "DMG Mori",
                "serial_number": "DMU50-2023-001",
                "power_rating": "15kW",
            },
        }

        if "post" in openapi_schema["paths"]["/api/v1/machines"]:
            openapi_schema["paths"]["/api/v1/machines"]["post"]["requestBody"][
                "content"
            ]["application/json"]["examples"] = {
                "new_machine": {
                    "summary": "Create a new CNC machine",
                    "value": machine_example,
                }
            }


def add_response_examples(openapi_schema: Dict[str, Any]):
    """Add response examples to OpenAPI schema."""
    if "paths" not in openapi_schema:
        return

    # Add examples for machine responses
    if "/api/v1/machines" in openapi_schema["paths"]:
        machine_response_example = [
            {
                "machine_id": "CNC-001",
                "name": "CNC Milling Machine Alpha",
                "location": "Factory Floor A",
                "model": "DMG Mori DMU 50",
                "installation_date": "2023-01-15T00:00:00Z",
                "last_maintenance": "2024-06-01T00:00:00Z",
                "status": "active",
                "open_alerts": 0,
                "metadata": {"manufacturer": "DMG Mori", "power_rating": "15kW"},
            }
        ]

        if "get" in openapi_schema["paths"]["/api/v1/machines"]:
            openapi_schema["paths"]["/api/v1/machines"]["get"]["responses"]["200"][
                "content"
            ]["application/json"]["examples"] = {
                "machine_list": {
                    "summary": "List of machines",
                    "value": machine_response_example,
                }
            }


def generate_api_docs():
    """Generate API documentation files."""
    # This could generate markdown docs, Postman collections, etc.
    docs = {
        "openapi_version": "3.0.0",
        "title": "IoT IIoT Intelligence Platform API",
        "version": "1.0.0",
        "description": "Complete API documentation",
        "endpoints": [
            {
                "path": "/api/v1/auth/login",
                "method": "POST",
                "description": "User login",
            },
            {
                "path": "/api/v1/machines",
                "method": "GET",
                "description": "List machines",
            },
            {
                "path": "/api/v1/machines",
                "method": "POST",
                "description": "Create machine",
            },
            {
                "path": "/api/v1/analytics/overview",
                "method": "GET",
                "description": "Analytics overview",
            },
            {"path": "/metrics", "method": "GET", "description": "Prometheus metrics"},
            {"path": "/health", "method": "GET", "description": "Health check"},
        ],
    }

    return docs


# API documentation templates
API_TEMPLATES = {
    "error_response": {
        "description": "Error response format",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Error description",
                    "type": "error_type",
                    "code": "ERROR_CODE",
                }
            }
        },
    },
    "success_response": {
        "description": "Success response format",
        "content": {
            "application/json": {
                "example": {
                    "data": {},
                    "meta": {
                        "timestamp": "2025-12-12T12:00:00Z",
                        "request_id": "req-123",
                    },
                }
            }
        },
    },
}
