import os
import tempfile

import pytest
from src.conversation_manager import ConversationManager


@pytest.fixture
def tmp_db_path():
    """Provide a temporary database file path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def conversation_manager(tmp_db_path):
    """Provide a ConversationManager with a temporary database."""
    cm = ConversationManager(db_path=tmp_db_path)
    yield cm
    cm.close()


@pytest.fixture
def sample_messages():
    """Provide sample chat messages for testing."""
    return [
        {"role": "user", "content": "What is Python?"},
        {
            "role": "assistant",
            "content": "Python is a high-level programming language.",
        },
        {"role": "user", "content": "What are its main features?"},
    ]


@pytest.fixture
def mock_ollama_models():
    """Provide mock Ollama API response for model listing."""
    return {
        "models": [
            {
                "name": "mistral:latest",
                "size": 4109853696,
                "modified_at": "2024-01-15T10:30:00Z",
            },
            {
                "name": "llama3.1:latest",
                "size": 4661723648,
                "modified_at": "2024-01-14T08:00:00Z",
            },
        ]
    }
