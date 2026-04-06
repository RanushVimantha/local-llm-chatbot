import time
from concurrent.futures import ThreadPoolExecutor

import streamlit as st

from src.chat_engine import ChatEngine
from src.config import (
    APP_ICON,
    APP_TITLE,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_REPEAT_PENALTY,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    PAGE_LAYOUT,
)
from src.conversation_manager import ConversationManager
from src.model_manager import ModelManager
from src.utils import check_ollama_connection, generate_conversation_title

# Page config
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout=PAGE_LAYOUT)


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "messages": [],
        "model_name": DEFAULT_MODEL,
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "top_p": DEFAULT_TOP_P,
        "repeat_penalty": DEFAULT_REPEAT_PENALTY,
        "model_manager": ModelManager(),
        "conversation_manager": ConversationManager(),
        "chat_engine": None,
        "current_conversation_id": None,
        "compare_mode": False,
        "compare_model_a": None,
        "compare_model_b": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_chat_engine() -> ChatEngine:
    """Get or create the ChatEngine with current settings."""
    if st.session_state.chat_engine is None or (
        st.session_state.chat_engine.model_name != st.session_state.model_name
        or st.session_state.chat_engine.temperature != st.session_state.temperature
        or st.session_state.chat_engine.max_tokens != st.session_state.max_tokens
        or st.session_state.chat_engine.top_p != st.session_state.top_p
        or st.session_state.chat_engine.repeat_penalty != st.session_state.repeat_penalty
        or st.session_state.chat_engine.system_prompt != st.session_state.system_prompt
    ):
        st.session_state.chat_engine = ChatEngine(
            model_name=st.session_state.model_name,
            system_prompt=st.session_state.system_prompt,
            temperature=st.session_state.temperature,
            max_tokens=st.session_state.max_tokens,
            top_p=st.session_state.top_p,
            repeat_penalty=st.session_state.repeat_penalty,
        )
    return st.session_state.chat_engine


def start_new_conversation():
    """Reset state for a new conversation."""
    st.session_state.messages = []
    st.session_state.current_conversation_id = None
    st.session_state.chat_engine = None


def load_conversation(conversation_id: str):
    """Load a conversation from the database into session state."""
    cm: ConversationManager = st.session_state.conversation_manager
    conv = cm.get_conversation(conversation_id)
    if not conv:
        return

    st.session_state.current_conversation_id = conversation_id
    st.session_state.model_name = conv["model_name"]
    st.session_state.system_prompt = conv["system_prompt"]
    st.session_state.temperature = conv["temperature"]
    st.session_state.chat_engine = None

    messages = cm.get_messages(conversation_id)
    st.session_state.messages = [
        {"role": msg["role"], "content": msg["content"]} for msg in messages
    ]


