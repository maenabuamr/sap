import streamlit as st


def render_global_filters(aging, sales):

    st.sidebar.header("🔍 الفلاتر")

    filters = {}

    # ==========================================
    # Company
    # ==========================================

    companies = ["الكل"]

    if "DB" in aging.columns:

        companies += sorted(
            aging["DB"].dropna().unique().tolist()
        )

    filters["company"] = st.sidebar.selectbox(
        "🏢 الشركة",
        companies
    )

    # ==========================================
    # Year
    # ==========================================

    years = ["الكل"]

    if "Year" in sales.columns:

        years += sorted(
            sales["Year"].dropna().unique().tolist()
        )

    filters["year"] = st.sidebar.selectbox(
        "📅 السنة",
        years
    )

    # ==========================================
    # Month
    # ==========================================

    months = ["الكل"]

    if "Month" in sales.columns:

        months += sorted(
            sales["Month"].dropna().unique().tolist()
        )

    filters["month"] = st.sidebar.selectbox(
        "📆 الشهر",
        months
    )

    # ==========================================
    # Salesperson
    # ==========================================

    salespersons = ["الكل"]

    if "Salesperson" in aging.columns:

        salespersons += sorted(
            aging["Salesperson"].dropna().unique().tolist()
        )

    filters["salesperson"] = st.sidebar.selectbox(
        "👨‍💼 المندوب",
        salespersons
    )

    # ==========================================
    # Customer
    # ==========================================

    filters["customer"] = st.sidebar.text_input(
        "👤 العميل"
    )

    return filters