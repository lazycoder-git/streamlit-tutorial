"""pages/4_Budgets.py — Set and track monthly spending budgets per category."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from utils import (
    load_data, load_budgets, save_budgets, get_symbol,
    EXPENSE_CATS, MONTHS,
)
from auth import require_login

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Budgets — Money Tracker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth gate ──────────────────────────────────────────────────────────────────
require_login()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Money Tracker")
    st.divider()
    sym = get_symbol()
    st.divider()

    now = datetime.now()
    sel_month_name = st.selectbox("📅 Month", MONTHS, index=now.month - 1, key="bud_month")
    sel_year  = st.number_input("Year", 2020, 2035, value=now.year, step=1, key="bud_year")
    month_num = MONTHS.index(sel_month_name) + 1

# ── Load data ──────────────────────────────────────────────────────────────────
df       = load_data()
budgets  = load_budgets()

st.title("🎯 Budgets")
st.caption(f"Set monthly spending limits and track your progress for **{sel_month_name} {int(sel_year)}**.")
st.divider()

# ── Compute spending this month per category ───────────────────────────────────
if not df.empty:
    month_exp = (
        df[
            (df["type"] == "Expense") &
            (df["date"].dt.month == month_num) &
            (df["date"].dt.year  == int(sel_year))
        ]
        .groupby("category")["amount"]
        .sum()
        .to_dict()
    )
else:
    month_exp = {}

# ── Two-column layout ──────────────────────────────────────────────────────────
set_col, track_col = st.columns([1, 2], gap="large")

# ── LEFT: Budget settings ──────────────────────────────────────────────────────
with set_col:
    st.subheader("⚙️ Set Budgets")
    st.caption("Enter 0 to remove a budget limit for that category.")

    # Get all known expense categories (default + used)
    used_cats = []
    if not df.empty:
        used_cats = df[df["type"] == "Expense"]["category"].dropna().unique().tolist()
    all_cats = sorted(set(EXPENSE_CATS + used_cats))

    updated_budgets = {}
    with st.form("budget_form"):
        for cat in all_cats:
            current = budgets.get(cat, 0.0)
            val = st.number_input(
                f"🏷️ {cat} ({sym})",
                min_value=0.0,
                value=float(current),
                step=500.0,
                format="%.2f",
                key=f"bud_{cat}",
            )
            if val > 0:
                updated_budgets[cat] = val

        saved = st.form_submit_button("💾 Save Budgets", type="primary", use_container_width=True)
        if saved:
            save_budgets(updated_budgets)
            budgets = updated_budgets
            st.success("✅ Budgets saved!")
            st.rerun()

# ── RIGHT: Budget tracker ──────────────────────────────────────────────────────
with track_col:
    st.subheader("📊 Budget Progress")

    if not budgets:
        st.info("👈 Set some budgets on the left to start tracking!")
    else:
        over_budget_cats  = []
        near_budget_cats  = []
        under_budget_cats = []

        for cat, limit in sorted(budgets.items()):
            spent     = float(month_exp.get(cat, 0.0))
            remaining = limit - spent
            pct       = spent / limit if limit > 0 else 0.0
            over      = spent > limit

            if over:
                over_budget_cats.append((cat, limit, spent, remaining, pct))
            elif pct >= 0.75:
                near_budget_cats.append((cat, limit, spent, remaining, pct))
            else:
                under_budget_cats.append((cat, limit, spent, remaining, pct))

        # ── OVER BUDGET alerts ─────────────────────────────────────────────────
        if over_budget_cats:
            st.markdown("#### 🔴 Over Budget")
            for cat, limit, spent, remaining, pct in over_budget_cats:
                excess = spent - limit
                st.markdown(f"""