def render_sidebar():
    """Render the sidebar with all controls."""
    with st.sidebar:
        st.header(f"{APP_ICON} {APP_TITLE}")

        # Connection status
        if not check_ollama_connection():
            st.error(
                "Ollama is not running. Please start Ollama first.\n\n"
                "Download: https://ollama.com/download"
            )
            st.stop()

        st.success("Ollama connected", icon="\u2705")

        # New conversation button
        if st.button("New Conversation", use_container_width=True, type="primary"):
            start_new_conversation()
            st.rerun()

        st.divider()

        # Model selection
        st.subheader("Model")
        mm: ModelManager = st.session_state.model_manager
        models = mm.list_models()

        if not models:
            st.warning("No models found. Pull a model first:\n\n`ollama pull mistral`")
            st.stop()

        model_names = [m["name"] for m in models]
        model_display = [f"{m['name']} ({ModelManager.format_size(m['size'])})" for m in models]

        # Compare mode toggle
        st.session_state.compare_mode = st.toggle(
            "Compare Mode", value=st.session_state.compare_mode
        )

        if st.session_state.compare_mode:
            # Two model selectors for comparison
            idx_a = 0
            if st.session_state.compare_model_a in model_names:
                idx_a = model_names.index(st.session_state.compare_model_a)

            sel_a = st.selectbox(
                "Model A",
                options=range(len(model_names)),
                format_func=lambda i: model_display[i],
                index=idx_a,
                key="sel_model_a",
            )
            st.session_state.compare_model_a = model_names[sel_a]

            idx_b = min(1, len(model_names) - 1)
            if st.session_state.compare_model_b in model_names:
                idx_b = model_names.index(st.session_state.compare_model_b)

            sel_b = st.selectbox(
                "Model B",
                options=range(len(model_names)),
                format_func=lambda i: model_display[i],
                index=idx_b,
                key="sel_model_b",
            )
            st.session_state.compare_model_b = model_names[sel_b]
        else:
            # Single model selector
            current_idx = 0
            if st.session_state.model_name in model_names:
                current_idx = model_names.index(st.session_state.model_name)

            selected = st.selectbox(
                "Select model",
                options=range(len(model_names)),
                format_func=lambda i: model_display[i],
                index=current_idx,
            )
            st.session_state.model_name = model_names[selected]

        # Download model
        with st.expander("Download Model", expanded=False):
            pull_name = st.text_input(
                "Model name",
                placeholder="e.g. mistral, llama3.1, phi3",
                label_visibility="collapsed",
            )
            if st.button("Pull Model", use_container_width=True):
                if pull_name:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    for progress in mm.pull_model(pull_name):
                        status_text.text(progress["status"])
                        total = progress.get("total", 0)
                        completed = progress.get("completed", 0)
                        if total > 0:
                            progress_bar.progress(completed / total)
                    progress_bar.progress(1.0)
                    st.toast(f"Model '{pull_name}' ready!")
                    st.rerun()

        st.divider()

        # System prompt
        with st.expander("System Prompt", expanded=False):
            cm: ConversationManager = st.session_state.conversation_manager
            prompts = cm.get_system_prompts()
            prompt_names = [p["name"] for p in prompts]
            prompt_map = {p["name"]: p["prompt"] for p in prompts}

            selected_preset = st.selectbox("Preset", options=prompt_names)
            if selected_preset and prompt_map.get(selected_preset):
                default_prompt = prompt_map[selected_preset]
            else:
                default_prompt = st.session_state.system_prompt

            st.session_state.system_prompt = st.text_area(
                "System prompt",
                value=default_prompt,
                height=120,
                label_visibility="collapsed",
            )

            # Save custom preset
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input(
                    "Name",
                    placeholder="My Preset",
                    label_visibility="collapsed",
                )
            with col2:
                if st.button("Save Preset"):
                    if new_name and st.session_state.system_prompt:
                        cm.save_system_prompt(new_name, st.session_state.system_prompt)
                        st.toast(f"Saved preset: {new_name}")
                        st.rerun()

        # Model parameters
        with st.expander("Model Parameters", expanded=False):
            st.session_state.temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.temperature,
                step=0.1,
                help="Higher = more random, lower = more deterministic.",
            )
            st.session_state.max_tokens = st.slider(
                "Max Tokens",
                min_value=100,
                max_value=4096,
                value=st.session_state.max_tokens,
                step=100,
                help="Maximum number of tokens to generate.",
            )
            st.session_state.top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.top_p,
                step=0.05,
                help="Nucleus sampling threshold.",
            )
            st.session_state.repeat_penalty = st.slider(
                "Repeat Penalty",
                min_value=1.0,
                max_value=2.0,
                value=st.session_state.repeat_penalty,
                step=0.05,
                help="Penalty for repeating tokens.",
            )

            if st.button("Reset to Defaults"):
                st.session_state.temperature = DEFAULT_TEMPERATURE
                st.session_state.max_tokens = DEFAULT_MAX_TOKENS
                st.session_state.top_p = DEFAULT_TOP_P
                st.session_state.repeat_penalty = DEFAULT_REPEAT_PENALTY
                st.rerun()

        st.divider()

        # Conversation history
        st.subheader("Conversations")

        cm: ConversationManager = st.session_state.conversation_manager

        # Search
        search_query = st.text_input(
            "Search conversations",
            placeholder="Search...",
            label_visibility="collapsed",
        )

        if search_query:
            conversations = cm.search_conversations(search_query)
        else:
            conversations = cm.get_conversations()

        if not conversations:
            st.caption("No conversations yet. Start chatting!")
        else:
            for conv in conversations:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        conv["title"],
                        key=f"conv_{conv['id']}",
                        use_container_width=True,
                    ):
                        load_conversation(conv["id"])
                        st.rerun()
                with col2:
                    if st.button(
                        "\U0001f5d1",
                        key=f"del_{conv['id']}",
                        help="Delete conversation",
                    ):
                        cm.delete_conversation(conv["id"])
                        if st.session_state.current_conversation_id == conv["id"]:
                            start_new_conversation()
                        st.rerun()


def _generate_response(model_name: str, messages: list[dict]) -> dict:
    """Generate a response from a specific model (used in comparison mode)."""
    engine = ChatEngine(
        model_name=model_name,
        system_prompt=st.session_state.system_prompt,
        temperature=st.session_state.temperature,
        max_tokens=st.session_state.max_tokens,
        top_p=st.session_state.top_p,
        repeat_penalty=st.session_state.repeat_penalty,
    )
    start = time.time()
    response = engine.get_response(messages)
    elapsed_ms = int((time.time() - start) * 1000)
    token_count = len(response.split()) if response else 0
    return {
        "model": model_name,
        "response": response,
        "elapsed_ms": elapsed_ms,
        "token_count": token_count,
    }


