import os
import streamlit as st
from dhan_api_engine import InstitutionalDataEngine

st.set_page_config(
    page_title="Institutional Quant Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("## 🌑 Institutional Quant Terminal (Master Core)")
st.markdown("---")
st.write("### 🚀 Welcome to the Institutional Multi-Page Desk")
st.write("👉 **निर्देश:** लाइव डेटा फेच करने के लिए बाएं साइडबार में अपना **Dhan API Client ID** और **Access Token** दर्ज करें (एक बार लॉगिन करने पर यह 24 घंटे तक सुरक्षित रहेगा)। इसके बाद किसी भी मॉड्यूल को एक्सेस करने के लिए साइडबार से पेज चुनें।")

# ==========================================================
# 1. LOAD PERSISTENT SESSION (From Backend Engine)
# ==========================================================
saved_client, saved_token = InstitutionalDataEngine.load_api_session()

# ==========================================================
# 2. INITIALIZE SESSION STATE
# ==========================================================
if "client_id" not in st.session_state:
    st.session_state.client_id = saved_client if saved_client else ""
if "access_token" not in st.session_state:
    st.session_state.access_token = saved_token if saved_token else ""
if "global_symbol" not in st.session_state:
    st.session_state.global_symbol = "NIFTY"

# ==========================================================
# 3. PROFESSIONAL SIDEBAR LOGIN & GATEWAY
# ==========================================================
st.sidebar.markdown("### 🔐 Broker Authentication")
st.sidebar.markdown("Dhan API Secure Gateway")

# कंडीशन: अगर सिस्टम के पास Keys नहीं हैं, तभी फॉर्म दिखाओ
if not saved_client or not saved_token:
    with st.sidebar.form("dhan_login_form"):
        client_id_input = st.text_input("Client ID", value="")
        access_token_input = st.text_input("Access Token", type="password", value="")
        login_submitted = st.form_submit_button("Connect & Save Credentials", use_container_width=True)

    if login_submitted:
        if client_id_input.strip() and access_token_input.strip():
            # इंजन के जरिए क्रेडेंशियल्स को 24 घंटे के लिए JSON में सेव करें
            success = InstitutionalDataEngine.save_api_session(client_id_input.strip(), access_token_input.strip())
            if success:
                st.session_state.client_id = client_id_input.strip()
                st.session_state.access_token = access_token_input.strip()
                st.sidebar.success("✅ Credentials secured for 24 Hours!")
                st.rerun() # UI को तुरंत रिफ्रेश करो ताकि फॉर्म गायब हो जाए
        else:
            st.sidebar.warning("⚠️ Please enter both Client ID and Token.")
else:
    # अगर Keys पहले से मौजूद हैं, तो सीधा Connected स्टेटस और Logout बटन दिखाओ
    st.sidebar.success(f"🟢 API Status: Connected\n\n👤 **User ID:** {saved_client}")
    
    if st.sidebar.button("Logout / Clear Session", use_container_width=True):
        # JSON फाइल को डिलीट करें और सेशन रीसेट करें
        if os.path.exists(InstitutionalDataEngine.AUTH_FILE):
            os.remove(InstitutionalDataEngine.AUTH_FILE)
        st.session_state.client_id = ""
        st.session_state.access_token = ""
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 बाएं दिए गए पेज नेविगेशन से किसी भी टर्मिनल मॉड्यूल (Master Option Chain, Graphical Terminal, आदि) पर जाएं।")
