"""FisTx dashboard: pick a module, view a table or chart, and request an AI insight.

Page layout and interaction only; loading, charts and the AI call live in ``erp_dashboard``.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from erp_dashboard import ai, config, ui
from erp_dashboard.loaders import DataLoadError
from erp_dashboard.modules import MODULES, MODULES_BY_NAME, ModuleSpec, View

load_dotenv()  # Local development only; on Streamlit Cloud the values come from st.secrets.


def get_ai_settings() -> ai.AISettings | None:
    try:
        section = st.secrets["openrouter"]
    except (KeyError, FileNotFoundError):
        section = None
    return ai.resolve_settings(os.environ, section)


def user_suggestions(store: ai.AILogStore, username: str) -> dict[str, Any]:
    """AI history of the logged-in user, reloaded whenever a different user is logged in."""
    if st.session_state.get(config.STATE_AI_OWNER) != username:
        st.session_state[config.STATE_AI_SUGGESTIONS] = store.load(username)
        st.session_state[config.STATE_AI_OWNER] = username
    return st.session_state[config.STATE_AI_SUGGESTIONS]


def select_view(spec: ModuleSpec) -> View:
    labels = [view.label for view in spec.views]
    choice = st.selectbox("Pilih visualisasi:", labels, key=f"view_{spec.name}")
    return spec.views[labels.index(choice)]


def render_view(view: View, df: pd.DataFrame) -> None:
    if view.chart is None:
        st.dataframe(df, use_container_width=True)
    else:
        st.pyplot(view.chart(df))


def request_insight(
    spec: ModuleSpec,
    df: pd.DataFrame,
    settings: ai.AISettings,
    key: str,
    store: ai.AILogStore,
    username: str,
    suggestions: dict[str, Any],
) -> None:
    """Call the model; store the result only on success so errors never look like insights."""
    with st.spinner("Memanggil AI..."):
        try:
            text = ai.generate_insight(settings, spec.name, df)
        except ai.AIError as exc:
            st.error(f"⚠️ Gagal memanggil AI: {exc}")
            return

    suggestions[key] = {"text": text, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    try:
        store.save(username, suggestions)
    except OSError:
        st.warning("Riwayat AI tidak dapat disimpan di server ini.")


def render_suggestion(suggestion: dict[str, str]) -> None:
    with st.container(border=True):
        st.markdown("**🤖 AI Suggestion:**")
        st.markdown(suggestion["text"])
        st.caption(f"🕒 Terakhir diperbarui: {suggestion['time']}")


def render_ai_block(
    spec: ModuleSpec,
    view: View,
    df: pd.DataFrame,
    settings: ai.AISettings | None,
    store: ai.AILogStore,
    username: str,
    suggestions: dict[str, Any],
) -> None:
    key = f"{spec.name}_{view.label}"
    sample_rows = min(config.AI_SAMPLE_ROWS, len(df))
    st.caption(f"ℹ️ AI hanya membaca {sample_rows} baris pertama dari {len(df)} baris data.")

    if settings is None:
        st.warning("⚠️ API Key OpenRouter belum diatur. Lihat bagian Konfigurasi di README.")
    else:
        run_column, refresh_column = st.columns(2)
        with run_column:
            run = st.button("🚀 Jalankan AI", use_container_width=True, key=f"run_{key}")
        with refresh_column:
            refresh = st.button(
                "🔄 Refresh Insight", use_container_width=True, key=f"refresh_{key}"
            )
        if run or refresh:
            request_insight(spec, df, settings, key, store, username, suggestions)

    if key in suggestions:
        render_suggestion(suggestions[key])


def main() -> None:
    username = ui.require_login()
    ui.apply_theme(ui.DASHBOARD_THEME)

    store = ai.AILogStore(config.AI_LOGS_DIR)
    suggestions = user_suggestions(store, username)
    settings = get_ai_settings()

    if st.button("⬅️ Kembali ke Dashboard", key="back_btn"):
        st.switch_page("main.py")
    ui.render_header("FisTx")

    names = [module.name for module in MODULES]
    st.session_state.setdefault(config.STATE_SELECTED_MODULE, config.DEFAULT_MODULE)
    st.subheader("Pilih Modul")
    selected = st.selectbox(
        "Pilih modul:", names, index=names.index(st.session_state[config.STATE_SELECTED_MODULE])
    )
    st.session_state[config.STATE_SELECTED_MODULE] = selected
    spec = MODULES_BY_NAME[selected]

    try:
        df = spec.load(config.FISTX_DATA_DIR)
    except DataLoadError as exc:
        st.error(f"❌ {exc}")
        return
    if df.empty:
        st.warning(f"⚠️ Data {spec.name} kosong atau gagal dimuat.")
        return

    main_column, ai_column = st.columns([2, 1], gap="large")
    with main_column:
        st.subheader(f"Data {spec.name}")
        view = select_view(spec)
        render_view(view, df)
    with ai_column:
        st.subheader("AI Suggestion")
        render_ai_block(spec, view, df, settings, store, username, suggestions)


main()
