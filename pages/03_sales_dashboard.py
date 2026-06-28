import streamlit as st

from data_loader import load_sales

from core.sales_metrics import SalesMetrics

st.set_page_config(
    page_title="Sales Analytics",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Sales Analytics")

# ==========================================================
# Load Data
# ==========================================================

sales = load_sales()

metrics = SalesMetrics(sales)

# ==========================================================
# Filters
# ==========================================================

st.sidebar.header("🔍 Filters")

years = ["الكل"] + sorted(sales["Year"].unique().tolist())

year = st.sidebar.selectbox(
    "السنة",
    years
)

if year != "الكل":

    sales = sales[sales["Year"] == year]

months = ["الكل"] + sorted(sales["Month"].unique().tolist())

month = st.sidebar.selectbox(
    "الشهر",
    months
)

if month != "الكل":

    sales = sales[sales["Month"] == month]

salespersons = ["الكل"] + sorted(sales["Salesperson"].unique().tolist())

sp = st.sidebar.selectbox(
    "المندوب",
    salespersons
)

if sp != "الكل":

    sales = sales[sales["Salesperson"] == sp]

metrics = SalesMetrics(sales)

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
        "📄 عدد الفواتير",
        metrics.invoices()
    )

with c3:

    st.metric(
        "📦 الكمية",
        f"{metrics.quantity():,.2f}"
    )

with c4:

    st.metric(
        "👥 العملاء",
        metrics.customers()
    )

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "👨‍💼 المندوبين",
        metrics.salespersons()
    )

with c2:

    st.metric(
        "📦 الأصناف",
        metrics.items()
    )

with c3:

    st.metric(
        "🏷️ المجموعات",
        metrics.item_groups()
    )

with c4:

    st.metric(
        "💵 متوسط الفاتورة",
        f"{metrics.average_invoice():,.3f}"
    )

st.divider()

# ==========================================================
# Monthly Sales
# ==========================================================

st.subheader("📈 المبيعات الشهرية")

monthly = metrics.monthly_sales()

st.bar_chart(
    monthly.set_index("Month")["Sales"],
    use_container_width=True
)

st.divider()

# ==========================================================
# Top Customers
# ==========================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader("🏆 أفضل العملاء")

    st.dataframe(

        metrics.top_customers(),

        use_container_width=True,

        hide_index=True

    )

with col2:

    st.subheader("📦 أفضل الأصناف")

    st.dataframe(

        metrics.top_items(),

        use_container_width=True,

        hide_index=True

    )

st.divider()

# ==========================================================
# Item Groups
# ==========================================================

st.subheader("🏷️ المبيعات حسب مجموعة الصنف")

groups = metrics.top_groups()

st.bar_chart(

    groups.set_index("ItemGroup")["Sales"],

    use_container_width=True

)

st.divider()

st.caption("ERP AI Analytics | Sales Dashboard V1")