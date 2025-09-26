import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load Credit Data ---
def load_credit_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "credit.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            credit_data = json.load(f)

        df_credit = pd.DataFrame([
            {
                "ID": c.get("id", ""),
                "Credit Ref": c.get("name", ""),
                "Customer": c.get("partner_id", {}).get("name", "Unknown"),
                "Credit Limit": c.get("credit_limit", 0),
                "Outstanding Amount": c.get("outstanding_amount", 0),
                "Currency": c.get("currency_id", "USD"),
                "Status": c.get("status", "Unknown")
            }
            for c in credit_data
        ])

        return df_credit

    except Exception as e:
        st.error(f"⚠️ Gagal load data Credit: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan Credit ---
def credit_summary_table(df):
    st.dataframe(df, use_container_width=True)
