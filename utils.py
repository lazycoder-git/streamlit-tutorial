"""utils.py — Shared constants, data persistence layer, and sidebar helpers for Money Tracker."""

import os
import json
import pandas as pd
import streamlit as st
from firebase_db import db, FIREBASE_AVAILABLE
from demo_data import seed_local_data_files, generate_12_month_case_study

_ROOT = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_ROOT, "data")
os.makedirs(_DATA_DIR, exist_ok=True)

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

# ─── Data columns ─────────────────────────────────────────────────────────────
COLUMNS = [
    "id", "date", "type", "category", "account",
    "transfer_to", "amount", "note", "description", "source",
]


def ensure_data_files():
    """Ensure data files exist and are populated with rich demo data if empty."""
    tx_file = os.path.join(_DATA_DIR, "transactions.csv")
    bud_file = os.path.join(_DATA_DIR, "budgets.json")
    debt_file = os.path.join(_DATA_DIR, "debts.json")
    goal_file = os.path.join(_DATA_DIR, "goals.json")
    asset_file = os.path.join(_DATA_DIR, "assets.json")
    rec_file = os.path.join(_DATA_DIR, "recurring.json")

    needs_seed = False
    for path in (tx_file, bud_file, debt_file, goal_file, asset_file, rec_file):
        if not os.path.exists(path) or os.path.getsize(path) < 10:
            needs_seed = True
            break

    if needs_seed:
        seed_local_data_files()


