from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage
from src.chat_engine import ChatEngine


class TestConvertMessages:
    def test_converts_all_roles(self):
        messages = [
            {"role": "system", "content": "Be helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = ChatEngine._convert_messages(messages)

        assert len(result) == 3
        assert isinstance(result[0], SystemMessage)
        assert isinstance(result[1], HumanMessage)
        assert isinstance(result[2], AIMessage)
        assert result[0].content == "Be helpful."
        assert result[1].content == "Hello"
        assert result[2].content == "Hi there!"

    def test_empty_messages(self):
        assert ChatEngine._convert_messages([]) == []


class TestBuildMessages:
    @patch("src.chat_engine.ChatOllama")
    def test_prepends_system_prompt(self, _mock_ollama):
        engine = ChatEngine(model_name="mistral", system_prompt="Be concise.")
        messages = [{"role": "user", "content": "Hello"}]
        result = engine._build_messages(messages)

        assert len(result) == 2
        assert isinstance(result[0], SystemMessage)
        assert result[0].content == "Be concise."
        assert isinstance(result[1], HumanMessage)

    @patch("src.chat_engine.ChatOllama")
    def test_no_system_prompt(self, _mock_ollama):
        engine = ChatEngine(model_name="mistral", system_prompt="")
        messages = [{"role": "user", "content": "Hello"}]
        result = engine._build_messages(messages)

        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)


class TestStreamResponse:
    @patch("src.chat_engine.ChatOllama")
    def test_yields_tokens(self, mock_ollama_cls):
        mock_llm = MagicMock()
        mock_llm.stream.return_value = [
            AIMessageChunk(content="Hello"),
            AIMessageChunk(content=" world"),
            AIMessageChunk(content="!"),
        ]
        mock_ollama_cls.return_value = mock_llm

        engine = ChatEngine(model_name="mistral")
        tokens = list(engine.stream_response([{"role": "user", "content": "Hi"}]))

        assert tokens == ["Hello", " world", "!"]
        mock_llm.stream.assert_called_once()

    @patch("src.chat_engine.ChatOllama")
    def test_skips_empty_chunks(self, mock_ollama_cls):
        mock_llm = MagicMock()
        mock_llm.stream.return_value = [
            AIMessageChunk(content="Hello"),
            AIMessageChunk(content=""),
            AIMessageChunk(content=" world"),
        ]
        mock_ollama_cls.return_value = mock_llm

        engine = ChatEngine(model_name="mistral")
        tokens = list(engine.stream_response([{"role": "user", "content": "Hi"}]))

        assert tokens == ["Hello", " world"]


class TestGetResponse:
    @patch("src.chat_engine.ChatOllama")
    def test_returns_full_response(self, mock_ollama_cls):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = AIMessage(content="Full response here.")
        mock_ollama_cls.return_value = mock_llm

        engine = ChatEngine(model_name="mistral")
        response = engine.get_response([{"role": "user", "content": "Hello"}])

        assert response == "Full response here."


class TestUpdateModel:
    @patch("src.chat_engine.ChatOllama")
    def test_update_model_name(self, mock_ollama_cls):
        engine = ChatEngine(model_name="mistral")
        engine.update_model("llama3.1")

        assert engine.model_name == "llama3.1"
        assert mock_ollama_cls.call_count == 2  # Initial + update


class TestUpdateParameters:
    @patch("src.chat_engine.ChatOllama")
    def test_update_temperature(self, mock_ollama_cls):
        engine = ChatEngine(model_name="mistral", temperature=0.7)
        engine.update_parameters(temperature=1.5)

        assert engine.temperature == 1.5

    @patch("src.chat_engine.ChatOllama")
    def test_partial_update(self, mock_ollama_cls):
        engine = ChatEngine(
            model_name="mistral",
            temperature=0.7,
            max_tokens=2048,
        )
        engine.update_parameters(temperature=1.0)

        assert engine.temperature == 1.0
        assert engine.max_tokens == 2048  # Unchanged
