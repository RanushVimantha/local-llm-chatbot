# Local LLM Chatbot

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.2%2B-1C3C3C?logo=langchain&logoColor=white)](https://langchain.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/RanushVimantha/local-llm-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/RanushVimantha/local-llm-chatbot/actions/workflows/ci.yml)

> A privacy-first AI chatbot running entirely on your machine.
> No API keys. No data leaves your computer. 100% free.

## Features

- **Fully Local** — Zero external API calls. Your data stays on your machine.
- **Multi-Model Support** — Switch between Mistral, Llama 3.1, Phi-3, Gemma 2, CodeLlama, Qwen, and more.
- **Real-Time Streaming** — Token-by-token response streaming for a natural chat experience.
- **Side-by-Side Model Comparison** — Send the same prompt to two models and compare responses.
- **Persistent Conversation History** — SQLite-backed storage that survives restarts.
- **Custom System Prompts** — Presets for General Assistant, Code Helper, Creative Writer, Tutor, DevOps Engineer, and your own.
- **Adjustable Parameters** — Temperature, Top-P, Max Tokens, and Repeat Penalty sliders.
- **Conversation Export** — Download any conversation as JSON or Markdown.
- **Conversation Search** — Find past conversations by title or message content.
- **Performance Metrics** — See tokens/second and generation time for every response.
- **Docker Support** — One command to run with Docker Compose.
- **CI/CD** — GitHub Actions for linting, testing, and Docker builds.

## Architecture

```
User's Browser (localhost:8501)
        |
        v
  Streamlit Frontend
  [Chat UI] [Model Select] [Settings Panel]
        |
        v
  Python Backend (app.py)
  [Chat Engine]  [Conversation Manager]  [Model Manager]
  [LangChain]    [SQLite]                [List/Switch/Compare]
        |
        v
  Ollama Server (localhost:11434)
  [Mistral] [Llama 3.1] [Phi-3] [Gemma 2] [...]
```

## Quick Start

### Prerequisites

- **Python 3.11+** — [Download](https://python.org)
- **Ollama** — [Download](https://ollama.com/download)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/RanushVimantha/local-llm-chatbot.git
cd local-llm-chatbot
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Start Ollama and pull a model**

```bash
ollama serve
ollama pull mistral
```

4. **Run the chatbot**

```bash
streamlit run src/app.py
```

The app opens at [http://localhost:8501](http://localhost:8501).

## Supported Models

| Model | Size | Best For | RAM Required |
|-------|------|----------|-------------|
| Mistral 7B | ~4.1 GB | General purpose, fast | 8 GB |
| Llama 3.1 8B | ~4.7 GB | Strong reasoning, multilingual | 8 GB |
| Phi-3 Mini | ~2.3 GB | Lightweight, good for low-RAM | 4 GB |
| Gemma 2 2B | ~1.6 GB | Ultra-lightweight, quick | 4 GB |
| CodeLlama 7B | ~3.8 GB | Code generation | 8 GB |
| Qwen 2.5 7B | ~4.4 GB | Multilingual, structured tasks | 8 GB |

Pull any model with:

```bash
ollama pull <model-name>
```

Or use the **Download Model** section in the app's sidebar.

## Model Comparison

Toggle **Compare Mode** in the sidebar to send the same prompt to two models simultaneously. Responses appear side-by-side with performance metrics, and the faster model is highlighted.

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `DB_PATH` | `data/conversations.db` | SQLite database path |

## Docker

Run the full stack (Ollama + Chatbot) with Docker Compose:

```bash
docker compose up -d
```

Then open [http://localhost:8501](http://localhost:8501).

To pull a model inside the Ollama container:

```bash
docker compose exec ollama ollama pull mistral
```

## Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Lint
ruff check src/ tests/
ruff format --check src/ tests/
```

## Project Structure

```
local-llm-chatbot/
├── .github/workflows/     # CI/CD pipelines
├── src/
│   ├── app.py             # Streamlit application
│   ├── chat_engine.py     # LangChain chat logic & streaming
│   ├── model_manager.py   # Ollama model management
│   ├── conversation_manager.py  # SQLite conversation CRUD
│   ├── config.py          # Configuration & constants
│   └── utils.py           # Helper functions
├── tests/                 # Unit tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── Makefile
└── README.md
```

## Tech Stack

- **LLM Runtime:** [Ollama](https://ollama.com)
- **LLM Integration:** [LangChain](https://langchain.com)
- **Web Interface:** [Streamlit](https://streamlit.io)
- **Database:** SQLite
- **Testing:** pytest
- **Linting:** ruff
- **Containerization:** Docker
- **CI/CD:** GitHub Actions

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
