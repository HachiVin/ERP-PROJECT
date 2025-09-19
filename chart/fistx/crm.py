import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load CRM Data ---
def load_crm_data():
    base_dir = Path(__file__).resolve().parent.parent.parent 
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "crm.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            crm_data = json.load(f)

        df_crm = pd.DataFrame([
            {
                "ID": crm.get("id", ""),
                "Opportunity": crm.get("name", ""),
                "Stage": crm.get("stage_id", "Unknown"),
                "Revenue": crm.get("expected_revenue", 0),
                "Probability": crm.get("probability", 0),
                "Customer": crm.get("partner_id", {}).get("name", "Unknown"),
                "Salesperson": crm.get("user_id", {}).get("name", "Unknown"),
                "Created": crm.get("create_date", None)
            }
            for crm in crm_data
        ])

        df_crm["Created"] = pd.to_datetime(df_crm["Created"], errors="coerce")
        return df_crm.dropna(subset=["Created"])

    except Exception as e:
        st.error(f"⚠️ Gagal load data CRM: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan CRM ---
def crm_summary_table(df):
    st.dataframe(df, use_container_width=True)
