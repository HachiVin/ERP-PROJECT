import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load Finance Data ---
def load_finance_data():
    base_dir = Path(__file__).resolve().parent.parent.parent 
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "finance.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            finance_data = json.load(f)

        df_finance = pd.DataFrame([
            {
                "ID": inv.get("id", ""),
                "Invoice": inv.get("name", ""),
                "Date": inv.get("invoice_date", None),
                "Customer": inv.get("partner_id", {}).get("name", "Unknown"),
                "Untaxed": inv.get("amount_untaxed", 0),
                "Tax": inv.get("amount_tax", 0),
                "Total": inv.get("amount_total", 0),
                "Payment State": inv.get("payment_state", "Unknown"),
                "Currency": inv.get("currency_id", "Unknown"),
                "Origin": inv.get("invoice_origin", "")
            }
            for inv in finance_data
        ])

        df_finance["Date"] = pd.to_datetime(df_finance["Date"], errors="coerce")
        return df_finance.dropna(subset=["Date"])

    except Exception as e:
        st.error(f"⚠️ Gagal load data Finance: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan Finance ---
def finance_summary_table(df):
    st.dataframe(df, use_container_width=True)
