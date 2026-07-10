"""pages/2_History.py — Filter, search, edit, delete, and export transactions."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
from datetime import date, datetime

import streamlit as st
import pandas as pd

from utils import (
    load_data, save_dataframe, get_symbol,
    ACCOUNTS, INCOME_CATS, EXPENSE_CATS, COLUMNS,
    inject_theme_css, render_theme_toggle,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="History — Money Tracker",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject theme CSS
inject_theme_css()

ALL_CATS = sorted(set(INCOME_CATS + EXPENSE_CATS + ["Transfer"]))

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💰 Money Tracker")
    st.divider()
    sym = get_symbol()
    st.divider()
    render_theme_toggle()
    st.divider()

    st.subheader("🔍 Filters")

    today = date.today()
    start_default = date(today.year, today.month, 1)
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("From", value=start_default, key="h_start")
    with c2:
        end_date = st.date_input("To",   value=today,         key="h_end")

    type_filter = st.selectbox(
        "Type", ["All", "Income", "Expense", "Transfer"], key="h_type"
    )

    if type_filter == "Income":
        cat_opts = INCOME_CATS
    elif type_filter == "Expense":
        cat_opts = EXPENSE_CATS
    elif type_filter == "Transfer":
        cat_opts = ["Transfer"]
    else:
        cat_opts = ALL_CATS

    sel_cats = st.multiselect("Category", cat_opts, key="h_cats")
    sel_accs = st.multiselect("Account",  ACCOUNTS, key="h_accs")


# ── Load data ──────────────────────────────────────────────────────────────────
df = load_data()

st.title("📋 Transaction History")

if df.empty:
    st.info("No transactions yet. Add some from the **Add Transaction** page!")
    st.stop()

# ── Text search bar ────────────────────────────────────────────────────────────
search_query = st.text_input(
    "🔎 Search",
    placeholder="Search by note, category, account, type…",
    key="h_search",
)

# ── Apply filters ──────────────────────────────────────────────────────────────
mask = (
    (df["date"].dt.date >= start_date) &
    (df["date"].dt.date <= end_date)
)
if type_filter != "All":
    mask &= df["type"] == type_filter
if sel_cats:
    mask &= df["category"].isin(sel_cats)
if sel_accs:
    mask &= df["account"].isin(sel_accs)

filtered = df[mask].copy().sort_values("date", ascending=False)

# ── Apply text search ──────────────────────────────────────────────────────────
if search_query.strip():
    q = search_query.strip().lower()
    text_mask = (
        filtered["note"].str.lower().str.contains(q, na=False) |
        filtered["category"].str.lower().str.contains(q, na=False) |
        filtered["account"].str.lower().str.contains(q, na=False) |
        filtered["type"].str.lower().str.contains(q, na=False) |
        filtered["description"].str.lower().str.contains(q, na=False)
    )
    filtered = filtered[text_mask]

st.caption(f"Showing **{len(filtered)}** of **{len(df)}** transactions")
st.divider()

# ── Summary metrics ────────────────────────────────────────────────────────────
inc = float(filtered[filtered["type"] == "Income"]["amount"].sum())
exp = float(filtered[filtered["type"] == "Expense"]["amount"].sum())
net = inc - exp
m1, m2, m3, m4 = st.columns(4)
m1.metric("Records",   len(filtered))
m2.metric("Income",    f"{sym}{inc:,.2f}")
m3.metric("Expenses",  f"{sym}{exp:,.2f}")
m4.metric("Net",       f"{sym}{net:,.2f}")

st.divider()

if filtered.empty:
    st.info("No transactions match the current filters.")
    st.stop()

# ── Tabs: View/Edit | Export ───────────────────────────────────────────────────
tab_view, tab_export = st.tabs(["📝 View & Edit", "⬇️ Export"])

# ─── TAB: View & Edit ────────────────────────────────────────────────────────
with tab_view:
    st.caption(
        "💡 **Tip:** You can edit cells directly in the table below. "
        "Check the **Delete** column to mark rows for removal, then click the buttons below."
    )

    # Build display frame
    display_cols = ["date", "type", "category", "account", "amount",
                    "note", "transfer_to"]
    display = filtered[display_cols].copy()
    display["date"] = display["date"].dt.strftime("%Y-%m-%d")

    orig_indices = filtered.index.tolist()
    display_reset = display.reset_index(drop=True)
    display_reset.insert(0, "🗑", False)

    edited = st.data_editor(
        display_reset,
        use_container_width=True,
        hide_index=True,
        column_config={
            "🗑":          st.column_config.CheckboxColumn("Delete", default=False),
            "amount":      st.column_config.NumberColumn("Amount", format="%.2f", min_value=0.01),
            "date":        st.column_config.TextColumn("Date"),
            "type":        st.column_config.SelectboxColumn(
                               "Type", options=["Income", "Expense", "Transfer"]
                           ),
            "category":    st.column_config.TextColumn("Category"),
            "account":     st.column_config.TextColumn("Account"),
            "note":        st.column_config.TextColumn("Note"),
            "transfer_to": st.column_config.TextColumn("Transfer To"),
        },
        # Leave all columns editable — data cols for inline edit, 🗑 for delete selection
        key="hist_editor",
        num_rows="fixed",
    )

    col_save, col_del, col_spacer = st.columns([1, 1, 3])

    # ── Save edits ─────────────────────────────────────────────────────────────
    with col_save:
        if st.button("💾 Save Edits", type="primary"):
            working = df.copy()
            edit_data = edited.drop(columns=["🗑"])
            for reset_pos, orig_idx in enumerate(orig_indices):
                row_edits = edit_data.iloc[reset_pos]
                for col in edit_data.columns:
                    working.at[orig_idx, col] = row_edits[col]
            # Re-parse date and amount
            working["date"]   = pd.to_datetime(working["date"], errors="coerce")
            working["amount"] = pd.to_numeric(working["amount"], errors="coerce").fillna(0.0)
            save_dataframe(working)
            st.success("✅ Changes saved!")
            st.rerun()

    # ── Delete selected rows ───────────────────────────────────────────────────
    with col_del:
        delete_positions = edited[edited["🗑"]].index.tolist()
        del_orig = [orig_indices[pos] for pos in delete_positions]
        n_del = len(del_orig)
        if st.button(
            f"🗑 Delete {n_del} row{'s' if n_del != 1 else ''}",
            disabled=(n_del == 0),
            type="secondary",
        ):
            remaining = df.drop(index=del_orig).reset_index(drop=True)
            save_dataframe(remaining)
            st.success(f"Deleted {n_del} transaction(s).")
            st.rerun()

# ─── TAB: Export ──────────────────────────────────────────────────────────────
with tab_export:
    st.subheader("⬇️ Export Transactions")

    ecol1, ecol2 = st.columns(2)

    # CSV download
    with ecol1:
        st.markdown("### 📄 CSV Export")
        st.caption("Export filtered transactions as a comma-separated values file.")
        export_df = filtered.copy()
        export_df["date"] = export_df["date"].dt.strftime("%Y-%m-%d")
        csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")  # utf-8-sig adds BOM for Excel compatibility
        fname_csv = f"transactions_{date.today().strftime('%Y-%m-%d')}.csv"
        st.download_button(
            "⬇️ Download CSV",
            data=csv_bytes,
            file_name=fname_csv,
            mime="text/csv",
            use_container_width=True,
            key="dl_csv",
        )

    # PDF download
    with ecol2:
        st.markdown("### 📑 PDF Export")
        st.caption("Export filtered transactions as a formatted PDF report.")

        if st.button("Generate PDF", use_container_width=True):
            try:
                from fpdf import FPDF

                def _safe(text: str) -> str:
                    """Strip non-latin1 characters so built-in Helvetica doesn't crash."""
                    return (
                        text
                        .replace("\u2014", "-")   # em dash —
                        .replace("\u2013", "-")   # en dash –
                        .replace("\u2194", "<->") # ↔
                        .replace("\u20b9", "Rs")  # ₹
                        .replace("\u20ac", "EUR") # €
                        .replace("\u00a3", "GBP") # £
                        .replace("\u00a5", "JPY") # ¥
                        .encode("latin-1", errors="replace")
                        .decode("latin-1")
                    )

                class PDF(FPDF):
                    def header(self):
                        self.set_font("Helvetica", "B", 14)
                        self.cell(0, 10, "Money Tracker - Transaction Report", align="C", new_x="LMARGIN", new_y="NEXT")
                        self.set_font("Helvetica", "", 9)
                        self.cell(0, 6, f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
                                  align="C", new_x="LMARGIN", new_y="NEXT")
                        self.ln(4)

                    def footer(self):
                        self.set_y(-15)
                        self.set_font("Helvetica", "I", 8)
                        self.cell(0, 10, f"Page {self.page_no()}", align="C")

                pdf = PDF(orientation="L", unit="mm", format="A4")
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()

                # Table header
                cols   = ["Date", "Type", "Category", "Account", "Amount", "Note"]
                widths = [28, 22, 38, 38, 30, 110]
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_fill_color(30, 30, 50)
                pdf.set_text_color(255, 255, 255)
                for w, col in zip(widths, cols):
                    pdf.cell(w, 8, col, border=1, fill=True)
                pdf.ln()

                # Rows
                pdf.set_font("Helvetica", "", 8)
                for _, row in filtered.iterrows():
                    if row["type"] == "Income":
                        pdf.set_text_color(46, 160, 90)
                    elif row["type"] == "Expense":
                        pdf.set_text_color(180, 60, 50)
                    else:
                        pdf.set_text_color(80, 80, 80)

                    sign = "+" if row["type"] == "Income" else ("-" if row["type"] == "Expense" else "~")
                    # Use sym_ascii fallback for currency symbols not in latin-1
                    sym_ascii = _safe(sym)
                    vals = [
                        row["date"].strftime("%d %b %Y") if hasattr(row["date"], "strftime") else str(row["date"]),
                        str(row["type"]),
                        _safe(str(row["category"])),
                        _safe(str(row["account"])),
                        f"{sign}{sym_ascii}{float(row['amount']):,.2f}",
                        _safe(str(row["note"]))[:50],
                    ]
                    for w, v in zip(widths, vals):
                        pdf.cell(w, 7, v, border=1)
                    pdf.ln()

                pdf_bytes = bytes(pdf.output())
                fname_pdf = f"transactions_{date.today().strftime('%Y-%m-%d')}.pdf"
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=fname_pdf,
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_pdf",
                )
            except ImportError:
                st.error("fpdf2 is not installed. Run: `pip install fpdf2`")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
