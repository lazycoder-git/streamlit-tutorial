"""auth.py — Login gate for Money Tracker. Call require_login() on every page."""

import os
import streamlit as st
import streamlit_authenticator as stauth
from firebase_db import db, FIREBASE_AVAILABLE

_DEFAULT_USERS = {
    "ghost": {
        "email": "ghost@example.com",
        "failed_login_attempts": 0,
        "logged_in": False,
        "name": "Ghost",
        "password": "$2b$12$SaWrBuP6.o3MMTvVZ0ZTyeRr2tMNvfoWVL9dc/qsagW34h53REnxy"  # 'money123'
    }
}


def _load_credentials() -> dict:
    """Fetch users from Firestore if available, otherwise return local default user."""
    if FIREBASE_AVAILABLE and db is not None:
        try:
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
            if not usernames:
                db.collection("users").document("ghost").set(_DEFAULT_USERS["ghost"])
                return {"usernames": _DEFAULT_USERS}
            return {"usernames": usernames}
        except Exception:
            return {"usernames": _DEFAULT_USERS}
    return {"usernames": _DEFAULT_USERS}


def _get_authenticator() -> stauth.Authenticate:
    """Load credentials and initialize stauth Authenticate class."""
    if "_mt_authenticator" not in st.session_state:
        creds = _load_credentials()
        
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
    Show login/register form or 1-click Instant Demo access if not authenticated.
    Adds user info + Logout button at the top of the sidebar.
    Returns the logged-in username as a string.
    """
    authenticator = _get_authenticator()

    # Only render the login/register form when not already authenticated in this session
    if st.session_state.get("authentication_status") is not True:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(124,58,237,0.12), rgba(124,58,237,0.03));
                    border: 1px solid rgba(124,58,237,0.25); border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <h3 style="margin: 0 0 8px 0; color: #7C3AED;">💰 Personal Finance & Intelligence Platform</h3>
            <p style="margin: 0; color: #E2E8F0; font-size: 0.95rem;">
                A comprehensive analytical dashboard tracking cash flows, 50/30/20 budget adherence,
                cash runway, debt optimization, and net worth trajectory across 12 months.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 1-Click Guest Tour Button for Evaluator
        col_demo, col_hint = st.columns([1, 1], gap="medium")
        with col_demo:
            if st.button("🚀 Instant Evaluator Tour (No Login Required)", type="primary", use_container_width=True):
                st.session_state["authentication_status"] = True
                st.session_state["username"] = "ghost"
                st.session_state["name"] = "Evaluator"
                st.rerun()
        with col_hint:
            st.caption("⚡ **Demo credentials**: `ghost` &nbsp;|&nbsp; password: `money123`")

        st.divider()

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
                st.error("❌ Incorrect username or password. Please try again or use the Instant Tour above.")
                st.stop()

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
                    user_data = authenticator.authentication_controller.authentication_model.credentials["usernames"][username]
                    db_user = {
                        "email": user_data.get("email", ""),
                        "failed_login_attempts": 0,
                        "logged_in": False,
                        "name": f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or username.capitalize(),
                        "password": user_data.get("password", "")
                    }
                    if FIREBASE_AVAILABLE and db is not None:
                        try:
                            db.collection("users").document(username).set(db_user)
                        except Exception:
                            pass
                    st.success("🎉 Registration successful! Please select '🔑 Log In' above to access your account.")
            except Exception as e:
                st.error(f"❌ Error during registration: {e}")
            st.stop()

    # ── Authenticated — add user chip + logout to sidebar top ─────────────────
    with st.sidebar:
        name = st.session_state.get("name", "Evaluator")
        st.markdown(
            f"""<div style="padding:6px 0 2px 0; font-size:0.88rem; opacity:0.85;">
            👤 &nbsp;<b>{name}</b> &nbsp;<span style="font-size:0.75rem; background:rgba(124,58,237,0.2); padding:2px 6px; border-radius:4px; color:#A78BFA;">Active</span></div>""",
            unsafe_allow_html=True,
        )
        if st.button("🚪 Logout", key="money_tracker_logout_btn", use_container_width=True):
            st.session_state["authentication_status"] = None
            st.session_state["username"] = None
            st.session_state["name"] = None
            st.rerun()
        st.divider()

    return st.session_state.get("username", "ghost")
