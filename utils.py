"""utils.py — Shared constants, Firestore data layer, and sidebar helpers for Money Tracker."""
# v4 — Firebase Firestore Integration

import os
import pandas as pd
import streamlit as st
from firebase_db import db

# ─── Currency map ─────────────────────────────────────────────────────────────
CURRENCIES: dict[str, str] = {
    "₹  Indian Rupee (INR)":      "₹",
    "$  US Dollar (USD)":          "$",
    "€  Euro (EUR)":               "€",
    "£  British Pound (GBP)":      "£",
    "¥  Japanese Yen (JPY)":       "¥",
    "¥  Chinese Yuan (CNY)":       "¥",
    "₩  South Korean Won (KRW)":   "₩",
    "A$ Australian Dollar (AUD)":  "A$",
    "C$ Canadian Dollar (CAD)":    "C$",
    "Fr Swiss Franc (CHF)":        "Fr",
    "﷼  Saudi Riyal (SAR)":       "﷼",
    "د.إ UAE Dirham (AED)":        "د.إ",
}
CURRENCY_KEYS = list(CURRENCIES.keys())

# ─── Accounts & categories ────────────────────────────────────────────────────
ACCOUNTS = ["Bank Account", "Cash", "Credit Card", "Savings", "Wallet"]

INCOME_CATS = [
    "Salary", "Freelance", "Business", "Investment", "Gift", "Refund", "Other"
]
EXPENSE_CATS = [
    "Food & Dining", "Transport", "Rent", "Utilities", "Entertainment",
    "Health", "Shopping", "Education", "Personal Care", "Travel",
    "Subscriptions", "Other",
]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

RECURRENCE_OPTS = ["Daily", "Weekly", "Monthly"]

GOAL_EMOJIS = ["🏠", "✈️", "🚗", "💻", "📱", "🎓", "💍", "🏖️", "🏋️", "🎯",
               "💰", "🛍️", "🎸", "📷", "⌚", "🌍", "🏥", "🎉", "🐾", "🌱"]

# ─── Firestore columns ────────────────────────────────────────────────────────
COLUMNS = [
    "id", "date", "type", "category", "account",
    "transfer_to", "amount", "note", "description", "source",
]


# ─── Data I/O ─────────────────────────────────────────────────────────────────
def ensure_data_file():
    """No-op for backward compatibility (formerly created local files)."""
    pass


def load_data() -> pd.DataFrame:
    """Load and type-cast the transactions from Firestore for the current user."""
    username = st.session_state.get("username", "default")
    tx_ref = db.collection("users").document(username).collection("transactions")
    docs = tx_ref.stream()

    rows = []
    for doc in docs:
        rows.append(doc.to_dict())

    if not rows:
        return pd.DataFrame(columns=COLUMNS)

    df = pd.DataFrame(rows, columns=COLUMNS)
    df["date"]   = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    for col in ("transfer_to", "note", "description", "source", "category", "account"):
        df[col] = df.get(col, pd.Series(dtype=str)).fillna("")
    return df


def is_first_run() -> bool:
    """Return True when the current user has no transaction data in Firestore yet."""
    username = st.session_state.get("username", "default")
    tx_ref = db.collection("users").document(username).collection("transactions")
    docs = tx_ref.limit(1).get()
    return len(docs) == 0


def auto_backup(df: pd.DataFrame):
    """No-op for backward compatibility (Firestore handles cloud durability)."""
    pass


def save_dataframe(df: pd.DataFrame):
    """Overwrite the Firestore transactions collection with the given DataFrame."""
    username = st.session_state.get("username", "default")
    tx_ref = db.collection("users").document(username).collection("transactions")

    # 1. Delete all existing transaction documents
    existing_docs = tx_ref.stream()
    for doc in existing_docs:
        doc.reference.delete()

    # 2. Write new rows
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        
        # Format date correctly
        if "date" in row_dict and pd.notnull(row_dict["date"]):
            if isinstance(row_dict["date"], pd.Timestamp):
                row_dict["date"] = row_dict["date"].strftime("%Y-%m-%d")
            else:
                row_dict["date"] = str(row_dict["date"])[:10]
        else:
            row_dict["date"] = ""

        row_dict["amount"] = float(row_dict.get("amount", 0.0))
        
        # Ensure we have a valid document ID
        doc_id = str(row_dict.get("id"))
        if not doc_id or doc_id == "nan" or doc_id == "None":
            import uuid
            doc_id = str(uuid.uuid4())[:8]
            row_dict["id"] = doc_id
            
        tx_ref.document(doc_id).set(row_dict)


