"""
Voice-First Multilingual Agricultural Assistant for Indian Farmers
Streamlit Frontend - frontend/app.py
"""

import streamlit as st
import requests
import os
import json
import time
from datetime import datetime

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ─────────────────────────────────────────────
# UI Strings (Marathi / Hindi)
# ─────────────────────────────────────────────
UI_STRINGS = {
    "mr": {
        "app_title": "🌾 शेतकरी सहाय्यक",
        "app_subtitle": "आपल्या शेताच्या प्रश्नांसाठी AI सहाय्य",
        "lang_label": "भाषा निवडा",
        "nav_chat": "💬 चॅट",
        "nav_mandi": "📊 मंडी भाव",
        "nav_weather": "🌦️ हवामान",
        "nav_admin": "📂 कागदपत्रे अपलोड करा",
        "question_label": "आपला प्रश्न येथे लिहा",
        "question_placeholder": "उदा: माझ्या कांद्याच्या पानावर पांढरे डाग आहेत, काय करावे?",
        "voice_label": "🎤 आवाज फाइल अपलोड करा (wav, mp3, ogg, m4a, webm)",
        "submit_btn": "✅ उत्तर मिळवा",
        "clear_btn": "🗑️ इतिहास साफ करा",
        "answer_label": "उत्तर",
        "sources_label": "स्रोत",
        "audio_label": "🔊 ऑडिओ उत्तर",
        "audio_download": "ऑडिओ डाउनलोड करा",
        "chat_history_label": "संभाषण इतिहास",
        "mandi_title": "📊 मंडी बाजारभाव",
        "commodity_label": "पीक निवडा",
        "market_label": "बाजार / राज्य",
        "fetch_mandi_btn": "भाव पाहा",
        "mandi_result_label": "बाजारभाव",
        "weather_title": "🌦️ हवामान माहिती",
        "location_label": "तुमचे गाव / शहर",
        "location_placeholder": "उदा: पुणे, नाशिक, औरंगाबाद",
        "fetch_weather_btn": "हवामान पाहा",
        "temp_label": "तापमान",
        "humidity_label": "आर्द्रता",
        "desc_label": "हवामान",
        "advisory_label": "शेती सल्ला",
        "admin_title": "📂 कागदपत्रे अपलोड करा",
        "upload_pdf_label": "PDF फाइल निवडा",
        "source_name_label": "स्रोताचे नाव (उदा: ICAR मार्गदर्शिका)",
        "topic_label": "विषय",
        "upload_btn": "अपलोड करा",
        "upload_success": "✅ कागदपत्र यशस्वीरित्या अपलोड झाले!",
        "upload_error": "❌ अपलोड अयशस्वी. पुन्हा प्रयत्न करा.",
        "connection_error": "⚠️ सर्व्हरशी जोडणी होऊ शकली नाही. कृपया नंतर प्रयत्न करा.",
        "loading": "प्रक्रिया सुरू आहे...",
        "you_label": "आपण",
        "assistant_label": "सहाय्यक",
        "no_history": "अद्याप कोणतेही संभाषण नाही.",
        "custom_commodity": "इतर (टाइप करा)",
        "topic_crop": "पीक",
        "topic_pest": "कीड / रोग",
        "topic_scheme": "सरकारी योजना",
        "topic_general": "सामान्य",
        "intent_label": "हेतू",
        "lang_detected": "भाषा ओळखली",
    },
    "hi": {
        "app_title": "🌾 किसान सहायक",
        "app_subtitle": "आपके खेत के सवालों के लिए AI सहायता",
        "lang_label": "भाषा चुनें",
        "nav_chat": "💬 चैट",
        "nav_mandi": "📊 मंडी भाव",
        "nav_weather": "🌦️ मौसम",
        "nav_admin": "📂 दस्तावेज़ अपलोड करें",
        "question_label": "अपना सवाल यहाँ लिखें",
        "question_placeholder": "उदा: मेरी प्याज की पत्तियों पर सफेद धब्बे हैं, क्या करूँ?",
        "voice_label": "🎤 आवाज फ़ाइल अपलोड करें (wav, mp3, ogg, m4a, webm)",
        "submit_btn": "✅ जवाब पाएं",
        "clear_btn": "🗑️ इतिहास साफ़ करें",
        "answer_label": "जवाब",
        "sources_label": "स्रोत",
        "audio_label": "🔊 ऑडियो जवाब",
        "audio_download": "ऑडियो डाउनलोड करें",
        "chat_history_label": "बातचीत का इतिहास",
        "mandi_title": "📊 मंडी बाज़ार भाव",
        "commodity_label": "फसल चुनें",
        "market_label": "मंडी / राज्य",
        "fetch_mandi_btn": "भाव देखें",
        "mandi_result_label": "बाज़ार भाव",
        "weather_title": "🌦️ मौसम जानकारी",
        "location_label": "आपका गाँव / शहर",
        "location_placeholder": "उदा: पुणे, नागपुर, औरंगाबाद",
        "fetch_weather_btn": "मौसम देखें",
        "temp_label": "तापमान",
        "humidity_label": "नमी",
        "desc_label": "मौसम",
        "advisory_label": "कृषि सलाह",
        "admin_title": "📂 दस्तावेज़ अपलोड करें",
        "upload_pdf_label": "PDF फ़ाइल चुनें",
        "source_name_label": "स्रोत का नाम (उदा: ICAR गाइड)",
        "topic_label": "विषय",
        "upload_btn": "अपलोड करें",
        "upload_success": "✅ दस्तावेज़ सफलतापूर्वक अपलोड हो गया!",
        "upload_error": "❌ अपलोड विफल। फिर से कोशिश करें।",
        "connection_error": "⚠️ सर्वर से कनेक्ट नहीं हो पाया। कृपया बाद में प्रयास करें।",
        "loading": "प्रक्रिया हो रही है...",
        "you_label": "आप",
        "assistant_label": "सहायक",
        "no_history": "अभी तक कोई बातचीत नहीं।",
        "custom_commodity": "अन्य (टाइप करें)",
        "topic_crop": "फसल",
        "topic_pest": "कीट / रोग",
        "topic_scheme": "सरकारी योजना",
        "topic_general": "सामान्य",
        "intent_label": "इरादा",
        "lang_detected": "भाषा पहचानी गई",
    },
}

