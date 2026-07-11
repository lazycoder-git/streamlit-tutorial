"""firebase_db.py — Initializes Firebase Admin SDK and exports the Firestore db client."""

import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

_ROOT = os.path.dirname(os.path.abspath(__file__))
_LOCAL_CREDS = os.path.join(_ROOT, "firebase_creds.json")


def get_firestore_client():
    """Initialize Firebase App if not already done, and return db client."""
    if not firebase_admin._apps:
        # 1. Check Streamlit Cloud secrets first
        creds_dict = None
        try:
            if "firebase" in st.secrets:
                creds_dict = dict(st.secrets["firebase"])
        except Exception:
            # Streamlit secrets file not found or firebase not in secrets
            pass

        if creds_dict:
            # We recreate a dictionary from secrets to bypass any AttrDict wrapping
            # Some properties like private_key can contain escaped newlines when configured as a secret string.
            # We must fix them so they are parsed correctly by Google OAuth library.
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(creds_dict)
        
        # 2. Fallback to local service account key file
        elif os.path.exists(_LOCAL_CREDS):
            cred = credentials.Certificate(_LOCAL_CREDS)
            
        else:
            # 3. Fallback to Application Default Credentials or raise a clear setup guide
            st.error(
                "❌ **Firebase credentials not found!**\n\n"
                "Please place your downloaded Firebase Service Account `.json` file at the root "
                "of this directory and rename it to **`firebase_creds.json`**.\n\n"
                "Or, if deploying on Streamlit Cloud, add the credentials under **Secrets** as "
                "a table named `[firebase]`."
            )
            st.stop()
            
        firebase_admin.initialize_app(cred)
        
    return firestore.client()


# Export database client instance
try:
    db = get_firestore_client()
except Exception as e:
    st.error(f"❌ Failed to connect to Firebase: {e}")
    st.stop()
