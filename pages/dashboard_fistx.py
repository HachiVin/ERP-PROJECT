import streamlit as st 
import chart.fistx.crm as fx_crm 
import chart.fistx.sales as fx_sales
import chart.fistx.finance as fx_finance
import chart.fistx.inventory as fx_inventory 
import chart.fistx.purchase as fx_purchase
import chart.fistx.payment as fx_payment
import chart.fistx.credit as fx_credit
import chart.fistx.hr as fx_hr
import chart.fistx.ga as fx_ga
import chart.fistx.partners as fx_partners
import chart.fistx.products as fx_products
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# --- Load ENV ---
load_dotenv()

API_KEY = (
    os.getenv("OPENROUTER_API_KEY") 
    or st.secrets["openrouter"]["api_key"]
)
MODEL_ID = (
    os.getenv("OPENROUTER_MODEL") 
    or st.secrets["openrouter"].get("model", "openai/gpt-oss-20b:free")
)

if not API_KEY:
    st.error("⚠️ API Key tidak ditemukan.")
    st.stop()

# --- Path logs AI ---
BASE_DIR = Path(__file__).resolve().parent.parent
AI_LOGS_DIR = BASE_DIR / "ai_logs"
AI_LOGS_DIR.mkdir(exist_ok=True)

def get_user_log_file(username: str):
    return AI_LOGS_DIR / f"{username}_ai_suggestions.json"

def load_ai_suggestions(username: str):
    file_path = get_user_log_file(username)
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_ai_suggestions(username: str, data: dict):
    file_path = get_user_log_file(username)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Proteksi login ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Kamu harus login dulu.")
    st.stop()

username = st.session_state.get("username", "")
if not username:
    st.error("⚠️ Username tidak ditemukan.")
    st.stop()

if "ai_suggestions" not in st.session_state:
    st.session_state.ai_suggestions = load_ai_suggestions(username)

if "selected_module" not in st.session_state:
    st.session_state.selected_module = "CRM"

# --- CSS ---
st.markdown("""<style>
body, .stApp {background-color:#121212;color:#f5f5f5;font-family:'Segoe UI',Tahoma,Verdana,sans-serif;}
[data-testid="stSidebar"] { display:none; }
#MainMenu, footer {visibility:hidden;}
.header {text-align:center;color:#fff;background:linear-gradient(90deg,#ff7a18,#af002d 85%);
padding:16px;border-radius:10px;font-size:22px;font-weight:bold;margin-bottom:20px;box-shadow:0px 3px 12px rgba(0,0,0,0.4);}
.stButton > button {background:linear-gradient(135deg,#8d35d6,#5a0f9c);color:#fff;border:none;border-radius:8px;
padding:12px 20px;font-weight:600;font-size:15px;box-shadow:0px 3px 8px rgba(0,0,0,0.4);cursor:pointer;}
.stButton > button:hover {background:linear-gradient(135deg,#a64ce6,#6c12b8);transform:scale(1.03);transition:all 0.2s ease-in-out;}
</style>""", unsafe_allow_html=True)

# --- Header ---
if st.button("⬅️ Kembali ke Dashboard", key="back_btn"):
    st.switch_page("main.py")

st.markdown('<div class="header">FisTx</div>', unsafe_allow_html=True)

modules = ["CRM", "Sales", "Finance", "Inventory", "Purchase", "Payment","Partners", "Products", "Credit", "HR", "GA"]
st.subheader("Pilih Modul")
selected_module = st.selectbox("Pilih modul:", modules, index=modules.index(st.session_state.selected_module))
st.session_state.selected_module = selected_module

# --- Fungsi AI ---
def get_ai_suggestion(module_name, df_head):
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=API_KEY
        )
        prompt = f"Analisa data untuk modul {module_name}. Berikut sample data:\n{df_head.to_string(index=False)}\n\nJawaban ringkas (maks 120 kata)."
        resp = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "You are an AI assistant for ERP data analysis."},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ Gagal memanggil AI: {e}"

# --- Layout ---
col1, col2 = st.columns([2, 1], gap="large")

