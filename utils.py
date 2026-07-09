"""utils.py — Shared constants, data layer, and sidebar helpers for Money Tracker."""

import os
import pandas as pd
import streamlit as st

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

# ─── CSV columns ──────────────────────────────────────────────────────────────
COLUMNS = [
    "id", "date", "type", "category", "account",
    "transfer_to", "amount", "note", "description", "source",
]

# ─── File paths ───────────────────────────────────────────────────────────────
_ROOT     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(_ROOT, "data")
DATA_FILE = os.path.join(DATA_DIR, "transactions.csv")


# ─── Data I/O ─────────────────────────────────────────────────────────────────
def ensure_data_file():
    """Create data/ dir and an empty CSV with headers if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)


def load_data() -> pd.DataFrame:
    """Load and type-cast the transactions CSV."""
    ensure_data_file()
    try:
        df = pd.read_csv(DATA_FILE, dtype=str)
    except Exception:
        return pd.DataFrame(columns=COLUMNS)
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df["date"]   = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    for col in ("transfer_to", "note", "description", "source", "category", "account"):
        df[col] = df.get(col, pd.Series(dtype=str)).fillna("")
    return df


def save_dataframe(df: pd.DataFrame):
    """Overwrite the CSV with the given DataFrame."""
    out = df.copy()
    if "date" in out.columns and pd.api.types.is_datetime64_any_dtype(out["date"]):
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_FILE, index=False)


def append_rows(rows: list[dict]):
    """Append one or more row dicts to the CSV."""
    ensure_data_file()
    pd.DataFrame(rows, columns=COLUMNS).to_csv(
        DATA_FILE, mode="a", header=False, index=False
    )


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
