"""
API Documentation Generator

A comprehensive tool for generating various API documentation formats from a FastAPI application,
including OpenAPI schemas, Postman collections, and Markdown files.
"""

import json
import argparse
from typing import Any, Dict, List
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

class APIDocumentationGenerator:
    """
    Generates API documentation from a FastAPI application instance.
    """
    def __init__(self, app: FastAPI, base_url: str = "http://127.0.0.1:8000"):
        self.app = app
        self.base_url = base_url
        self.openapi_schema: Dict[str, Any] = {}

    def generate_openapi_schema(self) -> Dict[str, Any]:
        """Generate and customize the OpenAPI schema."""
        if self.app.openapi_schema:
            self.openapi_schema = self.app.openapi_schema
            return self.openapi_schema

        openapi_schema = get_openapi(
            title=self.app.title,
            version=self.app.version,
            description=self._get_api_description(),
            routes=self.app.routes,
        )

        # Add security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http", "scheme": "bearer", "bearerFormat": "JWT",
                "description": "JWT Authorization header using the Bearer scheme.",
            }
        }
        openapi_schema["security"] = [{"BearerAuth": []}]
        openapi_schema["tags"] = self._get_api_tags()

        self.app.openapi_schema = openapi_schema
        self.openapi_schema = openapi_schema
        return openapi_schema

    def generate_postman_collection(self) -> Dict[str, Any]:
        """Generate a Postman collection from the OpenAPI schema."""
        if not self.openapi_schema:
            self.generate_openapi_schema()

        collection = {
            "info": {
                "name": self.app.title,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                "description": self.openapi_schema.get("info", {}).get("description", ""),
            },
            "item": [],
        }

        for path, path_item in self.openapi_schema.get("paths", {}).items():
            for method, operation in path_item.items():
                request = {
                    "method": method.upper(),
                    "header": [{"key": "Authorization", "value": "Bearer {{JWT_TOKEN}}"}],
                    "url": {"raw": f"{self.base_url}{path}", "host": [self.base_url], "path": path.strip('/').split('/')},
                    "description": operation.get("summary", ""),
                }

                # Add request body if present
                if "requestBody" in operation:
                    content = operation["requestBody"]["content"].get("application/json", {})
                    if "schema" in content:
                        request["body"] = {"mode": "raw", "raw": json.dumps(self._get_example_from_schema(content["schema"]), indent=2)}
                        request["header"].append({"key": "Content-Type", "value": "application/json"})

                collection["item"].append({"name": operation.get("summary", path), "request": request, "response": []})

        return collection

    def generate_markdown_docs(self) -> str:
        """Generate Markdown documentation from the OpenAPI schema."""
        if not self.openapi_schema:
            self.generate_openapi_schema()

        md = f"# {self.app.title} - API Documentation\n\n"
        md += f"{self.openapi_schema.get('info', {}).get('description', '')}\n\n"

        for path, path_item in self.openapi_schema.get("paths", {}).items():
            for method, operation in path_item.items():
                md += f"## {operation.get('summary', path)}\n\n"
                md += f"`{method.upper()} {path}`\n\n"
                md += f"{operation.get('description', '')}\n\n"

                # Request
                if "requestBody" in operation:
                    md += "### Request Body\n\n"
                    content = operation["requestBody"]["content"].get("application/json", {})
                    if "schema" in content:
                        example = self._get_example_from_schema(content["schema"])
                        md += "```json\n"
                        md += json.dumps(example, indent=2) + "\n"
                        md += "```\n\n"

                # Curl Example
                md += "### cURL Example\n\n"
                md += "```bash\n"
                md += f"curl -X {method.upper()} '{self.base_url}{path}' \\\n"
                md += "     -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\\n"
                md += "     -H 'Content-Type: application/json'"
                if "requestBody" in operation:
                    example = self._get_example_from_schema(operation["requestBody"]["content"]["application/json"]["schema"])
                    md += " \\\n     -d '" + json.dumps(example) + "'\n"
                else:
                    md += "\n"
                md += "```\n\n"

        return md

    def _get_example_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a dictionary example from a JSON schema."""
        if "example" in schema:
            return schema["example"]
        if "properties" in schema:
            example = {}
            for prop_name, prop_details in schema["properties"].items():
                if "example" in prop_details:
                    example[prop_name] = prop_details["example"]
                elif "type" in prop_details:
                    example[prop_name] = f"({prop_details['type']})"
            return example
        return {}

    def _get_api_description(self) -> str:
        """Get comprehensive API description."""
        # This function is kept for clarity
        return """
A comprehensive REST API for IoT and IIoT applications providing real-time monitoring, predictive analytics, and intelligent automation.
"""

    def _get_api_tags(self) -> List[Dict[str, Any]]:
        """Get API tags for organization."""
        # This function is kept for clarity
        return [{"name": "Machines", "description": "Manage and monitor machines."}]


def main():
    """CLI for the documentation generator."""
    parser = argparse.ArgumentParser(description="API Documentation Generator for FastAPI.")
    parser.add_argument(
        "format",
        choices=["openapi", "postman", "markdown"],
        help="The format of the documentation to generate."
    )
    parser.add_argument(
        "--output",
        "-o",
        default="docs",
        help="Output directory or file name prefix."
    )
    args = parser.parse_args()

    # --- Demo FastAPI Application ---
    # In a real project, this app would be imported from your main application file.
    from pydantic import BaseModel, Field
    from datetime import datetime

    app = FastAPI(
        title="IoT Intelligence Platform API",
        version="2.0.0",
        description="A demo API for the documentation generator."
    )

    class Machine(BaseModel):
        machine_id: str = Field(..., example="CNC-001")
        name: str = Field(..., example="CNC Milling Machine Alpha")
        status: str = Field("active", example="active")
        installation_date: datetime = Field(default_factory=datetime.now)

    @app.post("/api/v1/machines", tags=["Machines"], summary="Create a new machine")
    def create_machine(machine: Machine):
        return {"status": "success", "data": machine}

    @app.get("/api/v1/machines", tags=["Machines"], summary="List all machines")
    def list_machines():
        return {"data": []}

    # --- Generator ---
    generator = APIDocumentationGenerator(app)

    if args.format == "openapi":
        schema = generator.generate_openapi_schema()
        file_path = f"{args.output}_openapi.json"
        with open(file_path, "w") as f:
            json.dump(schema, f, indent=2)
        print(f"OpenAPI schema saved to {file_path}")

    elif args.format == "postman":
        collection = generator.generate_postman_collection()
        file_path = f"{args.output}_postman_collection.json"
        with open(file_path, "w") as f:
            json.dump(collection, f, indent=2)
        print(f"Postman collection saved to {file_path}")

    elif args.format == "markdown":
        markdown = generator.generate_markdown_docs()
        file_path = f"{args.output}_docs.md"
        with open(file_path, "w") as f:
            f.write(markdown)
        print(f"Markdown documentation saved to {file_path}")


if __name__ == "__main__":
    main()
