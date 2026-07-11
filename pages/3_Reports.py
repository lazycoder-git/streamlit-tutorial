"""pages/3_Reports.py — Charts and financial insights."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from utils import (
    load_data, get_symbol, MONTHS, EXPENSE_CATS,
)
from auth import require_login

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Reports — Money Tracker",
    page_icon="📊",
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
    sel_month = st.selectbox("📅 Month", MONTHS, index=now.month - 1, key="rep_month")
    sel_year  = st.number_input("Year", 2020, 2035, value=now.year, step=1, key="rep_year")
    month_num = MONTHS.index(sel_month) + 1

# ── Load data ──────────────────────────────────────────────────────────────────
df = load_data()

st.title("📊 Reports")
st.caption(f"Financial insights for **{sel_month} {int(sel_year)}**")
st.divider()

if df.empty:
    st.info("No data yet. Add some transactions first!")
    st.stop()

# Month filter
mask = (df["date"].dt.month == month_num) & (df["date"].dt.year == int(sel_year))
mdf  = df[mask].copy()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Monthly Breakdown",
    "📉 Trends",
    "🔍 Insights",
    "🗓️ Heatmap",
    "📉 Category Trend",
])

# ─── TAB 1: Monthly breakdown ──────────────────────────────────────────────────
with tab1:
    if mdf.empty:
        st.info(f"No transactions found for {sel_month} {int(sel_year)}.")
    else:
        col_a, col_b = st.columns(2, gap="large")

        with col_a:
            exp_df = (
                mdf[mdf["type"] == "Expense"]
                .groupby("category")["amount"]
                .sum()
                .reset_index()
                .sort_values("amount", ascending=True)
            )
            if not exp_df.empty:
                st.subheader("💸 Spending by Category")
                fig = px.bar(
                    exp_df, x="amount", y="category", orientation="h",
                    color="amount",
                    color_continuous_scale="Reds",
                    text=exp_df["amount"].apply(lambda v: f"{sym}{v:,.0f}"),
                    labels={"amount": "Amount", "category": ""},
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"), height=380,
                    margin=dict(t=10, b=10, l=10, r=60),
                    coloraxis_showscale=False,
                    xaxis=dict(showgrid=False, visible=False),
                    yaxis=dict(showgrid=False),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No expense data for this month.")

        with col_b:
            inc_df = (
                mdf[mdf["type"] == "Income"]
                .groupby("category")["amount"]
                .sum()
                .reset_index()
                .sort_values("amount", ascending=False)
            )
            if not inc_df.empty:
                st.subheader("💰 Income by Source")
                fig2 = px.pie(
                    inc_df, values="amount", names="category",
                    hole=0.48,
                    color_discrete_sequence=px.colors.sequential.Greens_r,
                )
                fig2.update_traces(
                    textinfo="percent+label",
                    hovertemplate="%{label}: " + sym + "%{value:,.2f}<extra></extra>",
                )
                fig2.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"), height=380,
                    margin=dict(t=10, b=10, l=10, r=10),
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No income data for this month.")

# ─── TAB 2: Trends ────────────────────────────────────────────────────────────
with tab2:
    col_c, col_d = st.columns(2, gap="large")

    with col_c:
        st.subheader("📈 Running Balance (All Time)")
        flow = df[df["type"].isin(["Income", "Expense"])].copy()
        flow["signed"] = flow.apply(
            lambda r: r["amount"] if r["type"] == "Income" else -r["amount"], axis=1
        )
        daily = (
            flow.groupby("date")["signed"]
            .sum()
            .sort_index()
            .cumsum()
            .reset_index()
        )
        daily.columns = ["Date", "Balance"]

        if not daily.empty:
            fig3 = px.line(
                daily, x="Date", y="Balance",
                labels={"Balance": f"Balance ({sym})", "Date": ""},
                color_discrete_sequence=["#7C3AED"],
            )
            fig3.update_traces(fill="tozeroy", fillcolor="rgba(124,58,237,0.15)")
            fig3.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=320,
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No data to display.")

    with col_d:
        st.subheader("📊 Last 6 Months — Income vs Expenses")
        df["_period"] = df["date"].dt.to_period("M")
        recent_6 = sorted(df["_period"].unique())[-6:]
        df6 = df[df["_period"].isin(recent_6) & df["type"].isin(["Income", "Expense"])].copy()
        df6["Month"] = df6["date"].dt.strftime("%b %Y")

        if not df6.empty:
            summary = (
                df6.groupby(["Month", "type"])["amount"]
                .sum()
                .reset_index()
            )
            order_map = {p.strftime("%b %Y"): i for i, p in enumerate(recent_6)}
            summary["_ord"] = summary["Month"].map(order_map)
            summary = summary.sort_values("_ord")

            fig4 = px.bar(
                summary, x="Month", y="amount", color="type",
                barmode="group",
                color_discrete_map={"Income": "#2ecc71", "Expense": "#e74c3c"},
                labels={"amount": f"Amount ({sym})", "Month": "", "type": ""},
            )
            fig4.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=320,
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
                xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Not enough data for 6-month comparison.")

# ─── TAB 3: Insights ──────────────────────────────────────────────────────────
with tab3:
    st.subheader("🔍 Quick Insights")

    if mdf.empty:
        st.info(f"No data for {sel_month} {int(sel_year)} to analyse.")
    else:
        exp_mdf = mdf[mdf["type"] == "Expense"]
        inc_mdf = mdf[mdf["type"] == "Income"]
        total_inc = float(inc_mdf["amount"].sum())
        total_exp = float(exp_mdf["amount"].sum())
        net       = total_inc - total_exp

        ca, cb = st.columns(2)
        with ca:
            if not exp_mdf.empty:
                top_cat = exp_mdf.groupby("category")["amount"].sum().idxmax()
                top_amt = exp_mdf.groupby("category")["amount"].sum().max()
                pct_exp = (top_amt / total_exp * 100) if total_exp > 0 else 0
                st.info(
                    f"🏆 **Top spending category:** {top_cat}\n\n"
                    f"{sym}{top_amt:,.2f}  ({pct_exp:.1f}% of expenses)"
                )
            else:
                st.info("No expense data this month.")

        with cb:
            if net >= 0:
                sav_pct = (net / total_inc * 100) if total_inc > 0 else 0
                st.success(
                    f"✅ **You saved {sym}{net:,.2f} this month!**\n\n"
                    f"That's **{sav_pct:.1f}%** of your income."
                )
            else:
                over_pct = (abs(net) / total_exp * 100) if total_exp > 0 else 0
                st.error(
                    f"⚠️ **Overspent by {sym}{abs(net):,.2f} this month.**\n\n"
                    f"Expenses exceeded income by **{over_pct:.1f}%**."
                )

        st.divider()

        prev_m = month_num - 1 if month_num > 1 else 12
        prev_y = int(sel_year) if month_num > 1 else int(sel_year) - 1
        prev_mask = (df["date"].dt.month == prev_m) & (df["date"].dt.year == prev_y)
        prev_df   = df[prev_mask]

        st.subheader(f"📊 vs {MONTHS[prev_m - 1]} {prev_y}")
        if not prev_df.empty and not exp_mdf.empty:
            cur_cats  = exp_mdf.groupby("category")["amount"].sum()
            prev_cats = prev_df[prev_df["type"] == "Expense"].groupby("category")["amount"].sum()
            rows = []
            for cat in cur_cats.index:
                cur  = float(cur_cats.get(cat, 0))
                prev = float(prev_cats.get(cat, 0))
                chg  = ((cur - prev) / prev * 100) if prev > 0 else None
                rows.append({
                    "Category":    cat,
                    "This Month":  f"{sym}{cur:,.2f}",
                    "Last Month":  f"{sym}{prev:,.2f}" if prev > 0 else "—",
                    "Change":      f"{chg:+.1f}%" if chg is not None else "New",
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Not enough data for month-on-month comparison.")

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
                dest = str(row.get("transfer_to", ""))
                if dest:
                    balances[dest] = balances.get(dest, 0.0) + amt

        if balances:
            bal_rows = [{"Account": k, "Balance": f"{sym}{v:,.2f}"}
                        for k, v in sorted(balances.items())]
            st.dataframe(pd.DataFrame(bal_rows), use_container_width=True, hide_index=True)

# ─── TAB 4: Day-of-Week Spending Heatmap ──────────────────────────────────────
with tab4:
    st.subheader("🗓️ Spending Heatmap — Day of Week × Week of Month")
    st.caption("See which days you tend to spend the most money.")

    exp_all = df[df["type"] == "Expense"].copy()

    if exp_all.empty:
        st.info("No expense data to display.")
    else:
        # Filter to selected month/year
        hmap_df = exp_all[
            (exp_all["date"].dt.month == month_num) &
            (exp_all["date"].dt.year  == int(sel_year))
        ].copy()

        if hmap_df.empty:
            st.info(f"No expense data for {sel_month} {int(sel_year)}.")
        else:
            hmap_df["day_name"]    = hmap_df["date"].dt.strftime("%a")  # Mon, Tue…
            hmap_df["week_of_mon"] = hmap_df["date"].apply(
                lambda d: f"Week {(d.day - 1) // 7 + 1}"
            )

            day_order  = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            week_order = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]

            pivot = (
                hmap_df.groupby(["week_of_mon", "day_name"])["amount"]
                .sum()
                .reset_index()
                .pivot(index="week_of_mon", columns="day_name", values="amount")
                .reindex(index=week_order, columns=day_order)
                .fillna(0)
            )

            fig_hmap = go.Figure(data=go.Heatmap(
                z=pivot.values,
                x=day_order,
                y=pivot.index.tolist(),
                colorscale="RdPu",
                hoverongaps=False,
                hovertemplate="<b>%{y} · %{x}</b><br>"
                              + sym + "%{z:,.2f}<extra></extra>",
                text=[[f"{sym}{v:,.0f}" if v > 0 else "" for v in row]
                      for row in pivot.values],
                texttemplate="%{text}",
            ))
            fig_hmap.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=320,
                margin=dict(t=20, b=20, l=10, r=10),
                xaxis=dict(showgrid=False, side="top"),
                yaxis=dict(showgrid=False, autorange="reversed"),
            )
            st.plotly_chart(fig_hmap, use_container_width=True)

            # Also show all-time heatmap
            st.divider()
            st.subheader("📅 All-Time Spending by Day of Week")
            dow_df = exp_all.copy()
            dow_df["day_name"] = dow_df["date"].dt.strftime("%a")
            dow_summary = (
                dow_df.groupby("day_name")["amount"]
                .sum()
                .reindex(day_order)
                .fillna(0)
                .reset_index()
            )
            dow_summary.columns = ["Day", "Total"]

            fig_dow = px.bar(
                dow_summary, x="Day", y="Total",
                color="Total",
                color_continuous_scale="Purples",
                text=dow_summary["Total"].apply(lambda v: f"{sym}{v:,.0f}"),
                labels={"Total": f"Total Spent ({sym})", "Day": ""},
            )
            fig_dow.update_traces(textposition="outside")
            fig_dow.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=280,
                margin=dict(t=10, b=10, l=10, r=10),
                coloraxis_showscale=False,
                yaxis=dict(showgrid=False, visible=False),
                xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_dow, use_container_width=True)

# ─── TAB 5: Category Trend ────────────────────────────────────────────────────
with tab5:
    st.subheader("📉 Category Spending Trend (Last 12 Months)")
    st.caption("Track how spending in a specific category has changed over time.")

    used_exp_cats = []
    if not df.empty:
        used_exp_cats = (
            df[df["type"] == "Expense"]["category"]
            .dropna().unique().tolist()
        )
    all_exp_cats = sorted(set(EXPENSE_CATS + used_exp_cats))

    if not all_exp_cats:
        st.info("No expense categories found.")
    else:
        sel_cat = st.selectbox("🏷️ Select Category", all_exp_cats, key="trend_cat")

        # Build last-12-months data
        df["_period"] = df["date"].dt.to_period("M")
        all_periods   = sorted(df["_period"].unique())[-12:]

        trend_df = (
            df[
                (df["type"] == "Expense") &
                (df["category"] == sel_cat) &
                (df["_period"].isin(all_periods))
            ]
            .groupby("_period")["amount"]
            .sum()
            .reindex(all_periods, fill_value=0)
            .reset_index()
        )
        trend_df.columns  = ["Period", "Amount"]
        trend_df["Month"] = trend_df["Period"].dt.strftime("%b %Y")

        if trend_df["Amount"].sum() == 0:
            st.info(f"No spending recorded under **{sel_cat}** in the last 12 months.")
        else:
            avg_spend = trend_df["Amount"].mean()

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=trend_df["Month"], y=trend_df["Amount"],
                mode="lines+markers+text",
                name=sel_cat,
                line=dict(color="#7C3AED", width=2.5),
                marker=dict(size=8, color="#7C3AED"),
                text=trend_df["Amount"].apply(lambda v: f"{sym}{v:,.0f}" if v > 0 else ""),
                textposition="top center",
                fill="tozeroy",
                fillcolor="rgba(124,58,237,0.12)",
                hovertemplate="<b>%{x}</b><br>" + sym + "%{y:,.2f}<extra></extra>",
            ))
            # Average line
            fig_trend.add_hline(
                y=avg_spend,
                line_dash="dot",
                line_color="rgba(255,200,0,0.6)",
                annotation_text=f"Avg {sym}{avg_spend:,.0f}",
                annotation_position="top right",
                annotation_font_color="rgba(255,200,0,0.9)",
            )
            fig_trend.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=360,
                margin=dict(t=30, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title=f"Amount ({sym})"),
                showlegend=False,
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            # Summary stats
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("📊 Avg / Month",  f"{sym}{avg_spend:,.2f}")
            sc2.metric("📈 Peak Month",   trend_df.loc[trend_df["Amount"].idxmax(), "Month"])
            sc3.metric("💰 Total (12mo)", f"{sym}{trend_df['Amount'].sum():,.2f}")
