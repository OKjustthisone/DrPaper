import sqlite3
from datetime import datetime
from app.config import DATABASE_URL

DB_PATH = DATABASE_URL.replace("sqlite:///", "")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS notebooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            system_prompt TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notebook_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER DEFAULT 0,
            file_path TEXT NOT NULL,
            chunk_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'ready',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notebook_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            citations_json TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notebook_id INTEGER NOT NULL,
            artifact_type TEXT NOT NULL,
            title TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS model_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            model_name TEXT NOT NULL,
            display_name TEXT DEFAULT '',
            api_key TEXT DEFAULT '',
            base_url TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    existing = conn.execute("SELECT COUNT(*) FROM model_configs WHERE provider = 'google'").fetchone()[0]
    if existing == 0:
        conn.execute("""
            INSERT INTO model_configs (provider, model_name, display_name, api_key, is_active, sort_order)
            VALUES ('google', 'gemini-2.5-flash', 'Gemini 2.5 Flash (Default)', '', 1, 0)
        """)
        conn.execute("""
            INSERT INTO model_configs (provider, model_name, display_name, api_key, is_active, sort_order)
            VALUES ('google', 'gemini-1.5-pro', 'Gemini 1.5 Pro', '', 0, 1)
        """)

    conn.commit()
    conn.close()
