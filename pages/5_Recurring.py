"""pages/5_Recurring.py — Manage and run recurring transaction templates."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import uuid
from datetime import date

from utils import (
    load_recurring, save_recurring, append_rows, get_symbol,
    RECURRENCE_OPTS,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Recurring — Money Tracker",
    page_icon="🔁",
    layout="wide",
    initial_sidebar_state="expanded",
)



# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Money Tracker")
    st.divider()
    sym = get_symbol()


# ── Page header ────────────────────────────────────────────────────────────────
st.title("🔁 Recurring Transactions")
st.caption(
    "Manage your recurring transaction templates. "
    "Use **Run Now** to log a transaction for today based on the template."
)
st.divider()

# ── Load templates ─────────────────────────────────────────────────────────────
templates = load_recurring()

# ── Add new template manually ──────────────────────────────────────────────────
with st.expander("➕ Add New Recurring Template", expanded=False):
    with st.form("new_recurring_form"):
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            r_type = st.selectbox("Type", ["Income", "Expense", "Transfer"], key="r_type")
            r_freq = st.selectbox("Frequency", RECURRENCE_OPTS, key="r_freq")
        with rc2:
            r_cat    = st.text_input("Category", placeholder="e.g. Salary", key="r_cat")
            r_acc    = st.text_input("Account",  placeholder="e.g. Bank Account", key="r_acc")
        with rc3:
            r_amount = st.number_input("Amount", min_value=0.01, value=1000.0,
                                        step=100.0, format="%.2f", key="r_amount")
            r_note   = st.text_input("Note", placeholder="e.g. Monthly rent", key="r_note")

        r_submit = st.form_submit_button("➕ Add Template", type="primary", use_container_width=True)
        if r_submit:
            if not r_cat or not r_acc:
                st.error("Category and Account are required.")
            else:
                new_tpl = dict(
                    id=str(uuid.uuid4())[:8],
                    type=r_type,
                    category=r_cat.strip(),
                    account=r_acc.strip(),
                    transfer_to="",
                    amount=r_amount,
                    note=r_note.strip(),
                    description="",
                    frequency=r_freq,
                    active=True,
                    created=str(date.today()),
                    last_run="",
                )
                templates.append(new_tpl)
                save_recurring(templates)
                st.success("✅ Recurring template added!")
                st.rerun()

st.divider()

# ── List templates ─────────────────────────────────────────────────────────────
if not templates:
    st.info(
        "No recurring templates yet. You can create one here, or check "
        "**🔁 Make this recurring** when adding a transaction."
    )
    st.stop()

# Separate active and inactive
active_tpls   = [t for t in templates if t.get("active", True)]
inactive_tpls = [t for t in templates if not t.get("active", True)]

FREQ_ICONS = {"Daily": "📆", "Weekly": "🗓️", "Monthly": "📅"}
TYPE_COLORS = {
    "Income":   ("#2ecc71", "rgba(46,204,113,0.1)",  "rgba(46,204,113,0.4)"),
    "Expense":  ("#e74c3c", "rgba(231,76,60,0.1)",   "rgba(231,76,60,0.4)"),
    "Transfer": ("#ecf0f1", "rgba(236,240,241,0.06)", "rgba(236,240,241,0.3)"),
}

def render_template_card(tpl: dict, idx: int, is_active: bool):
    color, bg, border = TYPE_COLORS.get(tpl["type"], TYPE_COLORS["Expense"])
    freq_icon = FREQ_ICONS.get(tpl.get("frequency", "Monthly"), "📅")
    last_run  = tpl.get("last_run", "") or "Never"

    st.markdown(f"""
<div style="
    background: {bg};
    border: 1px solid {border};
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 4px;
">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="color:{color}; font-size:1.05rem; font-weight:700;">
                {freq_icon} {tpl['type']} · {tpl['category']}
            </span>
            <span style="color:#aaa; font-size:0.85rem; margin-left:12px;">
                {tpl.get('frequency','Monthly')} · {tpl['account']}
            </span>
        </div>
        <span style="color:{color}; font-size:1.1rem; font-weight:700;">
            {sym}{float(tpl['amount']):,.2f}
        </span>
    </div>
    <div style="color:#888; font-size:0.8rem; margin-top:6px;">
        {('📝 ' + tpl['note']) if tpl.get('note') else ''}
        &nbsp;&nbsp;|&nbsp;&nbsp; Last run: {last_run}
    </div>
</div>
""", unsafe_allow_html=True)

    btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 4])
    with btn_c1:
        if is_active and st.button(
            "▶ Run Now", key=f"run_{tpl['id']}_{idx}", type="primary", use_container_width=True
        ):
            row = dict(
                id=str(uuid.uuid4())[:8],
                date=str(date.today()),
                type=tpl["type"],
                category=tpl["category"],
                account=tpl["account"],
                transfer_to=tpl.get("transfer_to", ""),
                amount=float(tpl["amount"]),
                note=tpl.get("note", ""),
                description=tpl.get("description", ""),
                source="recurring",
            )
            append_rows([row])
            # Update last_run
            for t in templates:
                if t["id"] == tpl["id"]:
                    t["last_run"] = str(date.today())
                    break
            save_recurring(templates)
            st.success(f"✅ {tpl['type']} of {sym}{float(tpl['amount']):,.2f} logged for today!")
            st.rerun()

    with btn_c2:
        toggle_label = "⏸ Pause" if is_active else "▶ Activate"
        if st.button(toggle_label, key=f"toggle_{tpl['id']}_{idx}", use_container_width=True):
            for t in templates:
                if t["id"] == tpl["id"]:
                    t["active"] = not t.get("active", True)
                    break
            save_recurring(templates)
            st.rerun()

    with btn_c3:
        if st.button("🗑 Delete", key=f"del_{tpl['id']}_{idx}", use_container_width=True):
            templates[:] = [t for t in templates if t["id"] != tpl["id"]]
            save_recurring(templates)
            st.success("Template deleted.")
            st.rerun()


# ── Render ACTIVE templates ────────────────────────────────────────────────────
st.subheader(f"✅ Active Templates ({len(active_tpls)})")
if active_tpls:
    for i, tpl in enumerate(active_tpls):
        render_template_card(tpl, i, is_active=True)
else:
    st.info("No active templates.")

# ── Render INACTIVE templates ──────────────────────────────────────────────────
if inactive_tpls:
    st.divider()
    st.subheader(f"⏸ Paused Templates ({len(inactive_tpls)})")
    for i, tpl in enumerate(inactive_tpls):
        render_template_card(tpl, i + len(active_tpls), is_active=False)

# ── Summary table ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("📋 All Templates Summary")
if templates:
    rows = [
        {
            "ID": t["id"],
            "Type": t["type"],
            "Category": t["category"],
            "Account": t["account"],
            "Amount": f"{sym}{float(t['amount']):,.2f}",
            "Frequency": t.get("frequency", "Monthly"),
            "Active": "✅" if t.get("active", True) else "⏸",
            "Last Run": t.get("last_run", "Never") or "Never",
            "Created": t.get("created", ""),
        }
        for t in templates
    ]
    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
