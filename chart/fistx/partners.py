import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load Partners Data ---
def load_partners_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "partners.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            partners_data = json.load(f)

        df_partners = pd.DataFrame([
            {
                "ID": partner.get("id", ""),
                "Name": partner.get("name", ""),
                "Type": partner.get("type", "Unknown")
            }
            for partner in partners_data
        ])

        return df_partners

    except Exception as e:
        st.error(f"⚠️ Gagal load data Partners: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan Partners ---
def partners_summary_table(df):
    st.dataframe(df, use_container_width=True)
