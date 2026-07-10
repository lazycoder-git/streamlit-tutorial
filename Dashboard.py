"""Dashboard.py — Dashboard page for Personal Money Tracker."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils import (
    load_data, render_currency_selector, MONTHS,
    inject_theme_css, render_theme_toggle, is_first_run
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Money Tracker — Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject theme CSS
inject_theme_css()

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
    st.divider()
    render_theme_toggle()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 Dashboard")

# ── Onboarding / Welcome screen (First run) ────────────────────────────────────
if is_first_run():
    st.caption("Welcome to Money Tracker! Let's get you set up.")
    st.divider()
    
    st.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(124,58,237,0.15) 0%, rgba(124,58,237,0.05) 100%);
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
">
    <h3 style="margin-top: 0; color:#7C3AED;">🎉 Welcome to Your Personal Money Tracker!</h3>
    <p>Track your income, expense, transfers, goals, and net worth all in one place. Follow these quick steps to get started:</p>
</div>
""", unsafe_allow_html=True)
    
    st.subheader("🏁 Quick Setup Guide")
    
    st.page_link("pages/1_Add_Transaction.py", label="Step 1: Add your first Transaction (Income or Expense)", icon="➕")
    st.page_link("pages/4_Budgets.py", label="Step 2: Set monthly Category Budgets to control spending", icon="🎯")
    st.page_link("pages/6_Goals.py", label="Step 3: Define your Savings Goals and Milestones", icon="💰")
    st.page_link("pages/7_Debts.py", label="Step 4: Keep track of Loans and credit card EMIs", icon="💳")
    st.page_link("pages/8_Net_Worth.py", label="Step 5: Check your consolidated Net Worth", icon="🏦")
    
    st.info("💡 Pro-Tip: You can change the base currency symbol and toggle Light/Dark mode directly from the sidebar on any page!")
    st.stop()

st.caption(f"Your financial overview for **{sel_month_name} {int(sel_year)}**")
st.divider()

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

# ── Metric cards ───────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
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
            font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E"),
            height=220,
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
                font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E"),
                height=300,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

# ── Account balances strip ─────────────────────────────────────────────────────
if not df.empty:
    st.divider()
    st.subheader("🏦 Account Balances (All Time)")

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

# ── Year-to-Date Savings Chart ─────────────────────────────────────────────────
if not df.empty:
    st.divider()
    st.subheader(f"📅 Year-to-Date Savings vs Goal — {int(sel_year)}")

    ytd = []
    for m in range(1, 13):
        m_mask = (df["date"].dt.month == m) & (df["date"].dt.year == int(sel_year))
        m_df   = df[m_mask]
        m_inc  = float(m_df[m_df["type"] == "Income"]["amount"].sum()) if not m_df.empty else 0.0
        m_exp  = float(m_df[m_df["type"] == "Expense"]["amount"].sum()) if not m_df.empty else 0.0
        ytd.append({
            "Month":    MONTHS[m - 1][:3],
            "Savings":  round(m_inc - m_exp, 2),
            "Goal":     savings_goal,
            "is_future": m > now.month and int(sel_year) == now.year,
        })

    ytd_df = pd.DataFrame(ytd)
    if int(sel_year) == now.year:
        ytd_plot = ytd_df[ytd_df["is_future"] == False].copy()
    else:
        ytd_plot = ytd_df.copy()

    if not ytd_plot.empty and ytd_plot["Savings"].abs().sum() > 0:
        fig_ytd = go.Figure()

        colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in ytd_plot["Savings"]]
        fig_ytd.add_trace(go.Bar(
            x=ytd_plot["Month"], y=ytd_plot["Savings"],
            name="Monthly Savings",
            marker_color=colors,
            opacity=0.85,
            hovertemplate="<b>%{x}</b><br>Savings: " + sym + "%{y:,.2f}<extra></extra>",
        ))

        fig_ytd.add_trace(go.Scatter(
            x=ytd_plot["Month"], y=ytd_plot["Goal"],
            mode="lines",
            name=f"Goal ({sym}{savings_goal:,.0f})",
            line=dict(color="#FFD700", width=2, dash="dash"),
            hovertemplate="Goal: " + sym + "%{y:,.2f}<extra></extra>",
        ))

        ytd_plot = ytd_plot.copy()
        ytd_plot["Cumulative"] = ytd_plot["Savings"].cumsum()
        fig_ytd.add_trace(go.Scatter(
            x=ytd_plot["Month"], y=ytd_plot["Cumulative"],
            mode="lines+markers",
            name="Cumulative Savings",
            line=dict(color="#7C3AED", width=2.5),
            marker=dict(size=7, color="#7C3AED"),
            hovertemplate="<b>%{x}</b><br>Cumulative: " + sym + "%{y:,.2f}<extra></extra>",
        ))

        fig_ytd.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E"),
            height=320,
            margin=dict(t=20, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)",
                       title=f"Amount ({sym})"),
            barmode="relative",
        )
        st.plotly_chart(fig_ytd, use_container_width=True)

        total_saved = float(ytd_plot["Savings"].sum())
        months_done = len(ytd_plot)
        ytd_c1, ytd_c2, ytd_c3 = st.columns(3)
        ytd_c1.metric("💰 Total Saved YTD",   f"{sym}{total_saved:,.2f}")
        ytd_c2.metric("📅 Months Tracked",    months_done)
        ytd_c3.metric("🎯 Goal Progress",
                      f"{(total_saved / (savings_goal * months_done) * 100):.1f}%"
                      if savings_goal > 0 else "—")
    else:
        st.info(f"No income/expense data found for {int(sel_year)} yet.")
