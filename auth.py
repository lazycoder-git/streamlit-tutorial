"""auth.py — Login gate for Money Tracker. Call require_login() on every page."""

import os
import streamlit as st
import streamlit_authenticator as stauth
from firebase_db import db


def _load_credentials_from_firebase() -> dict:
    """Fetch all users from Firestore 'users' collection."""
    users_ref = db.collection("users")
    docs = users_ref.stream()

    usernames = {}
    for doc in docs:
        data = doc.to_dict()
        usernames[doc.id] = {
            "email": data.get("email", ""),
            "failed_login_attempts": data.get("failed_login_attempts", 0),
            "logged_in": data.get("logged_in", False),
            "name": data.get("name", doc.id.capitalize()),
            "password": data.get("password", "")
        }

    # If no users exist in Firestore (first run), seed the default user
    if not usernames:
        default_user = {
            "email": "ghost@example.com",
            "failed_login_attempts": 0,
            "logged_in": False,
            "name": "Ghost",
            "password": "$2b$12$SaWrBuP6.o3MMTvVZ0ZTyeRr2tMNvfoWVL9dc/qsagW34h53REnxy"  # 'money123'
        }
        db.collection("users").document("ghost").set(default_user)
        usernames["ghost"] = default_user

    return {"usernames": usernames}


def _get_authenticator() -> stauth.Authenticate:
    """Load credentials from Firestore and initialize stauth Authenticate class."""
    if "_mt_authenticator" not in st.session_state:
        creds = _load_credentials_from_firebase()
        
        # Read cookie config from Streamlit secrets, or use defaults
        cookie_config = {}
        try:
            cookie_config = st.secrets.get("cookie", {})
        except Exception:
            pass

        cookie_name = cookie_config.get("name", "money_tracker_auth")
        cookie_key = cookie_config.get("key", "money_tracker_secret_key_xk92bv")
        cookie_expiry = float(cookie_config.get("expiry_days", 30.0))

        st.session_state["_mt_authenticator"] = stauth.Authenticate(
            creds,
            cookie_name,
            cookie_key,
            cookie_expiry,
            auto_hash=False,
        )
    return st.session_state["_mt_authenticator"]


def require_login() -> str:
    """
    Show login/register form if not authenticated.
    Adds user info + Logout button at the top of the sidebar.
    Returns the logged-in username as a string.

    Must be called AFTER st.set_page_config().
    """
    authenticator = _get_authenticator()

    # Only render the login/register form when not already authenticated in this session
    if st.session_state.get("authentication_status") is not True:
        auth_mode = st.radio(
            "Account Access Mode",
            ["🔑 Log In", "📝 Sign Up"],
            horizontal=True,
            label_visibility="collapsed",
            key="auth_mode_radio"
        )

        if auth_mode == "🔑 Log In":
            authenticator.login(
                location="main",
                key="money_tracker_login",
            )

            auth_status = st.session_state.get("authentication_status")

            if auth_status is False:
                st.error("❌ Incorrect username or password. Please try again.")
                st.stop()

            # auth_status is None (form shown, awaiting input) → stop rendering
            if auth_status is not True:
                st.stop()
        else:
            try:
                email, username, name = authenticator.register_user(
                    location="main",
                    key="money_tracker_register",
                    captcha=False,
                )
                if username:
                    # Retrieve the registered user info from authenticator credentials
                    user_data = authenticator.authentication_controller.authentication_model.credentials["usernames"][username]
                    
                    db_user = {
                        "email": user_data.get("email", ""),
                        "failed_login_attempts": user_data.get("failed_login_attempts", 0),
                        "logged_in": user_data.get("logged_in", False),
                        "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or username.capitalize(),
                        "password": user_data.get("password", "")
                    }
                    db.collection("users").document(username).set(db_user)
                    st.success("🎉 Registration successful! Please select '🔑 Log In' above to access your account.")
            except Exception as e:
                st.error(f"❌ Error during registration: {e}")
            st.stop()

    # ── Authenticated — add user chip + logout to sidebar top ─────────────────
    with st.sidebar:
        name = st.session_state.get("name", "User")
        st.markdown(
            f"""<div style="padding:6px 0 2px 0; font-size:0.88rem; opacity:0.75;">
            👤 &nbsp;<b>{name}</b></div>""",
            unsafe_allow_html=True,
        )
        authenticator.logout(
            button_name="🚪 Logout",
            location="sidebar",
            key="money_tracker_logout",
        )
        st.divider()

    return st.session_state.get("username", "")
