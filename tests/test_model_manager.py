from unittest.mock import MagicMock, patch

from src.model_manager import ModelManager


class TestIsAvailable:
    @patch("src.model_manager.requests.get")
    def test_available_when_server_running(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        mm = ModelManager()
        assert mm.is_available() is True

    @patch("src.model_manager.requests.get")
    def test_unavailable_on_connection_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.ConnectionError()
        mm = ModelManager()
        assert mm.is_available() is False

    @patch("src.model_manager.requests.get")
    def test_unavailable_on_timeout(self, mock_get):
        import requests

        mock_get.side_effect = requests.Timeout()
        mm = ModelManager()
        assert mm.is_available() is False


class TestListModels:
    @patch("src.model_manager.requests.get")
    def test_list_models_success(self, mock_get, mock_ollama_models):
        mock_response = MagicMock()
        mock_response.json.return_value = mock_ollama_models
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        mm = ModelManager()
        models = mm.list_models()

        assert len(models) == 2
        assert models[0]["name"] == "mistral:latest"
        assert models[0]["size"] == 4109853696
        assert models[1]["name"] == "llama3.1:latest"

    @patch("src.model_manager.requests.get")
    def test_list_models_empty_on_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.ConnectionError()
        mm = ModelManager()
        models = mm.list_models()
        assert models == []


class TestGetModelInfo:
    @patch("src.model_manager.requests.post")
    def test_get_info_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "modelfile": "FROM mistral",
            "parameters": "temperature 0.7",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        mm = ModelManager()
        info = mm.get_model_info("mistral")

        assert info is not None
        assert "modelfile" in info

    @patch("src.model_manager.requests.post")
    def test_get_info_returns_none_on_error(self, mock_post):
        import requests

        mock_post.side_effect = requests.ConnectionError()
        mm = ModelManager()
        assert mm.get_model_info("nonexistent") is None


class TestFormatSize:
    def test_zero_bytes(self):
        assert ModelManager.format_size(0) == "0 B"

    def test_bytes(self):
        assert ModelManager.format_size(500) == "500.0 B"

    def test_kilobytes(self):
        assert ModelManager.format_size(1024) == "1.0 KB"

    def test_megabytes(self):
        assert ModelManager.format_size(1048576) == "1.0 MB"

    def test_gigabytes(self):
        assert ModelManager.format_size(4109853696) == "3.8 GB"