COMMODITIES = [
    "Wheat / गेहूं / गहू",
    "Rice / चावल / तांदूळ",
    "Onion / प्याज / कांदा",
    "Tomato / टमाटर / टोमॅटो",
    "Cotton / कपास / कापूस",
    "Soybean / सोयाबीन",
    "Maize / मक्का",
    "Sugarcane / गन्ना / ऊस",
    "Groundnut / मूंगफली / शेंगदाणे",
    "Turmeric / हल्दी / हळद",
    "Chilli / मिर्च / मिरची",
    "Potato / आलू / बटाटा",
    "Garlic / लहसुन / लसूण",
    "Jowar / ज्वार",
    "Bajra / बाजरा",
]

STATES_MARKETS = [
    "Maharashtra - Pune",
    "Maharashtra - Nashik",
    "Maharashtra - Aurangabad",
    "Maharashtra - Nagpur",
    "Maharashtra - Kolhapur",
    "Maharashtra - Latur",
    "Maharashtra - Solapur",
    "Uttar Pradesh - Lucknow",
    "Uttar Pradesh - Kanpur",
    "Punjab - Amritsar",
    "Punjab - Ludhiana",
    "Rajasthan - Jaipur",
    "Madhya Pradesh - Bhopal",
    "Gujarat - Ahmedabad",
    "Karnataka - Bangalore",
    "Telangana - Hyderabad",
]

