import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load Purchase Data ---
def load_purchase_data():
    base_dir = Path(__file__).resolve().parent.parent.parent 
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "purchase.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            purchase_data = json.load(f)

        df_purchase = pd.DataFrame([
            {
                "ID": po.get("id", ""),
                "PO Number": po.get("name", ""),
                "Date": po.get("date_order", None),
                "Vendor": po.get("partner_id", {}).get("name", "Unknown"),
                "Product": line.get("product_id", {}).get("name", "Unknown"),
                "Quantity": line.get("product_qty", 0),
                "Price Unit": line.get("price_unit", 0),
                "Subtotal": line.get("price_subtotal", 0),
                "Amount Untaxed": po.get("amount_untaxed", 0),
                "Tax": po.get("amount_tax", 0),
                "Total": po.get("amount_total", 0),
                "Status": po.get("state", "Unknown")
            }
            for po in purchase_data
            for line in po.get("order_line", [])
        ])

        df_purchase["Date"] = pd.to_datetime(df_purchase["Date"], errors="coerce")
        return df_purchase.dropna(subset=["Date"])

    except Exception as e:
        st.error(f"⚠️ Gagal load data Purchase: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan Purchase ---
def purchase_summary_table(df):
    st.dataframe(df, use_container_width=True)
