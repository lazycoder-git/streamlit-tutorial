"""firebase_db.py — Initializes Firebase Admin SDK if credentials exist, or gracefully falls back to local mode."""

import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

_ROOT = os.path.dirname(os.path.abspath(__file__))
_LOCAL_CREDS = os.path.join(_ROOT, "firebase_creds.json")

FIREBASE_AVAILABLE = False
db = None


def get_firestore_client():
    """Initialize Firebase App if credentials are provided, or return None."""
    global FIREBASE_AVAILABLE
    if not firebase_admin._apps:
        creds_dict = None
        # 1. Check Streamlit Cloud secrets first
        try:
            if "firebase" in st.secrets:
                creds_dict = dict(st.secrets["firebase"])
        except Exception:
            pass

        if creds_dict:
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            FIREBASE_AVAILABLE = True
            return firestore.client()

        # 2. Check local credentials file
        elif os.path.exists(_LOCAL_CREDS):
            try:
                cred = credentials.Certificate(_LOCAL_CREDS)
                firebase_admin.initialize_app(cred)
                FIREBASE_AVAILABLE = True
                return firestore.client()
            except Exception:
                FIREBASE_AVAILABLE = False
                return None

        # 3. No credentials provided — fallback to local mode
        else:
            FIREBASE_AVAILABLE = False
            return None
    else:
        FIREBASE_AVAILABLE = True
        return firestore.client()


try:
    db = get_firestore_client()
    if db is not None:
        FIREBASE_AVAILABLE = True
except Exception:
    db = None
    FIREBASE_AVAILABLE = False
