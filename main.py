import streamlit as st

st.set_page_config(page_title="EPR Dashboard", layout="wide")

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
    font-size: 26px;
    font-weight: bold;
    margin-bottom: 20px;
    box-shadow: 0px 3px 12px rgba(0,0,0,0.4);
}

.stButton > button {
    background: linear-gradient(135deg, #8d35d6, #5a0f9c);
    color: #fff;
    border: none;
    border-radius: 8px;
    height: 60px;           
    min-width: 260px;       
    width: 100%;            
    font-weight: 600;
    font-size: 15px;
    box-shadow: 0px 3px 8px rgba(0,0,0,0.4);
    cursor: pointer;
    overflow: hidden;       
    text-overflow: ellipsis;
    white-space: nowrap;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #a64ce6, #6c12b8);
    transform: scale(1.03);
    transition: all 0.2s ease-in-out;
}

</style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

st.markdown('<div class="header">Dashboard</div>', unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.subheader("🔑 Login terlebih dahulu")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")
        if login_btn:
            if username == "admin" and password == "123":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login berhasil ✅")
                st.rerun()
            else:
                st.error("Username / Password salah ❌")
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
                    st.switch_page("pages/fistx.py")
                else:
                    st.warning(f"Halaman untuk {company} belum dibuat 🚧")
