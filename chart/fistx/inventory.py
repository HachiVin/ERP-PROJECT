import pandas as pd
import json
import streamlit as st
from pathlib import Path

# --- Load Inventory Data ---
def load_inventory_data():
    base_dir = Path(__file__).resolve().parent.parent.parent 
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "inventory.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            inventory_data = json.load(f)

        df_inventory = pd.DataFrame([
            {
                "Reference": inv.get("reference", ""),
                "Date": inv.get("scheduled_date", None),
                "Customer": inv.get("partner_id", {}).get("name", "Unknown"),
                "Origin": inv.get("origin", ""),
                "Picking Type": inv.get("picking_type_code", ""),
                "Product": move.get("product_id", {}).get("name", "Unknown"),
                "Quantity": move.get("product_uom_qty", 0),
                "State": move.get("state", "Unknown"),
            }
            for inv in inventory_data
            for move in inv.get("move_line_ids", [])
        ])
        df_inventory["Date"] = pd.to_datetime(df_inventory["Date"], errors="coerce")
        return df_inventory.dropna(subset=["Date"])
    except Exception as e:
        st.error(f"⚠️ Gagal load data Inventory: {e}")
        return pd.DataFrame()

# --- Tabel Ringkasan Inventory ---
def inventory_summary_table(df):
    st.dataframe(df, use_container_width=True)
