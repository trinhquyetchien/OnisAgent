"""Transaction summary and category dashboard."""

from typing import Any

import pandas as pd
import streamlit as st

from src.tools.calculator import summarize_transactions


def render_dashboard(transactions: list[dict[str, Any]]) -> None:
    """Render income, expense, balance, and expense-by-category summaries."""
    totals = summarize_transactions(transactions)
    income, expenses, balance = st.columns(3)
    income.metric("Tổng thu", f"{totals['income']:,.0f} ₫")
    expenses.metric("Tổng chi", f"{totals['expenses']:,.0f} ₫")
    balance.metric("Số dư", f"{totals['balance']:,.0f} ₫")

    expense_rows = [
        row for row in transactions if row["type"].strip().lower() == "expense"
    ]
    if not expense_rows:
        st.info("Chưa có giao dịch chi để hiển thị.")
        return

    frame = pd.DataFrame(expense_rows)
    frame["amount"] = pd.to_numeric(frame["amount"])
    by_category = frame.groupby("category", as_index=False)["amount"].sum()
    st.subheader("Chi tiêu theo danh mục")
    st.bar_chart(by_category.set_index("category")["amount"])
    with st.expander("Danh sách giao dịch"):
        st.dataframe(pd.DataFrame(transactions), use_container_width=True, hide_index=True)
