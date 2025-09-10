import streamlit as st
import chart.fistx as fx  
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

# --- Load ENV ---
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_ID = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

# --- Path untuk simpan AI logs ---
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
    st.error("⚠️ Kamu harus login dulu untuk mengakses halaman ini.")
    st.stop()

if "username" not in st.session_state or not st.session_state.username:
    st.error("⚠️ Username tidak ditemukan, silakan login ulang.")
    st.stop()

username = st.session_state.username

if "ai_suggestions" not in st.session_state:
    st.session_state.ai_suggestions = load_ai_suggestions(username)

if "selected_module" not in st.session_state:
    st.session_state.selected_module = "CRM"

# --- CSS Style ---
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

# --- Dashboard ---
if st.button("⬅️ Kembali ke Dashboard", key="back_btn"):
    st.switch_page("main.py")

# --- Header ---
st.markdown('<div class="header">FisTx</div>', unsafe_allow_html=True)

# --- Modul list ---
modules = ["CRM", "Sales", "Inventory", "Purchase", "Finance", "Payment", "Credit", "HR", "GA"]
st.subheader("Pilih Modul")
selected_module = st.selectbox("Pilih salah satu modul:", modules, index=modules.index(st.session_state.selected_module))
st.session_state.selected_module = selected_module

# --- Fungsi AI Suggestion ---
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

if st.session_state.selected_module == "Sales":
    try:
        df_sales = fx.load_sales_data()  
        if not df_sales.empty:
            with col1:
                st.subheader("Data Modul: Sales")
                visual_options = ["Data Sales", "Performa Sales", "Tren Penjualan", "Distribusi Status Order"]
                selected_visual = st.selectbox("Pilih tampilan visualisasi:", visual_options)
                
                if selected_visual == "Data Sales":
                    fx.sales_summary_table(df_sales)
                elif selected_visual == "Performa Sales":
                    fx.sales_by_salesperson_chart(df_sales)
                elif selected_visual == "Tren Penjualan":
                    fx.sales_trend_chart(df_sales)
                elif selected_visual == "Distribusi Status Order":
                    fx.sales_status_distribution_chart(df_sales)
                    
            with col2:
                st.subheader("AI Suggestion")
                suggestion_key = f"Sales_{selected_visual}"
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🚀 Jalankan AI", use_container_width=True):
                        suggestion = get_ai_suggestion("Sales", df_sales.head())
                        st.session_state.ai_suggestions[suggestion_key] = {
                            "text": suggestion,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        save_ai_suggestions(username, st.session_state.ai_suggestions)
                with col_btn2:
                    if st.button("🔄 Refresh Insight", use_container_width=True):
                        suggestion = get_ai_suggestion("Sales", df_sales.head())
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
    except Exception as e:
        st.error(f"⚠️ Gagal load data Sales: {e}")
else:
    with col1:
        st.subheader(f"ini adalah visualisasi {st.session_state.selected_module}")
    with col2:
        st.info(f"AI untuk modul {st.session_state.selected_module} masih placeholder 🚧")
