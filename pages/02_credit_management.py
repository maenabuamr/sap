import streamlit as st

from data_loader import (
    load_aging,
    load_sales,
    load_checks,
)

from engine.mapper import map_aging_columns
from engine.credit_risk import classify_risk
from engine.credit_kpi import calculate_kpis
from engine.credit_alerts import generate_alerts
from engine.credit_collection import build_collection_list
from engine.customer360 import build_customer360
from engine.data_model import ERPDataModel

from components.global_filters import render_global_filters
from components.credit_kpi import render_credit_kpis
from components.credit_charts import render_credit_charts
from components.collection_priority import render_collection_priority
from components.credit_table import render_credit_table
from components.customer_card import render_customer_card


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Credit Management",
    page_icon="💰",
    layout="wide",
)

st.title("💰 Credit Management")


# ==========================================================
# LOAD DATA
# ==========================================================

aging = load_aging()
sales = load_sales()
checks = load_checks()

aging = map_aging_columns(aging)
aging = classify_risk(aging)


# ==========================================================
# GLOBAL FILTERS
# ==========================================================

filters = render_global_filters(
    aging,
    sales,
)


# ==========================================================
# DATA MODEL
# ==========================================================

model = ERPDataModel(
    aging,
    sales,
    checks,
)

model.apply_filters(

    company=filters["company"],

    year=filters["year"],

    month=filters["month"],

    salesperson=filters["salesperson"],

    customer=filters["customer"],

)


# ==========================================================
# CUSTOMER 360
# ==========================================================

customer360 = build_customer360(

    model.aging,

    model.sales,

    model.checks,

)


filtered = customer360.copy()


# ==========================================================
# CREDIT ENGINE
# ==========================================================

collection = build_collection_list(filtered)

kpis = calculate_kpis(filtered)

alerts = generate_alerts(filtered)


# ==========================================================
# TABS
# ==========================================================

tab1, tab2, tab3, tab4 = st.tabs(

    [

        "📊 Dashboard",

        "📞 Collection Center",

        "👥 Customers",

        "👤 Customer 360",

    ]

)


# ==========================================================
# DASHBOARD
# ==========================================================

with tab1:

    render_credit_kpis(kpis)

    st.divider()

    if alerts:

        st.subheader("🚨 التنبيهات")

        for alert in alerts:

            st.warning(alert)

    st.divider()

    render_credit_charts(filtered)


# ==========================================================
# COLLECTION CENTER
# ==========================================================

with tab2:

    render_collection_priority(collection)


# ==========================================================
# CUSTOMERS
# ==========================================================

with tab3:

    render_credit_table(filtered)


# ==========================================================
# CUSTOMER 360
# ==========================================================

with tab4:

    render_customer_card(filtered)


# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.caption("ERP AI Analytics | Credit Management V3.0")