# ─── Data I/O ─────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    """
    Load and type-cast transactions from Firestore or local data files.
    Guarantees non-empty data by falling back to the 12-month case study dataset.
    """
    username = st.session_state.get("username", "ghost")
    rows = []

    # 1. Attempt load from Firestore if available
    if FIREBASE_AVAILABLE and db is not None:
        try:
            tx_ref = db.collection("users").document(username).collection("transactions")
            docs = list(tx_ref.stream())
            for doc in docs:
                rows.append(doc.to_dict())
        except Exception:
            rows = []

    # 2. If no cloud rows found or Firebase disabled, load from local CSV
    if not rows:
        ensure_data_files()
        tx_file = os.path.join(_DATA_DIR, "transactions.csv")
        try:
            df_local = pd.read_csv(tx_file)
            if not df_local.empty:
                rows = df_local.to_dict(orient="records")
        except Exception:
            rows = []

    if not rows:
        return pd.DataFrame(columns=COLUMNS)

    df = pd.DataFrame(rows, columns=COLUMNS)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    for col in ("transfer_to", "note", "description", "source", "category", "account"):
        df[col] = df.get(col, pd.Series(dtype=str)).fillna("")
    return df


def is_first_run() -> bool:
    """Return True only if there is genuinely zero transaction data in both cloud and local."""
    df = load_data()
    return df.empty


def auto_backup(df: pd.DataFrame):
    """Save local backup for reliability."""
    try:
        backup_path = os.path.join(_DATA_DIR, "backup")
        os.makedirs(backup_path, exist_ok=True)
        df.to_csv(os.path.join(backup_path, "transactions_backup.csv"), index=False)
    except Exception:
        pass


def save_dataframe(df: pd.DataFrame):
    """Save DataFrame locally and synchronize with Firestore if available."""
    # 1. Save locally
    tx_file = os.path.join(_DATA_DIR, "transactions.csv")
    df.to_csv(tx_file, index=False)

    # 2. Sync to Firestore if available
    if FIREBASE_AVAILABLE and db is not None:
        try:
            username = st.session_state.get("username", "ghost")
            tx_ref = db.collection("users").document(username).collection("transactions")
            
            # Delete old docs
            for doc in tx_ref.stream():
                doc.reference.delete()

            # Write new docs
            for _, row in df.iterrows():
                row_dict = row.to_dict()
                if "date" in row_dict and pd.notnull(row_dict["date"]):
                    if isinstance(row_dict["date"], pd.Timestamp):
                        row_dict["date"] = row_dict["date"].strftime("%Y-%m-%d")
                    else:
                        row_dict["date"] = str(row_dict["date"])[:10]
                else:
                    row_dict["date"] = ""
                row_dict["amount"] = float(row_dict.get("amount", 0.0))
                doc_id = str(row_dict.get("id"))
                if not doc_id or doc_id in ("nan", "None"):
                    import uuid
                    doc_id = str(uuid.uuid4())[:8]
                    row_dict["id"] = doc_id
                tx_ref.document(doc_id).set(row_dict)
        except Exception:
            pass


def append_rows(rows: list[dict]):
    """Append one or more row dicts to local file and Firestore if active."""
    df = load_data()
    new_df = pd.DataFrame(rows)
    combined = pd.concat([df, new_df], ignore_index=True)
    save_dataframe(combined)


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
    ensure_data_files()
    fpath = os.path.join(_DATA_DIR, "budgets.json")
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return {k: float(v) for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}


def save_budgets(budgets: dict[str, float]):
    fpath = os.path.join(_DATA_DIR, "budgets.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(budgets, f, indent=2)


# ─── Recurring transaction helpers ────────────────────────────────────────────
def load_recurring() -> list[dict]:
    ensure_data_files()
    fpath = os.path.join(_DATA_DIR, "recurring.json")
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_recurring(templates: list[dict]):
    fpath = os.path.join(_DATA_DIR, "recurring.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(templates, f, indent=2)


# ─── Goals helpers ────────────────────────────────────────────────────────────
def load_goals() -> list[dict]:
    ensure_data_files()
    fpath = os.path.join(_DATA_DIR, "goals.json")
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_goals(goals: list[dict]):
    fpath = os.path.join(_DATA_DIR, "goals.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=2)


# ─── Debt helpers ─────────────────────────────────────────────────────────────
def load_debts() -> list[dict]:
    ensure_data_files()
    fpath = os.path.join(_DATA_DIR, "debts.json")
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_debts(debts: list[dict]):
    fpath = os.path.join(_DATA_DIR, "debts.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(debts, f, indent=2)


# ─── Assets helpers ───────────────────────────────────────────────────────────
def load_assets() -> dict[str, float]:
    ensure_data_files()
    fpath = os.path.join(_DATA_DIR, "assets.json")
    if os.path.exists(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return {k: float(v) for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}


def save_assets(assets: dict[str, float]):
    fpath = os.path.join(_DATA_DIR, "assets.json")
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(assets, f, indent=2)


# ─── Reset Demo Dataset Helper ────────────────────────────────────────────────
def reset_demo_data():
    """Regenerates the complete 12-month case study dataset across all collections."""
    seed_local_data_files()
    if FIREBASE_AVAILABLE and db is not None:
        try:
            study = generate_12_month_case_study()
            save_dataframe(pd.DataFrame(study["transactions"]))
        except Exception:
            pass


def render_demo_reset_sidebar():
    """Render a one-click button in sidebar to reload rich demo data."""
    st.sidebar.divider()
    st.sidebar.markdown("##### ⚡ Evaluator Tools")
    if st.sidebar.button("🔄 Reload 12-Mo Case Study Data", use_container_width=True, help="Re-seeds 12 months of rich financial data, budgets, goals, and debts"):
        reset_demo_data()
        st.sidebar.success("✅ Reloaded 12-month Case Study!")
        st.rerun()


# ─── Sidebar currency selector ────────────────────────────────────────────────
def render_currency_selector() -> str:
    """
    Render currency selectbox in sidebar and return the chosen symbol.
    Uses a stable key so the selection persists across pages.
    """
    stored = st.session_state.get("currency_selectbox", CURRENCY_KEYS[0])
    idx = CURRENCY_KEYS.index(stored) if stored in CURRENCY_KEYS else 0
    chosen = st.selectbox("🌐 Currency", CURRENCY_KEYS, index=idx,
                          key="currency_selectbox")
    sym = CURRENCIES[chosen]
    st.session_state["currency_symbol"] = sym
    return sym


def get_symbol() -> str:
    return st.session_state.get("currency_symbol", "₹")
