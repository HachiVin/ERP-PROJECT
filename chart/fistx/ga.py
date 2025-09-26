import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load GA Data ---
def load_ga_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "ga.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            ga_data = json.load(f)

        df_ga = pd.DataFrame([
            {
                "ID": ga.get("id", ""),
                "Name": ga.get("name", ""),
                "Category": ga.get("category", "Unknown"),
                "Amount": ga.get("amount", 0),
                "Currency": ga.get("currency_id", "Unknown"),
                "Responsible": ga.get("responsible_id", {}).get("name", "Unknown"),
                "State": ga.get("state", "Unknown"),
                "Date": ga.get("date", None)
            }
            for ga in ga_data
        ])

        df_ga["Date"] = pd.to_datetime(df_ga["Date"], errors="coerce")
        return df_ga.dropna(subset=["Date"])

    except Exception as e:
        st.error(f"⚠️ Gagal load data GA: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan GA ---
def ga_summary_table(df):
    st.dataframe(df, use_container_width=True)
