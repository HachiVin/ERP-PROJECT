import streamlit as st
import bcrypt
import json
import os
from dotenv import load_dotenv, set_key

st.set_page_config(page_title="EPR Dashboard", layout="wide")

# --- Load ENV ---
load_dotenv()
users = st.secrets["users"]

# --- Session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- CSS Style ---
st.markdown("""
<style>
body, .stApp {background-color:#121212;color:#f5f5f5;font-family:'Segoe UI', Tahoma, Verdana, sans-serif;}
[data-testid="stSidebar"] {display:none;}
#MainMenu, footer {visibility:hidden;}
.header {text-align:center;color:#fff;background:linear-gradient(90deg,#ff7a18,#af002d 85%);
padding:16px;border-radius:10px;font-size:26px;font-weight:bold;margin-bottom:20px;box-shadow:0px 3px 12px rgba(0,0,0,0.4);}
.stButton > button {background:linear-gradient(135deg,#8d35d6,#5a0f9c);color:#fff;border:none;border-radius:8px;
height:60px;min-width:260px;width:100%;font-weight:600;font-size:15px;box-shadow:0px 3px 8px rgba(0,0,0,0.4);cursor:pointer;}
.stButton > button:hover {background:linear-gradient(135deg,#a64ce6,#6c12b8);transform:scale(1.03);transition:all 0.2s ease-in-out;}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<div class="header">Dashboard</div>', unsafe_allow_html=True)

def save_user(username, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = hashed
    os.environ["USERS"] = json.dumps(users)
    set_key(".env", "USERS", json.dumps(users))

def delete_user(username):
    if username in users:
        del users[username]
        os.environ["USERS"] = json.dumps(users)
        set_key(".env", "USERS", json.dumps(users))
        return True
    return False

# --- Login / Register / Admin ---
if not st.session_state.logged_in:
    tab_login, tab_register, tab_admin = st.tabs(["🔑 Login", "📝 Register", "👑 Admin Panel"])

    with tab_login:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if username in users and bcrypt.checkpw(password.encode(), users[username].encode()):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("✅ Login berhasil")
                st.rerun()
            else:
                st.error("❌ Username / Password salah")

    with tab_register:
        st.subheader("Registrasi")
        new_user = st.text_input("Username", key="reg_user")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Register"):
            if new_user in users:
                st.error("⚠️ Username sudah ada, pilih yang lain")
            elif new_user and new_pass:
                save_user(new_user, new_pass)
                st.success("✅ Registrasi berhasil, silakan login")
            else:
                st.error("⚠️ Username & Password harus diisi")

    with tab_admin:
        st.subheader("👑 Admin Panel")

        if users:
            st.write("📋 **Daftar Akun Terdaftar**:")
            for u in users.keys():
                st.write(f"- {u}")

            del_user = st.text_input("Masukkan username yang ingin dihapus:")
            if st.button("Hapus Akun"):
                if delete_user(del_user):
                    st.success(f"✅ Akun {del_user} berhasil dihapus")
                else:
                    st.error("❌ Akun tidak ditemukan")
        else:
            st.warning("Belum ada akun yang registrasi.")

else:

    st.markdown(f"Halo, **{st.session_state.username}** 👋")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.markdown("Pilih Perusahaan:")

    companies = [
        "FisTx", "Maximus", "MSMB", "Widya Life Science", "Widya Genomic",
        "Sandhiguna", "Robotic", "BCK", "Widya Anaytic", "Lectro", "SEIA"
    ]

    cols = st.columns(4, gap="small")
    for i, company in enumerate(companies):
        with cols[i % 4]:
            if st.button(company, key=f"btn_{company}"):
                if company == "FisTx":
                    st.switch_page("pages/dashboard_fistx.py") 
                else:
                    st.warning(f"Halaman untuk {company} belum dibuat 🚧")
