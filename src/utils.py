import os
from datetime import datetime

import requests

from src.config import DB_PATH, OLLAMA_BASE_URL


def check_ollama_connection(base_url: str = OLLAMA_BASE_URL) -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False
    except requests.Timeout:
        return False


def format_timestamp(dt: datetime) -> str:
    """Format a datetime object into a human-readable string."""
    return dt.strftime("%b %d, %Y %I:%M %p")


def generate_conversation_title(first_message: str, max_length: int = 50) -> str:
    """Generate a conversation title from the first user message."""
    title = first_message.strip().replace("\n", " ")
    if len(title) > max_length:
        title = title[:max_length].rsplit(" ", 1)[0] + "..."
    return title


def ensure_data_dir() -> None:
    """Create the data directory for the SQLite database if it doesn't exist."""
    data_dir = os.path.dirname(DB_PATH)
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)
