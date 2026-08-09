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
st.write("👉 **निर्देश:** बाएं हाथ के **Sidebar** में अपने **Dhan API Login Credentials** दर्ज करें, जिससे पूरा टर्मिनल लाइव डेटा फेچ कर सके।")

# Initialize Session State for Login Credentials
if "client_id" not in st.session_state:
    st.session_state.client_id = ""
if "access_token" not in st.session_state:
    st.session_state.access_token = ""
if "global_symbol" not in st.session_state:
    st.session_state.global_symbol = "NIFTY"

# 🔐 Sidebar Login Credentials Section
st.sidebar.markdown("### 🔐 Dhan API Login Credentials")
st.sidebar.markdown("अपने ब्रोकर अकाउंट की डिटेल्स भरें:")

client_id_input = st.sidebar.text_input("Client ID", value=st.session_state.client_id, type="default")
access_token_input = st.sidebar.text_input("Access Token", value=st.session_state.access_token, type="password")

# Save credentials to session state dynamically
if client_id_input:
    st.session_state.client_id = client_id_input.strip()
if access_token_input:
    st.session_state.access_token = access_token_input.strip()

# Connection Status Badge in Sidebar
if st.session_state.client_id and st.session_state.access_token:
    st.sidebar.success("🟢 API Connected & Saved")
else:
    st.sidebar.warning("🟡 Awaiting Credentials Setup")

st.sidebar.markdown("---")
all_symbols = ["NIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "RELIANCE", "TCS", "SBIN"]
st.session_state.global_symbol = st.sidebar.selectbox(
    "Select Global Asset", 
    all_symbols, 
    index=all_symbols.index(st.session_state.global_symbol) if st.session_state.global_symbol in all_symbols else 0
)

st.sidebar.markdown("---")
st.sidebar.info("💡 क्रेडेंशियल्स दर्ज करने के बाद अब आप साइडबार से किसी भी पेज पर जाकर लाइव डेटा एक्सेस कर सकते हैं।")
