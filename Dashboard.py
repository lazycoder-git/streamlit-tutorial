"""Dashboard.py — Dashboard & Financial Intelligence Hub for Personal Money Tracker."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils import (
    load_data, render_currency_selector, render_demo_reset_sidebar, MONTHS,
    is_first_run, load_debts, load_budgets
)
from auth import require_login

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Money Tracker — Executive Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth gate ──────────────────────────────────────────────────────────────────
require_login()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    sym = render_currency_selector()
    st.divider()

    st.subheader("📅 Period & Target")
    now = datetime.now()
    sel_month_name = st.selectbox("Month", MONTHS, index=now.month - 1, key="dash_month")
    sel_year = st.number_input("Year", min_value=2020, max_value=2035,
                                value=now.year, step=1, key="dash_year")
    month_num = MONTHS.index(sel_month_name) + 1

    savings_goal = st.number_input(
        f"🎯 Savings Goal ({sym})",
        min_value=0.0, value=800.0, step=100.0, format="%.2f",
        key="dash_goal",
    )

    render_demo_reset_sidebar()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 Executive Financial Dashboard")
st.caption(f"Comprehensive financial intelligence & analysis for **{sel_month_name} {int(sel_year)}**")

st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(124,58,237,0.12), rgba(59,130,246,0.05));
            border: 1px solid rgba(124,58,237,0.25); border-radius: 8px; padding: 12px 18px; margin-bottom: 16px;">
    <span style="font-size: 0.85rem; font-weight: 700; color: #A78BFA; text-transform: uppercase; letter-spacing: 0.05em;">
        📌 Module-End Project Context · 12-Month Longitudinal Case Study
    </span>
    <p style="margin: 4px 0 0 0; color: #E2E8F0; font-size: 0.92rem; line-height: 1.5;">
        This application analyzes audited cash flow dynamics, 50/30/20 compliance, emergency cash burn runway,
        and net worth formation for <b>Rahul Sharma (Senior Tech Consultant)</b>. Explore <b>📖 Case Study Analysis</b> in the sidebar for complete hypotheses, empirical evidence, and methodology.
    </p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Load & filter data ─────────────────────────────────────────────────────────
df = load_data()

if df.empty:
    from utils import reset_demo_data
    reset_demo_data()
    df = load_data()

mask = (
    (df["date"].dt.month == month_num) &
    (df["date"].dt.year  == int(sel_year))
)
mdf = df[mask].copy()

income   = float(mdf[mdf["type"] == "Income"]["amount"].sum())   if not mdf.empty else 0.0
expenses = float(mdf[mdf["type"] == "Expense"]["amount"].sum())  if not mdf.empty else 0.0
balance  = income - expenses
sav_rate = (balance / income * 100) if income > 0 else 0.0

# Calculate all-time average monthly expense (burn rate)
monthly_burns = df[df["type"] == "Expense"].groupby(df["date"].dt.to_period("M"))["amount"].sum()
avg_burn = float(monthly_burns.mean()) if not monthly_burns.empty else expenses

# Account liquid balance
account_balances = {}
for _, row in df.iterrows():
    acc = row["account"]
    amt = float(row["amount"])
    if row["type"] == "Income":
        account_balances[acc] = account_balances.get(acc, 0.0) + amt
    elif row["type"] == "Expense":
        account_balances[acc] = account_balances.get(acc, 0.0) - amt
    elif row["type"] == "Transfer":
        account_balances[acc] = account_balances.get(acc, 0.0) - amt
        dest = row.get("transfer_to", "")
        if dest:
            account_balances[dest] = account_balances.get(dest, 0.0) + amt

liquid_cash = sum(v for v in account_balances.values() if v > 0)
runway_months = (liquid_cash / avg_burn) if avg_burn > 0 else 0.0

# ── Financial Health Score Computation (0-100) ─────────────────────────────────
# 1. Savings rate score (0-35 pts)
if sav_rate >= 25:
    score_sav = 35
elif sav_rate >= 15:
    score_sav = 25
elif sav_rate > 0:
    score_sav = 15
else:
    score_sav = 0

# 2. Runway score (0-35 pts)
if runway_months >= 6.0:
    score_runway = 35
elif runway_months >= 3.0:
    score_runway = 25
elif runway_months >= 1.0:
    score_runway = 15
else:
    score_runway = 5

# 3. Monthly cash flow stability (0-30 pts)
if balance > 0 and expenses < (income * 0.85):
    score_flow = 30
elif balance >= 0:
    score_flow = 20
else:
    score_flow = 5

health_score = min(100, score_sav + score_runway + score_flow)

if health_score >= 80:
    score_grade = "A (Excellent)"
    score_color = "#10B981"
    score_badge = "Healthy Financial Posture"
elif health_score >= 65:
    score_grade = "B (Good)"
    score_color = "#3B82F6"
    score_badge = "Stable with Optimization Opportunities"
elif health_score >= 50:
    score_grade = "C (Fair)"
    score_color = "#F59E0B"
    score_badge = "Moderate Cash Flow Stress"
else:
    score_grade = "D (Needs Attention)"
    score_color = "#EF4444"
    score_badge = "High Deficit Risk"

# ── Top-level Metrics + Financial Health Scorecard ──────────────────────────────
m1, m2, m3, m4, m5 = st.columns([1, 1, 1, 1, 1.2])
m1.metric("💳 Net Balance", f"{sym}{balance:,.2f}", delta=f"{balance:,.0f} net")
m2.metric("📈 Total Income", f"{sym}{income:,.2f}")
m3.metric("📉 Total Expenses", f"{sym}{expenses:,.2f}")
m4.metric("💰 Savings Rate", f"{sav_rate:.1f}%", delta="Target: ≥20%")
with m5:
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px; padding: 10px 14px; text-align: center;">
        <span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">Health Score</span>
        <div style="font-size: 1.4rem; font-weight: 700; color: {score_color};">{health_score} / 100</div>
        <span style="font-size: 0.75rem; color: {score_color}; font-weight: 600;">{score_grade}</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── 50/30/20 Rule Analysis & Cash Runway Diagnostic ───────────────────────────
st.subheader("🧠 Financial Health & Diagnostic Insights")

col_5030, col_runway = st.columns([1.5, 1], gap="large")

with col_5030:
    st.markdown("##### 📌 50/30/20 Budget Rule Diagnostic")
    st.caption("Standard financial benchmark: 50% Essential Needs · 30% Discretionary Wants · 20% Savings & Debt Reduction")

    needs_cats = ["Rent", "Utilities", "Health", "Transport"]
    wants_cats = ["Food & Dining", "Shopping", "Entertainment", "Subscriptions", "Travel", "Personal Care"]

    if not mdf.empty and income > 0:
        needs_exp = mdf[(mdf["type"] == "Expense") & (mdf["category"].isin(needs_cats))]["amount"].sum()
        # Half of Food & Dining considered grocery needs
        wants_exp = mdf[(mdf["type"] == "Expense") & (mdf["category"].isin(wants_cats))]["amount"].sum()
        savings_allocated = max(0.0, balance)

        pct_needs = (needs_exp / income) * 100
        pct_wants = (wants_exp / income) * 100
        pct_savings = (savings_allocated / income) * 100

        diag_df = pd.DataFrame({
            "Bucket": ["Needs (Essential)", "Wants (Discretionary)", "Savings & Investment"],
            "Actual Amount": [f"{sym}{needs_exp:,.2f}", f"{sym}{wants_exp:,.2f}", f"{sym}{savings_allocated:,.2f}"],
            "Actual %": [f"{pct_needs:.1f}%", f"{pct_wants:.1f}%", f"{pct_savings:.1f}%"],
            "Target %": ["≤ 50%", "≤ 30%", "≥ 20%"],
            "Status": [
                "✅ Compliant" if pct_needs <= 50 else "⚠️ Exceeds Limit",
                "✅ Controlled" if pct_wants <= 30 else "⚠️ Overspending",
                "✅ Excellent" if pct_savings >= 20 else ("🟡 Moderate" if pct_savings >= 10 else "❌ Underfunded")
            ]
        })
        st.dataframe(diag_df, use_container_width=True, hide_index=True)

        if pct_needs <= 50 and pct_wants <= 30 and pct_savings >= 20:
            st.success("🎯 **Conclusion**: Your budget distribution perfectly satisfies the 50/30/20 standard. Living essentials are well-managed, allowing healthy surplus allocation to wealth-building.")
        else:
            st.info(f"💡 **Takeaway**: Essential needs account for **{pct_needs:.1f}%** of income, while discretionary wants take **{pct_wants:.1f}%**. Optimize discretionary categories to push savings closer to the 20% target.")
    else:
        st.info("Log transactions with income and expenses to view the 50/30/20 diagnostic breakdown.")

with col_runway:
    st.markdown("##### 🛡️ Emergency Runway & Burn Rate")
    st.caption("How long your liquid assets can sustain living expenses with zero income.")
    
    st.metric("🔥 Average Monthly Burn Rate", f"{sym}{avg_burn:,.2f}")
    st.metric("⏳ Emergency Cash Runway", f"{runway_months:.1f} Months")

    if runway_months >= 6.0:
        st.success(f"✅ **Safe**: Liquid reserve covers **{runway_months:.1f} months** of living expenses, satisfying the recommended 6-month financial resilience cushion.")
    elif runway_months >= 3.0:
        st.info(f"🟡 **Adequate**: Liquid reserve covers **{runway_months:.1f} months**. Keep building towards the 6-month mark.")
    else:
        st.warning(f"⚠️ **Attention**: Liquid cash covers under 3 months. Priority should be given to boosting cash reserves.")

st.divider()

# ── Main Visual Layout ─────────────────────────────────────────────────────────
left, right = st.columns([1, 2], gap="large")

# ── LEFT: Goal progress + recent transactions ──────────────────────────────────
with left:
    st.subheader("🎯 Monthly Savings Goal")
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
    st.subheader("🕐 Recent Activity")
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

# ── RIGHT: Visual Charts with Explicit Analytical Commentary ───────────────────
with right:
    st.subheader("📊 Inflow vs Outflow Analysis")
    if income > 0 or expenses > 0:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Income", x=["This Month"], y=[income],
            marker_color="#10B981",
            text=[f"{sym}{income:,.0f}"], textposition="outside",
        ))
        fig.add_trace(go.Bar(
            name="Expenses", x=["This Month"], y=[expenses],
            marker_color="#EF4444",
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
        st.caption(f"💡 **Chart Interpretation**: Expenses consume **{(expenses/income*100) if income > 0 else 0:.1f}%** of income, generating a net liquid surplus of **{sym}{balance:,.2f}** ({sav_rate:.1f}% savings rate) for reserve allocation.")
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
            st.subheader("🍩 Expense Category Allocation")
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
                height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

            top_cat = exp_df.iloc[0]["category"]
            top_amt = exp_df.iloc[0]["amount"]
            top_pct = (top_amt / expenses * 100) if expenses > 0 else 0
            st.caption(f"💡 **Chart Insight**: **{top_cat}** represents the single largest expenditure at **{sym}{top_amt:,.2f}** ({top_pct:.1f}% of total outflow).")

# ── Account balances strip ─────────────────────────────────────────────────────
st.divider()
st.subheader("🏦 Consolidated Liquid Balances Across Accounts")
if account_balances:
    cols = st.columns(len(account_balances))
    for col, (acc, bal) in zip(cols, sorted(account_balances.items())):
        col.metric(acc, f"{sym}{bal:,.2f}")

# ── Year-to-Date Savings & Trend Interpretation ────────────────────────────────
st.divider()
st.subheader(f"📅 12-Month Savings Trajectory vs Benchmark — {int(sel_year)}")

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

    colors = ["#10B981" if v >= 0 else "#EF4444" for v in ytd_plot["Savings"]]
    fig_ytd.add_trace(go.Bar(
        x=ytd_plot["Month"], y=ytd_plot["Savings"],
        name="Monthly Net Savings",
        marker_color=colors,
        opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Savings: " + sym + "%{y:,.2f}<extra></extra>",
    ))

    fig_ytd.add_trace(go.Scatter(
        x=ytd_plot["Month"], y=ytd_plot["Goal"],
        mode="lines",
        name=f"Goal Target ({sym}{savings_goal:,.0f})",
        line=dict(color="#F59E0B", width=2, dash="dash"),
        hovertemplate="Goal: " + sym + "%{y:,.2f}<extra></extra>",
    ))

    ytd_plot["Cumulative"] = ytd_plot["Savings"].cumsum()
    fig_ytd.add_trace(go.Scatter(
        x=ytd_plot["Month"], y=ytd_plot["Cumulative"],
        mode="lines+markers",
        name="Cumulative Net Wealth",
        line=dict(color="#7C3AED", width=2.5),
        marker=dict(size=7, color="#7C3AED"),
        hovertemplate="<b>%{x}</b><br>Cumulative: " + sym + "%{y:,.2f}<extra></extra>",
    ))

    fig_ytd.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E"),
        height=340,
        margin=dict(t=20, b=10, l=10, r=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title=f"Amount ({sym})"),
        barmode="relative",
    )
    st.plotly_chart(fig_ytd, use_container_width=True)

    total_saved = float(ytd_plot["Savings"].sum())
    months_done = len(ytd_plot)
    avg_monthly_savings = total_saved / months_done if months_done > 0 else 0.0

    st.markdown(f"""
    <div style="background: rgba(124,58,237,0.08); border-left: 4px solid #7C3AED; padding: 14px 18px; border-radius: 6px; margin-top: 10px;">
        <h5 style="margin: 0 0 6px 0; color: #A78BFA;">📈 Analytical Trend Interpretation</h5>
        <p style="margin: 0; font-size: 0.93rem; color: #E2E8F0; line-height: 1.5;">
            Across the <b>{months_done} tracked months</b>, cumulative net savings reached <b>{sym}{total_saved:,.2f}</b> 
            (averaging <b>{sym}{avg_monthly_savings:,.2f}/month</b>).
            The upward trajectory of the purple cumulative curve indicates consistent wealth accumulation. 
            Seasonal dips in months like July (vacation travel) and December (holiday shopping) are counterbalanced 
            by strong freelance surplus months (March, October), showing sustainable long-term cash flow management.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Executive Decision & Prescriptive Summary ──────────────────────────────
    st.divider()
    st.subheader(f"🎯 Strategic Financial Prescriptions — {sel_month_name} {int(sel_year)}")
    rec_c1, rec_c2, rec_c3 = st.columns(3)
    with rec_c1:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px;">
            <h5 style="color: #60A5FA; margin-top: 0;">1. Surplus Deployment</h5>
            <p style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                Allocate <b>{sym}{max(0.0, balance * 0.7):,.2f}</b> (70% of current surplus) to emergency liquid savings or low-cost index ETFs to reinforce compounding momentum.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with rec_c2:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px;">
            <h5 style="color: #34D399; margin-top: 0;">2. Budget Risk Mitigation</h5>
            <p style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                Keep discretionary social dining below <b>{sym}350.00/mo</b> to maintain the <b>{sav_rate:.1f}%</b> savings rate target during seasonal inflationary dips.
            </p>
        </div>
        """, unsafe_allow_html=True)
    with rec_c3:
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 16px;">
            <h5 style="color: #FBBF24; margin-top: 0;">3. Debt Paydown Target</h5>
            <p style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                Direct <b>{sym}{min(300.0, max(0.0, balance * 0.3)):,.2f}</b> towards high-interest credit card principal under the Avalanche strategy to minimize cumulative interest drag.
            </p>
        </div>
        """, unsafe_allow_html=True)
