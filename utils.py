"""utils.py — Shared constants, data layer, and sidebar helpers for Money Tracker."""
# v2

import os
import json
import shutil
from datetime import datetime, timedelta

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

RECURRENCE_OPTS = ["Daily", "Weekly", "Monthly"]

GOAL_EMOJIS = ["🏠", "✈️", "🚗", "💻", "📱", "🎓", "💍", "🏖️", "🏋️", "🎯",
               "💰", "🛍️", "🎸", "📷", "⌚", "🌍", "🏥", "🎉", "🐾", "🌱"]

# ─── CSV columns ──────────────────────────────────────────────────────────────
COLUMNS = [
    "id", "date", "type", "category", "account",
    "transfer_to", "amount", "note", "description", "source",
]

# ─── File paths ───────────────────────────────────────────────────────────────
_ROOT          = os.path.dirname(os.path.abspath(__file__))
DATA_DIR       = os.path.join(_ROOT, "data")
DATA_FILE      = os.path.join(DATA_DIR, "transactions.csv")
BACKUP_DIR     = os.path.join(DATA_DIR, "backup")
BUDGET_FILE    = os.path.join(DATA_DIR, "budgets.json")
RECURRING_FILE = os.path.join(DATA_DIR, "recurring.json")
GOALS_FILE     = os.path.join(DATA_DIR, "goals.json")
DEBTS_FILE     = os.path.join(DATA_DIR, "debts.json")


# ─── Data I/O ─────────────────────────────────────────────────────────────────
def ensure_data_file():
    """Create data/ dir and an empty CSV with headers if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
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


def is_first_run() -> bool:
    """Return True when the app has no transaction data yet."""
    if not os.path.exists(DATA_FILE):
        return True
    try:
        df = pd.read_csv(DATA_FILE, dtype=str)
        return df.empty
    except Exception:
        return True


def auto_backup(df: pd.DataFrame):
    """Copy current data to data/backup/YYYY-MM.csv (monthly snapshot)."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m")
    dst   = os.path.join(BACKUP_DIR, f"transactions_{stamp}.csv")
    out   = df.copy()
    if "date" in out.columns and pd.api.types.is_datetime64_any_dtype(out["date"]):
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(dst, index=False)


def save_dataframe(df: pd.DataFrame):
    """Overwrite the CSV with the given DataFrame and create a monthly backup."""
    out = df.copy()
    if "date" in out.columns and pd.api.types.is_datetime64_any_dtype(out["date"]):
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_FILE, index=False)
    auto_backup(df)


def append_rows(rows: list[dict]):
    """Append one or more row dicts to the CSV."""
    ensure_data_file()
    pd.DataFrame(rows, columns=COLUMNS).to_csv(
        DATA_FILE, mode="a", header=False, index=False
    )


# ─── Duplicate detection ──────────────────────────────────────────────────────
def check_duplicate(df: pd.DataFrame, tx_type: str, category: str,
                    amount: float, tx_date, window_days: int = 7) -> bool:
    """Return True if a very similar transaction exists within window_days."""
    if df.empty:
        return False
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
    if not os.path.exists(BUDGET_FILE):
        return {}
    try:
        with open(BUDGET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_budgets(budgets: dict[str, float]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BUDGET_FILE, "w", encoding="utf-8") as f:
        json.dump(budgets, f, indent=2)


# ─── Recurring transaction helpers ────────────────────────────────────────────
def load_recurring() -> list[dict]:
    if not os.path.exists(RECURRING_FILE):
        return []
    try:
        with open(RECURRING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_recurring(templates: list[dict]):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RECURRING_FILE, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2, default=str)


# ─── Goals helpers ────────────────────────────────────────────────────────────
def load_goals() -> list[dict]:
    """Load financial goals from JSON."""
    if not os.path.exists(GOALS_FILE):
        return []
    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_goals(goals: list[dict]):
    """Persist financial goals to JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=2, default=str)


# ─── Debt helpers ─────────────────────────────────────────────────────────────
def load_debts() -> list[dict]:
    """Load debt records from JSON."""
    if not os.path.exists(DEBTS_FILE):
        return []
    try:
        with open(DEBTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_debts(debts: list[dict]):
    """Persist debt records to JSON."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DEBTS_FILE, "w", encoding="utf-8") as f:
        json.dump(debts, f, indent=2, default=str)


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
