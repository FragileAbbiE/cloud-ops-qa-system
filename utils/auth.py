import hashlib
import uuid
from datetime import datetime, timedelta
import streamlit as st
from utils.db import (
    create_user,
    create_session,
    deactivate_session,
    get_session,
    get_user_by_username,
    update_last_login,
)

SESSION_KEY = "session_token"

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def ensure_default_admin():
    admin = get_user_by_username("admin")
    if not admin:
        create_user(
            username="admin",
            password_hash=sha256_text("admin123"),
            email="admin@example.com",
            role="admin",
        )

def authenticate(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return None
    if user.get("is_active", 1) != 1:
        return None
    if user["password_hash"] != sha256_text(password):
        return None
    update_last_login(user["id"])
    return user

def login(username: str, password: str) -> bool:
    user = authenticate(username, password)
    if not user:
        return False
    token = str(uuid.uuid4())
    expires_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    create_session(user["id"], token, expires_at)
    st.session_state[SESSION_KEY] = token
    st.session_state["user"] = user
    st.session_state["redirect_to"] = "工作台"
    return True

def get_current_user():
    if "user" in st.session_state:
        return st.session_state["user"]

    token = st.session_state.get(SESSION_KEY)
    if not token:
        return None
    sess = get_session(token)
    if not sess:
        return None

    exp = datetime.strptime(sess["expires_at"], "%Y-%m-%d %H:%M:%S")
    if exp < datetime.now():
        deactivate_session(token)
        return None

    return st.session_state.get("user")

def logout():
    token = st.session_state.get(SESSION_KEY)
    if token:
        deactivate_session(token)
    st.session_state.pop(SESSION_KEY, None)
    st.session_state.pop("user", None)

def require_admin(user: dict) -> bool:
    return bool(user and user.get("role") == "admin")
