# app.py
import streamlit as st
import requests
import uuid

# 1. Page Configuration
st.set_page_config(
    page_title="TN Farmers Welfare AI",
    page_icon="🌾",
    layout="wide"
)

API_STREAM_URL = "http://127.0.0.1:8000/chat/stream"

# 2. Dynamic Mode Color Map
MODE_STYLES = {
    "Short": {"bg": "#E8F5E9", "border": "#81C784", "text": "#1B5E20"},
    "Medium": {"bg": "#FFF8E1", "border": "#FFE082", "text": "#B78103"},
    "Long": {"bg": "#E3F2FD", "border": "#90CAF9", "text": "#0D47A1"}
}

current_mode_key = st.session_state.get("detail_level_selection", "Short")
clean_mode = "Short"
if "Medium" in current_mode_key:
    clean_mode = "Medium"
elif "Long" in current_mode_key:
    clean_mode = "Long"

active_theme = MODE_STYLES.get(clean_mode, MODE_STYLES["Short"])

# 3. CSS Overrides: Transparent Bottom Bar, Inline Input Alignment, and Dynamic Dropdown Colors
st.markdown(f"""
    <style>
    /* Remove white top header bar */
    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}
    .stAppViewMain {{
        top: 0 !important;
    }}

    /* Photorealistic Golden Sunrise Field Background */
    .stApp {{
        background: linear-gradient(rgba(0, 0, 0, 0.12), rgba(0, 0, 0, 0.12)),
                    url('https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=2000&q=90');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* Vibrant Green Sidebar */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #1B5E20 0%, #2E7D32 100%) !important;
    }}

    /* Transparent Bottom Container (Fixes Issue #4) */
    div[data-testid="stBottom"] {{
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }}

    div[data-testid="stBottom"] > div {{
        background: transparent !important;
    }}

    /* Align Mode Dropdown and Input Bar Inline at the Bottom */
    div[data-testid="stHorizontalBlock"] {{
        align-items: center !important;
    }}

    /* Dynamic Colored Dropdown Box (Fixes Issue #1 & Color Fill) */
    div[data-baseweb="select"] > div {{
        background-color: {active_theme['bg']} !important;
        border: 2px solid {active_theme['border']} !important;
        color: {active_theme['text']} !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        height: 46px !important;
    }}

    div[data-baseweb="select"] span {{
        color: {active_theme['text']} !important;
        font-weight: 700 !important;
    }}

    /* White Opaque Chat Cards for Response Text */
    .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.98) !important;
        border-radius: 12px !important;
        padding: 16px 22px !important;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.15) !important;
        margin-bottom: 14px !important;
        border-left: 5px solid #2E7D32 !important;
    }}

    /* Clean Sidebar Buttons */
    [data-testid="stSidebar"] .stButton > button {{
        border-radius: 8px !important;
        font-weight: 600 !important;
    }}
    </style>
""", unsafe_allow_html=True)

# 4. Session State Initialization
GREETING_MSG = "🙏 **Vanakkam!** Welcome to Tamil Nadu Farmers Welfare Assistant. How can I help you regarding state agricultural schemes, subsidies, or crop insurance today?"

if "chats" not in st.session_state:
    default_id = str(uuid.uuid4())
    st.session_state.chats = {
        default_id: {
            "title": "New Conversation",
            "messages": [{"role": "assistant", "content": GREETING_MSG}]
        }
    }
    st.session_state.current_session_id = default_id

# 5. DIALOGS FOR RENAME & DELETE CONFIRMATION (Fixes Issues #2 & #3)
@st.dialog("✏️ Rename Chat")
def rename_dialog(sess_id):
    chat_title = st.session_state.chats[sess_id]["title"]
    new_name = st.text_input("New Title (Max 50 chars):", value=chat_title[:50], max_chars=50)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", use_container_width=True):
            if new_name.strip():
                st.session_state.chats[sess_id]["title"] = new_name.strip()
            st.rerun()  # Auto-closes dialog
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

