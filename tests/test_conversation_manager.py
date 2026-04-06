import json


class TestCreateConversation:
    def test_returns_id(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(
            model_name="mistral", system_prompt="You are helpful.", temperature=0.7
        )
        assert conv_id is not None
        assert isinstance(conv_id, str)
        assert len(conv_id) == 32

    def test_get_conversation(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(
            model_name="mistral", system_prompt="Test prompt.", temperature=0.5
        )
        conv = conversation_manager.get_conversation(conv_id)
        assert conv is not None
        assert conv["model_name"] == "mistral"
        assert conv["system_prompt"] == "Test prompt."
        assert conv["temperature"] == 0.5


class TestMessages:
    def test_add_and_get_messages(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(model_name="mistral")
        conversation_manager.add_message(conv_id, "user", "Hello")
        conversation_manager.add_message(
            conv_id, "assistant", "Hi there!", tokens_used=5, generation_time_ms=200
        )

        messages = conversation_manager.get_messages(conv_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["tokens_used"] == 5
        assert messages[1]["generation_time_ms"] == 200

    def test_messages_ordered_chronologically(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(model_name="mistral")
        conversation_manager.add_message(conv_id, "user", "First")
        conversation_manager.add_message(conv_id, "assistant", "Second")
        conversation_manager.add_message(conv_id, "user", "Third")

        messages = conversation_manager.get_messages(conv_id)
        assert [m["content"] for m in messages] == ["First", "Second", "Third"]


class TestConversationList:
    def test_get_conversations_ordered_by_updated(self, conversation_manager):
        id1 = conversation_manager.create_conversation(model_name="mistral")
        conversation_manager.create_conversation(model_name="llama3")

        # Update first conversation to make it more recent
        conversation_manager.add_message(id1, "user", "New message")

        convs = conversation_manager.get_conversations()
        assert len(convs) == 2
        assert convs[0]["id"] == id1  # Most recently updated

    def test_empty_list(self, conversation_manager):
        convs = conversation_manager.get_conversations()
        assert convs == []


class TestDeleteConversation:
    def test_delete_removes_conversation(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(model_name="mistral")
        conversation_manager.add_message(conv_id, "user", "Test")

        conversation_manager.delete_conversation(conv_id)

        assert conversation_manager.get_conversation(conv_id) is None
        assert conversation_manager.get_messages(conv_id) == []


class TestRenameConversation:
    def test_rename(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(model_name="mistral")
        conversation_manager.rename_conversation(conv_id, "My Chat")

        conv = conversation_manager.get_conversation(conv_id)
        assert conv["title"] == "My Chat"


class TestSearchConversations:
    def test_search_by_title(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(model_name="mistral")
        conversation_manager.rename_conversation(conv_id, "Python Tutorial")

        results = conversation_manager.search_conversations("Python")
        assert len(results) == 1
        assert results[0]["title"] == "Python Tutorial"

    def test_search_by_message_content(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(model_name="mistral")
        conversation_manager.add_message(conv_id, "user", "Tell me about Docker")

        results = conversation_manager.search_conversations("Docker")
        assert len(results) == 1

    def test_search_no_results(self, conversation_manager):
        results = conversation_manager.search_conversations("nonexistent")
        assert results == []


class TestSystemPrompts:
    def test_default_prompts_exist(self, conversation_manager):
        prompts = conversation_manager.get_system_prompts()
        names = [p["name"] for p in prompts]
        assert "General Assistant" in names
        assert "Code Helper" in names
        assert "Creative Writer" in names
        assert "Tutor" in names
        assert "DevOps Engineer" in names

    def test_save_custom_prompt(self, conversation_manager):
        conversation_manager.save_system_prompt("My Prompt", "Be concise.")
        prompts = conversation_manager.get_system_prompts()
        names = [p["name"] for p in prompts]
        assert "My Prompt" in names

    def test_delete_prompt(self, conversation_manager):
        conversation_manager.save_system_prompt("Temp", "Temporary prompt.")
        prompts = conversation_manager.get_system_prompts()
        temp = [p for p in prompts if p["name"] == "Temp"][0]

        conversation_manager.delete_system_prompt(temp["id"])
        prompts = conversation_manager.get_system_prompts()
        names = [p["name"] for p in prompts]
        assert "Temp" not in names


class TestExport:
    def test_export_json(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(
            model_name="mistral", system_prompt="Be helpful."
        )
        conversation_manager.rename_conversation(conv_id, "Test Chat")
        conversation_manager.add_message(conv_id, "user", "Hello")
        conversation_manager.add_message(
            conv_id, "assistant", "Hi!", tokens_used=3, generation_time_ms=100
        )

        json_str = conversation_manager.export_as_json(conv_id)
        data = json.loads(json_str)

        assert data["conversation"]["title"] == "Test Chat"
        assert data["conversation"]["model"] == "mistral"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["tokens_used"] == 3

    def test_export_markdown(self, conversation_manager):
        conv_id = conversation_manager.create_conversation(model_name="mistral")
        conversation_manager.rename_conversation(conv_id, "MD Test")
        conversation_manager.add_message(conv_id, "user", "Hello")
        conversation_manager.add_message(conv_id, "assistant", "Hi there!")

        md = conversation_manager.export_as_markdown(conv_id)

        assert "# MD Test" in md
        assert "### User" in md
        assert "### Assistant" in md
        assert "Hello" in md
        assert "Hi there!" in md

    def test_export_nonexistent_conversation(self, conversation_manager):
        assert conversation_manager.export_as_json("nonexistent") == "{}"
        assert conversation_manager.export_as_markdown("nonexistent") == ""
