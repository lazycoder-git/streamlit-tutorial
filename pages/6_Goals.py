"""pages/6_Goals.py — Set and track savings goals with visual progress indicators."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime

from utils import (
    load_goals, save_goals, get_symbol, GOAL_EMOJIS,
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

st.title("🎯 Financial Goals")
st.caption("Track your savings milestones and stay on top of your financial dreams.")
st.divider()

goals = load_goals()

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
    # Quick update section for contributions
    st.subheader("📊 Your Active Milestones")
    
    # Loop over goals and render beautiful cards
    for idx, goal in enumerate(goals):
        target = float(goal["target"])
        saved = float(goal["saved"])
        pct = (saved / target) if target > 0 else 0
        pct_display = min(pct, 1.0) * 100
        
        # Calculate days remaining
        deadline_dt = datetime.strptime(goal["deadline"], "%Y-%m-%d").date()
        today = date.today()
        days_left = (deadline_dt - today).days
        
        status = "Achieved 🎉" if saved >= target else ("On Track" if days_left > 30 else "Action Needed ⚠️")
        status_color = "#2ecc71" if saved >= target else ("#3498db" if days_left > 30 else "#e67e22")
        
        # Grid layout for each goal
        col_chart, col_info = st.columns([1, 2], gap="medium")
        
        with col_chart:
            # Gauge / donut chart for progress
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = saved,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"Progress ({pct*100:.1f}%)", 'font': {'size': 14}},
                number = {'prefix': sym, 'font': {'size': 20}},
                gauge = {
                    'axis': {'range': [None, target], 'tickprefix': sym},
                    'bar': {'color': "#7C3AED"},
                    'steps': [
                        {'range': [0, target * 0.5], 'color': "rgba(124, 58, 237, 0.1)"},
                        {'range': [target * 0.5, target * 0.8], 'color': "rgba(124, 58, 237, 0.2)"},
                        {'range': [target * 0.8, target], 'color': "rgba(124, 58, 237, 0.3)"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
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
            st.plotly_chart(fig, use_container_width=True, key=f"gauge_{goal['id']}")
            
        with col_info:
            st.markdown(f"### {goal['emoji']} {goal['name']}")
            st.markdown(f"**Target:** {sym}{target:,.2f} | **Saved:** {sym}{saved:,.2f}")
            
            # Days remaining indicator
            if days_left < 0:
                st.error(f"Expired {abs(days_left)} days ago (Deadline: {deadline_dt.strftime('%d %b %Y')})")
            elif saved >= target:
                st.success(f"Goal met! Target completed on time.")
            else:
                st.info(f"⏳ **{days_left}** days remaining (Deadline: {deadline_dt.strftime('%d %b %Y')})")
                
            # Quick contribute input
            with st.expander("💸 Add Contribution / Withdraw", expanded=False):
                with st.form(f"contrib_form_{goal['id']}"):
                    c_amt = st.number_input("Amount to add (negative to withdraw)", value=1000.0, step=100.0, key=f"amt_val_{goal['id']}")
                    c_submit = st.form_submit_button("Update Balance")
                    if c_submit:
                        new_saved = saved + c_amt
                        if new_saved < 0:
                            st.error("Saved savings cannot be negative.")
                        else:
                            goals[idx]["saved"] = float(new_saved)
                            save_goals(goals)
                            st.success("Goal balance updated successfully!")
                            st.rerun()
            
            # Delete button
            if st.button("🗑️ Delete Goal", key=f"del_{goal['id']}", type="secondary"):
                goals.pop(idx)
                save_goals(goals)
                st.success("Goal deleted.")
                st.rerun()
                
        st.divider()
