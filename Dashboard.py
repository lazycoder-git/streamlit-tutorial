"""Dashboard.py — Dashboard page for Personal Money Tracker."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils import load_data, render_currency_selector, MONTHS

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Money Tracker — Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Money Tracker")
    st.divider()
    sym = render_currency_selector()
    st.divider()

    now = datetime.now()
    sel_month_name = st.selectbox("📅 Month", MONTHS, index=now.month - 1,
                                   key="dash_month")
    sel_year = st.number_input("Year", min_value=2020, max_value=2035,
                                value=now.year, step=1, key="dash_year")
    month_num = MONTHS.index(sel_month_name) + 1

    st.divider()
    savings_goal = st.number_input(
        f"🎯 Monthly Savings Goal ({sym})",
        min_value=0.0, value=5000.0, step=500.0, format="%.2f",
        key="dash_goal",
    )

# ── Load & filter data ─────────────────────────────────────────────────────────
df = load_data()

if not df.empty:
    mask = (
        (df["date"].dt.month == month_num) &
        (df["date"].dt.year  == int(sel_year))
    )
    mdf = df[mask].copy()
else:
    mdf = pd.DataFrame()

income   = float(mdf[mdf["type"] == "Income"]["amount"].sum())   if not mdf.empty else 0.0
expenses = float(mdf[mdf["type"] == "Expense"]["amount"].sum())  if not mdf.empty else 0.0
balance  = income - expenses
sav_rate = (balance / income * 100) if income > 0 else 0.0

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 Dashboard")
st.caption(f"Your financial overview for **{sel_month_name} {int(sel_year)}**")
st.divider()

# ── Metric cards ───────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
bal_color = "normal" if balance >= 0 else "inverse"
c1.metric("💳 Net Balance",     f"{sym}{balance:,.2f}")
c2.metric("📈 Total Income",    f"{sym}{income:,.2f}")
c3.metric("📉 Total Expenses",  f"{sym}{expenses:,.2f}")
c4.metric("💰 Savings Rate",    f"{sav_rate:.1f}%")

st.divider()

# ── Main layout ────────────────────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

# ── LEFT: Goal progress + recent transactions ──────────────────────────────────
with left:
    st.subheader("🎯 Savings Goal Progress")
    prog = float(min(balance / savings_goal, 1.0)) if savings_goal > 0 and balance > 0 else 0.0
    st.progress(prog)
    pct_label = f"{prog * 100:.1f}%"
    if balance >= savings_goal:
        st.success(f"🎉 Goal reached! {sym}{balance:,.2f} / {sym}{savings_goal:,.2f} ({pct_label})")
    elif balance > 0:
        st.caption(f"{sym}{balance:,.2f} saved  ·  Goal: {sym}{savings_goal:,.2f}  ({pct_label})")
    else:
        st.caption(f"No savings yet this month  ·  Goal: {sym}{savings_goal:,.2f}")

    st.divider()
    st.subheader("🕐 Recent Transactions")
    if not df.empty:
        recent = (
            df.sort_values("date", ascending=False)
            .head(7)[["date", "type", "category", "amount", "note"]]
            .copy()
        )
        recent["date"] = recent["date"].dt.strftime("%d %b")
        recent["amount"] = recent.apply(
            lambda r: f"+{sym}{r['amount']:,.2f}" if r["type"] == "Income"
                      else (f"↔ {sym}{r['amount']:,.2f}" if r["type"] == "Transfer"
                            else f"-{sym}{r['amount']:,.2f}"),
            axis=1,
        )
        recent.columns = ["Date", "Type", "Category", "Amount", "Note"]
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet. Head to **Add Transaction** to get started!")

# ── RIGHT: Charts ──────────────────────────────────────────────────────────────
with right:
    st.subheader("📊 Income vs Expenses")
    if income > 0 or expenses > 0:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Income", x=["This Month"], y=[income],
            marker_color="#2ecc71",
            text=[f"{sym}{income:,.0f}"], textposition="outside",
        ))
        fig.add_trace(go.Bar(
            name="Expenses", x=["This Month"], y=[expenses],
            marker_color="#e74c3c",
            text=[f"{sym}{expenses:,.0f}"], textposition="outside",
        ))
        fig.update_layout(
            barmode="group",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"), height=220,
            margin=dict(t=30, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis=dict(showgrid=False, zeroline=False),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for this month yet.")

    # Expense breakdown donut
    if not mdf.empty:
        exp_df = (
            mdf[mdf["type"] == "Expense"]
            .groupby("category")["amount"]
            .sum()
            .reset_index()
            .sort_values("amount", ascending=False)
        )
        if not exp_df.empty:
            st.subheader("🍩 Expense Breakdown")
            fig2 = px.pie(
                exp_df, values="amount", names="category",
                hole=0.52,
                color_discrete_sequence=px.colors.sequential.Plasma_r,
            )
            fig2.update_traces(
                textinfo="percent+label",
                hovertemplate="%{label}: " + sym + "%{value:,.2f}<extra></extra>",
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=300,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

# ── Account balances strip ─────────────────────────────────────────────────────
if not df.empty:
    st.divider()
    st.subheader("🏦 Account Balances (All Time)")

    # Compute per-account balance
    balances: dict[str, float] = {}
    for _, row in df.iterrows():
        acc = row["account"]
        amt = float(row["amount"])
        if row["type"] == "Income":
            balances[acc] = balances.get(acc, 0.0) + amt
        elif row["type"] == "Expense":
            balances[acc] = balances.get(acc, 0.0) - amt
        elif row["type"] == "Transfer":
            balances[acc] = balances.get(acc, 0.0) - amt
            dest = row.get("transfer_to", "")
            if dest:
                balances[dest] = balances.get(dest, 0.0) + amt

    if balances:
        cols = st.columns(len(balances))
        for col, (acc, bal) in zip(cols, sorted(balances.items())):
            col.metric(acc, f"{sym}{bal:,.2f}")
