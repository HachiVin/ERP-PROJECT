import pandas as pd
import json
import streamlit as st
import matplotlib.pyplot as plt
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

# --- Pie Chart: Distribusi Stage ---
def crm_stage_distribution_chart(df):
    fig, ax = plt.subplots()
    stage_count = df["Stage"].value_counts()
    ax.pie(stage_count, labels=stage_count.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("Distribusi Stage CRM")
    st.pyplot(fig)
    plt.close(fig)

# --- Bar Chart: Revenue per Salesperson ---
def crm_revenue_by_salesperson_chart(df):
    fig, ax = plt.subplots()
    df.groupby("Salesperson")["Revenue"].sum().plot(kind="bar", ax=ax)
    ax.set_title("Revenue per Salesperson")
    ax.set_ylabel("Total Revenue")
    st.pyplot(fig)
    plt.close(fig)

# --- Line Chart: Tren Revenue per Tanggal ---
def crm_trend_chart(df):
    fig, ax = plt.subplots()
    df.groupby("Created")["Revenue"].sum().plot(kind="line", marker="o", ax=ax)
    ax.set_title("Tren Revenue CRM per Tanggal")
    ax.set_ylabel("Total Revenue")
    st.pyplot(fig)
    plt.close(fig)
