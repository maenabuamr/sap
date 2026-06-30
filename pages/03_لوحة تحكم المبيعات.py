import streamlit as st
import pandas as pd
from data_loader import load_sales
from core.sales_metrics import SalesMetrics

# إعدادات الصفحة
st.set_page_config(
    page_title="Sales Analytics",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Sales Analytics")

# ==========================================================
# Load Data
# ==========================================================
sales_raw = load_sales()

# ==========================================================
# Filters (Sidebar)
# ==========================================================
st.sidebar.header("🔍 Filters")

# 1. فلتر السنة
years = ["الكل"] + sorted(sales_raw["Year"].unique().tolist())
year = st.sidebar.selectbox("السنة", years)

sales_filtered = sales_raw.copy()
if year != "الكل":
    sales_filtered = sales_filtered[sales_filtered["Year"] == year]

# 2. فلتر الشهر
months = ["الكل"] + sorted(sales_filtered["Month"].unique().tolist())
month = st.sidebar.selectbox("الشهر", months)

if month != "الكل":
    sales_filtered = sales_filtered[sales_filtered["Month"] == month]

# 3. فلتر المندوب
salespersons_list = ["الكل"] + sorted(sales_filtered["Salesperson"].unique().tolist())
sp = st.sidebar.selectbox("المندوب", salespersons_list)

if sp != "الكل":
    sales_filtered = sales_filtered[sales_filtered["Salesperson"] == sp]

# 4. فلتر مجموعة المواد (ItemGroup)
item_group_col = "ItemGroup" if "ItemGroup" in sales_filtered.columns else ("Item_Group" if "Item_Group" in sales_filtered.columns else None)

if item_group_col:
    groups_list = ["الكل"] + sorted(sales_filtered[item_group_col].dropna().unique().tolist())
    selected_group = st.sidebar.selectbox("مجموعة المواد", groups_list)
    
    if selected_group != "الكل":
        sales_filtered = sales_filtered[sales_filtered[item_group_col] == selected_group]

# 5. فلتر اسم المادة (ItemDescription)
item_desc_col = "ItemDescription"

if item_desc_col in sales_filtered.columns:
    items_list = ["الكل"] + sorted(sales_filtered[item_desc_col].dropna().unique().tolist())
    selected_item = st.sidebar.selectbox("اسم المادة", items_list)
    
    if selected_item != "الكل":
        sales_filtered = sales_filtered[sales_filtered[item_desc_col] == selected_item]

# 6. 🆕 فلتر اسم العميل الجديد (CustomerName)
customer_col = "CustomerName"

if customer_col in sales_filtered.columns:
    # يعرض العملاء المتاحين بناءً على المادة والمندوب والفترات المختارة سابقاً
    customers_list = ["الكل"] + sorted(sales_filtered[customer_col].dropna().unique().tolist())
    selected_customer = st.sidebar.selectbox("اسم العميل", customers_list)
    
    if selected_customer != "الكل":
        sales_filtered = sales_filtered[sales_filtered[customer_col] == selected_customer]


# تهيئة كلاس المقاييس بناءً على البيانات المفلترة بالكامل
metrics = SalesMetrics(sales_filtered)

# ==========================================================
# KPIs - السطر الأول
# ==========================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    total_sales_val = metrics.total_sales() if hasattr(metrics, 'total_sales') else 0.0
    st.metric("💰 إجمالي المبيعات", f"{total_sales_val:,.3f}")

with c2:
    invoices_count = 0
    if hasattr(metrics, 'invoices'):
        try:
            invoices_count = int(metrics.invoices())
        except Exception:
            invoices_count = len(metrics.invoices())
    st.metric("📄 عدد الفواتير", f"{invoices_count:,}")

with c3:
    qty_val = metrics.quantity() if hasattr(metrics, 'quantity') else 0.0
    st.metric("📦 الكمية", f"{qty_val:,.2f}")

with c4:
    customers_count = 0
    if hasattr(metrics, 'customers'):
        try:
            customers_count = int(metrics.customers())
        except Exception:
            customers_count = len(metrics.customers())
    else:
        customers_count = sales_filtered[customer_col].nunique() if customer_col in sales_filtered.columns else 0
    st.metric("👥 العملاء", f"{customers_count:,}")

# ==========================================================
# KPIs - السطر الثاني
# ==========================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    sp_count = 0
    if hasattr(metrics, 'salespersons'):
        try:
            sp_count = int(metrics.salespersons())
        except Exception:
            sp_count = len(metrics.salespersons())
    st.metric("👨‍💼 المندوبين", f"{sp_count:,}")

with c2:
    items_count = 0
    if hasattr(metrics, 'items'):
        try:
            items_count = int(metrics.items())
        except Exception:
            items_count = len(metrics.items())
    else:
        items_count = sales_filtered[item_desc_col].nunique() if item_desc_col in sales_filtered.columns else 0
        
    st.metric("📦 الأصناف", f"{items_count:,}")

with c3:
    groups_count = 0
    if hasattr(metrics, 'item_groups'):
        try:
            groups_count = int(metrics.item_groups())
        except Exception:
            groups_count = len(metrics.item_groups())
    else:
        groups_count = sales_filtered[item_group_col].nunique() if item_group_col else 0

    st.metric("🏷️ المجموعات", f"{groups_count:,}")

with c4:
    avg_invoice_val = metrics.average_invoice() if hasattr(metrics, 'average_invoice') else 0.0
    st.metric("💵 متوسط الفاتورة", f"{avg_invoice_val:,.3f}")

st.divider()

# ==========================================================
# Monthly Sales
# ==========================================================
st.subheader("📈 المبيعات الشهرية")
if hasattr(metrics, 'monthly_sales'):
    monthly = metrics.monthly_sales()
    if isinstance(monthly, pd.DataFrame) and not monthly.empty:
        st.bar_chart(
            monthly.set_index("Month")["Sales"],
            use_container_width=True
        )
    else:
        st.info("لا توجد بيانات مبيعات شهرية للفلاتر المختارة.")
else:
    st.info("دالة المبيعات الشهرية غير متوفرة.")

st.divider()

# ==========================================================
# Top Customers & Items
# ==========================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 أفضل العملاء")
    if hasattr(metrics, 'top_customers'):
        st.dataframe(
            metrics.top_customers(),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("البيانات غير متوفرة.")

with col2:
    st.subheader("📦 أفضل الأصناف")
    if hasattr(metrics, 'top_items'):
        st.dataframe(
            metrics.top_items(),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("البيانات غير متوفرة.")

st.divider()

# ==========================================================
# Item Groups
# ==========================================================
st.subheader("🏷️ المبيعات حسب مجموعة الصنف")
if hasattr(metrics, 'top_groups'):
    groups = metrics.top_groups()
    if isinstance(groups, pd.DataFrame) and not groups.empty:
        st.bar_chart(
            groups.set_index("ItemGroup")["Sales"],
            use_container_width=True
        )
    else:
        st.info("لا توجد بيانات مجموعات للفلاتر المختارة.")
else:
    st.info("دالة مبيعات المجموعات غير متوفرة.")

st.divider()
st.caption("ERP AI Analytics | Sales Dashboard V1")