def show_ai_block(module_name, selected_visual, df):
    suggestion_key = f"{module_name}_{selected_visual}"
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Jalankan AI", use_container_width=True, key=f"run_{module_name}_{selected_visual}"):
            suggestion = get_ai_suggestion(module_name, df.head())
            st.session_state.ai_suggestions[suggestion_key] = {
                "text": suggestion,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_ai_suggestions(username, st.session_state.ai_suggestions)
    with col_btn2:
        if st.button("🔄 Refresh Insight", use_container_width=True, key=f"refresh_{module_name}_{selected_visual}"):
            suggestion = get_ai_suggestion(module_name, df.head())
            st.session_state.ai_suggestions[suggestion_key] = {
                "text": suggestion,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_ai_suggestions(username, st.session_state.ai_suggestions)

    if suggestion_key in st.session_state.ai_suggestions:
        suggestion_data = st.session_state.ai_suggestions[suggestion_key]
        st.markdown(f"""
        <div style="background:#222;padding:15px;border-radius:10px;
                    box-shadow:0px 3px 8px rgba(0,0,0,0.5);margin-top:10px">
            <b>🤖 AI Suggestion:</b><br>
            {suggestion_data["text"]}<br><br>
            <small>🕒 Terakhir diperbarui: {suggestion_data["time"]}</small>
        </div>
        """, unsafe_allow_html=True)

# --- Modul CRM ---
if selected_module == "CRM":
    df = fx_crm.load_crm_data()
    if not df.empty:
        with col1:
            st.subheader("Data CRM")
            visual_options = [
                "Data CRM", 
                "Distribusi Stage", 
                "Revenue per Salesperson", 
                "Tren Revenue"
            ]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)
            
            if selected_visual == "Data CRM":
                fx_crm.crm_summary_table(df)
            elif selected_visual == "Distribusi Stage":
                fx_crm.crm_stage_distribution_chart(df)
            elif selected_visual == "Revenue per Salesperson":
                fx_crm.crm_revenue_by_salesperson_chart(df)
            elif selected_visual == "Tren Revenue":
                fx_crm.crm_trend_chart(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("CRM", selected_visual, df)
    else:
        st.warning("⚠️ Data CRM kosong atau gagal dimuat.")


# --- Modul Sales ---
elif selected_module == "Sales":
    df = fx_sales.load_sales_data()
    if not df.empty:
        with col1:
            st.subheader("Data Sales")
            visual_options = ["Data Sales", "Performa Sales", "Tren Penjualan", "Distribusi Status Order"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)
            if selected_visual == "Data Sales":
                fx_sales.sales_summary_table(df)
            elif selected_visual == "Performa Sales":
                fx_sales.sales_by_salesperson_chart(df)
            elif selected_visual == "Tren Penjualan":
                fx_sales.sales_trend_chart(df)
            elif selected_visual == "Distribusi Status Order":
                fx_sales.sales_status_distribution_chart(df)
        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("Sales", selected_visual, df)

# --- Modul Finance ---
elif selected_module == "Finance":
    df = fx_finance.load_finance_data()
    if not df.empty:
        with col1:
            st.subheader("Data Finance")
            visual_options = ["Data Finance"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)
            
            if selected_visual == "Data Finance":
                fx_finance.finance_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("Finance", selected_visual, df)
    else:
        st.warning("⚠️ Data Finance kosong atau gagal dimuat.")

# --- Modul Inventory ---
elif selected_module == "Inventory":
    df = fx_inventory.load_inventory_data()
    if not df.empty:
        with col1:
            st.subheader("Data Inventory")
            visual_options = ["Data Inventory"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)
            
            if selected_visual == "Data Inventory":
                fx_inventory.inventory_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("Inventory", selected_visual, df)
    else:
        st.warning("⚠️ Data Inventory kosong atau gagal dimuat.")

# --- Modul Purchase ---
elif selected_module == "Purchase":
    df = fx_purchase.load_purchase_data()
    if not df.empty:
        with col1:
            st.subheader("Data Purchase")
            visual_options = ["Data Purchase"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)
            
            if selected_visual == "Data Purchase":
                fx_purchase.purchase_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("Purchase", selected_visual, df)
    else:
        st.warning("⚠️ Data Purchase kosong atau gagal dimuat.")

# --- Modul Partners ---
elif selected_module == "Partners":
    df = fx_partners.load_partners_data()
    if not df.empty:
        with col1:
            st.subheader("Data Partners")
            visual_options = ["Data Partners"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)

            if selected_visual == "Data Partners":
                fx_partners.partners_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("Partners", selected_visual, df)
    else:
        st.warning("⚠️ Data Partners kosong atau gagal dimuat.")

# --- Modul Products ---
elif selected_module == "Products":
    df = fx_products.load_products_data()
    if not df.empty:
        with col1:
            st.subheader("Data Products")
            visual_options = ["Data Products"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)

            if selected_visual == "Data Products":
                fx_products.products_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("Products", selected_visual, df)
    else:
        st.warning("⚠️ Data Products kosong atau gagal dimuat.")

# --- Modul Payment ---
elif selected_module == "Payment":
    df = fx_payment.load_payment_data()
    if not df.empty:
        with col1:
            st.subheader("Data Payment")
            visual_options = ["Data Payment"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)

            if selected_visual == "Data Payment":
                fx_payment.payment_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("Payment", selected_visual, df)
    else:
        st.warning("⚠️ Data Payment kosong atau gagal dimuat.")

# --- Modul Credit ---
elif selected_module == "Credit":
    df = fx_credit.load_credit_data()
    if not df.empty:
        with col1:
            st.subheader("Data Credit")
            visual_options = ["Data Credit"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)

            if selected_visual == "Data Credit":
                fx_credit.credit_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("Credit", selected_visual, df)
    else:
        st.warning("⚠️ Data Credit kosong atau gagal dimuat.")

# --- Modul HR ---
elif selected_module == "HR":
    df = fx_hr.load_hr_data()
    if not df.empty:
        with col1:
            st.subheader("Data HR")
            visual_options = ["Data HR"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)

            if selected_visual == "Data HR":
                fx_hr.hr_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("HR", selected_visual, df)
    else:
        st.warning("⚠️ Data HR kosong atau gagal dimuat.")

# --- Modul GA ---
elif selected_module == "GA":
    df = fx_ga.load_ga_data()
    if not df.empty:
        with col1:
            st.subheader("Data GA")
            visual_options = ["Data GA"]
            selected_visual = st.selectbox("Pilih visualisasi:", visual_options)

            if selected_visual == "Data GA":
                fx_ga.ga_summary_table(df)

        with col2:
            st.subheader("AI Suggestion")
            show_ai_block("GA", selected_visual, df)
    else:
        st.warning("⚠️ Data GA kosong atau gagal dimuat.")


# --- Modul lain masih placeholder ---
else:
    with col1:
        st.subheader(f"Modul {selected_module}")
        st.info("Visualisasi untuk modul ini masih dalam pengembangan 🚧")
    with col2:
        st.info("AI Suggestion belum tersedia 🚧")
