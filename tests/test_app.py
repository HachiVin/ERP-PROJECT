"""End-to-end tests: the real Streamlit pages run under ``AppTest``; the AI client is faked."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from erp_dashboard import ai, config
from erp_dashboard.modules import MODULES
from tests.conftest import PASSWORD
from tests.fakes import FakeClient, reply, status_error

ROOT = Path(__file__).resolve().parents[1]
FREE_MODEL = "openai/gpt-oss-20b:free"
TIMEOUT = 60


def make_app(path: str, secrets: dict | None = None) -> AppTest:
    app = AppTest.from_file(str(ROOT / path), default_timeout=TIMEOUT)
    for section, values in (secrets or {}).items():
        app.secrets[section] = values
    return app


def home(password_hash: str, extra: dict | None = None) -> AppTest:
    secrets = {"users": {"kevin": password_hash, "rina": password_hash}, **(extra or {})}
    return make_app("main.py", secrets).run()


def log_in(app: AppTest, username: str = "kevin", password: str = PASSWORD) -> AppTest:
    app.text_input(key="login_user").input(username)
    app.text_input(key="login_pass").input(password)
    return app.button[0].click().run()


def dashboard(username: str | None = "kevin", ai_section: dict | None = None) -> AppTest:
    secrets = {"openrouter": ai_section} if ai_section else {}
    app = make_app("pages/dashboard_fistx.py", secrets)
    if username is not None:
        app.session_state[config.STATE_LOGGED_IN] = True
        app.session_state[config.STATE_USERNAME] = username
    return app.run()


def fake_ai(monkeypatch, outcome) -> FakeClient:
    client = FakeClient(outcome)
    monkeypatch.setattr(ai, "_create_client", lambda settings: client)
    return client


def click(app: AppTest, key: str) -> AppTest:
    return app.button(key=key).click().run()


def click_label(app: AppTest, label: str) -> AppTest:
    return next(button for button in app.button if button.label == label).click().run()


def chart_count(app: AppTest) -> int:
    # st.pyplot is reported as "imgs" by Streamlit 1.37 and as "image" by newer releases.
    return len(app.get("imgs")) + len(app.get("image"))


def texts(elements) -> list[str]:
    return [element.value for element in elements]


def saved_log(username: str = "kevin") -> dict:
    path = ai.AILogStore(config.AI_LOGS_DIR).path_for(username)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


FREE_KEY = {"api_key": "sk-or-test", "model": FREE_MODEL}


# --- login page ------------------------------------------------------------------------
def test_login_page_offers_only_login(password_hash):
    app = home(password_hash)

    assert not app.exception
    assert [button.label for button in app.button] == ["Login"]
    assert not app.tabs
    assert len(app.text_input) == 2
    page_text = " ".join(texts(app.markdown) + texts(app.subheader))
    for removed in ("Register", "Admin", "Hapus Akun"):
        assert removed not in page_text


def test_login_page_never_lists_accounts(password_hash):
    app = home(password_hash)
    page_text = " ".join(texts(app.markdown) + texts(app.text) + texts(app.caption))
    assert "kevin" not in page_text
    assert "rina" not in page_text


def test_wrong_password_shows_an_error_and_stays_logged_out(password_hash):
    app = log_in(home(password_hash), password="salah")

    assert any("Username / Password salah" in message for message in texts(app.error))
    assert config.STATE_LOGGED_IN not in app.session_state
    assert [button.label for button in app.button] == ["Login"]


def test_unknown_user_cannot_log_in(password_hash):
    app = log_in(home(password_hash), username="penyusup")
    assert any("salah" in message for message in texts(app.error))


def test_correct_login_shows_the_company_picker(password_hash):
    app = log_in(home(password_hash))

    assert not app.exception
    assert app.session_state[config.STATE_LOGGED_IN] is True
    assert app.session_state[config.STATE_USERNAME] == "kevin"
    assert any("Halo, **kevin**" in text for text in texts(app.markdown))
    company_buttons = [b.label for b in app.button if (b.key or "").startswith("btn_")]
    assert sorted(company_buttons) == sorted(config.COMPANIES)  # AppTest lists columns first


def test_company_without_a_page_shows_a_notice(password_hash):
    app = log_in(home(password_hash))

    app = click(app, "btn_Maximus")

    assert any("Maximus" in message and "belum dibuat" in message for message in texts(app.warning))


def test_missing_accounts_in_secrets_gives_a_clear_message():
    app = make_app("main.py").run()

    assert any("Akun belum dikonfigurasi" in message for message in texts(app.error))
    assert not app.text_input
    assert not app.exception


def test_malformed_accounts_section_gives_a_clear_message():
    app = make_app("main.py", {"users": "bukan-tabel"}).run()
    assert any("Akun belum dikonfigurasi" in message for message in texts(app.error))


def test_logout_clears_the_session_and_the_ai_history(password_hash):
    app = log_in(home(password_hash))
    app.session_state[config.STATE_AI_SUGGESTIONS] = {"k": {"text": "rahasia", "time": "x"}}
    app.session_state[config.STATE_AI_OWNER] = "kevin"

    app = click_label(app, "Logout")

    assert not app.session_state[config.STATE_LOGGED_IN]
    assert config.STATE_AI_SUGGESTIONS not in app.session_state
    assert [button.label for button in app.button] == ["Login"]


# --- dashboard: access -----------------------------------------------------------------
def test_dashboard_requires_login():
    app = dashboard(username=None)

    assert any("harus login" in message for message in texts(app.error))
    assert not app.selectbox
    assert not app.exception


def test_dashboard_rejects_a_session_without_a_username():
    app = dashboard(username="")
    assert any("Username tidak ditemukan" in message for message in texts(app.error))
    assert not app.selectbox


# --- dashboard: data views -------------------------------------------------------------
def test_every_module_and_view_renders():
    app = dashboard()
    assert not app.exception

    assert list(app.selectbox[0].options) == [spec.name for spec in MODULES]
    views_seen = charts_seen = 0
    for spec in MODULES:
        app.selectbox[0].select(spec.name).run()
        assert not app.exception, spec.name
        for view in spec.views:
            app.selectbox(key=f"view_{spec.name}").select(view.label).run()
            assert not app.exception, f"{spec.name} / {view.label}"
            views_seen += 1
            if view.chart is not None:
                charts_seen += 1
                assert chart_count(app) == 1, f"{spec.name} / {view.label}"
            else:
                assert len(app.dataframe) == 1, f"{spec.name} / {view.label}"

    assert (views_seen, charts_seen) == (17, 6)


def test_ai_caption_states_how_many_rows_the_model_sees():
    app = dashboard()
    app.selectbox[0].select("Sales").run()
    assert any("AI hanya membaca 5 baris pertama dari 100 baris" in c for c in texts(app.caption))


def test_ai_caption_does_not_overstate_for_tiny_tables():
    app = dashboard()
    app.selectbox[0].select("Products").run()
    assert any("5 baris pertama dari 5 baris" in c for c in texts(app.caption))


def test_missing_data_file_is_reported_not_a_crash(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "FISTX_DATA_DIR", tmp_path)
    app = dashboard()
    assert any("tidak ditemukan" in message for message in texts(app.error))
    assert not app.exception


# --- dashboard: AI insight -------------------------------------------------------------
def test_without_api_key_the_dashboard_works_and_the_ai_buttons_are_hidden():
    app = dashboard()

    assert not app.exception
    assert any("API Key OpenRouter belum diatur" in message for message in texts(app.warning))
    assert not [b for b in app.button if (b.key or "").startswith(("run_", "refresh_"))]


def test_successful_insight_is_shown_and_saved_for_the_user(monkeypatch):
    client = fake_ai(monkeypatch, reply("Pipeline didominasi tahap Qualified."))
    app = dashboard(ai_section=FREE_KEY)

    app = click(app, "run_CRM_Data CRM")

    assert not app.error
    assert "Pipeline didominasi tahap Qualified." in texts(app.markdown)
    assert len(client.calls) == 1
    assert client.calls[0]["model"] == FREE_MODEL
    entry = saved_log("kevin")["CRM_Data CRM"]
    assert entry["text"] == "Pipeline didominasi tahap Qualified."
    assert entry["time"]


def test_saved_insight_is_still_there_after_a_new_session(monkeypatch):
    fake_ai(monkeypatch, reply("Insight lama."))
    click(dashboard(ai_section=FREE_KEY), "run_CRM_Data CRM")

    fresh = dashboard(ai_section=FREE_KEY)

    assert "Insight lama." in texts(fresh.markdown)


def test_refresh_button_replaces_the_previous_insight(monkeypatch):
    fake_ai(monkeypatch, reply("Versi pertama."))
    app = click(dashboard(ai_section=FREE_KEY), "run_CRM_Data CRM")
    fake_ai(monkeypatch, reply("Versi kedua."))

    app = click(app, "refresh_CRM_Data CRM")

    assert "Versi kedua." in texts(app.markdown)
    assert "Versi pertama." not in texts(app.markdown)
    assert saved_log("kevin")["CRM_Data CRM"]["text"] == "Versi kedua."


def test_the_model_only_receives_the_first_five_rows(monkeypatch):
    client = fake_ai(monkeypatch, reply("ok"))
    app = dashboard(ai_section=FREE_KEY)
    app.selectbox[0].select("Sales").run()

    click(app, "run_Sales_Data Sales")

    prompt = client.calls[0]["messages"][1]["content"]
    assert "5 dari 100 baris" in prompt
    assert "SO101" in prompt
    assert "SO105" in prompt
    assert "SO106" not in prompt


@pytest.mark.parametrize(
    ("error", "hint"),
    [
        (status_error(401), "API key tidak valid"),
        (status_error(402), "Kredit OpenRouter"),
        (status_error(429), "Batas request"),
    ],
)
def test_failed_call_shows_the_reason_and_saves_nothing(monkeypatch, error, hint):
    fake_ai(monkeypatch, error)
    app = click(dashboard(ai_section=FREE_KEY), "run_CRM_Data CRM")

    assert any("Gagal memanggil AI" in message and hint in message for message in texts(app.error))
    assert saved_log("kevin") == {}
    assert not app.exception


def test_failed_refresh_keeps_the_previous_insight(monkeypatch):
    fake_ai(monkeypatch, reply("Insight yang masih berlaku."))
    app = click(dashboard(ai_section=FREE_KEY), "run_CRM_Data CRM")
    fake_ai(monkeypatch, status_error(429))

    app = click(app, "refresh_CRM_Data CRM")

    assert any("Gagal memanggil AI" in message for message in texts(app.error))
    assert "Insight yang masih berlaku." in texts(app.markdown)
    assert saved_log("kevin")["CRM_Data CRM"]["text"] == "Insight yang masih berlaku."


def test_a_paid_model_is_refused_before_any_request_is_sent(monkeypatch):
    client = fake_ai(monkeypatch, reply("tidak boleh"))
    app = dashboard(ai_section={"api_key": "sk-or-test", "model": "openai/gpt-4o"})

    app = click(app, "run_CRM_Data CRM")

    assert any("bukan model gratis" in message for message in texts(app.error))
    assert client.calls == []
    assert saved_log("kevin") == {}


def test_model_can_be_set_from_the_environment(monkeypatch):
    client = fake_ai(monkeypatch, reply("ok"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-env")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")

    click(dashboard(), "run_CRM_Data CRM")

    assert client.calls[0]["model"] == "openrouter/free"


# --- dashboard: accounts stay separate -------------------------------------------------
def test_one_users_insights_are_not_shown_to_another(monkeypatch):
    fake_ai(monkeypatch, reply("Hanya untuk Kevin."))
    app = click(dashboard(username="kevin", ai_section=FREE_KEY), "run_CRM_Data CRM")
    assert "Hanya untuk Kevin." in texts(app.markdown)

    app.session_state[config.STATE_USERNAME] = "rina"
    app.run()

    assert "Hanya untuk Kevin." not in texts(app.markdown)
    assert saved_log("rina") == {}

    app.session_state[config.STATE_USERNAME] = "kevin"
    app.run()

    assert "Hanya untuk Kevin." in texts(app.markdown)


def test_each_user_gets_their_own_history_file(monkeypatch):
    fake_ai(monkeypatch, reply("Milik rina."))
    click(dashboard(username="rina", ai_section=FREE_KEY), "run_CRM_Data CRM")

    assert saved_log("rina")["CRM_Data CRM"]["text"] == "Milik rina."
    assert saved_log("kevin") == {}
