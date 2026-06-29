import streamlit as st

from data_loader import load_sales

from core.sales_metrics import SalesMetrics

from components.sales_charts import render_sales_charts


st.set_page_config(
    page_title="Sales Analytics",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Sales Analytics")

sales = load_sales()

metrics = SalesMetrics(sales)

# =====================================================
# KPIs
# =====================================================

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric(
        "💰 Total Sales",
        f"{metrics.total_sales():,.3f}"
    )

with c2:
    st.metric(
        "📦 Qty",
        f"{metrics.total_qty():,.2f}"
    )

with c3:
    st.metric(
        "📄 Invoices",
        metrics.invoices()
    )

with c4:
    st.metric(
        "👥 Customers",
        metrics.customers()
    )

with c5:
    st.metric(
        "🧾 Avg Invoice",
        f"{metrics.avg_invoice():,.3f}"
    )

st.divider()

render_sales_charts(metrics)

st.divider()

left, right = st.columns(2)

with left:

    st.subheader("🏆 Top Customers")

    st.dataframe(
        metrics.top_customers(),
        use_container_width=True,
        hide_index=True
    )

with right:

    st.subheader("📦 Top Items")

    st.dataframe(
        metrics.top_items(),
        use_container_width=True,
        hide_index=True
    )