"""
app.py
------
Streamlit chat UI for the FAQ chatbot.

Run with:
    streamlit run app.py
"""

import os

import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration – MUST be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="🛒 E-Commerce Support Chatbot",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS – clean, professional look
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ── Global ────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Sidebar ────────────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(160deg, #0f1729 0%, #1a2744 100%);
        color: #e8edf5;
    }
    [data-testid="stSidebar"] * {
        color: #e8edf5 !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #2d4068;
    }

    /* ── Chat messages ──────────────────────────────────────────────────── */
    [data-testid="stChatMessage"] {
        border-radius: 14px;
        padding: 4px 8px;
        margin-bottom: 4px;
    }

    /* ── Input bar ──────────────────────────────────────────────────────── */
    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: 1.5px solid #3a5a9a !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Expander (match details) ───────────────────────────────────────── */
    .streamlit-expanderHeader {
        font-size: 0.82rem;
        color: #6b8ccc !important;
        background: transparent !important;
    }

    /* ── Buttons ────────────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 10px;
        border: 1.5px solid #3a5a9a;
        background: transparent;
        color: #a0bfef;
        transition: all 0.2s ease;
        font-family: 'Inter', sans-serif;
    }
    .stButton > button:hover {
        background: #1e3560;
        border-color: #6b8ccc;
        color: #ffffff;
    }

    /* ── Topic badge list ───────────────────────────────────────────────── */
    .topic-badge {
        display: inline-block;
        background: #1e3560;
        color: #a0bfef;
        border: 1px solid #3a5a9a;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.78rem;
        margin: 3px 2px;
    }

    /* ── Metric card ────────────────────────────────────────────────────── */
    .stat-card {
        background: #1e3560;
        border: 1px solid #3a5a9a;
        border-radius: 12px;
        padding: 12px 16px;
        text-align: center;
    }
    .stat-card .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #5b9cf6;
    }
    .stat-card .stat-label {
        font-size: 0.78rem;
        color: #8baed4;
        margin-top: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Import chatbot module – show a friendly error on import failure
# ---------------------------------------------------------------------------
try:
    from chatbot import get_best_match, get_topic_hints, load_faqs
except Exception as exc:
    import traceback
    st.error("❌ **Could not import chatbot.py**")
    st.code(traceback.format_exc())
    st.info("Make sure `chatbot.py` is in the same directory as `app.py` and all requirements are installed.")
    st.stop()

# ---------------------------------------------------------------------------
# Load FAQs – show a friendly error on load failure
# ---------------------------------------------------------------------------

# Resolve path relative to this file's directory, falling back to CWD
_here = os.path.dirname(os.path.abspath(__file__))
FAQ_PATH = os.path.join(_here, "faqs.json")
# Also check uppercase variant (FAQS.json) common on Windows
if not os.path.exists(FAQ_PATH):
    _upper = os.path.join(_here, "FAQS.json")
    if os.path.exists(_upper):
        FAQ_PATH = _upper


@st.cache_resource(show_spinner="Loading FAQ knowledge base…")
def _load_cached_faqs(path: str):
    """Cache the FAQ list so it is only loaded once per session."""
    return load_faqs(path)


# Load outside the cache wrapper so exceptions surface cleanly
try:
    # Bust the cache if path has changed between runs
    faqs = _load_cached_faqs(FAQ_PATH)
except Exception:  # pragma: no cover – show all errors, never blank page
    import traceback
    st.error("❌ **Failed to load FAQs. Full error:**")
    st.code(traceback.format_exc())
    st.info(
        "**Common fix:** Make sure `faqs.json` (or `FAQS.json`) is in the "
        "same folder as `app.py` and that its JSON structure is valid."
    )
    st.stop()

topic_hints: list[str] = get_topic_hints(faqs)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
WELCOME_MSG = (
    "Hello! 👋 I'm your e-commerce support assistant. "
    "I can help with **orders**, **shipping**, **returns**, **payments**, and more. "
    "What can I help you with today?"
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": WELCOME_MSG, "score": None, "matched": None}
    ]

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    # ── Branding ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center; padding: 16px 0 8px 0;">
            <div style="font-size: 2.4rem;">🛍️</div>
            <div style="font-size: 1.15rem; font-weight: 700; letter-spacing: 0.3px; margin-top: 4px;">
                Support Assistant
            </div>
            <div style="font-size: 0.78rem; color: #8baed4; margin-top: 4px;">
                Powered by TF-IDF · Cosine Similarity
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Stats ─────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-number">{len(faqs)}</div>
            <div class="stat-label">FAQs Loaded</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Topic hints ───────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-weight:600; font-size:0.85rem; margin-bottom:8px;'>"
        "💡 I can help with:</div>",
        unsafe_allow_html=True,
    )
    badges_html = "".join(
        f'<span class="topic-badge">{topic}</span>' for topic in topic_hints
    )
    st.markdown(badges_html, unsafe_allow_html=True)
    st.divider()

    # ── Tips ──────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="font-size: 0.78rem; color: #8baed4; line-height: 1.7;">
        <b>💬 Example questions:</b><br>
        • How do I track my order?<br>
        • What is your return policy?<br>
        • Can I use a promo code?<br>
        • Do you offer gift wrapping?<br>
        • How long does shipping take?
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Clear chat ────────────────────────────────────────────────────────
    if st.button("🗑️  Clear Chat", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": WELCOME_MSG, "score": None, "matched": None}
        ]
        st.rerun()

# ---------------------------------------------------------------------------
# Main chat area header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <h1 style="font-size:1.7rem; font-weight:700; margin-bottom:0;">
        🛒 E-Commerce Support Chatbot
    </h1>
    <p style="color:#8baed4; font-size:0.87rem; margin-top:4px;">
        Ask me anything about your orders, shipping, returns, or account.
    </p>
    <hr style="margin: 8px 0 20px 0; border-color: #2d3748;">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Render existing chat history
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show match details expander for bot replies that had a successful match
        if (
            message["role"] == "assistant"
            and message.get("score") is not None
            and message["score"] > 0
            and message.get("matched")
        ):
            with st.expander("ℹ️ Match details"):
                st.markdown(
                    f"**Matched FAQ:** {message['matched']}\n\n"
                    f"**Confidence:** {message['score']:.0%}"
                )

# ---------------------------------------------------------------------------
# User input
# ---------------------------------------------------------------------------
if user_text := st.chat_input("Type your question here…"):

    # Ignore blank / whitespace-only input
    if not user_text.strip():
        st.stop()

    # ── Display user message ───────────────────────────────────────────────
    st.session_state.messages.append(
        {"role": "user", "content": user_text, "score": None, "matched": None}
    )
    with st.chat_message("user"):
        st.markdown(user_text)

    # ── Compute bot response ───────────────────────────────────────────────
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            result = get_best_match(user_text, faqs)

        bot_reply   = result["answer"]
        match_score = result["score"]
        matched_q   = result["matched_question"]

        st.markdown(bot_reply)

        if match_score > 0 and matched_q:
            with st.expander("ℹ️ Match details"):
                st.markdown(
                    f"**Matched FAQ:** {matched_q}\n\n"
                    f"**Confidence:** {match_score:.0%}"
                )

    # ── Persist assistant message ──────────────────────────────────────────
    st.session_state.messages.append(
        {
            "role":    "assistant",
            "content": bot_reply,
            "score":   match_score,
            "matched": matched_q,
        }
    )