def append_rows(rows: list[dict]):
    """Append one or more row dicts as documents in Firestore."""
    username = st.session_state.get("username", "default")
    tx_ref = db.collection("users").document(username).collection("transactions")
    
    for row in rows:
        row_dict = dict(row)
        row_dict["amount"] = float(row_dict.get("amount", 0.0))
        
        # Ensure we have a valid document ID
        doc_id = str(row_dict.get("id"))
        if not doc_id or doc_id == "nan" or doc_id == "None":
            import uuid
            doc_id = str(uuid.uuid4())[:8]
            row_dict["id"] = doc_id
            
        tx_ref.document(doc_id).set(row_dict)


# ─── Duplicate detection ──────────────────────────────────────────────────────
def check_duplicate(df: pd.DataFrame, tx_type: str, category: str,
                    amount: float, tx_date, window_days: int = 7) -> bool:
    """Return True if a very similar transaction exists within window_days."""
    if df.empty:
        return False
    from datetime import timedelta
    cutoff = pd.Timestamp(tx_date) - timedelta(days=window_days)
    recent = df[df["date"] >= cutoff]
    if recent.empty:
        return False
    matches = recent[
        (recent["type"]     == tx_type) &
        (recent["category"] == category) &
        (recent["amount"].between(amount * 0.99, amount * 1.01))
    ]
    return len(matches) > 0


# ─── Budget helpers ───────────────────────────────────────────────────────────
def load_budgets() -> dict[str, float]:
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("budgets")
    doc = doc_ref.get()
    if doc.exists:
        return {k: float(v) for k, v in doc.to_dict().items()}
    return {}


def save_budgets(budgets: dict[str, float]):
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("budgets")
    data = {k: float(v) for k, v in budgets.items()}
    doc_ref.set(data)


# ─── Recurring transaction helpers ────────────────────────────────────────────
def load_recurring() -> list[dict]:
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("recurring")
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("list", [])
    return []


def save_recurring(templates: list[dict]):
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("recurring")
    doc_ref.set({"list": templates})


# ─── Goals helpers ────────────────────────────────────────────────────────────
def load_goals() -> list[dict]:
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("goals")
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("list", [])
    return []


def save_goals(goals: list[dict]):
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("goals")
    doc_ref.set({"list": goals})


# ─── Debt helpers ─────────────────────────────────────────────────────────────
def load_debts() -> list[dict]:
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("debts")
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get("list", [])
    return []


def save_debts(debts: list[dict]):
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("debts")
    doc_ref.set({"list": debts})


# ─── Assets helpers ───────────────────────────────────────────────────────────
def load_assets() -> dict[str, float]:
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("assets")
    doc = doc_ref.get()
    if doc.exists:
        return {k: float(v) for k, v in doc.to_dict().items()}
    return {}


def save_assets(assets: dict[str, float]):
    username = st.session_state.get("username", "default")
    doc_ref = db.collection("users").document(username).collection("data").document("assets")
    data = {k: float(v) for k, v in assets.items()}
    doc_ref.set(data)


# ─── Sidebar currency selector ────────────────────────────────────────────────
def render_currency_selector() -> str:
    """
    Render currency selectbox in sidebar and return the chosen symbol.
    Uses a stable key so the selection persists across pages.
    """
    stored = st.session_state.get("currency_selectbox", CURRENCY_KEYS[0])
    idx    = CURRENCY_KEYS.index(stored) if stored in CURRENCY_KEYS else 0
    chosen = st.selectbox("🌐 Currency", CURRENCY_KEYS, index=idx,
                          key="currency_selectbox")
    sym = CURRENCIES[chosen]
    st.session_state["currency_symbol"] = sym
    return sym


def get_symbol() -> str:
    return st.session_state.get("currency_symbol", "₹")
