import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
import matplotlib.pyplot as plt

# --- Proteksi login ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Kamu harus login dulu untuk mengakses halaman ini.")
    st.stop()

if "selected_module" not in st.session_state:
    st.session_state.selected_module = "CRM"

# --- CSS Style ---
st.markdown("""
<style>
body, .stApp {
    background-color: #121212;
    color: #f5f5f5;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

[data-testid="stSidebar"] { display:none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.header {
    text-align: center;
    color: #ffffff;
    background: linear-gradient(90deg, #ff7a18, #af002d 85%);
    padding: 16px;
    border-radius: 10px;
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 20px;
    box-shadow: 0px 3px 12px rgba(0,0,0,0.4);
}

/* Tombol umum */
.stButton > button {
    background: linear-gradient(135deg, #8d35d6, #5a0f9c);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
    font-weight: 600;
    font-size: 15px;
    box-shadow: 0px 3px 8px rgba(0,0,0,0.4);
    cursor: pointer;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #a64ce6, #6c12b8);
    transform: scale(1.03);
    transition: all 0.2s ease-in-out;
}
</style>
""", unsafe_allow_html=True)

# --- Back to dashboard ---
if st.button("⬅️ Kembali ke Dashboard", key="back_btn"):
    st.switch_page("main.py")

# --- Header ---
st.markdown('<div class="header">FisTx</div>', unsafe_allow_html=True)

# --- Modul list ---
modules = ["CRM", "Sales", "Inventory", "Purchase", "Finance",
           "Payment", "Credit", "HR", "GA"]

st.subheader("Pilih Modul")
selected_module = st.selectbox(
    "Pilih salah satu modul:",
    modules,
    index=modules.index(st.session_state.selected_module)
)
st.session_state.selected_module = selected_module

# --- Placeholder konten per modul ---
module_contents = {
    "Inventory": ["📦 Placeholder Inventory: Stok Barang", "📦 Placeholder Inventory: Riwayat Gudang"],
    "Purchase": ["🛒 Placeholder Purchase: Daftar Pembelian", "🛒 Placeholder Purchase: Supplier Management"],
    "Finance": ["💰 Placeholder Finance: Laporan Keuangan", "💰 Placeholder Finance: Arus Kas"],
    "Payment": ["💳 Placeholder Payment: Daftar Transaksi", "💳 Placeholder Payment: Status Pembayaran"],
    "Credit": ["🏦 Placeholder Credit: Limit Kredit", "🏦 Placeholder Credit: Riwayat Pinjaman"],
    "HR": ["👥 Placeholder HR: Data Karyawan", "👥 Placeholder HR: Absensi"],
    "GA": ["🏢 Placeholder GA: Fasilitas Kantor", "🏢 Placeholder GA: Maintenance"]
}

base_dir = Path(__file__).resolve().parent.parent
data_dir = base_dir / "data"
file_path = data_dir / "sales_orders_FisTx.json"

col1, col2 = st.columns([2, 1], gap="large")

with col1:
    st.subheader(f"Data Modul: {st.session_state.selected_module}")
    # SALES
    if st.session_state.selected_module == "Sales":
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    sales_data = json.load(f)
                    
                df_sales = pd.DataFrame([
                    {
                        "SO Number": so["name"],
                        "Customer": so["partner_id"]["name"],
                        "Date": so["date_order"],
                        "Salesperson": so["sales_person"],
                        "Amount": so["amount_total"],
                        "Status": so["state"]
                    }
                    for so in sales_data
                ])
                
                visual_options = ["Data Sales", "Performa Sales", "Tren Penjualan", "Distribusi Status Order"]
                selected_visual = st.selectbox("Pilih tampilan visualisasi:", visual_options)
                
                if selected_visual == "Data Sales":
                    st.dataframe(df_sales, use_container_width=True)
                elif selected_visual == "Performa Sales":
                    sales_by_person = df_sales.groupby("Salesperson")["Amount"].sum()
                    fig1, ax1 = plt.subplots()
                    sales_by_person.plot(kind="bar", ax=ax1)
                    ax1.set_ylabel("Total Amount")
                    ax1.set_xlabel("Salesperson")
                    ax1.set_title("Performa Sales")
                    st.pyplot(fig1)
                elif selected_visual == "Tren Penjualan":
                    df_sales["Date"] = pd.to_datetime(df_sales["Date"], errors="coerce")
                    sales_by_date = df_sales.groupby("Date")["Amount"].sum()
                    fig2, ax2 = plt.subplots()
                    sales_by_date.plot(kind="line", marker="o", ax=ax2)
                    ax2.set_ylabel("Total Amount")
                    ax2.set_xlabel("Date")
                    ax2.set_title("Tren Penjualan")
                    st.pyplot(fig2)
                elif selected_visual == "Distribusi Status Order":
                    status_count = df_sales["Status"].value_counts()
                    fig3, ax3 = plt.subplots()
                    ax3.pie(status_count, labels=status_count.index, autopct="%1.1f%%", startangle=90)
                    ax3.set_title("Distribusi Status Order")
                    st.pyplot(fig3)
            except Exception as e:
                st.error(f"⚠️ Gagal load data Sales: {e}")
        else:
            st.error(f"❌ File {file_path} tidak ditemukan")
    
    # CRM
    elif st.session_state.selected_module == "CRM":
        st.subheader("ini adalah visualisasi CRM")
    # INVENTORY
    elif st.session_state.selected_module == "Inventory":
        st.subheader("ini adalah visualisasi Inventory")
    # PURCHASE
    elif st.session_state.selected_module == "Purchase":
        st.subheader("ini adalah visualisasi Purchase")
    # FINANCE
    elif st.session_state.selected_module == "Finance":
        st.subheader("ini adalah visualisasi Finance")
    # PAYMENT
    elif st.session_state.selected_module == "Payment":
        st.subheader("ini adalah visualisasi Payment")
    # CREDIT
    elif st.session_state.selected_module == "Credit":
        st.subheader("ini adalah visualisasi Credit")
    # HR
    elif st.session_state.selected_module == "HR":
        st.subheader("ini adalah visualisasi HR")
    # GA
    elif st.session_state.selected_module == "GA":
        st.subheader("ini adalah visualisasi GA")

    else:
        for content in module_contents.get(
            st.session_state.selected_module,
            [f"📄 Konten {st.session_state.selected_module} belum tersedia"]
        ):
            st.info(content)

    st.write("")
    if st.button("🚀 Jalankan AI", use_container_width=True):
        st.success(f"AI running untuk modul {st.session_state.selected_module}...")

with col2:
    st.subheader("AI Suggestion")
    st.markdown(f"""
    <div style="background:#222;padding:15px;border-radius:10px;
                box-shadow:0px 3px 8px rgba(0,0,0,0.5);margin-top:10px">
        <b>🤖 AI Suggestion:</b><br>
        Placeholder untuk modul <b>{st.session_state.selected_module}</b>
    </div>
    """, unsafe_allow_html=True)
