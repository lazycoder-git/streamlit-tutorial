"""auth.py — Login gate for Money Tracker. Call require_login() on every page."""

import os
import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth

_ROOT       = os.path.dirname(os.path.abspath(__file__))
_CREDS_FILE = os.path.join(_ROOT, "credentials.yaml")


def _get_authenticator() -> stauth.Authenticate:
    """Load or retrieve cached authenticator from session state."""
    if "_mt_authenticator" not in st.session_state:
        # 1. Try loading from Streamlit secrets first (useful for secure cloud deployment)
        if "credentials" in st.secrets and "cookie" in st.secrets:
            config = {
                "credentials": st.secrets["credentials"],
                "cookie": st.secrets["cookie"]
            }
        else:
            # 2. Fallback to credentials.yaml, auto-generating it if missing
            if not os.path.exists(_CREDS_FILE):
                default_config = {
                    "credentials": {
                        "usernames": {
                            "ghost": {
                                "email": "ghost@example.com",
                                "failed_login_attempts": 0,
                                "logged_in": False,
                                "name": "Ghost",
                                "password": "$2b$12$SaWrBuP6.o3MMTvVZ0ZTyeRr2tMNvfoWVL9dc/qsagW34h53REnxy"
                            }
                        }
                    },
                    "cookie": {
                        "expiry_days": 30.0,
                        "key": "money_tracker_secret_key_xk92bv",
                        "name": "money_tracker_auth"
                    }
                }
                with open(_CREDS_FILE, "w", encoding="utf-8") as f:
                    yaml.dump(default_config, f)

            with open(_CREDS_FILE, encoding="utf-8") as f:
                config = yaml.load(f, Loader=SafeLoader)

        st.session_state["_mt_authenticator"] = stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
            auto_hash=False,
        )
    return st.session_state["_mt_authenticator"]


def require_login() -> str:
    """
    Show login form if not authenticated.
    Adds user info + Logout button at the top of the sidebar.
    Returns the logged-in username as a string.

    Must be called AFTER st.set_page_config().
    """
    authenticator = _get_authenticator()

    # Only render the login form when not already authenticated in this session
    if st.session_state.get("authentication_status") is not True:
        _, auth_status, _ = authenticator.login(
            location="main",
            key="money_tracker_login",
        )

        if auth_status is False:
            st.error("❌ Incorrect username or password. Please try again.")
            st.stop()

        # auth_status is None (form shown, awaiting input) → stop rendering
        if st.session_state.get("authentication_status") is not True:
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
