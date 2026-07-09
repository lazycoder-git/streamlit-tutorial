"""pages/2_History.py — Filter, view, delete, and export transactions."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from datetime import date

from utils import (
    load_data, save_dataframe, get_symbol,
    ACCOUNTS, INCOME_CATS, EXPENSE_CATS,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="History — Money Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

ALL_CATS = sorted(set(INCOME_CATS + EXPENSE_CATS + ["Transfer"]))

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Money Tracker")
    st.divider()
    sym = get_symbol()

    st.subheader("🔍 Filters")

    today = date.today()
    start_default = date(today.year, today.month, 1)
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("From", value=start_default, key="h_start")
    with c2:
        end_date = st.date_input("To",   value=today,         key="h_end")

    type_filter = st.selectbox(
        "Type", ["All", "Income", "Expense", "Transfer"], key="h_type"
    )

    if type_filter == "Income":
        cat_opts = INCOME_CATS
    elif type_filter == "Expense":
        cat_opts = EXPENSE_CATS
    elif type_filter == "Transfer":
        cat_opts = ["Transfer"]
    else:
        cat_opts = ALL_CATS

    sel_cats = st.multiselect("Category", cat_opts, key="h_cats")
    sel_accs = st.multiselect("Account",  ACCOUNTS, key="h_accs")




# ── Load data ──────────────────────────────────────────────────────────────────
df = load_data()

st.title("📋 Transaction History")

if df.empty:
    st.info("No transactions yet. Add some from the **Add Transaction** page!")
    st.stop()

# ── Apply filters ──────────────────────────────────────────────────────────────
mask = (
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
)
if type_filter != "All":
    mask &= df["type"] == type_filter
if sel_cats:
    mask &= df["category"].isin(sel_cats)
if sel_accs:
    mask &= df["account"].isin(sel_accs)

filtered = df[mask].copy().sort_values("date", ascending=False)

st.caption(f"Showing **{len(filtered)}** of **{len(df)}** transactions")
st.divider()

# ── Summary metrics ────────────────────────────────────────────────────────────
inc = float(filtered[filtered["type"] == "Income"]["amount"].sum())
exp = float(filtered[filtered["type"] == "Expense"]["amount"].sum())
net = inc - exp
m1, m2, m3, m4 = st.columns(4)
m1.metric("Records",   len(filtered))
m2.metric("Income",    f"{sym}{inc:,.2f}")
m3.metric("Expenses",  f"{sym}{exp:,.2f}")
m4.metric("Net",       f"{sym}{net:,.2f}")

st.divider()

# ── Data table with delete checkboxes ─────────────────────────────────────────
if filtered.empty:
    st.info("No transactions match the current filters.")
    st.stop()

# Build display frame — keep original index for deletion mapping
display_cols = ["date", "type", "category", "account", "amount",
                "note", "transfer_to", "source"]
display = filtered[display_cols].copy()
display["date"] = display["date"].dt.strftime("%d %b %Y")

# Store original row indices for deletion
orig_indices = filtered.index.tolist()
display_reset = display.reset_index(drop=True)
display_reset.insert(0, "🗑", False)

edited = st.data_editor(
    display_reset,
    use_container_width=True,
    hide_index=True,
    column_config={
        "🗑":         st.column_config.CheckboxColumn("Delete", default=False),
        "amount":     st.column_config.NumberColumn("Amount", format="%.2f"),
        "date":       st.column_config.TextColumn("Date"),
        "type":       st.column_config.TextColumn("Type"),
        "category":   st.column_config.TextColumn("Category"),
        "account":    st.column_config.TextColumn("Account"),
        "note":       st.column_config.TextColumn("Note"),
        "transfer_to":st.column_config.TextColumn("Transfer To"),
        "source":     st.column_config.TextColumn("Source"),
    },
    disabled=["date","type","category","account","amount",
              "note","transfer_to","source"],
    key="hist_editor",
)

# Map checked rows back to original df indices
delete_positions = edited[edited["🗑"]].index.tolist()
del_orig = [orig_indices[pos] for pos in delete_positions]
n_del = len(del_orig)

col_del, col_dl, _ = st.columns([1, 2, 2])
with col_del:
    if st.button(
        f"🗑 Delete {n_del} row{'s' if n_del != 1 else ''}",
        disabled=(n_del == 0),
        type="secondary",
    ):
        remaining = df.drop(index=del_orig).reset_index(drop=True)
        save_dataframe(remaining)
        st.success(f"Deleted {n_del} transaction(s).")
        st.rerun()

with col_dl:
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download filtered data as CSV",
        data=csv_bytes,
        file_name="transactions_filtered.csv",
        mime="text/csv",
    )
