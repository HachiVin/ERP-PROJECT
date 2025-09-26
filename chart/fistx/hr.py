import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load HR Data ---
def load_hr_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "hr.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            hr_data = json.load(f)

        df_hr = pd.DataFrame([
            {
                "ID": h.get("id", ""),
                "Name": h.get("name", ""),
                "Job Title": h.get("job_title", "Unknown"),
                "Department": h.get("department_id", "Unknown"),
                "Email": h.get("work_email", ""),
                "Phone": h.get("work_phone", ""),
                "Status": h.get("status", "Unknown")
            }
            for h in hr_data
        ])

        return df_hr

    except Exception as e:
        st.error(f"⚠️ Gagal load data HR: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan HR ---
def hr_summary_table(df):
    st.dataframe(df, use_container_width=True)
