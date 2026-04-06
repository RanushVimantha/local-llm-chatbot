import os

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = "mistral"

# Database
DB_PATH = os.getenv("DB_PATH", "data/conversations.db")

# App
APP_TITLE = "Local LLM Chatbot"
APP_ICON = "\U0001f916"
PAGE_LAYOUT = "wide"

# Default Model Parameters
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TOP_P = 0.9
DEFAULT_REPEAT_PENALTY = 1.1

# Default System Prompt
DEFAULT_SYSTEM_PROMPT = "You are a helpful, accurate, and friendly AI assistant."

# Preset System Prompts
PRESET_SYSTEM_PROMPTS = {
    "General Assistant": "You are a helpful, accurate, and friendly AI assistant.",
    "Code Helper": (
        "You are an expert programmer. Provide clean, well-commented code with explanations. "
        "Use best practices and modern patterns."
    ),
    "Creative Writer": (
        "You are a creative writer with a vivid imagination. Write engaging, original content "
        "with rich descriptions and compelling narratives."
    ),
    "Tutor": (
        "You are a patient and knowledgeable tutor. Explain concepts step-by-step, use analogies, "
        "and check for understanding. Adapt your explanations to the student level."
    ),
    "DevOps Engineer": (
        "You are a senior DevOps engineer. Provide solutions using Docker, Kubernetes, Terraform, "
        "CI/CD, and cloud best practices. Always consider security, scalability, and cost."
    ),
}
