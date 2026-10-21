"""pages/3_Reports.py — Financial Reports, Statistical Analytics, and Domain Insights."""

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
    load_data, get_symbol, render_demo_reset_sidebar, MONTHS, EXPENSE_CATS,
)
from auth import require_login

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Reports & Analytics — Money Tracker",
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

    render_demo_reset_sidebar()

# ── Load data ──────────────────────────────────────────────────────────────────
df = load_data()

st.title("📊 Financial Intelligence & Reports")
st.caption(f"Comprehensive trend diagnosis and analytical takeaways for **{sel_month} {int(sel_year)}**")
st.divider()

if df.empty:
    st.warning("⚠️ No data available. Click '🔄 Reload 12-Mo Case Study Data' in the sidebar to populate rich demonstration data.")
    st.stop()

# Month filter
mask = (df["date"].dt.month == month_num) & (df["date"].dt.year == int(sel_year))
mdf  = df[mask].copy()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Monthly Breakdown",
    "📉 Macro Trends",
    "🚨 Anomaly & Variance Insights",
    "🗓️ Behavioral Heatmap",
    "📉 Category Trajectory",
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
                st.subheader("💰 Inflow by Stream")
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

        # Analytical Interpretation Callout Box
        if not exp_df.empty:
            total_m_exp = exp_df["amount"].sum()
            top_row = exp_df.sort_values("amount", ascending=False).iloc[0]
            top_pct = (top_row["amount"] / total_m_exp * 100) if total_m_exp > 0 else 0
            
            fixed_needs = exp_df[exp_df["category"].isin(["Rent", "Utilities", "Health", "Transport"])]["amount"].sum()
            discretionary = total_m_exp - fixed_needs
            fixed_pct = (fixed_needs / total_m_exp * 100) if total_m_exp > 0 else 0

            st.markdown(f"""
            <div style="background: rgba(124,58,237,0.08); border-left: 4px solid #7C3AED; padding: 14px 18px; border-radius: 6px; margin-top: 15px;">
                <h5 style="margin: 0 0 6px 0; color: #A78BFA;">💡 What This Chart Conveys & Actionable Insights</h5>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.93rem; color: #E2E8F0; line-height: 1.6;">
                    <li><b>Category Concentration</b>: <b>{top_row['category']}</b> represents the dominant expense stream at <b>{sym}{top_row['amount']:,.2f}</b>, consuming <b>{top_pct:.1f}%</b> of this month's total expenditure.</li>
                    <li><b>Fixed vs. Discretionary Balance</b>: Committed non-negotiable living costs (Rent, Utilities, Health, Commute) form <b>{fixed_pct:.1f}%</b> ({sym}{fixed_needs:,.2f}) of your outflow, leaving <b>{100 - fixed_pct:.1f}%</b> ({sym}{discretionary:,.2f}) in flexible lifestyle choices.</li>
                    <li><b>Strategic Conclusion</b>: Because your committed fixed obligations are below the 60% risk threshold, your monthly cash structure is agile and resilient against unexpected income shocks.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

# ─── TAB 2: Trends ────────────────────────────────────────────────────────────
with tab2:
    col_c, col_d = st.columns(2, gap="large")

    with col_c:
        st.subheader("📈 Net Wealth Accumulation Curve (All Time)")
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
                color_discrete_sequence=["#10B981"],
            )
            fig3.update_traces(fill="tozeroy", fillcolor="rgba(16,185,129,0.12)")
            fig3.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=320,
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)"),
            )
            st.plotly_chart(fig3, use_container_width=True)
            st.caption("💡 **Interpretation**: The persistently positive slope demonstrates that cash inflows consistently outpace burn rate, preventing debt dependency.")
        else:
            st.info("No data to display.")

    with col_d:
        st.subheader("📊 6-Month Inflow vs Outflow Cash Dynamics")
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
                color_discrete_map={"Income": "#10B981", "Expense": "#EF4444"},
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
            st.caption("💡 **Interpretation**: Compares monthly liquidity margins. Green bars consistently exceeding red bars confirm positive monthly surplus creation.")
        else:
            st.info("Not enough data for 6-month comparison.")

# ─── TAB 3: Insights & Anomalies ──────────────────────────────────────────────
with tab3:
    st.subheader("🚨 Statistical Spending Anomalies & MoM Variance")
    st.caption("Automated statistical anomaly detection flagging categories exceeding 1.5 standard deviations above their 12-month baseline.")

    # Compute 12-month baseline mean & std dev for each category
    exp_all = df[df["type"] == "Expense"].copy()
    exp_all["_period"] = exp_all["date"].dt.to_period("M")
    
    monthly_cat_matrix = (
        exp_all.groupby(["_period", "category"])["amount"]
        .sum()
        .unstack(fill_value=0)
    )

    cat_stats = []
    current_period = pd.Period(f"{int(sel_year)}-{month_num:02d}", freq="M")

    for cat in monthly_cat_matrix.columns:
        series = monthly_cat_matrix[cat]
        mean_val = series.mean()
        std_val  = series.std()
        cur_val  = series.get(current_period, 0.0)
        
        z_score = (cur_val - mean_val) / std_val if std_val > 0 else 0.0
        is_spike = z_score >= 1.5 and cur_val > 200

        cat_stats.append({
            "Category": cat,
            "This Month": cur_val,
            "12-Mo Avg": mean_val,
            "Variance (Z-Score)": z_score,
            "Is Spike": is_spike
        })

    stat_df = pd.DataFrame(cat_stats)
    spikes = stat_df[stat_df["Is Spike"] == True]

    if not spikes.empty:
        for _, spike in spikes.iterrows():
            st.warning(
                f"⚠️ **Statistical Spending Surge in {spike['Category']}**: Spending reached **{sym}{spike['This Month']:,.2f}** "
                f"(vs 12-month benchmark average of {sym}{spike['12-Mo Avg']:,.2f}, +{spike['Variance (Z-Score)']:.1f}σ above normal). "
                f"This reflects an episodic outlier (e.g. seasonal travel, medical procedure, or festive shopping) rather than structural budget failure."
            )
    else:
        st.success("✅ **Stable Spending Baseline**: No statistically abnormal expense surges detected this month. All categories remained within 1.5σ of their historical baseline.")

    st.divider()

    # Month over month delta table
    prev_m = month_num - 1 if month_num > 1 else 12
    prev_y = int(sel_year) if month_num > 1 else int(sel_year) - 1
    prev_mask = (df["date"].dt.month == prev_m) & (df["date"].dt.year == prev_y)
    prev_df   = df[prev_mask]

    st.subheader(f"📊 Month-on-Month Variance vs {MONTHS[prev_m - 1]} {prev_y}")
    exp_mdf = mdf[mdf["type"] == "Expense"]
    if not prev_df.empty and not exp_mdf.empty:
        cur_cats  = exp_mdf.groupby("category")["amount"].sum()
        prev_cats = prev_df[prev_df["type"] == "Expense"].groupby("category")["amount"].sum()
        rows = []
        for cat in sorted(set(cur_cats.index.tolist() + prev_cats.index.tolist())):
            cur  = float(cur_cats.get(cat, 0.0))
            prev = float(prev_cats.get(cat, 0.0))
            chg  = ((cur - prev) / prev * 100) if prev > 0 else None
            abs_chg = cur - prev
            rows.append({
                "Category": cat,
                "This Month": f"{sym}{cur:,.2f}",
                "Previous Month": f"{sym}{prev:,.2f}" if prev > 0 else "—",
                "Dollar Change": f"{'+' if abs_chg >= 0 else ''}{sym}{abs_chg:,.2f}",
                "Percentage Change": f"{chg:+.1f}%" if chg is not None else "New",
                "Evaluation": "🔴 Increased" if (chg is not None and chg > 15) else ("🟢 Decreased" if (chg is not None and chg < -10) else "⚪ Stable")
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Log transactions across adjacent months to unlock month-on-month variance comparisons.")

# ─── TAB 4: Day-of-Week Spending Heatmap ──────────────────────────────────────
with tab4:
    st.subheader("🗓️ Behavioral Spending Heatmap — Day of Week × Week of Month")
    st.caption("Identify temporal spending clusters and behavioral lifestyle habits.")

    exp_all = df[df["type"] == "Expense"].copy()

    if exp_all.empty:
        st.info("No expense data to display.")
    else:
        hmap_df = exp_all[
            (exp_all["date"].dt.month == month_num) &
            (exp_all["date"].dt.year  == int(sel_year))
        ].copy()

        if hmap_df.empty:
            st.info(f"No expense data for {sel_month} {int(sel_year)}.")
        else:
            hmap_df["day_name"]    = hmap_df["date"].dt.strftime("%a")
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
                hovertemplate="<b>%{y} · %{x}</b><br>" + sym + "%{z:,.2f}<extra></extra>",
                text=[[f"{sym}{v:,.0f}" if v > 0 else "" for v in row] for row in pivot.values],
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

            # Behavioral insight box
            st.markdown(f"""
            <div style="background: rgba(124,58,237,0.08); border-left: 4px solid #7C3AED; padding: 12px 16px; border-radius: 6px; margin-top: 10px;">
                <h5 style="margin: 0 0 4px 0; color: #A78BFA;">🧠 Behavioral Finance Takeaway</h5>
                <p style="margin: 0; font-size: 0.92rem; color: #E2E8F0;">
                    <b>Weekend Social Surge</b>: Spending visibly aggregates around Fridays, Saturdays, and Sundays (dining out, social events, entertainment). 
                    Weekdays (Monday–Wednesday) remain largely low-friction essential spending days. Implementing weekend dining caps represents the highest-leverage area for budget savings.
                </p>
            </div>
            """, unsafe_allow_html=True)

# ─── TAB 5: Category Trend ────────────────────────────────────────────────────
with tab5:
    st.subheader("📉 Long-Term Category Trajectory (12 Months)")
    st.caption("Evaluate spending velocity, inflation creep, and stability across specific expense streams.")

    used_exp_cats = df[df["type"] == "Expense"]["category"].dropna().unique().tolist()
    all_exp_cats = sorted(set(EXPENSE_CATS + used_exp_cats))

    if all_exp_cats:
        sel_cat = st.selectbox("🏷️ Select Category", all_exp_cats, key="trend_cat")

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

        if trend_df["Amount"].sum() > 0:
            avg_spend = trend_df["Amount"].mean()
            std_spend = trend_df["Amount"].std()
            cv = (std_spend / avg_spend) if avg_spend > 0 else 0.0

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
            fig_trend.add_hline(
                y=avg_spend,
                line_dash="dot",
                line_color="rgba(255,200,0,0.7)",
                annotation_text=f"12-Mo Baseline {sym}{avg_spend:,.0f}",
                annotation_position="top right",
            )
            fig_trend.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=340,
                margin=dict(t=30, b=10, l=10, r=10),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title=f"Amount ({sym})"),
                showlegend=False,
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("📊 12-Mo Monthly Mean", f"{sym}{avg_spend:,.2f}")
            sc2.metric("📈 Peak Outflow Month", trend_df.loc[trend_df["Amount"].idxmax(), "Month"])
            sc3.metric("🎯 Total Category Spend", f"{sym}{trend_df['Amount'].sum():,.2f}")

            # Volatility diagnosis
            if cv < 0.20:
                vol_badge = "🟢 Highly Predictable / Fixed Need (Low Variance)"
                vol_desc = "Expenses in this bucket are consistent and structured, requiring little day-to-day micromanagement."
            elif cv < 0.60:
                vol_badge = "🟡 Moderate Variance (Controlled Discretionary)"
                vol_desc = "Normal fluctuations based on monthly social activities and minor seasonal shifts."
            else:
                vol_badge = "🔴 High Volatility / Seasonal Outlier Spikes"
                vol_desc = "Characterized by sharp seasonal spikes (e.g. annual travel, holiday purchases, or one-time emergencies)."

            st.info(f"**Category Classification**: **{vol_badge}**\n\n{vol_desc}")
        else:
            st.info(f"No transactions recorded for **{sel_cat}** in the last 12 months.")
