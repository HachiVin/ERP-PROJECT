"""Login verification and session bookkeeping. Free of Streamlit imports.

Accounts are defined in Streamlit secrets as ``username = "<bcrypt hash>"`` under ``[users]``.
There is no self-registration: secrets are read-only at runtime.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping

import bcrypt

from erp_dashboard import config


class AuthConfigError(ValueError):
    """Raised when the ``[users]`` secrets section is missing or malformed."""


def load_users(section: object) -> dict[str, str]:
    """Copy the ``[users]`` secrets section into a plain ``{username: bcrypt_hash}`` dict."""
    if not isinstance(section, Mapping):
        raise AuthConfigError("Bagian [users] di secrets harus berisi pasangan username = hash.")
    return {str(name): str(hashed) for name, hashed in section.items()}


def verify_login(users: Mapping[str, str], username: str, password: str) -> bool:
    """Return True only if ``username`` exists and ``password`` matches its bcrypt hash."""
    hashed = users.get(username)
    if not username or not password or hashed is None:
        return False
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        # Malformed hash, or a password longer than bcrypt's 72-byte limit.
        return False


def start_session(state: MutableMapping, username: str) -> None:
    """Mark ``username`` as logged in."""
    state[config.STATE_LOGGED_IN] = True
    state[config.STATE_USERNAME] = username


def end_session(state: MutableMapping) -> None:
    """Log out and drop every per-user value so the next login starts clean."""
    state[config.STATE_LOGGED_IN] = False
    state[config.STATE_USERNAME] = ""
    for key in (
        config.STATE_AI_SUGGESTIONS,
        config.STATE_AI_OWNER,
        config.STATE_SELECTED_MODULE,
    ):
        state.pop(key, None)
