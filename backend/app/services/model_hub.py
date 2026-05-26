import os
from app.models.database import get_db


def get_active_models():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM model_configs WHERE is_active = 1 ORDER BY sort_order ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_models():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM model_configs ORDER BY sort_order ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_model_by_id(model_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM model_configs WHERE id = ?", (model_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_model_by_key(provider: str, model_name: str):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM model_configs WHERE provider = ? AND model_name = ? AND is_active = 1",
        (provider, model_name)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_model(data: dict) -> int:
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO model_configs (provider, model_name, display_name, api_key, base_url, is_active, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (data["provider"], data["model_name"], data.get("display_name", ""),
         data.get("api_key", ""), data.get("base_url", ""),
         int(data.get("is_active", True)), data.get("sort_order", 0))
    )
    conn.commit()
    mid = cursor.lastrowid
    conn.close()
    return mid


def update_model(model_id: int, data: dict):
    conn = get_db()
    fields = []
    values = []
    for key in ["provider", "model_name", "display_name", "api_key", "base_url", "is_active", "sort_order"]:
        if key in data and data[key] is not None:
            fields.append(f"{key} = ?")
            values.append(data[key] if key != "is_active" else int(data[key]))
    if fields:
        values.append(model_id)
        conn.execute(f"UPDATE model_configs SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()


def delete_model(model_id: int):
    conn = get_db()
    conn.execute("DELETE FROM model_configs WHERE id = ?", (model_id,))
    conn.commit()
    conn.close()


def build_llm(provider: str, model_name: str, api_key: str, base_url: str):
    """Build LangChain LLM instance based on provider."""
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = api_key or os.getenv("GOOGLE_API_KEY", "")
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=key, temperature=0.3)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        kwargs = dict(model=model_name, temperature=0.3)
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        kwargs = dict(model=model_name, temperature=0.3)
        if api_key:
            kwargs["anthropic_api_key"] = api_key
        if base_url:
            kwargs["anthropic_api_url"] = base_url
        return ChatAnthropic(**kwargs)
    elif provider == "deepseek":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY", ""),
            base_url=base_url or "https://api.deepseek.com/v1",
            temperature=0.3,
        )
    elif provider == "ollama":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key="ollama",
            base_url=base_url or "http://localhost:11434/v1",
            temperature=0.3,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model_name,
            api_key=api_key or "not-needed",
            base_url=base_url or "http://localhost:11434/v1",
            temperature=0.3,
        )


def resolve_llm(model_key: str | None = None):
    """Resolve LLM from model config. Uses active default if model_key is None."""
    conn = get_db()
    if model_key:
        parts = model_key.split(":", 1)
        if len(parts) == 2:
            row = conn.execute(
                "SELECT * FROM model_configs WHERE provider = ? AND model_name = ? AND is_active = 1",
                (parts[0], parts[1])
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM model_configs WHERE id = ? AND is_active = 1",
                (model_key,)
            ).fetchone()
    else:
        row = conn.execute(
            "SELECT * FROM model_configs WHERE is_active = 1 ORDER BY sort_order ASC LIMIT 1"
        ).fetchone()
    conn.close()

    if not row:
        raise ValueError("No active model configured. Please configure a model in Settings.")

    cfg = dict(row)
    return build_llm(cfg["provider"], cfg["model_name"], cfg.get("api_key", ""), cfg.get("base_url", ""))