@st.dialog("⚠️ Confirm Deletion")
def delete_dialog(sess_id):
    st.write(f"Are you sure you want to delete **'{st.session_state.chats[sess_id]['title']}'**?")
    st.warning("This action cannot be undone.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            del st.session_state.chats[sess_id]
            if st.session_state.current_session_id == sess_id:
                remaining = list(st.session_state.chats.keys())
                if remaining:
                    st.session_state.current_session_id = remaining[0]
                else:
                    fresh_id = str(uuid.uuid4())
                    st.session_state.chats[fresh_id] = {
                        "title": "New Conversation",
                        "messages": [{"role": "assistant", "content": GREETING_MSG}]
                    }
                    st.session_state.current_session_id = fresh_id
            st.rerun()  # Auto-closes dialog
    with col2:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

# 6. SIDEBAR: Navigation & Chat History
with st.sidebar:
    st.markdown("<h2 style='color:white;'>🌾 TN Farmer Assistant</h2>", unsafe_allow_html=True)
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {
            "title": f"Chat {len(st.session_state.chats) + 1}",
            "messages": [{"role": "assistant", "content": GREETING_MSG}]
        }
        st.session_state.current_session_id = new_id
        st.rerun()

    st.markdown("---")
    st.markdown("<h3 style='color:white;'>📜 Chat History</h3>", unsafe_allow_html=True)

    for sess_id, chat_data in list(st.session_state.chats.items()):
        is_active = (sess_id == st.session_state.current_session_id)
        badge = "⭐ " if is_active else "💬 "
        display_title = chat_data['title'][:18] + ("..." if len(chat_data['title']) > 18 else "")
        
        col_btn, col_dots = st.columns([4, 1])
        
        with col_btn:
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{badge}{display_title}", key=f"nav_{sess_id}", use_container_width=True, type=btn_type):
                st.session_state.current_session_id = sess_id
                st.rerun()

        with col_dots:
            with st.popover("⚙️"):
                if st.button("✏️ Rename", key=f"btn_ren_{sess_id}", use_container_width=True):
                    rename_dialog(sess_id)
                if st.button("🗑️ Delete", key=f"btn_del_{sess_id}", use_container_width=True):
                    delete_dialog(sess_id)

# 7. MAIN AREA: Title & Active Conversation
st.markdown("<h1 style='text-align:center; color:#1B5E20; font-size: 2.2rem;'>🌾 Tamil Nadu Farmers Welfare Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#1B5E20; font-weight:700;'>Get instant guidelines on agricultural schemes, subsidies, and insurance.</p>", unsafe_allow_html=True)

if st.session_state.current_session_id not in st.session_state.chats:
    st.session_state.current_session_id = list(st.session_state.chats.keys())[0]

active_chat = st.session_state.chats[st.session_state.current_session_id]

# Render Messages
for msg in active_chat["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

# 8. BOTTOM FIXED INLINE ROW: Text Box + Dynamic Color Mode Dropdown (Fixes Issue #1 & #4)
with st.container():
    col_input, col_mode = st.columns([4, 1])

    with col_mode:
        selected_mode_label = st.selectbox(
            "Response Mode",
            options=["🟢 Short (Crisp)", "🟡 Medium (Balanced)", "🔵 Long (Detailed)"],
            index=0,
            key="detail_level_selection",
            label_visibility="collapsed"
        )
        
        if "Medium" in selected_mode_label:
            detail_level = "Medium"
        elif "Long" in selected_mode_label:
            detail_level = "Long"
        else:
            detail_level = "Short"

    with col_input:
        user_input = st.chat_input("Ask about TN Farmer Welfare Schemes...")

# 9. PROCESS USER INPUT
if user_input:
    clean_input = user_input.strip().lower()

    if len(active_chat["messages"]) == 1:
        active_chat["title"] = user_input[:20] + ("..." if len(user_input) > 20 else "")

    active_chat["messages"].append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        if clean_input in ["exit", "quit"]:
            thank_you_msg = (
                "🙏 **Thank you for using the Tamil Nadu Farmers Welfare Assistant!**\n\n"
                "We wish you high yield and prosperity in your farming endeavors. 🌾\n\n"
                "*(You can continue asking questions anytime in this session or click '➕ New Chat' to start fresh.)*"
            )
            st.markdown(thank_you_msg)
            active_chat["messages"].append({"role": "assistant", "content": thank_you_msg})
            st.rerun()
        else:
            def response_generator():
                try:
                    res = requests.post(
                        API_STREAM_URL,
                        json={
                            "query": user_input,
                            "session_id": st.session_state.current_session_id,
                            "detail_level": detail_level
                        },
                        stream=True,
                        timeout=30
                    )
                    if res.status_code == 200:
                        for chunk in res.iter_content(chunk_size=None, decode_unicode=True):
                            if chunk:
                                yield chunk
                    else:
                        yield f"⚠️ Server Error: {res.status_code}"
                except requests.exceptions.ConnectionError:
                    yield "❌ **Connection Error**: FastAPI backend is offline. Start `api.py`!"

            full_response = st.write_stream(response_generator)
            active_chat["messages"].append({"role": "assistant", "content": full_response})
            st.rerun()