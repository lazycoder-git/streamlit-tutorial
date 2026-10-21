"""pages/1_Add_Transaction.py — Log income, expense, or transfer."""

from sympy import div
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import uuid
from datetime import date

from utils import (
    load_data, append_rows, render_currency_selector, render_demo_reset_sidebar,
    ACCOUNTS, INCOME_CATS, EXPENSE_CATS,
    load_budgets, check_duplicate,
)
from auth import require_login

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Add Transaction — Money Tracker",
    page_icon="➕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth gate ──────────────────────────────────────────────────────────────────
require_login()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Money Tracker")
    st.divider()
    sym = render_currency_selector()
    render_demo_reset_sidebar()

# ── Type themes ────────────────────────────────────────────────────────────────
THEMES = {
    "Income": {
        "color":    "#2ecc71",
        "bg":       "rgba(46,204,113,0.09)",
        "border":   "rgba(46,204,113,0.5)",
        "icon":     "📈",
        "label":    "Income Transaction",
        "btn_type": "primary",
    },
    "Expense": {
        "color":    "#e74c3c",
        "bg":       "rgba(231,76,60,0.09)",
        "border":   "rgba(231,76,60,0.5)",
        "icon":     "📉",
        "label":    "Expense Transaction",
        "btn_type": "primary",
    },
    "Transfer": {
        "color":    "#ecf0f1",
        "bg":       "rgba(236,240,241,0.06)",
        "border":   "rgba(236,240,241,0.35)",
        "icon":     "↔",
        "label":    "Transfer Between Accounts",
        "btn_type": "secondary",
    },
}

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("➕ Add Transaction")
st.caption("Record a new income, expense, or transfer between accounts.")
st.divider()

# Load existing transactions to extract custom entries dynamically
df = load_data()
budgets = load_budgets()

# Extract unique accounts and categories dynamically
used_accounts = []
used_categories = []
if not df.empty:
    used_accounts = df["account"].dropna().unique().tolist()
    used_categories = df["category"].dropna().unique().tolist()
    used_categories = [c for c in used_categories if c and c != "Transfer"]

# Build merged lists
accounts_list = sorted(list(set(ACCOUNTS + used_accounts)))

# ── Transaction type selector ─────────────────────────────────────────────────
tx_type = st.radio(
    "Transaction Type",
    ["Income", "Expense", "Transfer"],
    index=1,
    horizontal=True,
    key="tx_type_radio",
    label_visibility="collapsed",
)

theme = THEMES[tx_type]

# Coloured banner



st.markdown(f"""
<div style="
    background: linear-gradient(90deg, {theme['bg']}, transparent);
    border-left: 4px solid {theme['color']};
    border-radius: 8px;
    padding: 14px 20px;
    margin: 0.8rem 0 1.2rem 0;
">
    <span style="color:{theme['color']}; font-size:1.15rem; font-weight:700;">
        {theme['icon']}&nbsp;&nbsp;{theme['label']}
    </span>
</div>
""", unsafe_allow_html=True)

# ── Form fields ────────────────────────────────────────────────────────────────
if tx_type == "Transfer":
    col1, col2 = st.columns(2)
    with col1:
        tx_date   = st.date_input("📅 Date", value=date.today(), key="tx_date")
        tx_amount = st.number_input(
            f"💵 Amount ({sym})", min_value=0.01, value=1000.0,
            step=100.0, format="%.2f", key="tx_amount",
        )
    with col2:
        from_acc_opts = accounts_list + ["➕ Add Custom Account..."]
        from_acc_sel = st.selectbox("🏦 From Account", from_acc_opts, key="tx_from_acc_select")
        if from_acc_sel == "➕ Add Custom Account...":
            from_acc = st.text_input("📝 Enter New From Account", key="tx_from_acc_custom").strip()
        else:
            from_acc = from_acc_sel

        to_base_opts = [a for a in accounts_list if a != from_acc]
        to_acc_opts = to_base_opts + ["➕ Add Custom Account..."]
        to_acc_sel = st.selectbox("➡️ To Account", to_acc_opts, key="tx_to_acc_select")
        if to_acc_sel == "➕ Add Custom Account...":
            to_acc = st.text_input("📝 Enter New To Account", key="tx_to_acc_custom").strip()
        else:
            to_acc = to_acc_sel

    col3, col4 = st.columns(2)
    with col3:
        tx_note = st.text_input(
            "📝 Note", placeholder="e.g. Moving to savings", key="tx_note",
        )
    with col4:
        tx_desc = st.text_area(
            "📋 Description (optional)",
            placeholder="Any additional details…",
            height=102, key="tx_desc",
        )
    submit_label = "↔  Add Transfer"
    tx_cat = "Transfer"
    tx_acc = from_acc

    is_recurring = False
    recur_freq = None

