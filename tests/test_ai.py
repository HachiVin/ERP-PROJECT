import json

import pandas as pd
import pytest

from erp_dashboard import ai, config
from tests.fakes import FakeClient, connection_error, reply, status_error, timeout_error

SETTINGS = ai.AISettings(api_key="sk-or-test", model="openai/gpt-oss-20b:free")


@pytest.fixture
def table() -> pd.DataFrame:
    return pd.DataFrame({"Customer": [f"Pelanggan-{i}" for i in range(1, 21)], "Amount": range(20)})


def use_client(monkeypatch, outcome) -> FakeClient:
    client = FakeClient(outcome)
    monkeypatch.setattr(ai, "_create_client", lambda settings: client)
    return client


# --- settings -------------------------------------------------------------------------
def test_no_api_key_means_no_settings():
    assert ai.resolve_settings({}, None) is None
    assert ai.resolve_settings({}, {"model": "x:free"}) is None
    assert ai.resolve_settings({"OPENROUTER_API_KEY": "   "}, {"api_key": ""}) is None


def test_settings_come_from_secrets_with_the_free_default_model():
    settings = ai.resolve_settings({}, {"api_key": "sk-or-1"})
    assert settings == ai.AISettings(api_key="sk-or-1", model=config.DEFAULT_MODEL)
    assert settings.model.endswith(":free")


def test_environment_overrides_secrets():
    env = {"OPENROUTER_API_KEY": "sk-env", "OPENROUTER_MODEL": "a/b:free"}
    settings = ai.resolve_settings(env, {"api_key": "sk-secret", "model": "c/d:free"})
    assert settings == ai.AISettings(api_key="sk-env", model="a/b:free")


def test_pasted_whitespace_is_stripped_from_key_and_model():
    settings = ai.resolve_settings({}, {"api_key": " sk-or-1\n", "model": " a/b:free "})
    assert settings == ai.AISettings(api_key="sk-or-1", model="a/b:free")


@pytest.mark.parametrize(
    ("model", "free"),
    [
        ("openai/gpt-oss-20b:free", True),
        ("openrouter/free", True),
        ("openai/gpt-oss-20b", False),
        ("anthropic/claude-sonnet-4", False),
        ("free", False),
        ("model:free-extra", False),
    ],
)
def test_is_free_model(model, free):
    assert ai.is_free_model(model) is free


# --- prompt ---------------------------------------------------------------------------
def test_prompt_discloses_that_the_model_only_sees_a_sample(table):
    prompt = ai.build_prompt("Sales", table.head(5), len(table))
    assert "modul Sales" in prompt
    assert "5 dari 20 baris" in prompt
    assert "jangan menyimpulkan total" in prompt


# --- generate_insight -----------------------------------------------------------------
def test_insight_is_returned_and_only_the_first_rows_are_sent(monkeypatch, table):
    client = use_client(monkeypatch, reply("  Ringkasan singkat.  "))

    text = ai.generate_insight(SETTINGS, "Sales", table)

    assert text == "Ringkasan singkat."
    (call,) = client.calls
    assert call["model"] == "openai/gpt-oss-20b:free"
    user_message = call["messages"][1]["content"]
    assert call["messages"][0]["role"] == "system"
    assert "Pelanggan-1 " in user_message
    assert f"Pelanggan-{config.AI_SAMPLE_ROWS}" in user_message
    assert f"Pelanggan-{config.AI_SAMPLE_ROWS + 1} " not in user_message


def test_a_paid_model_is_refused_without_calling_the_api(monkeypatch, table):
    client = use_client(monkeypatch, reply("tidak boleh sampai sini"))
    paid = ai.AISettings(api_key="sk-or-test", model="openai/gpt-4o")

    with pytest.raises(ai.AIError, match="bukan model gratis"):
        ai.generate_insight(paid, "Sales", table)

    assert client.calls == []


@pytest.mark.parametrize("content", [None, "", "   "])
def test_empty_reply_is_an_error(monkeypatch, table, content):
    use_client(monkeypatch, reply(content))
    with pytest.raises(ai.AIError, match="kosong"):
        ai.generate_insight(SETTINGS, "Sales", table)


def test_reply_without_choices_is_an_error(monkeypatch, table):
    from types import SimpleNamespace

    use_client(monkeypatch, SimpleNamespace(choices=[]))
    with pytest.raises(ai.AIError, match="kosong"):
        ai.generate_insight(SETTINGS, "Sales", table)


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (status_error(401), "API key tidak valid"),
        (status_error(402), "Kredit OpenRouter"),
        (status_error(404), "Model tidak ditemukan"),
        (status_error(429), "Batas request"),
        (status_error(500, "gangguan"), "HTTP 500: gangguan"),
        (connection_error(), "Tidak dapat terhubung"),
        (timeout_error(), "timeout"),
    ],
)
def test_api_failures_become_readable_errors(monkeypatch, table, error, expected):
    use_client(monkeypatch, error)
    with pytest.raises(ai.AIError, match=expected):
        ai.generate_insight(SETTINGS, "Sales", table)


def test_error_messages_never_contain_the_api_key(monkeypatch, table):
    use_client(monkeypatch, status_error(401))
    with pytest.raises(ai.AIError) as caught:
        ai.generate_insight(SETTINGS, "Sales", table)
    assert SETTINGS.api_key not in str(caught.value)


# --- history store --------------------------------------------------------------------
def test_history_round_trip(tmp_path):
    store = ai.AILogStore(tmp_path / "logs")
    data = {"CRM_Data CRM": {"text": "Ringkasan ✓", "time": "2025-09-26 10:00:00"}}

    store.save("kevin", data)

    assert store.load("kevin") == data
    assert (tmp_path / "logs" / "kevin_ai_suggestions.json").exists()


def test_history_file_name_matches_the_original_format():
    assert ai.AILogStore(config.AI_LOGS_DIR).path_for("kevin").name == "kevin_ai_suggestions.json"


def test_unknown_user_has_empty_history(tmp_path):
    assert ai.AILogStore(tmp_path).load("belum-pernah-login") == {}


@pytest.mark.parametrize("content", ["{rusak", "[1, 2]", '"teks"', ""])
def test_corrupt_history_is_treated_as_empty(tmp_path, content):
    store = ai.AILogStore(tmp_path)
    store.path_for("kevin").write_text(content, encoding="utf-8")
    assert store.load("kevin") == {}


def test_history_paths_cannot_escape_the_log_directory(tmp_path):
    store = ai.AILogStore(tmp_path / "logs")
    for hostile in ["../../etc/passwd", "..\\..\\x", "a/b", "kevin/../rina"]:
        assert store.path_for(hostile).parent == tmp_path / "logs"


def test_sanitised_usernames_do_not_collide(tmp_path):
    store = ai.AILogStore(tmp_path)
    assert store.path_for("a.b") != store.path_for("a_b")
    assert store.path_for("a.b") != store.path_for("a/b")


def test_history_is_one_json_object(tmp_path):
    store = ai.AILogStore(tmp_path)
    store.save("kevin", {"k": {"text": "t", "time": "w"}})
    assert isinstance(json.loads(store.path_for("kevin").read_text(encoding="utf-8")), dict)