def render_compare():
    """Render the model comparison interface."""
    st.title("Model Comparison")

    model_a = st.session_state.compare_model_a
    model_b = st.session_state.compare_model_b
    st.caption(f"Comparing **{model_a}** vs **{model_b}**")

    # Display previous comparison messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        elif message["role"] == "comparison":
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{message['model_a_name']}**")
                st.markdown(message["model_a_response"])
                st.caption(message["model_a_metrics"])
            with col2:
                st.markdown(f"**{message['model_b_name']}**")
                st.markdown(message["model_b_response"])
                st.caption(message["model_b_metrics"])

    # Chat input for comparison
    if prompt := st.chat_input("Send a message to both models..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build message list for the models (user messages only)
        chat_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if m["role"] == "user"
        ]

        # Generate responses in parallel
        with st.spinner("Generating responses from both models..."):
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_a = executor.submit(_generate_response, model_a, chat_messages)
                future_b = executor.submit(_generate_response, model_b, chat_messages)
                result_a = future_a.result()
                result_b = future_b.result()

        # Display side-by-side
        col1, col2 = st.columns(2)

        a_speed = (
            (result_a["token_count"] / (result_a["elapsed_ms"] / 1000))
            if result_a["elapsed_ms"] > 0
            else 0
        )
        b_speed = (
            (result_b["token_count"] / (result_b["elapsed_ms"] / 1000))
            if result_b["elapsed_ms"] > 0
            else 0
        )

        a_metrics = (
            f"~{result_a['token_count']} tokens in "
            f"{result_a['elapsed_ms'] / 1000:.1f}s "
            f"({a_speed:.1f} tok/s)"
        )
        b_metrics = (
            f"~{result_b['token_count']} tokens in "
            f"{result_b['elapsed_ms'] / 1000:.1f}s "
            f"({b_speed:.1f} tok/s)"
        )

        # Highlight faster model
        a_faster = result_a["elapsed_ms"] < result_b["elapsed_ms"]
        a_label = f"**{model_a}** \u26a1" if a_faster else f"**{model_a}**"
        b_label = f"**{model_b}** \u26a1" if not a_faster else f"**{model_b}**"

        with col1:
            st.markdown(a_label)
            st.markdown(result_a["response"])
            st.caption(a_metrics)
        with col2:
            st.markdown(b_label)
            st.markdown(result_b["response"])
            st.caption(b_metrics)

        # Save comparison to session state
        st.session_state.messages.append(
            {
                "role": "comparison",
                "content": "",
                "model_a_name": model_a,
                "model_a_response": result_a["response"],
                "model_a_metrics": a_metrics,
                "model_b_name": model_b,
                "model_b_response": result_b["response"],
                "model_b_metrics": b_metrics,
            }
        )


def render_chat():
    """Render the main chat interface."""
    st.title(APP_TITLE)

    current_id = st.session_state.current_conversation_id
    if current_id:
        cm: ConversationManager = st.session_state.conversation_manager
        conv = cm.get_conversation(current_id)
        if conv:
            st.caption(f"**{conv['title']}** \u2014 {st.session_state.model_name}")
        else:
            st.caption(f"Currently using **{st.session_state.model_name}**")
    else:
        st.caption(f"Currently using **{st.session_state.model_name}**")

    # Export buttons for existing conversations
    if current_id and st.session_state.messages:
        cm: ConversationManager = st.session_state.conversation_manager
        col1, col2, _spacer = st.columns([1, 1, 4])
        with col1:
            json_data = cm.export_as_json(current_id)
            st.download_button(
                "Export JSON",
                data=json_data,
                file_name="conversation.json",
                mime="application/json",
            )
        with col2:
            md_data = cm.export_as_markdown(current_id)
            st.download_button(
                "Export Markdown",
                data=md_data,
                file_name="conversation.md",
                mime="text/markdown",
            )

    # Display existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Send a message..."):
        cm: ConversationManager = st.session_state.conversation_manager

        # Create conversation on first message
        if st.session_state.current_conversation_id is None:
            conv_id = cm.create_conversation(
                model_name=st.session_state.model_name,
                system_prompt=st.session_state.system_prompt,
                temperature=st.session_state.temperature,
            )
            st.session_state.current_conversation_id = conv_id
            title = generate_conversation_title(prompt)
            cm.rename_conversation(conv_id, title)

        conv_id = st.session_state.current_conversation_id

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        cm.add_message(conv_id, "user", prompt)
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and stream assistant response
        with st.chat_message("assistant"):
            engine = get_chat_engine()
            start_time = time.time()
            response = st.write_stream(engine.stream_response(st.session_state.messages))
            elapsed_ms = int((time.time() - start_time) * 1000)

        # Save assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})
        token_count = len(response.split()) if response else 0
        cm.add_message(conv_id, "assistant", response, token_count, elapsed_ms)

        # Show generation metrics
        tokens_per_sec = (token_count / (elapsed_ms / 1000)) if elapsed_ms > 0 else 0
        st.caption(
            f"Generated ~{token_count} tokens in "
            f"{elapsed_ms / 1000:.1f}s "
            f"({tokens_per_sec:.1f} tokens/sec) "
            f"\u2014 {st.session_state.model_name}"
        )


def main():
    init_session_state()
    render_sidebar()

    if st.session_state.compare_mode:
        render_compare()
    else:
        render_chat()


if __name__ == "__main__":
    main()
