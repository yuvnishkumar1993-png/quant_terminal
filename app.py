# app.py
import streamlit as st

st.set_page_config(
    page_title="Institutional Quant Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("## 🌑 Institutional Quant Terminal (Master Core)")
st.markdown("---")
st.write("### 🚀 Welcome to the Institutional Multi-Page Desk")
st.write("👉 **निर्देश:** लाइव डेटा फेच करने के लिए बाएं साइडबार में अपना **Dhan API Client ID** और **Access Token** दर्ज करें। इसके बाद किसी भी मॉड्यूल को एक्सेस करने के लिए साइडबार से पेज चुनें।")

# Initialize Session State
if "client_id" not in st.session_state:
    st.session_state.client_id = ""
if "access_token" not in st.session_state:
    st.session_state.access_token = ""
if "global_symbol" not in st.session_state:
    st.session_state.global_symbol = "NIFTY"

# 🔐 Professional Sidebar Login Section
st.sidebar.markdown("### 🔐 Broker Authentication")
st.sidebar.markdown("Dhan API Secure Gateway")

with st.sidebar.form("dhan_login_form"):
    client_id_input = st.text_input("Client ID", value=st.session_state.client_id, type="default")
    access_token_input = st.text_input("Access Token", value=st.session_state.access_token, type="password")
    login_submitted = st.form_submit_button("Connect & Save Credentials", use_container_width=True)

if login_submitted:
    st.session_state.client_id = client_id_input.strip()
    st.session_state.access_token = access_token_input.strip()
    st.success("Credentials updated successfully!")

# Connection Status Badge in Sidebar
st.sidebar.markdown("---")
if st.session_state.client_id and st.session_state.access_token:
    st.sidebar.success("🟢 API Status: Connected")
else:
    st.sidebar.warning("🟡 API Status: Awaiting Login")

st.sidebar.markdown("---")
st.sidebar.info("💡 बाएं दिए गए पेज नेविगेशन से किसी भी टर्मिनल मॉड्यूल (Master Option Chain, Graphical Terminal, आदि) पर जाएं।")
