import re
import os
import fitz  # PyMuPDF
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from db import register_user, login_user, create_table, init_db
from query import get_answer

load_dotenv()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="EV Assistant", layout="wide")

# ---------------- DB INIT ----------------
init_db()
create_table()

# ---------------- CSS ----------------
def apply_styles():
    st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top, #0a1a2f, #02050a);
        color: white;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #007cf0, #00dfd8);
        color: white;
        border-radius: 25px;
        padding: 10px 20px;
        border: none;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #0057c2, #00a8a8);
    }
    </style>
    """, unsafe_allow_html=True)

apply_styles()

# ---------------- SESSION STATE ----------------
if "manual_uploaded" not in st.session_state:
    st.session_state.manual_uploaded = False

if "page" not in st.session_state:
    st.session_state.page = "login"

if "user" not in st.session_state:
    st.session_state.user = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

# ---------------- DASHBOARD ----------------
def render_dashboard():
    st.title("⚡ EV Diagnostic Assistant")
    st.subheader("Smart EV Diagnostics Platform")
    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🤖 EV Assistant\nAsk questions about EV diagnostics")
        if st.button("Open Chat", key="dash_chat"):
            st.session_state.page = "chat"
            st.rerun()

    with col2:
        st.markdown("### 📄 Upload Manuals\nUpload PDF manuals for better answers")
        if st.button("Upload", key="dash_upload"):
            st.session_state.page = "upload"
            st.rerun()

    with col3:
        st.markdown("### 🕘 Chat History\nView previous conversations")
        if st.button("View History", key="dash_history"):
            st.session_state.page = "history"
            st.rerun()

# ---------------- LOGIN ----------------
if st.session_state.page == "login":
    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(email, password)
        if user:
            st.session_state.user = user
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.button("Create Account"):
        st.session_state.page = "signup"
        st.rerun()

# ---------------- SIGNUP ----------------
elif st.session_state.page == "signup":
    st.title("Create Account")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if password != confirm:
            st.error("Passwords do not match")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters")
        else:
            result = register_user(username, email, password)
            if result == "success":
                st.success("Account created")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error("Email already exists")

    if st.button("⬅ Back"):
        st.session_state.page = "login"
        st.rerun()

# ---------------- MAIN APP ----------------
else:
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚡ EV Assistant")

        if st.button("🏠 Dashboard"):
            st.session_state.page = "dashboard"
        if st.button("🤖 EV Assistant"):
            st.session_state.page = "chat"
        if st.button("🕘 Chat History"):
            st.session_state.page = "history"
        if st.button("📄 Upload Manuals"):
            st.session_state.page = "upload"

        st.markdown("---")

        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.session_state.page = "login"
            st.rerun()

    # Profile icon in top-right
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("👤"):
            st.session_state.page = "profile"
            st.rerun()

    # Page routing
    if st.session_state.page == "profile":
        if st.button("⬅ Back"):
            st.session_state.page = "dashboard"
            st.rerun()
        user = st.session_state.get("user", {})
        st.title("My Profile")
        st.write("Username:", user.get("username", "Not found"))
        st.write("Email:", user.get("email", "Not found"))

    elif st.session_state.page == "dashboard":
        render_dashboard()

    elif st.session_state.page == "chat":
        if st.button("⬅ Back"):
            st.session_state.page = "dashboard"
            st.rerun()

        st.header("EV Assistant")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask EV question...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            try:
                response = get_answer(user_input)
            except Exception as e:
                response = f"Error: {str(e)}"

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.history.append({
                "time": datetime.now().strftime("%I:%M %p"),
                "question": user_input,
                "chat": st.session_state.messages.copy()
            })
            st.rerun()

    elif st.session_state.page == "history":
        if st.button("⬅ Back"):
            st.session_state.page = "dashboard"
            st.rerun()

        st.header("Chat History")

        if not st.session_state.history:
            st.info("No conversations yet.")
        else:
            for i, item in enumerate(st.session_state.history):
                if st.button(f"{item['time']} - {item['question']}", key=f"hist_{i}"):
                    st.session_state.messages = item["chat"]
                    st.session_state.page = "chat"
                    st.rerun()

    elif st.session_state.page == "upload":
        if st.button("⬅ Back"):
            st.session_state.page = "dashboard"
            st.rerun()

        st.header("Upload Manuals")

        if st.button("🗑 Clear Old Manual"):
            if os.path.exists("stored_chunks.txt"):
                os.remove("stored_chunks.txt")
            st.session_state.manual_uploaded = False
            st.success("Old manual deleted!")

        file = st.file_uploader("Upload PDF", type=["pdf"])

        if file:
            with st.spinner("Processing manual..."):
                doc = fitz.open(stream=file.read(), filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text("text") + "\n"

                text = re.sub(r'\s+', ' ', text)
                sentences = re.split(r'(?<=[.!?])\s+', text)
                cleaned = []

                for s in sentences:
                    s = s.strip()
                    if len(s) < 40:
                        continue
                    if s.isupper():
                        continue
                    if any(word in s.lower() for word in ["trademark", "status area", "touchscreen", "display"]):
                        continue
                    cleaned.append(s)

                with open("stored_chunks.txt", "w", encoding="utf-8") as f:
                    for s in cleaned:
                        f.write(s + "\n")

            st.session_state.manual_uploaded = True
            st.success("✅ Manual uploaded successfully!")