else:
    defaults = INCOME_CATS if tx_type == "Income" else EXPENSE_CATS
    used_type_cats = []
    if not df.empty:
        used_type_cats = df[df["type"] == tx_type]["category"].dropna().unique().tolist()
    categories_list = sorted(list(set(defaults + used_type_cats)))

    col1, col2 = st.columns(2)
    with col1:
        tx_date   = st.date_input("📅 Date", value=date.today(), key="tx_date")
        tx_amount = st.number_input(
            f"💵 Amount ({sym})",
            min_value=0.01,
            value=100.0 if tx_type == "Expense" else 1000.0,
            step=100.0, format="%.2f", key="tx_amount",
        )
    with col2:
        cat_opts = categories_list + ["➕ Add Custom Category..."]
        tx_cat_sel = st.selectbox("🏷️ Category", cat_opts, key="tx_cat_select")
        if tx_cat_sel == "➕ Add Custom Category...":
            tx_cat = st.text_input("📝 Enter New Category", key="tx_cat_custom").strip()
        else:
            tx_cat = tx_cat_sel

        acc_opts = accounts_list + ["➕ Add Custom Account..."]
        tx_acc_sel = st.selectbox("🏦 Account", acc_opts, key="tx_acc_select")
        if tx_acc_sel == "➕ Add Custom Account...":
            tx_acc = st.text_input("📝 Enter New Account", key="tx_acc_custom").strip()
        else:
            tx_acc = tx_acc_sel

    col3, col4 = st.columns(2)
    with col3:
        tx_note = st.text_input(
            "📝 Note",
            placeholder='"Monthly salary"' if tx_type == "Income" else '"Dinner out"',
            key="tx_note",
        )
    with col4:
        tx_desc = st.text_area(
            "📋 Description (optional)",
            placeholder="Any additional details…",
            height=102, key="tx_desc",
        )

    # ── Real-Time Financial Impact & Analytical Sensitivity Simulator ────────
    if tx_type == "Expense" and tx_cat and tx_amount > 0:
        month_num = tx_date.month
        year_num  = tx_date.year
        m_mask = (df["date"].dt.month == month_num) & (df["date"].dt.year == year_num)
        mdf_cur = df[m_mask] if not df.empty else pd.DataFrame()
        
        cur_inc = float(mdf_cur[mdf_cur["type"] == "Income"]["amount"].sum()) if not mdf_cur.empty else 4200.0
        cur_exp = float(mdf_cur[mdf_cur["type"] == "Expense"]["amount"].sum()) if not mdf_cur.empty else 0.0
        
        cur_savings = cur_inc - cur_exp
        cur_sav_rate = (cur_savings / cur_inc * 100) if cur_inc > 0 else 0.0
        
        post_exp = cur_exp + tx_amount
        post_savings = cur_inc - post_exp
        post_sav_rate = (post_savings / cur_inc * 100) if cur_inc > 0 else 0.0
        
        # Budget check
        budget_limit = budgets.get(tx_cat, 0.0)
        cat_spent = float(mdf_cur[(mdf_cur["type"] == "Expense") & (mdf_cur["category"] == tx_cat)]["amount"].sum()) if not mdf_cur.empty else 0.0
        new_cat_spent = cat_spent + tx_amount

        st.markdown("##### ⚡ Real-Time Financial Impact Simulation")
        sim_col1, sim_col2, sim_col3 = st.columns(3)
        sim_col1.metric(
            "This Month's Outflow",
            f"{sym}{post_exp:,.2f}",
            delta=f"+{sym}{tx_amount:,.2f} increase",
            delta_color="inverse"
        )
        sim_col2.metric(
            "Projected Savings Rate",
            f"{post_sav_rate:.1f}%",
            delta=f"{post_sav_rate - cur_sav_rate:.1f}% shift",
            delta_color="normal" if post_sav_rate >= 20 else "inverse"
        )
        if budget_limit > 0:
            pct_used = (new_cat_spent / budget_limit) * 100
            sim_col3.metric(
                f"{tx_cat} Budget Utilization",
                f"{pct_used:.1f}%",
                delta=f"{sym}{budget_limit - new_cat_spent:,.2f} remaining" if new_cat_spent <= budget_limit else f"-{sym}{new_cat_spent - budget_limit:,.2f} over limit",
                delta_color="normal" if new_cat_spent <= budget_limit else "inverse"
            )
        else:
            sim_col3.metric("Category Allocation", tx_cat, delta="Unbudgeted category")

        # Behavioral & Analytical Insight Box
        st.markdown(f"""
        <div style="background: rgba(124,58,237,0.08); border-left: 4px solid #7C3AED; padding: 12px 16px; border-radius: 6px; margin-top: 10px; margin-bottom: 15px;">
            <span style="font-size: 0.85rem; font-weight: 700; color: #A78BFA; text-transform: uppercase;">🧠 What This Entry Conveys & Analytical Takeaway</span>
            <p style="margin: 4px 0 0 0; font-size: 0.92rem; color: #E2E8F0; line-height: 1.5;">
                Adding this <b>{sym}{tx_amount:,.2f}</b> expense to <b>{tx_cat}</b> adjusts your monthly net savings rate from <b>{cur_sav_rate:.1f}%</b> to <b>{post_sav_rate:.1f}%</b>.
                {' Maintaining a savings rate above 20% complies with wealth accumulation targets.' if post_sav_rate >= 20 else ' ⚠️ Note: This pushes your savings rate below the recommended 20% threshold. Consider balancing with non-essential spending reductions elsewhere.'}
            </p>
        </div>
        """, unsafe_allow_html=True)

    icon = "📈" if tx_type == "Income" else "📉"
    submit_label = f"{icon}  Add {tx_type}"
    to_acc = ""

    is_recurring = False
    recur_freq = None

