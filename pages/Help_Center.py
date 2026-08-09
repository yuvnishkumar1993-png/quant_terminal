import streamlit as st

st.set_page_config(
    page_title="Help Center & Support Desk",
    page_icon="🛠️",
    layout="wide"
)

st.markdown("## 🛠️ Quant Terminal Pro - Help Center & Support Desk")
st.markdown("---")

st.markdown("""
### 📖 Quick User Guide & Instructions

1. **Dhan API Authentication:**
   - मुख्य पेज (`app.py`) पर जाएं और बाएं साइडबार में अपना **Client ID** और **Access Token** दर्ज करें। क्रेडेंशियल्स सेव होने पर ग्रीन इंडिकेटर दिखाई देगा।

2. **Master Option Chain (`1_Master_Option_Chain.py`):**
   - यहाँ से आप किसी भी एसेट (NIFTY, BANKNIFTY, SENSEX, RELIANCE आदि) को चुनकर लाइव ऑप्शन चेन, ग्रीक्स ($\Delta, \Gamma, \Theta, \nu$), GEX प्रोफाइल, और OI कंसंट्रेशन वॉल्स देख सकते हैं।

3. **Server-Synced Lot Size:**
   - लॉट साइज़ सीधे सर्वर (स्क्रीप मास्टर) से ऑटोमैटिकली सिंक होता है, जिसे आप ज़रूरत पड़ने पर साइडबार से ओवरराइड भी कर सकते हैं।

4. **Multi-Page Terminal Modules:**
   - **Graphical Terminal:** एडवांस्ड टेक्निकल और क्वांट चार्टिंग के लिए।
   - **Gamma Flip Gatekeeper:** ज़ीरो-गामा पिवट और मार्केट गेक्स एक्सपोजर ट्रैक करने के लिए।
   - **Quant Screener Bot:** हाई-प्रोबेबिलिटी ट्रेडिंग सेटअप और स्कैनर्स के लिए।
   - **Historical Time Travel:** पास्ट मार्केट डेटा और ऑप्शन बिहेवियर के बैकटेस्टिंग के लिए।
""")

st.markdown("---")
st.info("💡 यदि आपको लाइव डेटा फेच करने में कोई दिक्कत आ रही है, तो सुनिश्चित करें कि आपके Dhan API क्रेडेंशियल्स सही हैं और आपका इंटरनेट कनेक्शन सक्रिय है।")
