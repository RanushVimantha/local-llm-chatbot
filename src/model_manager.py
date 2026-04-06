import json
from collections.abc import Generator

import requests

from src.config import OLLAMA_BASE_URL


class ModelManager:
    """Manages Ollama model operations: listing, info, and availability checks."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url

    def is_available(self) -> bool:
        """Check if the Ollama server is reachable."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def list_models(self) -> list[dict]:
        """List all locally installed Ollama models.

        Returns a list of dicts with keys: name, size, modified_at.
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            models = []
            for model in data.get("models", []):
                models.append(
                    {
                        "name": model.get("name", ""),
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                    }
                )
            return models
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
            return []

    def get_model_info(self, model_name: str) -> dict | None:
        """Get detailed information about a specific model."""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
            return None

    def pull_model(self, model_name: str) -> Generator[dict, None, None]:
        """Pull (download) a model from Ollama registry.

        Yields progress dicts with keys: status, completed, total.
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=600,
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    yield {
                        "status": data.get("status", ""),
                        "completed": data.get("completed", 0),
                        "total": data.get("total", 0),
                    }
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            yield {"status": f"Error: {e}", "completed": 0, "total": 0}

    def delete_model(self, model_name: str) -> bool:
        """Delete a locally installed model."""
        try:
            response = requests.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name},
                timeout=30,
            )
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError):
            return False

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format byte size to human-readable string."""
        if size_bytes == 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024 and i < len(units) - 1:
            size /= 1024
            i += 1
        return f"{size:.1f} {units[i]}"
