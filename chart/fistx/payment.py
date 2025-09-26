import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load Payment Data ---
def load_payment_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "payment.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payment_data = json.load(f)

        df_payment = pd.DataFrame([
            {
                "ID": pay.get("id", ""),
                "Payment": pay.get("name", ""),
                "Date": pay.get("date", None),
                "Customer/Vendor": pay.get("partner_id", {}).get("name", "Unknown"),
                "Amount": pay.get("amount", 0),
                "Currency": pay.get("currency_id", ""),
                "Type": pay.get("payment_type", ""),
                "Journal": pay.get("journal_id", ""),
                "Status": pay.get("state", ""),
                "Reference": pay.get("ref", "")
            }
            for pay in payment_data
        ])

        # Konversi Date
        df_payment["Date"] = pd.to_datetime(df_payment["Date"], errors="coerce")
        return df_payment

    except Exception as e:
        st.error(f"⚠️ Gagal load data Payment: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan Payment ---
def payment_summary_table(df):
    st.dataframe(df, use_container_width=True)