TOPICS_MAP = {
    "mr": {"crop": "topic_crop", "pest": "topic_pest", "scheme": "topic_scheme", "general": "topic_general"},
    "hi": {"crop": "topic_crop", "pest": "topic_pest", "scheme": "topic_scheme", "general": "topic_general"},
}

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="शेतकरी / किसान सहाय्यक",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS — Agricultural Theme
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Root palette ── */
    :root {
        --green-dark:   #2D6A4F;
        --green-mid:    #52B788;
        --green-light:  #95D5B2;
        --bg-warm:      #FEFAE0;
        --bg-light:     #F8F9FA;
        --text-dark:    #1B1B1B;
        --text-muted:   #555555;
    }

    /* ── Global background ── */
    .stApp { background-color: var(--bg-warm); }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background-color: var(--green-dark) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-size: 1.1rem;
        font-weight: 600;
    }

    /* ── Headings ── */
    h1, h2, h3 { color: var(--green-dark); }

    /* ── Primary button ── */
    .stButton > button {
        background-color: var(--green-dark) !important;
        color: white !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
        padding: 0.6rem 1.5rem !important;
        border: none !important;
        font-weight: 700 !important;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: var(--green-mid) !important;
        color: white !important;
    }

    /* ── Chat bubbles ── */
    .bubble-user {
        background: var(--green-mid);
        color: #fff;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        margin: 8px 0;
        margin-left: 20%;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    .bubble-assistant {
        background: #FFFFFF;
        color: var(--text-dark);
        border-radius: 18px 18px 18px 4px;
        padding: 12px 18px;
        margin: 8px 0;
        margin-right: 20%;
        font-size: 1.05rem;
        line-height: 1.6;
        border: 1px solid var(--green-light);
    }
    .bubble-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        margin-bottom: 2px;
        font-weight: 600;
    }
    .bubble-label-right { text-align: right; margin-right: 4px; }

    /* ── Answer box ── */
    .answer-box {
        background: #FFFFFF;
        border-left: 5px solid var(--green-mid);
        border-radius: 8px;
        padding: 16px 20px;
        margin: 10px 0;
        font-size: 1.1rem;
        line-height: 1.8;
        color: var(--text-dark);
        box-shadow: 0 2px 6px rgba(0,0,0,0.07);
    }

    /* ── Sources box ── */
    .sources-box {
        background: var(--bg-light);
        border-radius: 8px;
        padding: 10px 15px;
        margin: 6px 0;
        font-size: 0.95rem;
        border: 1px solid var(--green-light);
    }

    /* ── Weather card ── */
    .weather-card {
        background: linear-gradient(135deg, var(--green-dark), var(--green-mid));
        color: white;
        border-radius: 14px;
        padding: 24px 28px;
        font-size: 1.1rem;
        line-height: 2;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* ── Mandi table ── */
    .mandi-table { width: 100%; border-collapse: collapse; }
    .mandi-table th {
        background: var(--green-dark);
        color: white;
        padding: 10px 14px;
        text-align: left;
        font-size: 1rem;
    }
    .mandi-table td {
        padding: 9px 14px;
        border-bottom: 1px solid var(--green-light);
        font-size: 1rem;
    }
    .mandi-table tr:nth-child(even) { background: var(--bg-light); }

    /* ── Upload section ── */
    .upload-section {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        border: 2px dashed var(--green-mid);
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--green-dark);
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid var(--green-dark) !important;
        color: var(--green-dark) !important;
    }

    /* ── Input fields ── */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        font-size: 1.05rem !important;
        border-radius: 8px !important;
        border: 1.5px solid var(--green-light) !important;
    }

    /* ── File uploader ── */
    .stFileUploader {
        border: 2px dashed var(--green-mid) !important;
        border-radius: 10px !important;
        padding: 10px !important;
    }

    /* ── Info / warning banners ── */
    .stAlert { border-radius: 8px !important; }

    /* ── Spinner text ── */
    .stSpinner > div { color: var(--green-dark) !important; }

    /* ── Hide streamlit branding ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Session State Init
# ─────────────────────────────────────────────
if "language" not in st.session_state:
    st.session_state.language = "mr"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "last_response" not in st.session_state:
    st.session_state.last_response = None


def t(key):
    """Return the UI string for the current language."""
    lang = st.session_state.get("language", "mr")
    return UI_STRINGS.get(lang, UI_STRINGS["mr"]).get(key, key)


# ─────────────────────────────────────────────
# API Helpers
# ─────────────────────────────────────────────
def api_post(endpoint, payload=None, files=None, timeout=25):
    """POST to backend. Returns (data_dict, error_str)."""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if files:
            resp = requests.post(url, data=payload or {}, files=files, timeout=timeout)
        else:
            resp = requests.post(url, json=payload or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, t("connection_error")
    except requests.exceptions.Timeout:
        return None, "⏱️ Request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"❌ Error: {detail}"
    except Exception as e:
        return None, f"❌ Unexpected error: {str(e)}"


def api_get(endpoint, params=None, timeout=20):
    """GET from backend. Returns (data_dict, error_str)."""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        resp = requests.get(url, params=params or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, t("connection_error")
    except requests.exceptions.Timeout:
        return None, "⏱️ Request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"❌ Error: {detail}"
    except Exception as e:
        return None, f"❌ Unexpected error: {str(e)}"


def fetch_audio_bytes(audio_path):
    """Fetch audio bytes from backend static endpoint."""
    try:
        # audio_path is e.g. "audio/response_xyz.mp3"
        filename = os.path.basename(audio_path)
        url = f"{BACKEND_URL}/audio/{filename}"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.content, resp.headers.get("content-type", "audio/mpeg")
        return None, None
    except Exception:
        return None, None


# ─────────────────────────────────────────────
# Sidebar — Language & Navigation
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌾 कृषि सहाय्यक / किसान सहायक")
    st.markdown("---")

    # Language selector
    lang_choice = st.radio(
        "🌐 Language / भाषा",
        options=["mr", "hi"],
        format_func=lambda x: "🟠 मराठी" if x == "mr" else "🟢 हिंदी",
        index=0 if st.session_state.language == "mr" else 1,
        key="lang_radio",
    )
    if lang_choice != st.session_state.language:
        st.session_state.language = lang_choice
        st.rerun()

    st.markdown("---")

    # Navigation
    nav_options = [t("nav_chat"), t("nav_mandi"), t("nav_weather"), t("nav_admin")]
    nav_choice = st.radio("📋 Navigation", nav_options, index=0, key="nav_radio")

    st.markdown("---")
    st.markdown(
        f"""
        <div style='font-size:0.8rem; color:#ccc;'>
        🔗 Backend: <code style='color:#95D5B2'>{BACKEND_URL}</code><br>
        🕐 Session: <code style='color:#95D5B2'>{st.session_state.session_id[-8:]}</code>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# Helper: Render response
# ─────────────────────────────────────────────
def render_response(resp_data):
    """Render answer box, sources, and audio player from API response dict."""
    if not resp_data:
        return

    answer = resp_data.get("answer") or resp_data.get("response_text", "")
    sources = resp_data.get("sources", [])
    audio_path = resp_data.get("audio_path", "")
    detected_lang = resp_data.get("detected_lang", "")
    intent = resp_data.get("intent", "")

    # Meta tags
    meta_parts = []
    if detected_lang:
        meta_parts.append(f"**{t('lang_detected')}:** {detected_lang}")
    if intent:
        meta_parts.append(f"**{t('intent_label')}:** {intent}")
    if meta_parts:
        st.markdown(" &nbsp;|&nbsp; ".join(meta_parts))

    # Answer
    if answer:
        st.markdown(f"### {t('answer_label')}")
        st.markdown(
            f"<div class='answer-box'>{answer}</div>",
            unsafe_allow_html=True,
        )

    # Sources
    if sources:
        st.markdown(f"**📚 {t('sources_label')}:**")
        sources_html = "<div class='sources-box'><ul style='margin:0;padding-left:1.2rem;'>"
        for src in sources:
            if isinstance(src, dict):
                src_text = src.get("source", src.get("filename", str(src)))
                score = src.get("score", "")
                score_str = f" <em style='color:#888'>({score:.2f})</em>" if isinstance(score, float) else ""
                sources_html += f"<li>{src_text}{score_str}</li>"
            else:
                sources_html += f"<li>{src}</li>"
        sources_html += "</ul></div>"
        st.markdown(sources_html, unsafe_allow_html=True)

    # Audio
    if audio_path:
        st.markdown(f"#### {t('audio_label')}")
        audio_bytes, content_type = fetch_audio_bytes(audio_path)
        if audio_bytes:
            st.audio(audio_bytes, format=content_type or "audio/mpeg")
            st.download_button(
                label=f"⬇️ {t('audio_download')}",
                data=audio_bytes,
                file_name=os.path.basename(audio_path),
                mime=content_type or "audio/mpeg",
            )
        else:
            st.info("Audio file not yet available.")


# ─────────────────────────────────────────────
# Helper: Chat history bubbles
# ─────────────────────────────────────────────
def render_chat_history():
    history = st.session_state.chat_history
    if not history:
        st.info(t("no_history"))
        return

    for entry in history:
        role = entry.get("role", "user")
        text = entry.get("text", "")
        ts = entry.get("time", "")

        if role == "user":
            st.markdown(
                f"<div class='bubble-label bubble-label-right'>{t('you_label')} · {ts}</div>"
                f"<div class='bubble-user'>{text}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='bubble-label'>{t('assistant_label')} · {ts}</div>"
                f"<div class='bubble-assistant'>{text}</div>",
                unsafe_allow_html=True,
            )


def add_to_history(role, text):
    ts = datetime.now().strftime("%H:%M")
    st.session_state.chat_history.append({"role": role, "text": text, "time": ts})


# ─────────────────────────────────────────────
# PAGE: Main Chat
# ─────────────────────────────────────────────
def page_chat():
    lang = st.session_state.language
    st.markdown(f"# {t('app_title')}")
    st.markdown(f"<p style='color:#555; font-size:1.05rem;'>{t('app_subtitle')}</p>", unsafe_allow_html=True)
    st.markdown("---")

    col_input, col_history = st.columns([3, 2])

    with col_input:
        # Text question
        question = st.text_area(
            label=t("question_label"),
            placeholder=t("question_placeholder"),
            height=130,
            key="question_input",
        )

        # Voice file upload
        st.markdown(f"**{t('voice_label')}**")
        audio_file = st.file_uploader(
            label="Upload audio",
            type=["wav", "mp3", "ogg", "m4a", "webm"],
            label_visibility="collapsed",
            key="audio_uploader",
        )
        if audio_file:
            st.audio(audio_file, format=audio_file.type)

        col_btn, col_clear = st.columns([3, 1])
        with col_btn:
            submit = st.button(t("submit_btn"), key="submit_btn", use_container_width=True)
        with col_clear:
            clear = st.button(t("clear_btn"), key="clear_btn", use_container_width=True)

        if clear:
            st.session_state.chat_history = []
            st.session_state.last_response = None
            st.rerun()

        if submit:
            if not question.strip() and not audio_file:
                st.warning("कृपया एक प्रश्न लिहा किंवा आवाज अपलोड करा." if lang == "mr" else "कृपया एक सवाल लिखें या आवाज़ अपलोड करें।")
            else:
                with st.spinner(t("loading")):
                    if audio_file:
                        # Voice query
                        files = {"audio": (audio_file.name, audio_file.getvalue(), audio_file.type)}
                        payload = {"language": lang, "session_id": st.session_state.session_id}
                        data, err = api_post("/api/voice-query", payload=payload, files=files, timeout=25)
                    else:
                        # Text query
                        payload = {
                            "query": question.strip(),
                            "language": lang,
                            "session_id": st.session_state.session_id,
                        }
                        data, err = api_post("/api/query", payload=payload, timeout=25)

                if err:
                    st.error(err)
                elif data:
                    user_text = question.strip() if question.strip() else f"[{t('voice_label')}]"
                    add_to_history("user", user_text)
                    answer_text = data.get("answer") or data.get("response_text", "")
                    add_to_history("assistant", answer_text)
                    st.session_state.last_response = data
                    st.rerun()

        # Render last response
        if st.session_state.last_response:
            st.markdown("---")
            render_response(st.session_state.last_response)

    with col_history:
        st.markdown(f"### 📜 {t('chat_history_label')}")
        render_chat_history()


# ─────────────────────────────────────────────
# PAGE: Mandi Prices
# ─────────────────────────────────────────────
def page_mandi():
    st.markdown(f"# {t('mandi_title')}")
    st.markdown("---")

    all_commodities = COMMODITIES + [t("custom_commodity")]
    commodity_choice = st.selectbox(t("commodity_label"), all_commodities, key="commodity_select")

    if commodity_choice == t("custom_commodity"):
        commodity_input = st.text_input(
            "Custom commodity / पीक का नाम लिखें / पिकाचे नाव",
            key="custom_commodity_input",
        )
    else:
        commodity_input = commodity_choice.split("/")[0].strip()

    market_choice = st.selectbox(t("market_label"), STATES_MARKETS, key="market_select")
    state_part = market_choice.split("-")[0].strip()
    market_part = market_choice.split("-")[1].strip() if "-" in market_choice else market_choice

    fetch_btn = st.button(t("fetch_mandi_btn"), key="fetch_mandi_btn", use_container_width=False)

    if fetch_btn:
        if not commodity_input.strip():
            st.warning("कृपया पीक नाव प्रविष्ट करा / कृपया फसल का नाम डालें।")
        else:
            with st.spinner(t("loading")):
                params = {
                    "commodity": commodity_input.strip(),
                    "state": state_part,
                    "market": market_part,
                }
                data, err = api_get("/api/mandi-prices", params=params, timeout=20)

            if err:
                st.error(err)
            elif data:
                st.markdown(f"### {t('mandi_result_label')}")
                prices = data.get("prices", [])
                if prices:
                    rows_html = ""
                    for row in prices:
                        min_p = row.get("min_price", "-")
                        max_p = row.get("max_price", "-")
                        modal_p = row.get("modal_price", "-")
                        market_name = row.get("market", market_part)
                        date_str = row.get("arrival_date", "-")
                        rows_html += (
                            f"<tr>"
                            f"<td>{market_name}</td>"
                            f"<td><strong>₹{modal_p}</strong></td>"
                            f"<td>₹{min_p}</td>"
                            f"<td>₹{max_p}</td>"
                            f"<td>{date_str}</td>"
                            f"</tr>"
                        )
                    table_html = f"""
                    <table class='mandi-table'>
                        <thead>
                            <tr>
                                <th>Market / बाजार</th>
                                <th>Modal / सामान्य</th>
                                <th>Min / किमान</th>
                                <th>Max / कमाल</th>
                                <th>Date / दिनांक</th>
                            </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                    """
                    st.markdown(table_html, unsafe_allow_html=True)
                else:
                    summary = data.get("summary", "")
                    if summary:
                        st.info(summary)
                    else:
                        st.info("No price data available for this commodity and market.")


# ─────────────────────────────────────────────
# PAGE: Weather
# ─────────────────────────────────────────────
def page_weather():
    st.markdown(f"# {t('weather_title')}")
    st.markdown("---")

    location = st.text_input(
        t("location_label"),
        placeholder=t("location_placeholder"),
        key="weather_location",
    )
    fetch_btn = st.button(t("fetch_weather_btn"), key="fetch_weather_btn", use_container_width=False)

    if fetch_btn:
        if not location.strip():
            st.warning("कृपया गाव/शहर प्रविष्ट करा / कृपया गाँव/शहर डालें।")
        else:
            with st.spinner(t("loading")):
                data, err = api_get("/api/weather", params={"location": location.strip()}, timeout=20)

            if err:
                st.error(err)
            elif data:
                temp = data.get("temperature", "-")
                humidity = data.get("humidity", "-")
                desc = data.get("description", "-")
                advisory = data.get("agricultural_advisory", "")
                city_name = data.get("city", location.strip())

                st.markdown(
                    f"""
                    <div class='weather-card'>
                        <h2 style='color:white; margin-top:0;'>📍 {city_name}</h2>
                        <div>🌡️ <b>{t("temp_label")}:</b> {temp}°C</div>
                        <div>💧 <b>{t("humidity_label")}:</b> {humidity}%</div>
                        <div>🌤️ <b>{t("desc_label")}:</b> {desc}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if advisory:
                    st.markdown(f"### 🌱 {t('advisory_label')}")
                    st.markdown(
                        f"<div class='answer-box'>{advisory}</div>",
                        unsafe_allow_html=True,
                    )


# ─────────────────────────────────────────────
# PAGE: Admin — Upload Documents
# ─────────────────────────────────────────────
def page_admin():
    st.markdown(f"# {t('admin_title')}")
    st.markdown("---")

    lang = st.session_state.language
    topic_options = {
        t("topic_crop"): "crop",
        t("topic_pest"): "pest",
        t("topic_scheme"): "scheme",
        t("topic_general"): "general",
    }

    with st.container():
        st.markdown("<div class='upload-section'>", unsafe_allow_html=True)

        pdf_file = st.file_uploader(
            t("upload_pdf_label"),
            type=["pdf"],
            key="pdf_uploader",
        )

        source_name = st.text_input(
            t("source_name_label"),
            placeholder="ICAR / कृषि विभाग / Agriculture Dept.",
            key="source_name_input",
        )

        topic_label = st.selectbox(
            t("topic_label"),
            list(topic_options.keys()),
            key="topic_select",
        )
        topic_value = topic_options[topic_label]

        upload_btn = st.button(t("upload_btn"), key="upload_btn", use_container_width=False)
        st.markdown("</div>", unsafe_allow_html=True)

    if upload_btn:
        if not pdf_file:
            st.warning("कृपया PDF फाइल निवडा / कृपया PDF फ़ाइल चुनें।")
        elif not source_name.strip():
            st.warning("कृपया स्रोताचे नाव प्रविष्ट करा / कृपया स्रोत का नाम डालें।")
        else:
            with st.spinner(t("loading")):
                files = {"file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")}
                payload = {
                    "source": source_name.strip(),
                    "topic": topic_value,
                }
                data, err = api_post("/api/upload-document", payload=payload, files=files, timeout=60)

            if err:
                st.error(t("upload_error") + f"\n\n{err}")
            elif data:
                chunks = data.get("chunks_created", data.get("chunks", ""))
                pages = data.get("pages", "")
                st.success(t("upload_success"))
                detail_parts = []
                if pages:
                    detail_parts.append(f"Pages: {pages}")
                if chunks:
                    detail_parts.append(f"Chunks: {chunks}")
                if detail_parts:
                    st.info(" | ".join(detail_parts))


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────
chat_label = t("nav_chat")
mandi_label = t("nav_mandi")
weather_label = t("nav_weather")
admin_label = t("nav_admin")

nav = st.session_state.get("nav_radio", chat_label)

if nav == chat_label:
    page_chat()
elif nav == mandi_label:
    page_mandi()
elif nav == weather_label:
    page_weather()
elif nav == admin_label:
    page_admin()
else:
    page_chat()
