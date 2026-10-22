"""LLM insight via OpenRouter, plus the per-user history store. Free of Streamlit imports.

This is a single chat-completion call over a small sample of rows. It has no tools, no loop and
no memory, so it is an "LLM-generated insight", not an autonomous agent.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, OpenAIError

from erp_dashboard import config


class AIError(RuntimeError):
    """An AI call failed. The message is written for the user and is safe to display."""


@dataclass(frozen=True)
class AISettings:
    api_key: str
    model: str


_STATUS_HINTS = {
    401: "API key tidak valid atau sudah dicabut. Buat key baru lalu perbarui secrets.",
    402: "Kredit OpenRouter tidak mencukupi atau saldo akun negatif.",
    404: "Model tidak ditemukan. Periksa ID model di secrets.",
    429: "Batas request model gratis tercapai (per menit/hari) atau provider sedang penuh.",
}


def is_free_model(model_id: str) -> bool:
    """Free OpenRouter models end in ``:free``; ``openrouter/free`` is the free-model router."""
    return model_id.endswith(":free") or model_id == config.FREE_ROUTER_MODEL


def resolve_settings(
    env: Mapping[str, str], secrets_section: Mapping[str, Any] | None
) -> AISettings | None:
    """Combine environment variables (local ``.env``) and Streamlit secrets.

    Environment variables win over secrets. Returns ``None`` when no API key is configured.
    """
    section = secrets_section or {}
    api_key = (env.get("OPENROUTER_API_KEY") or section.get("api_key") or "").strip()
    if not api_key:
        return None
    model = (env.get("OPENROUTER_MODEL") or section.get("model") or config.DEFAULT_MODEL).strip()
    return AISettings(api_key=api_key, model=model)


def build_prompt(module_name: str, sample: pd.DataFrame, total_rows: int) -> str:
    """Prompt that tells the model it only sees a sample, so it does not extrapolate."""
    return (
        f"Analisa data untuk modul {module_name}. "
        f"Berikut sample data ({len(sample)} dari {total_rows} baris; hanya sampel, "
        "jangan menyimpulkan total atau tren seluruh data):\n"
        f"{sample.to_string(index=False)}\n\n"
        f"Jawaban ringkas (maks {config.AI_MAX_WORDS} kata)."
    )


def _create_client(settings: AISettings) -> OpenAI:
    return OpenAI(
        base_url=config.OPENROUTER_BASE_URL,
        api_key=settings.api_key,
        timeout=config.AI_TIMEOUT_SECONDS,
        max_retries=1,
    )


def _describe_error(exc: OpenAIError) -> str:
    if isinstance(exc, APITimeoutError):
        return "Permintaan ke OpenRouter timeout. Coba lagi."
    if isinstance(exc, APIConnectionError):
        return "Tidak dapat terhubung ke OpenRouter."
    if isinstance(exc, APIStatusError):
        detail = f"HTTP {exc.status_code}: {exc.message}"
        hint = _STATUS_HINTS.get(exc.status_code)
        return f"{detail}. {hint}" if hint else detail
    return str(exc) or type(exc).__name__


def generate_insight(settings: AISettings, module_name: str, df: pd.DataFrame) -> str:
    """Ask the model for a short analysis of the first ``AI_SAMPLE_ROWS`` rows of ``df``.

    Raises:
        AIError: If the model is not free, the call fails, or the reply is empty.
    """
    if not is_free_model(settings.model):
        raise AIError(
            f"Model '{settings.model}' bukan model gratis, jadi tidak dipanggil. "
            "Gunakan ID model berakhiran ':free' atau 'openrouter/free'."
        )

    sample = df.head(config.AI_SAMPLE_ROWS)
    messages = [
        {"role": "system", "content": config.AI_SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(module_name, sample, len(df))},
    ]
    try:
        response = _create_client(settings).chat.completions.create(
            model=settings.model, messages=messages
        )
    except OpenAIError as exc:
        raise AIError(_describe_error(exc)) from exc

    text = ""
    if response.choices:
        text = (response.choices[0].message.content or "").strip()
    if not text:
        raise AIError("Model mengembalikan respons kosong. Coba lagi atau ganti model.")
    return text


class AILogStore:
    """Per-user JSON history of AI insights: ``{"<module>_<view>": {"text", "time"}}``."""

    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)

    def path_for(self, username: str) -> Path:
        """File for ``username``. Unsafe characters are replaced, with a hash to avoid clashes."""
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", username) or "_"
        if safe != username:
            safe = f"{safe}-{hashlib.sha1(username.encode()).hexdigest()[:8]}"
        return self.directory / f"{safe}_ai_suggestions.json"

    def load(self, username: str) -> dict[str, dict[str, str]]:
        try:
            data = json.loads(self.path_for(username).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def save(self, username: str, suggestions: Mapping[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path_for(username).write_text(
            json.dumps(suggestions, ensure_ascii=False, indent=2), encoding="utf-8"
        )
