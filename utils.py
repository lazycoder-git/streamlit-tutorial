"""utils.py — Shared constants, data layer, and sidebar helpers for Money Tracker."""
# v3 — per-user data directories

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

# ─── Root paths ───────────────────────────────────────────────────────────────
_ROOT          = os.path.dirname(os.path.abspath(__file__))
_BASE_DATA_DIR = os.path.join(_ROOT, "data")

# DATA_DIR kept for backwards compatibility (imported by 8_Net_Worth.py)
DATA_DIR = _BASE_DATA_DIR


# ─── Per-user data directory ──────────────────────────────────────────────────
def get_user_data_dir() -> str:
    """Return and create the data directory for the currently logged-in user."""
    username = st.session_state.get("username", "default")
    d = os.path.join(_BASE_DATA_DIR, username)
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(d, "backup"), exist_ok=True)
    return d


# ─── Internal path helpers ────────────────────────────────────────────────────
def _data_file()      -> str: return os.path.join(get_user_data_dir(), "transactions.csv")
def _backup_dir()     -> str: return os.path.join(get_user_data_dir(), "backup")
def _budget_file()    -> str: return os.path.join(get_user_data_dir(), "budgets.json")
def _recurring_file() -> str: return os.path.join(get_user_data_dir(), "recurring.json")
def _goals_file()     -> str: return os.path.join(get_user_data_dir(), "goals.json")
def _debts_file()     -> str: return os.path.join(get_user_data_dir(), "debts.json")
def _assets_file()    -> str: return os.path.join(get_user_data_dir(), "assets.json")


# ─── Data I/O ─────────────────────────────────────────────────────────────────
def ensure_data_file():
    """Create the user's data dir and an empty CSV with headers if missing."""
    data_file = _data_file()
    if not os.path.exists(data_file):
        pd.DataFrame(columns=COLUMNS).to_csv(data_file, index=False)


def load_data() -> pd.DataFrame:
    """Load and type-cast the transactions CSV for the current user."""
    ensure_data_file()
    try:
        df = pd.read_csv(_data_file(), dtype=str)
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
    """Return True when the current user has no transaction data yet."""
    f = _data_file()
    if not os.path.exists(f):
        return True
    try:
        df = pd.read_csv(f, dtype=str)
        return df.empty
    except Exception:
        return True


def auto_backup(df: pd.DataFrame):
    """Copy current data to backup/YYYY-MM.csv (monthly snapshot)."""
    stamp = datetime.now().strftime("%Y-%m")
    dst   = os.path.join(_backup_dir(), f"transactions_{stamp}.csv")
    out   = df.copy()
    if "date" in out.columns and pd.api.types.is_datetime64_any_dtype(out["date"]):
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(dst, index=False)


def save_dataframe(df: pd.DataFrame):
    """Overwrite the CSV with the given DataFrame and create a monthly backup."""
    out = df.copy()
    if "date" in out.columns and pd.api.types.is_datetime64_any_dtype(out["date"]):
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(_data_file(), index=False)
    auto_backup(df)


def append_rows(rows: list[dict]):
    """Append one or more row dicts to the CSV."""
    ensure_data_file()
    pd.DataFrame(rows, columns=COLUMNS).to_csv(
        _data_file(), mode="a", header=False, index=False
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
    f = _budget_file()
    if not os.path.exists(f):
        return {}
    try:
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return {}


def save_budgets(budgets: dict[str, float]):
    with open(_budget_file(), "w", encoding="utf-8") as fp:
        json.dump(budgets, fp, indent=2)


# ─── Recurring transaction helpers ────────────────────────────────────────────
def load_recurring() -> list[dict]:
    f = _recurring_file()
    if not os.path.exists(f):
        return []
    try:
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return []


def save_recurring(templates: list[dict]):
    with open(_recurring_file(), "w", encoding="utf-8") as fp:
        json.dump(templates, fp, indent=2, default=str)


# ─── Goals helpers ────────────────────────────────────────────────────────────
def load_goals() -> list[dict]:
    """Load financial goals from JSON."""
    f = _goals_file()
    if not os.path.exists(f):
        return []
    try:
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return []


def save_goals(goals: list[dict]):
    """Persist financial goals to JSON."""
    with open(_goals_file(), "w", encoding="utf-8") as fp:
        json.dump(goals, fp, indent=2, default=str)


# ─── Debt helpers ─────────────────────────────────────────────────────────────
def load_debts() -> list[dict]:
    """Load debt records from JSON."""
    f = _debts_file()
    if not os.path.exists(f):
        return []
    try:
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return []


def save_debts(debts: list[dict]):
    """Persist debt records to JSON."""
    with open(_debts_file(), "w", encoding="utf-8") as fp:
        json.dump(debts, fp, indent=2, default=str)


# ─── Assets helpers ───────────────────────────────────────────────────────────
def load_assets() -> dict[str, float]:
    """Load manual assets (e.g. stocks, gold) from JSON."""
    f = _assets_file()
    if not os.path.exists(f):
        return {}
    try:
        with open(f, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return {}


def save_assets(assets: dict[str, float]):
    """Persist manual assets to JSON."""
    with open(_assets_file(), "w", encoding="utf-8") as fp:
        json.dump(assets, fp, indent=2)


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
