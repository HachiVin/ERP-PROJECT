import bcrypt
import pytest

from erp_dashboard import config

PASSWORD = "rahasia123"


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    """Keep every test independent of the developer's real .env, API key and ai_logs folder."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setattr(config, "AI_LOGS_DIR", tmp_path / "ai_logs")


@pytest.fixture(scope="session")
def password_hash() -> str:
    # rounds=4 is bcrypt's minimum; it keeps the tests fast and is irrelevant to correctness.
    return bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()
