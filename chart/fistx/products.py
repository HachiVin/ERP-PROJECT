import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load Products Data ---
def load_products_data():
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "products.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            products_data = json.load(f)

        df_products = pd.DataFrame([
            {
                "ID": product.get("id", ""),
                "Name": product.get("name", ""),
                "UoM": product.get("uom", "Unit"),
                "Price": product.get("price", 0.0)
            }
            for product in products_data
        ])

        return df_products

    except Exception as e:
        st.error(f"⚠️ Gagal load data Products: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan Products ---
def products_summary_table(df):
    st.dataframe(df, use_container_width=True)
