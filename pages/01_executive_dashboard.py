import streamlit as st

from data_loader import (
    load_aging,
    load_sales,
    load_checks,
)

from engine.mapper import map_aging_columns
from engine.credit_risk import classify_risk
from engine.customer360 import build_customer360

from core.metrics import Metrics


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(

    page_title="Executive Dashboard",

    page_icon="📊",

    layout="wide",

)

st.title("📊 Executive Dashboard")


# ==========================================================
# LOAD DATA
# ==========================================================

aging = load_aging()
sales = load_sales()
checks = load_checks()

aging = map_aging_columns(aging)
aging = classify_risk(aging)

customer360 = build_customer360(
    aging,
    sales,
    checks,
)

metrics = Metrics(customer360)

# ==========================================================
# KPIs
# ==========================================================

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(

        "💰 إجمالي المبيعات",

        f"{metrics.total_sales():,.3f}"

    )

with c2:

    st.metric(

        "💳 الذمم الحالية",

        f"{metrics.current_balance():,.3f}"

    )

with c3:

    st.metric(

        "🚨 أكثر من 90 يوم",

        f"{metrics.overdue_90():,.3f}"

    )

with c4:

    st.metric(

        "🏦 قيمة الشيكات",

        f"{metrics.checks_value():,.3f}"

    )

st.divider()

# ==========================================================
# SECOND KPIs
# ==========================================================

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(

        "👥 العملاء",

        metrics.customers()

    )

with c2:

    st.metric(

        "📄 الفواتير",

        metrics.invoices()

    )

with c3:

    st.metric(

        "📦 الكميات",

        f"{metrics.quantity():,.2f}"

    )

with c4:

    st.metric(

        "🔴 العملاء عالي الخطورة",

        metrics.high_risk()

    )

st.divider()

# ==========================================================
# TOP RISK
# ==========================================================

st.subheader("🔴 أعلى العملاء خطورة")

risk = metrics.top_risk(10)

st.dataframe(

    risk[
        [

            "CustomerName",

            "CurrentBalance",

            "DueBalance",

            "Age_90_Plus",

            "Risk",

        ]

    ],

    use_container_width=True,

    hide_index=True,

)

st.divider()

# ==========================================================
# TOP SALES
# ==========================================================

st.subheader("🏆 أعلى العملاء مبيعاً")

sales = metrics.top_customers(10)

st.dataframe(

    sales[
        [

            "CustomerName",

            "TotalSales",

            "InvoiceCount",

            "TotalQty",

        ]

    ],

    use_container_width=True,

    hide_index=True,

)

st.divider()

st.caption("ERP AI Analytics | Executive Dashboard V1")