import json
import streamlit as st          # streamlit le chai python code lai easy web app ma convert garcha
from match import FAQMatcher    # hamro matching logic import garyo


st.set_page_config(page_title="Support Assistant", page_icon="💬", layout="wide")


@st.cache_resource
def load_matcher():
    with open("data/faqs.json", "r", encoding="utf-8") as f:
        faqs = json.load(f)
    return FAQMatcher(faqs)


@st.cache_data
def load_faq_questions():
    with open("data/faqs.json", "r", encoding="utf-8") as f:
        faqs = json.load(f)
    return [item["question"] for item in faqs]


matcher = load_matcher()
faq_questions = load_faq_questions()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:wght@500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* pura page ko background */
    .stApp {
        background-color: #F2F4F1;
    }

    /* streamlit ko default top padding ghataune, header le jaga liyera */
    .block-container {
        padding-top: 1rem;
        max-width: 900px;
    }

    /* -------------------- HEADER BAR -------------------- */
    .chat-header {
        display: flex;
        align-items: center;
        gap: 14px;
        background-color: #16433C;
        padding: 16px 22px;
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .chat-header .avatar {
        width: 46px;
        height: 46px;
        border-radius: 50%;
        background-color: #D98E2B;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        flex-shrink: 0;
    }
    .chat-header .info h2 {
        font-family: 'Fraunces', serif;
        color: #FFFFFF;
        margin: 0;
        font-size: 20px;
        font-weight: 600;
    }
    .chat-header .status {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #C9E4DA;
        font-size: 13px;
        margin-top: 2px;
    }
    .chat-header .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #5BD98A;
        display: inline-block;
    }

    /* -------------------- CHAT BUBBLES -------------------- */
    .bubble-row {
        display: flex;
        margin: 10px 0;
        align-items: flex-end;
        gap: 8px;
    }
    .bubble-row.user {
        justify-content: flex-end;
    }
    .bubble-row.bot {
        justify-content: flex-start;
    }
    .bubble-avatar {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        flex-shrink: 0;
        background-color: #16433C;
    }
    .bubble {
        max-width: 65%;
        padding: 11px 16px;
        font-size: 15px;
        line-height: 1.45;
    }
    .bubble.bot {
        background-color: #FFFFFF;
        color: #1C2321;
        border: 1px solid #DCE3DF;
        border-radius: 16px 16px 16px 4px;
    }
    .bubble.user {
        background-color: #16433C;
        color: #FFFFFF;
        border-radius: 16px 16px 4px 16px;
    }
    .bubble .confidence {
        display: block;
        margin-top: 6px;
        font-size: 11.5px;
        opacity: 0.65;
    }

    /* -------------------- SIDEBAR (FAQ quick replies) -------------------- */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #DCE3DF;
    }
    section[data-testid="stSidebar"] h3 {
        font-family: 'Fraunces', serif;
        color: #16433C;
    }
    section[data-testid="stSidebar"] .stButton button {
        background-color: #F2F4F1;
        color: #16433C;
        border: 1px solid #DCE3DF;
        border-radius: 20px;
        padding: 8px 14px;
        font-size: 13.5px;
        text-align: left;
        width: 100%;
        margin-bottom: 6px;
        transition: 0.15s;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #16433C;
        color: #FFFFFF;
        border-color: #16433C;
    }

    /* suggestion chips on empty state (main area, not sidebar) */
    div[data-testid="stMainBlockContainer"] .stButton button,
    .main .stButton button {
        background-color: #16433C;
        color: #FFFFFF !important;
        border: 1px solid #16433C;
        border-radius: 20px;
        padding: 10px 16px;
        font-size: 14px;
        font-weight: 500;
        width: 100%;
    }
    div[data-testid="stMainBlockContainer"] .stButton button:hover,
    .main .stButton button:hover {
        background-color: #0E322C;
        color: #FFFFFF !important;
        border-color: #0E322C;
    }
    div[data-testid="stMainBlockContainer"] .stButton button:focus,
    .main .stButton button:focus {
        color: #FFFFFF !important;
        box-shadow: none;
    }
    div[data-testid="stMainBlockContainer"] .stButton button p,
    .main .stButton button p {
        color: #FFFFFF !important;
    }

    /* chat input box styling */
    .stChatInput textarea, .stChatInput input {
        border-radius: 20px !important;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="chat-header">
    <div class="avatar">🤖</div>
    <div class="info">
        <h2>Support Assistant</h2>
        <div class="status"><span class="dot"></span> Online — answers FAQs instantly</div>
    </div>
</div>
""", unsafe_allow_html=True)


def handle_question(question_text: str):
    """User ko question process garera answer nikalne ra history ma add garne."""
    st.session_state.messages.append({"role": "user", "content": question_text})
    result = matcher.find_best_match(question_text)
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "confidence": result["confidence"],
    })


def render_bubble(role: str, content: str, confidence=None):
    """
    Euta message lai chat bubble (HTML) ko form ma render garne.
    role = "user" bhaye dahine (right) tira, "assistant" bhaye
    baye (left) tira deखिन्छ - real chat app jastै.
    """
    if role == "user":
        st.markdown(f"""
        <div class="bubble-row user">
            <div class="bubble user">{content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        conf_html = f'<span class="confidence">Confidence: {confidence}%</span>' if confidence is not None else ""
        st.markdown(f"""
        <div class="bubble-row bot">
            <div class="bubble-avatar">🤖</div>
            <div class="bubble bot">{content}{conf_html}</div>
        </div>
        """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### 💬 Quick questions")
    st.caption("Tap a question to get an instant answer")

    for i, question in enumerate(faq_questions):
        if st.button(question, key=f"faq_{i}"):
            handle_question(question)

    st.divider()
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.messages:
    # Chat khali xa bhane - welcome bubble + suggestion chips dekhaune
    render_bubble("assistant", "Hi there! 👋 I'm your support assistant. Pick a question from the sidebar, or try one of these:")

    cols = st.columns(2)
    for i, question in enumerate(faq_questions[:4]):
        with cols[i % 2]:
            if st.button(question, key=f"suggest_{i}"):
                handle_question(question)
                st.rerun()
else:
    # purano sabai message haru bubble ko roop ma dekhaune
    for msg in st.session_state.messages:
        render_bubble(msg["role"], msg["content"], msg.get("confidence"))


user_input = st.chat_input("Type your question here...")

if user_input:
    handle_question(user_input)
    st.rerun()