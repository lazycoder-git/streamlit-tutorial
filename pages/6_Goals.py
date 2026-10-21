"""pages/6_Goals.py — Set, track, and project financial savings milestones."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime

from utils import (
    load_goals, save_goals, load_data, get_symbol, render_demo_reset_sidebar, GOAL_EMOJIS,
)
from auth import require_login

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Goals — Money Tracker",
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
    render_demo_reset_sidebar()

st.title("🎯 Financial Goals & Milestone Intelligence")
st.caption("Track progress, project feasibility dates, and optimize wealth accumulation velocity.")
st.divider()

goals = load_goals()
df = load_data()

# ── Form to add new goal ───────────────────────────────────────────────────────
with st.expander("➕ Create a New Savings Goal", expanded=not goals):
    with st.form("new_goal_form"):
        gc1, gc2 = st.columns(2)
        with gc1:
            g_name = st.text_input("🎯 Goal Name", placeholder="e.g. Vacation, New Laptop, Emergency Fund")
            g_target = st.number_input(f"💵 Target Amount ({sym})", min_value=1.0, value=10000.0, step=500.0)
            g_emoji = st.selectbox("🏷️ Select Icon", GOAL_EMOJIS)
        with gc2:
            g_saved = st.number_input(f"💰 Starting Savings ({sym})", min_value=0.0, value=0.0, step=500.0)
            g_date = st.date_input("📅 Target Date / Deadline", value=date(date.today().year + 1, 12, 31))

        submitted = st.form_submit_button("Create Goal", type="primary", use_container_width=True)
        if submitted:
            if not g_name.strip():
                st.error("Please enter a goal name.")
            elif g_saved > g_target:
                st.error("Starting savings cannot be greater than the target amount.")
            else:
                new_goal = {
                    "id": str(datetime.now().timestamp()).replace(".", ""),
                    "name": g_name.strip(),
                    "target": float(g_target),
                    "saved": float(g_saved),
                    "emoji": g_emoji,
                    "deadline": g_date.strftime("%Y-%m-%d"),
                    "created_at": date.today().strftime("%Y-%m-%d")
                }
                goals.append(new_goal)
                save_goals(goals)
                st.success(f"🎉 Goal '{g_name}' created successfully!")
                st.rerun()

# ── Render active goals ────────────────────────────────────────────────────────
if not goals:
    st.info("No savings goals set yet. Use the form above to add your first goal!")
else:
    # Summary Metrics across goals
    tot_target = sum(float(g.get("target", 0.0)) for g in goals)
    tot_saved = sum(float(g.get("saved", g.get("current", 0.0))) for g in goals)
    overall_progress = (tot_saved / tot_target * 100) if tot_target > 0 else 0.0

    g1, g2, g3 = st.columns(3)
    g1.metric("🎯 Total Portfolio Target", f"{sym}{tot_target:,.2f}")
    g2.metric("💰 Total Capital Accumulated", f"{sym}{tot_saved:,.2f}")
    g3.metric("📈 Aggregate Completion", f"{overall_progress:.1f}%")
    st.divider()

    st.subheader("📊 Active Milestones")
    
    # Loop over goals and render cards
    for idx, goal in enumerate(goals):
        target = float(goal.get("target", 0.0))
        saved = float(goal.get("saved", goal.get("current", 0.0)))
        pct = (saved / target) if target > 0 else 0
        pct_display = min(pct, 1.0) * 100
        
        # Calculate days remaining
        deadline_str = goal.get("deadline", goal.get("target_date", "2027-12-31"))
        try:
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        except Exception:
            deadline_dt = date(date.today().year + 1, 12, 31)
        today = date.today()
        days_left = (deadline_dt - today).days
        months_left = max(0.1, days_left / 30.4)
        remaining_amt = max(0.0, target - saved)
        req_monthly = remaining_amt / months_left if remaining_amt > 0 else 0.0
        
        col_chart, col_info = st.columns([1, 2], gap="medium")
        
        with col_chart:
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = saved,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"Progress ({pct*100:.1f}%)", 'font': {'size': 14}},
                number = {'prefix': sym, 'font': {'size': 20}},
                gauge = {
                    'axis': {'range': [None, target], 'tickprefix': sym},
                    'bar': {'color': "#10B981" if saved >= target else "#7C3AED"},
                    'steps': [
                        {'range': [0, target * 0.5], 'color': "rgba(124, 58, 237, 0.1)"},
                        {'range': [target * 0.5, target * 0.8], 'color': "rgba(124, 58, 237, 0.2)"},
                        {'range': [target * 0.8, target], 'color': "rgba(124, 58, 237, 0.3)"}
                    ],
                    'threshold': {
                        'line': {'color': "#10B981", 'width': 4},
                        'thickness': 0.75,
                        'value': target
                    }
                }
            ))
            fig.update_layout(
                height=180, 
                margin=dict(t=30, b=10, l=30, r=30),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E")
            )
            st.plotly_chart(fig, use_container_width=True, key=f"gauge_{goal.get('id', idx)}")
            
        with col_info:
            st.markdown(f"### {goal.get('emoji', '🎯')} {goal.get('name', 'Goal')}")
            st.markdown(f"**Target:** {sym}{target:,.2f} | **Saved:** {sym}{saved:,.2f} | **Remaining:** {sym}{remaining_amt:,.2f}")
            
            if days_left < 0:
                st.error(f"Expired {abs(days_left)} days ago (Deadline: {deadline_dt.strftime('%d %b %Y')})")
            elif saved >= target:
                st.success(f"🎉 Goal fully achieved! Capital is secured and available.")
            else:
                st.info(f"⏳ **{days_left} days remaining** (Deadline: {deadline_dt.strftime('%d %b %Y')}) · Required Velocity: **{sym}{req_monthly:,.2f}/month**")
                
            # Quick contribute input
            with st.expander("💸 Add Contribution / Withdraw", expanded=False):
                with st.form(f"contrib_form_{goal.get('id', idx)}"):
                    c_amt = st.number_input("Amount to add (negative to withdraw)", value=500.0, step=100.0, key=f"amt_val_{goal.get('id', idx)}")
                    c_submit = st.form_submit_button("Update Balance")
                    if c_submit:
                        new_saved = saved + c_amt
                        if new_saved < 0:
                            st.error("Saved savings cannot be negative.")
                        else:
                            goals[idx]["saved"] = float(new_saved)
                            goals[idx]["current"] = float(new_saved)
                            save_goals(goals)
                            st.success("Goal balance updated successfully!")
                            st.rerun()
            
            # Delete button
            if st.button("🗑️ Delete Goal", key=f"del_{goal.get('id', idx)}", type="secondary"):
                goals.pop(idx)
                save_goals(goals)
                st.success("Goal deleted.")
                st.rerun()
                
        st.divider()

    # ── Analytical Velocity & Feasibility Assessment ───────────────────────────
    # Compute user's average net monthly savings over tracked history
    if not df.empty:
        monthly_net = df.groupby(df["date"].dt.to_period("M")).apply(
            lambda g: g[g["type"] == "Income"]["amount"].sum() - g[g["type"] == "Expense"]["amount"].sum()
        )
        avg_savings_velocity = float(monthly_net.mean()) if not monthly_net.empty else 0.0
    else:
        avg_savings_velocity = 800.0

    total_unfunded = sum(max(0.0, float(g.get("target", 0.0)) - float(g.get("saved", g.get("current", 0.0)))) for g in goals)
    months_to_clear_all = (total_unfunded / avg_savings_velocity) if avg_savings_velocity > 0 else 0.0

    # ── Interactive Multi-Milestone Projection Chart ───────────────────────────
    st.subheader("📈 Projected Multi-Milestone Capital Accumulation Timeline")
    st.caption("Forecast of capital growth over the next 18 months based on empirical surplus velocity.")

    if avg_savings_velocity > 0:
        projection_months = 18
        proj_dates = [date.today() + pd.DateOffset(months=i) for i in range(projection_months + 1)]
        proj_df = pd.DataFrame({
            "Date": [d.strftime("%b %Y") for d in proj_dates],
            "Projected Capital": [tot_saved + (i * avg_savings_velocity) for i in range(projection_months + 1)]
        })

        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(
            x=proj_df["Date"], y=proj_df["Projected Capital"],
            mode="lines+markers",
            name="Projected Accumulated Capital",
            line=dict(color="#10B981", width=3),
            fill="tozeroy",
            fillcolor="rgba(16,185,129,0.12)",
            hovertemplate="<b>%{x}</b><br>Projected Capital: " + sym + "%{y:,.2f}<extra></extra>"
        ))

        # Add target horizontal line
        fig_proj.add_hline(
            y=tot_target,
            line_dash="dash",
            line_color="#F59E0B",
            annotation_text=f"Total Portfolio Target: {sym}{tot_target:,.0f}",
            annotation_position="top left"
        )

        fig_proj.update_layout(
            height=300,
            margin=dict(t=20, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title=f"Capital ({sym})")
        )
        st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown(f"""
    <div style="background: rgba(124,58,237,0.08); border-left: 4px solid #7C3AED; padding: 14px 18px; border-radius: 6px;">
        <h5 style="margin: 0 0 6px 0; color: #A78BFA;">🎯 Goal Feasibility & Capital Sequencing Insights</h5>
        <ul style="margin: 0; padding-left: 20px; font-size: 0.93rem; color: #E2E8F0; line-height: 1.6;">
            <li><b>What This Chart Conveys</b>: The green projection line tracks your future savings trajectory assuming your empirical net monthly surplus of <b>{sym}{avg_savings_velocity:,.2f}</b> persists. The intersection with the amber dashed line indicates full portfolio completion.</li>
            <li><b>Portfolio Runway</b>: Remaining unfunded commitments equal <b>{sym}{total_unfunded:,.2f}</b>. At your current pace, all active targets will be fully achieved in <b>{months_to_clear_all:.1f} months</b>.</li>
            <li><b>Milestone Sequencing Conclusion</b>: Rather than splitting capital evenly across all goals, apply a <b>Waterfall Allocation</b>: fully fund the <i>Emergency Cushion</i> (3–6 months burn) first to insulate against shocks before directing monthly cash flow to secondary lifestyle goals.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