<div style="
    background: rgba(231,76,60,0.12);
    border: 1px solid rgba(231,76,60,0.5);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:#e74c3c; font-size:1rem;">🏷️ {cat}</span>
        <span style="color:#e74c3c; font-size:0.9rem; font-weight:600;">
            Over by {sym}{excess:,.2f}
        </span>
    </div>
    <div style="color:#aaa; font-size:0.82rem; margin-top:4px;">
        Spent {sym}{spent:,.2f} of {sym}{limit:,.2f} budget ({pct*100:.0f}%)
    </div>
</div>
""", unsafe_allow_html=True)
                st.progress(min(pct, 1.0))

        # ── NEAR LIMIT warnings ────────────────────────────────────────────────
        if near_budget_cats:
            st.markdown("#### 🟡 Near Limit")
            for cat, limit, spent, remaining, pct in near_budget_cats:
                st.markdown(f"""
<div style="
    background: rgba(243,156,18,0.10);
    border: 1px solid rgba(243,156,18,0.45);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:#f39c12; font-size:1rem;">🏷️ {cat}</span>
        <span style="color:#f39c12; font-size:0.9rem; font-weight:600;">
            {sym}{remaining:,.2f} left
        </span>
    </div>
    <div style="color:#aaa; font-size:0.82rem; margin-top:4px;">
        Spent {sym}{spent:,.2f} of {sym}{limit:,.2f} ({pct*100:.0f}%)
    </div>
</div>
""", unsafe_allow_html=True)
                st.progress(pct)

        # ── UNDER BUDGET (healthy) ─────────────────────────────────────────────
        if under_budget_cats:
            st.markdown("#### 🟢 On Track")
            for cat, limit, spent, remaining, pct in under_budget_cats:
                st.markdown(f"""
<div style="
    background: rgba(46,204,113,0.08);
    border: 1px solid rgba(46,204,113,0.3);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:700; color:#2ecc71; font-size:1rem;">🏷️ {cat}</span>
        <span style="color:#2ecc71; font-size:0.9rem; font-weight:600;">
            {sym}{remaining:,.2f} remaining
        </span>
    </div>
    <div style="color:#aaa; font-size:0.82rem; margin-top:4px;">
        Spent {sym}{spent:,.2f} of {sym}{limit:,.2f} ({pct*100:.0f}%)
    </div>
</div>
""", unsafe_allow_html=True)
                st.progress(pct)

        # ── Categories with NO budget set but have spending ────────────────────
        st.divider()
        unbudgeted = [c for c in month_exp if c not in budgets and month_exp[c] > 0]
        if unbudgeted:
            st.markdown("#### ⚪ Unbudgeted Categories (have spending)")
            rows = [{"Category": c, "Spent": f"{sym}{month_exp[c]:,.2f}", "Budget": "Not set"}
                    for c in unbudgeted]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Summary radar chart ────────────────────────────────────────────────────────
if budgets and month_exp:
    st.divider()
    st.subheader("🕸️ Budget Overview Radar")
    cats_with_both = [c for c in budgets if month_exp.get(c, 0) > 0]
    if cats_with_both:
        r_spent  = [min(month_exp.get(c, 0) / budgets[c], 1.5) * 100 for c in cats_with_both]
        theta    = cats_with_both + [cats_with_both[0]]
        r_vals   = r_spent + [r_spent[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=r_vals, theta=theta,
            fill="toself",
            fillcolor="rgba(124,58,237,0.2)",
            line=dict(color="#7C3AED", width=2),
            name="% of Budget Used",
        ))
        # 100% reference circle
        fig_radar.add_trace(go.Scatterpolar(
            r=[100] * (len(cats_with_both) + 1), theta=theta,
            mode="lines",
            line=dict(color="rgba(255,215,0,0.5)", width=1.5, dash="dot"),
            name="Budget Limit (100%)",
            showlegend=True,
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 150],
                                ticksuffix="%",
                                gridcolor="rgba(255,255,255,0.1)"),
                angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                bgcolor="rgba(0,0,0,0)",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=380,
            margin=dict(t=20, b=20, l=40, r=40),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15),
        )
        st.plotly_chart(fig_radar, use_container_width=True)