st.divider()

# ── Submit button ──────────────────────────────────────────────────────────────
_, btn_col, _ = st.columns([2, 1, 2])
with btn_col:
    submitted = st.button(submit_label, type="primary", use_container_width=True)

if submitted:
    if tx_amount <= 0:
        st.error("Amount must be greater than zero.")
    elif tx_type == "Transfer" and from_acc == to_acc:
        st.error("From Account and To Account cannot be the same.")
    elif tx_type == "Transfer" and (not from_acc or not to_acc):
        st.error("Please enter names for both From Account and To Account.")
    elif tx_type != "Transfer" and (not tx_cat or not tx_acc):
        st.error("Please enter names for both Category and Account.")
    else:
        # ── Duplicate detection ────────────────────────────────────────────────
        if check_duplicate(df, tx_type, tx_cat, tx_amount, tx_date):
            st.warning(
                f"⚠️ **Possible duplicate detected!** A similar **{tx_type}** of "
                f"**{sym}{tx_amount:,.2f}** in **{tx_cat}** was already recorded "
                f"within the last 7 days. If this is intentional, submit again to confirm.",
                icon="⚠️",
            )
            # Use session state flag to allow second-click confirmation
            if not st.session_state.get("dup_confirmed", False):
                st.session_state["dup_confirmed"] = True
                st.stop()

        st.session_state["dup_confirmed"] = False

        row = dict(
            id=str(uuid.uuid4())[:8],
            date=str(tx_date),
            type=tx_type,
            category=tx_cat,
            account=tx_acc,
            transfer_to=to_acc,
            amount=tx_amount,
            note=tx_note.strip(),
            description=tx_desc.strip(),
            source="user",
        )
        append_rows([row])

        if tx_type == "Transfer":
            st.success(
                f"✅ Transfer of **{sym}{tx_amount:,.2f}** from "
                f"**{from_acc}** → **{to_acc}** recorded!"
            )
        else:
            st.success(
                f"✅ **{tx_type}** of **{sym}{tx_amount:,.2f}** "
                f"({tx_cat}) recorded successfully!"
            )

# ── Recent entries preview ────────────────────────────────────────────────────
st.divider()
st.subheader("🕐 Recent Entries")
df = load_data()
if not df.empty:
    recent = (
        df.sort_values("date", ascending=False)
        .head(8)[["date", "type", "category", "account", "amount", "note"]]
        .copy()
    )
    recent["date"] = recent["date"].dt.strftime("%d %b %Y")
    recent["amount"] = recent.apply(
        lambda row: f"+{sym}{row['amount']:,.2f}" if row["type"] == "Income"
                    else (f"↔ {sym}{row['amount']:,.2f}" if row["type"] == "Transfer"
                          else f"-{sym}{row['amount']:,.2f}"),
        axis=1,
    )
    recent.columns = ["Date", "Type", "Category", "Account", "Amount", "Note"]
    st.dataframe(recent, use_container_width=True, hide_index=True)
else:
    st.info("No transactions yet.")
