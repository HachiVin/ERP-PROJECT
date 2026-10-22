import pytest

from erp_dashboard import auth, config
from tests.conftest import PASSWORD


@pytest.fixture
def users(password_hash):
    return {"kevin": password_hash}


def test_correct_credentials_are_accepted(users):
    assert auth.verify_login(users, "kevin", PASSWORD)


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("kevin", "salah"),
        ("kevin", ""),
        ("", PASSWORD),
        ("orang-lain", PASSWORD),
        ("KEVIN", PASSWORD),
    ],
)
def test_wrong_credentials_are_rejected(users, username, password):
    assert not auth.verify_login(users, username, password)


def test_password_longer_than_bcrypt_limit_is_rejected_not_a_crash(users):
    assert not auth.verify_login(users, "kevin", "x" * 100)


def test_malformed_hash_is_rejected_not_a_crash():
    assert not auth.verify_login({"kevin": "bukan-hash-bcrypt"}, "kevin", PASSWORD)


def test_load_users_copies_a_mapping_into_a_plain_dict(password_hash):
    loaded = auth.load_users({"kevin": password_hash})
    assert loaded == {"kevin": password_hash}
    assert type(loaded) is dict


@pytest.mark.parametrize("bad_section", ["teks", None, 42, ["kevin"]])
def test_load_users_rejects_a_non_mapping_section(bad_section):
    with pytest.raises(auth.AuthConfigError):
        auth.load_users(bad_section)


def test_start_session_marks_the_user_logged_in():
    state: dict = {}
    auth.start_session(state, "kevin")
    assert state[config.STATE_LOGGED_IN] is True
    assert state[config.STATE_USERNAME] == "kevin"


def test_end_session_clears_all_per_user_state():
    state = {
        config.STATE_LOGGED_IN: True,
        config.STATE_USERNAME: "kevin",
        config.STATE_AI_SUGGESTIONS: {"CRM_Data CRM": {"text": "rahasia", "time": "x"}},
        config.STATE_AI_OWNER: "kevin",
        config.STATE_SELECTED_MODULE: "Sales",
    }
    auth.end_session(state)

    assert state[config.STATE_LOGGED_IN] is False
    assert state[config.STATE_USERNAME] == ""
    assert config.STATE_AI_SUGGESTIONS not in state
    assert config.STATE_AI_OWNER not in state
    assert config.STATE_SELECTED_MODULE not in state


def test_end_session_on_an_empty_state_does_not_fail():
    state: dict = {}
    auth.end_session(state)
    assert state[config.STATE_LOGGED_IN] is False
