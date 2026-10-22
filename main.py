"""Entry point: log in, then pick a company. Page layout and interaction only."""

from __future__ import annotations

import streamlit as st

from erp_dashboard import auth, config, ui

st.set_page_config(page_title=config.APP_TITLE, layout="wide")

COLUMNS_PER_ROW = 4


def load_users() -> dict[str, str]:
    """Read accounts from Streamlit secrets, or stop the page with a clear message."""
    try:
        return auth.load_users(st.secrets["users"])
    except (KeyError, FileNotFoundError, auth.AuthConfigError):
        st.error(
            "⚠️ Akun belum dikonfigurasi. Tambahkan bagian [users] di Streamlit secrets "
            "(lihat README)."
        )
        st.stop()


def render_login(users: dict[str, str]) -> None:
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        if auth.verify_login(users, username, password):
            auth.start_session(st.session_state, username)
            st.rerun()
        else:
            st.error("❌ Username / Password salah")


def render_company_picker() -> None:
    st.markdown(f"Halo, **{st.session_state[config.STATE_USERNAME]}** 👋")
    if st.button("Logout"):
        auth.end_session(st.session_state)
        st.rerun()

    st.markdown("Pilih Perusahaan:")
    columns = st.columns(COLUMNS_PER_ROW, gap="small")
    for index, (company, page) in enumerate(config.COMPANIES.items()):
        with columns[index % COLUMNS_PER_ROW]:
            if st.button(company, key=f"btn_{company}"):
                if page:
                    st.switch_page(page)
                else:
                    st.warning(f"Halaman untuk {company} belum dibuat 🚧")


def main() -> None:
    ui.apply_theme(ui.HOME_THEME)
    ui.render_header("Dashboard")
    users = load_users()

    if st.session_state.get(config.STATE_LOGGED_IN):
        render_company_picker()
    else:
        render_login(users)


main()
