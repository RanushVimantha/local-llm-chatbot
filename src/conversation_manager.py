import json
import sqlite3

from src.config import DB_PATH, PRESET_SYSTEM_PROMPTS
from src.utils import ensure_data_dir


class ConversationManager:
    """Manages conversation persistence using SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        ensure_data_dir()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._init_db()

    def _init_db(self):
        """Create tables and seed default data."""
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                title TEXT NOT NULL DEFAULT 'New Conversation',
                model_name TEXT NOT NULL,
                system_prompt TEXT DEFAULT 'You are a helpful assistant.',
                temperature REAL DEFAULT 0.7,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                tokens_used INTEGER,
                generation_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS system_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Seed default system prompts
        for name, prompt in PRESET_SYSTEM_PROMPTS.items():
            cursor.execute(
                "INSERT OR IGNORE INTO system_prompts (name, prompt) VALUES (?, ?)",
                (name, prompt),
            )
        self.conn.commit()

    def create_conversation(
        self,
        model_name: str,
        system_prompt: str = "",
        temperature: float = 0.7,
    ) -> str:
        """Create a new conversation and return its ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO conversations (id, model_name, system_prompt, temperature)
               VALUES (lower(hex(randomblob(16))), ?, ?, ?)""",
            (model_name, system_prompt, temperature),
        )
        self.conn.commit()
        return cursor.execute(
            "SELECT id FROM conversations ORDER BY created_at DESC LIMIT 1"
        ).fetchone()["id"]

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tokens_used: int | None = None,
        generation_time_ms: int | None = None,
    ) -> None:
        """Add a message to a conversation."""
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO messages
               (conversation_id, role, content, tokens_used, generation_time_ms)
               VALUES (?, ?, ?, ?, ?)""",
            (conversation_id, role, content, tokens_used, generation_time_ms),
        )
        cursor.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
        )
        self.conn.commit()

    def get_conversations(self) -> list[dict]:
        """Get all conversations ordered by most recently updated."""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            """SELECT id, title, model_name, system_prompt, temperature, created_at, updated_at
               FROM conversations ORDER BY updated_at DESC"""
        ).fetchall()
        return [dict(row) for row in rows]

    def get_messages(self, conversation_id: str) -> list[dict]:
        """Get all messages for a conversation in chronological order."""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            """SELECT id, role, content, tokens_used, generation_time_ms, created_at
               FROM messages WHERE conversation_id = ?
               ORDER BY created_at ASC""",
            (conversation_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation and all its messages."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        self.conn.commit()

    def rename_conversation(self, conversation_id: str, title: str) -> None:
        """Update a conversation's title."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (title, conversation_id),
        )
        self.conn.commit()

    def get_conversation(self, conversation_id: str) -> dict | None:
        """Get a single conversation by ID."""
        cursor = self.conn.cursor()
        row = cursor.execute(
            """SELECT id, title, model_name, system_prompt, temperature, created_at, updated_at
               FROM conversations WHERE id = ?""",
            (conversation_id,),
        ).fetchone()
        return dict(row) if row else None

    def search_conversations(self, query: str) -> list[dict]:
        """Search conversations by title or message content."""
        cursor = self.conn.cursor()
        search_term = f"%{query}%"
        rows = cursor.execute(
            """SELECT DISTINCT c.id, c.title, c.model_name, c.system_prompt,
                      c.temperature, c.created_at, c.updated_at
               FROM conversations c
               LEFT JOIN messages m ON c.id = m.conversation_id
               WHERE c.title LIKE ? OR m.content LIKE ?
               ORDER BY c.updated_at DESC""",
            (search_term, search_term),
        ).fetchall()
        return [dict(row) for row in rows]

    # System prompts
    def get_system_prompts(self) -> list[dict]:
        """Get all saved system prompts."""
        cursor = self.conn.cursor()
        rows = cursor.execute(
            "SELECT id, name, prompt, created_at FROM system_prompts ORDER BY id ASC"
        ).fetchall()
        return [dict(row) for row in rows]

    def save_system_prompt(self, name: str, prompt: str) -> None:
        """Save a new system prompt."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO system_prompts (name, prompt) VALUES (?, ?)",
            (name, prompt),
        )
        self.conn.commit()

    def delete_system_prompt(self, prompt_id: int) -> None:
        """Delete a saved system prompt."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM system_prompts WHERE id = ?", (prompt_id,))
        self.conn.commit()

    # Export
    def export_as_json(self, conversation_id: str) -> str:
        """Export a conversation as a JSON string."""
        conv = self.get_conversation(conversation_id)
        if not conv:
            return "{}"
        messages = self.get_messages(conversation_id)
        export = {
            "conversation": {
                "id": conv["id"],
                "title": conv["title"],
                "model": conv["model_name"],
                "system_prompt": conv["system_prompt"],
                "temperature": conv["temperature"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
            },
            "messages": [
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "tokens_used": msg["tokens_used"],
                    "generation_time_ms": msg["generation_time_ms"],
                    "timestamp": msg["created_at"],
                }
                for msg in messages
            ],
        }
        return json.dumps(export, indent=2)

    def export_as_markdown(self, conversation_id: str) -> str:
        """Export a conversation as a Markdown string."""
        conv = self.get_conversation(conversation_id)
        if not conv:
            return ""
        messages = self.get_messages(conversation_id)

        lines = [
            f"# {conv['title']}",
            "",
            f"**Model:** {conv['model_name']}",
            f"**Created:** {conv['created_at']}",
            "",
            "---",
            "",
        ]
        for msg in messages:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"### {role_label}")
            lines.append("")
            lines.append(msg["content"])
            lines.append("")

        return "\n".join(lines)

    def close(self):
        """Close the database connection."""
        self.conn.close()
