import streamlit as st
import pandas as pd


def render_credit_filters(df: pd.DataFrame):

    filtered = df.copy()

    st.subheader("🔍 الفلاتر")

    col1, col2, col3 = st.columns(3)

    # =============================
    # Salesperson
    # =============================

    salespersons = ["الكل"] + sorted(
        filtered["Salesperson"].dropna().unique().tolist()
    )

    selected_salesperson = col1.selectbox(
        "المندوب",
        salespersons
    )

    if selected_salesperson != "الكل":
        filtered = filtered[
            filtered["Salesperson"] == selected_salesperson
        ]

    # =============================
    # Customer
    # =============================

    customers = ["الكل"] + sorted(
        filtered["CustomerName"].dropna().unique().tolist()
    )

    selected_customer = col2.selectbox(
        "العميل",
        customers
    )

    if selected_customer != "الكل":
        filtered = filtered[
            filtered["CustomerName"] == selected_customer
        ]

    # =============================
    # Risk
    # =============================

    risks = ["الكل"] + sorted(
        filtered["Risk"].dropna().unique().tolist()
    )

    selected_risk = col3.selectbox(
        "مستوى الخطورة",
        risks
    )

    if selected_risk != "الكل":
        filtered = filtered[
            filtered["Risk"] == selected_risk
        ]

    st.divider()

    return filtered