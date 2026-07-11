"""pages/8_Net_Worth.py — Manage, track, and visualize net worth over time."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime

from utils import (
    load_data, load_debts, get_symbol, load_assets, save_assets
)
from auth import require_login

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Net Worth — Money Tracker",
    page_icon="🏦",
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

st.title("🏦 Net Worth Tracker")
st.caption("Calculate your total net worth by combining account balances, physical assets, and current liabilities.")
st.divider()

manual_assets = load_assets()
debts = load_debts()
df = load_data()

# ── 1. Calculate Liquid Assets from Accounts ───────────────────────────────────
account_balances = {}
if not df.empty:
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

liquid_assets_val = sum(v for v in account_balances.values() if v > 0)

# ── 2. Calculate Manual/Other Assets ───────────────────────────────────────────
other_assets_val = sum(manual_assets.values())
total_assets = liquid_assets_val + other_assets_val

# ── 3. Calculate Liabilities ───────────────────────────────────────────────────
total_liabilities = sum(float(d["remaining"]) for d in debts)

# ── 4. Calculate Net Worth ─────────────────────────────────────────────────────
net_worth = total_assets - total_liabilities

# ── Visual Metrics ─────────────────────────────────────────────────────────────
nw1, nw2, nw3 = st.columns(3)
nw1.metric("🏦 Total Net Worth", f"{sym}{net_worth:,.2f}")
nw2.metric("🟢 Total Assets", f"{sym}{total_assets:,.2f}")
nw3.metric("🔴 Total Liabilities", f"{sym}{total_liabilities:,.2f}")

st.divider()

col_left, col_right = st.columns([1, 1], gap="large")

# ── LEFT: Edit Assets and Liabilities ──────────────────────────────────────────
with col_left:
    st.subheader("🛠️ Asset Settings")
    st.caption("Manage non-cash assets (e.g. Stocks, Crypto, Real Estate, Gold, PF).")
    
    # Form to add custom asset
    with st.form("add_asset_form"):
        ac1, ac2 = st.columns([2, 1])
        with ac1:
            asset_name = st.text_input("Asset Class Name", placeholder="e.g. Mutual Funds, Gold, Real Estate")
        with ac2:
            asset_val = st.number_input("Value", min_value=0.0, value=50000.0, step=1000.0)
        
        submitted = st.form_submit_button("Add/Update Asset", type="primary")
        if submitted and asset_name.strip():
            manual_assets[asset_name.strip()] = float(asset_val)
            save_assets(manual_assets)
            st.success(f"Updated '{asset_name}' asset value!")
            st.rerun()
            
    # List and delete manual assets
    if manual_assets:
        st.markdown("#### Current Manual Assets")
        del_asset = None
        for k, v in manual_assets.items():
            ac_lbl, ac_btn = st.columns([3, 1])
            with ac_lbl:
                st.markdown(f"💼 **{k}:** {sym}{v:,.2f}")
            with ac_btn:
                if st.button("🗑️ Remove", key=f"del_ast_{k}", type="secondary"):
                    del_asset = k
        if del_asset:
            manual_assets.pop(del_asset)
            save_assets(manual_assets)
            st.rerun()
    else:
        st.info("No manual assets added yet.")

# ── RIGHT: Waterfall / Net Worth Breakdown Chart ──────────────────────────────
with col_right:
    st.subheader("📊 Net Worth Breakdown")
    
    # Prepare waterfall chart labels and values
    labels = []
    values = []
    
    # Liquid accounts
    if liquid_assets_val > 0:
        labels.append("Liquid Cash")
        values.append(liquid_assets_val)
        
    # Manual assets
    for k, v in manual_assets.items():
        if v > 0:
            labels.append(k)
            values.append(v)
            
    # Liabilities
    for d in debts:
        rem = float(d["remaining"])
        if rem > 0:
            labels.append(f"Debt: {d['name']}")
            values.append(-rem)
            
    if not labels:
        st.info("Add some assets or debts to see a breakdown chart.")
    else:
        fig = go.Figure(go.Waterfall(
            name="Net Worth",
            orientation="v",
            measure=["relative"] * len(labels) + ["total"],
            x=labels + ["Net Worth"],
            textposition="outside",
            text=[f"{sym}{v:,.0f}" if v > 0 else (f"-{sym}{abs(v):,.0f}" if v < 0 else "") for v in values] + [f"{sym}{net_worth:,.0f}"],
            y=values + [0], # waterfall final total
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#e74c3c"}},
            increasing={"marker": {"color": "#2ecc71"}},
            totals={"marker": {"color": "#7C3AED"}}
        ))
        
        fig.update_layout(
            title="Waterfall Chart of Net Worth Component Allocation",
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E"),
            height=380,
            margin=dict(t=40, b=10, l=10, r=10)
        )
        st.plotly_chart(fig, use_container_width=True, key="net_worth_waterfall")

# ── Historical Net Worth Line Chart ────────────────────────────────────────────
st.divider()
st.subheader("📈 Net Worth Trend Over Time")
st.caption("Historical estimation of your net worth calculated from monthly savings trends.")

if df.empty:
    st.info("No transaction data to display trends.")
else:
    # Compute net worth progression month-by-month for the past 12 months
    df["_period"] = df["date"].dt.to_period("M")
    all_periods = sorted(df["_period"].unique())[-12:]
    
    historical_nw = []
    
    # Baseline manual assets and liabilities
    running_assets = other_assets_val
    running_liab = total_liabilities
    
    # Loop chronologically to build cumulative savings
    cumulative_savings = 0.0
    for p in all_periods:
        p_df = df[df["_period"] == p]
        p_inc = float(p_df[p_df["type"] == "Income"]["amount"].sum())
        p_exp = float(p_df[p_df["type"] == "Expense"]["amount"].sum())
        month_savings = p_inc - p_exp
        cumulative_savings += month_savings
        
        # Approximate historical net worth
        h_net_worth = liquid_assets_val - (liquid_assets_val - cumulative_savings) + running_assets - running_liab
        
        historical_nw.append({
            "Month": p.strftime("%b %Y"),
            "Net Worth": h_net_worth
        })
        
    trend_df = pd.DataFrame(historical_nw)
    
    if not trend_df.empty:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=trend_df["Month"], y=trend_df["Net Worth"],
            mode="lines+markers+text",
            line=dict(color="#7C3AED", width=2.5),
            marker=dict(size=8, color="#7C3AED"),
            text=trend_df["Net Worth"].apply(lambda v: f"{sym}{v:,.0f}"),
            textposition="top center",
            fill="tozeroy",
            fillcolor="rgba(124,58,237,0.12)",
            hovertemplate="<b>%{x}</b><br>Net Worth: " + sym + "%{y:,.2f}<extra></extra>"
        ))
        
        fig_trend.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E"),
            height=320,
            margin=dict(t=20, b=10, l=10, r=10),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title=f"Value ({sym})")
        )
        st.plotly_chart(fig_trend, use_container_width=True, key="net_worth_trend_chart")
