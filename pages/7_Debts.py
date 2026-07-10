"""pages/7_Debts.py — Track loans, EMIs, and debt payoff progress."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import uuid
import plotly.express as px
from datetime import date, datetime

from utils import (
    load_debts, save_debts, append_rows, get_symbol,
    inject_theme_css, render_theme_toggle,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Debts — Money Tracker",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject theme CSS
inject_theme_css()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Money Tracker")
    st.divider()
    sym = get_symbol()
    render_theme_toggle()

st.title("💸 Debt & EMI Tracker")
st.caption("Manage loans, credit card payoffs, EMIs, and visualize your debt-free journey.")
st.divider()

debts = load_debts()

# ── Add New Debt Form ──────────────────────────────────────────────────────────
with st.expander("➕ Add New Debt or Loan", expanded=not debts):
    with st.form("new_debt_form"):
        dc1, dc2 = st.columns(2)
        with dc1:
            d_name = st.text_input("Name / Institution", placeholder="e.g. Home Loan, HDFC Credit Card, Car Loan")
            d_principal = st.number_input(f"Original Principal Amount ({sym})", min_value=1.0, value=50000.0, step=1000.0)
            d_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, max_value=100.0, value=8.5, step=0.1)
        with dc2:
            d_emi = st.number_input(f"Monthly EMI / Payment ({sym})", min_value=0.0, value=2500.0, step=100.0)
            d_remaining = st.number_input(f"Current Remaining Balance ({sym})", min_value=0.0, value=50000.0, step=1000.0)
            d_due_day = st.number_input("Monthly Due Date (Day of Month)", min_value=1, max_value=31, value=5)

        submitted = st.form_submit_button("Add Debt", type="primary", use_container_width=True)
        if submitted:
            if not d_name.strip():
                st.error("Please enter the debt name.")
            elif d_remaining > d_principal:
                st.error("Current remaining balance cannot be greater than the original principal.")
            else:
                new_debt = {
                    "id": str(uuid.uuid4())[:8],
                    "name": d_name.strip(),
                    "principal": float(d_principal),
                    "remaining": float(d_remaining),
                    "interest_rate": float(d_rate),
                    "emi": float(d_emi),
                    "due_day": int(d_due_day),
                    "payments_made": 0,
                    "created_at": date.today().strftime("%Y-%m-%d")
                }
                debts.append(new_debt)
                save_debts(debts)
                st.success(f"💸 Debt for '{d_name}' successfully added!")
                st.rerun()

# ── Render Debts ───────────────────────────────────────────────────────────────
if not debts:
    st.info("No active debts tracked. Add a loan or EMI using the expander above.")
else:
    # Summary of all debts
    total_original = sum(d["principal"] for d in debts)
    total_remaining = sum(d["remaining"] for d in debts)
    total_paid = total_original - total_remaining
    paid_pct = (total_paid / total_original * 100) if total_original > 0 else 0.0

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("💳 Total Remaining Debt", f"{sym}{total_remaining:,.2f}")
    mc2.metric("📈 Total Original Principal", f"{sym}{total_original:,.2f}")
    mc3.metric("🎉 Debt Paid Off", f"{paid_pct:.1f}%")
    st.progress(paid_pct / 100.0)
    st.divider()

    for idx, debt in enumerate(debts):
        p_original = float(debt["principal"])
        p_remaining = float(debt["remaining"])
        rate = float(debt["interest_rate"])
        emi = float(debt["emi"])
        paid = p_original - p_remaining
        pct = (paid / p_original) if p_original > 0 else 0
        
        # Next due date construction
        today = date.today()
        due_day = int(debt["due_day"])
        try:
            next_due = date(today.year, today.month, due_day)
            if next_due < today:
                # Due next month
                if today.month == 12:
                    next_due = date(today.year + 1, 1, due_day)
                else:
                    next_due = date(today.year, today.month + 1, due_day)
        except ValueError:
            # Handle Feb 29/30/31 case
            next_due = date(today.year, today.month, 28)

        st.subheader(f"🏷️ {debt['name']}")
        
        # Color coding progress bars (green = paid off, red = high remaining)
        c_left, c_right = st.columns([2, 1], gap="large")
        
        with c_left:
            # Custom Progress Indicator
            st.markdown(f"**Principal:** {sym}{p_original:,.2f} | **Remaining:** {sym}{p_remaining:,.2f} (**{pct*100:.1f}% paid**)")
            
            # Use red/orange/green color scheme
            bar_color = "red" if pct < 0.3 else ("orange" if pct < 0.7 else "green")
            st.progress(pct)
            
            st.markdown(f"📊 **Interest Rate:** {rate}% APR  ·  **Monthly EMI:** {sym}{emi:,.2f}  ·  **Next Due Date:** {next_due.strftime('%d %b %Y')}")
            
            # Interactive action inputs
            act1, act2 = st.columns(2)
            with act1:
                # Button to Pay Monthly EMI
                if p_remaining <= 0:
                    st.success("🎉 This debt is fully paid off!")
                else:
                    if st.button(f"💵 Pay EMI ({sym}{emi:,.0f})", key=f"pay_emi_{debt['id']}"):
                        # Log transaction in transactions.csv
                        row = dict(
                            id=str(uuid.uuid4())[:8],
                            date=str(date.today()),
                            type="Expense",
                            category="Debt Payment",
                            account="Bank Account",
                            transfer_to="",
                            amount=emi,
                            note=f"EMI payment for {debt['name']}",
                            description=f"Automated payment logged from Debt Tracker.",
                            source="debt_tracker"
                        )
                        append_rows([row])

                        # Deduct from debt remaining balance
                        new_rem = max(p_remaining - emi, 0.0)
                        debts[idx]["remaining"] = float(new_rem)
                        debts[idx]["payments_made"] = int(debt.get("payments_made", 0)) + 1
                        save_debts(debts)
                        st.success(f"Recorded EMI payment of {sym}{emi:,.2f} and logged it as an Expense!")
                        st.rerun()

            with act2:
                # Custom Extra Payoff contribution
                with st.popover("➕ Extra Payment"):
                    with st.form(f"extra_pay_form_{debt['id']}"):
                        extra_amt = st.number_input("Enter Amount", min_value=1.0, value=1000.0, step=100.0)
                        extra_submit = st.form_submit_button("Pay Extra")
                        if extra_submit:
                            row = dict(
                                id=str(uuid.uuid4())[:8],
                                date=str(date.today()),
                                type="Expense",
                                category="Debt Payment",
                                account="Bank Account",
                                transfer_to="",
                                amount=extra_amt,
                                note=f"Extra payment for {debt['name']}",
                                description=f"Extra custom payoff logged from Debt Tracker.",
                                source="debt_tracker"
                            )
                            append_rows([row])

                            new_rem = max(p_remaining - extra_amt, 0.0)
                            debts[idx]["remaining"] = float(new_rem)
                            save_debts(debts)
                            st.success(f"Recorded extra payment of {sym}{extra_amt:,.2f}!")
                            st.rerun()

        with c_right:
            # Amortization / Payoff structure chart
            if p_original > 0:
                payoff_data = pd.DataFrame({
                    "Status": ["Paid", "Remaining"],
                    "Amount": [paid, p_remaining]
                })
                fig = px.pie(
                    payoff_data, values="Amount", names="Status",
                    color_discrete_map={"Paid": "#2ecc71", "Remaining": "#e74c3c"},
                    hole=0.4,
                    height=160
                )
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white" if st.session_state.get("theme", "dark") == "dark" else "#1A1A2E")
                )
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{debt['id']}")
            
        # Delete debt
        col_del, _ = st.columns([1, 4])
        with col_del:
            if st.button("🗑️ Delete Tracker", key=f"del_{debt['id']}", type="secondary", use_container_width=True):
                debts.pop(idx)
                save_debts(debts)
                st.success("Debt tracker removed.")
                st.rerun()
                
        st.divider()
