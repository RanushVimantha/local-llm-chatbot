# Contributing to Local LLM Chatbot

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. **Fork the repository** and clone it locally
2. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```
3. **Start Ollama** and pull at least one model:
   ```bash
   ollama pull mistral
   ```
4. **Run the app:**
   ```bash
   streamlit run src/app.py
   ```

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Run lint and tests before committing:
   ```bash
   ruff check src/ tests/
   ruff format src/ tests/
   pytest tests/ -v
   ```
4. Commit with a clear, descriptive message
5. Open a pull request against `main`

## Code Style

- Follow PEP 8 conventions
- Use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Line length limit: 100 characters
- All code must pass `ruff check` and `ruff format --check`

## Testing

- Write tests for new features in `tests/`
- Mock all Ollama API calls (tests must run without Ollama)
- Run `pytest tests/ -v` to verify all tests pass

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Your OS, Python version, and Ollama version

## Suggesting Features

Open an issue describing:
- The problem you want to solve
- Your proposed solution
- Any alternatives you considered

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
