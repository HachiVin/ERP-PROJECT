import pandas as pd
import json
import streamlit as st
import matplotlib.pyplot as plt
from pathlib import Path

# --- Load Sales Data ---
def load_sales_data():
    base_dir = Path(__file__).resolve().parent.parent  
    data_dir = base_dir / "data" / "fistx"
    file_path = data_dir / "sales_orders_FisTx.json"

    if not file_path.exists():
        st.error(f"❌ File {file_path} tidak ditemukan")
        return pd.DataFrame()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sales_data = json.load(f)

        df_sales = pd.DataFrame([
            {
                "SO Number": so.get("name", ""),
                "Customer": so.get("partner_id", {}).get("name", "Unknown"),
                "Date": so.get("date_order", None),
                "Salesperson": so.get("sales_person", "Unknown"),
                "Amount": so.get("amount_total", 0),
                "Status": so.get("state", "Unknown")
            }
            for so in sales_data
        ])
        df_sales["Date"] = pd.to_datetime(df_sales["Date"], errors="coerce")
        return df_sales.dropna(subset=["Date"])
    except Exception as e:
        st.error(f"⚠️ Gagal load data Sales: {e}")
        return pd.DataFrame()


# --- Tabel Ringkasan Sales ---
def sales_summary_table(df):
    st.dataframe(df, use_container_width=True)


# --- Bar Chart: Sales per Salesperson ---
def sales_by_salesperson_chart(df):
    fig, ax = plt.subplots()
    df.groupby("Salesperson")["Amount"].sum().plot(kind="bar", ax=ax)
    ax.set_title("Sales per Salesperson")
    ax.set_ylabel("Total Amount")
    st.pyplot(fig)
    plt.close(fig)


# --- Line Chart: Tren Sales per Tanggal ---
def sales_trend_chart(df):
    fig, ax = plt.subplots()
    df.groupby("Date")["Amount"].sum().plot(kind="line", marker="o", ax=ax)
    ax.set_title("Tren Sales per Tanggal")
    ax.set_ylabel("Total Amount")
    st.pyplot(fig)
    plt.close(fig)


# --- Pie Chart: Distribusi Status Order ---
def sales_status_distribution_chart(df):
    fig, ax = plt.subplots()
    status_count = df["Status"].value_counts()
    ax.pie(status_count, labels=status_count.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("Distribusi Status Order")
    st.pyplot(fig)
    plt.close(fig)
