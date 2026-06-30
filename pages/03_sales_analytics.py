import streamlit as st
import pandas as pd
from data_loader import load_sales
from core.sales_metrics import SalesMetrics
from components.sales_charts import render_sales_charts

# ==========================================================
# إعدادات الصفحة
# ==========================================================
st.set_page_config(
    page_title="Sales Analytics",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Sales Analytics")

# ==========================================================
# تحميل البيانات وتنظيفها وتجهيز معرّف الكيانات الموحد
# ==========================================================
sales_raw = load_sales()

# تنظيف البيانات لضمان عدم حدوث أخطاء أثناء التجميع أو الفلترة
sales_raw["CustomerName"] = sales_raw["CustomerName"].fillna("عميل غير معروف")
sales_raw["ReferenceNumber"] = sales_raw["ReferenceNumber"].astype(str).str.strip().fillna("-")

# دالة ذكية: تعزل الـ (-) بناءً على اسم العميل وتدمج الباقي بناءً على الرقم المرجعي
def create_calc_group_id(row):
    val = str(row["ReferenceNumber"]).strip()
    if val == "" or val == "-":
        return f"UNLINKED_{row['CustomerName']}"
    return val

# تطبيق المعرّف الموحد على البيانات الخام
sales_raw["Calc_Group_ID"] = sales_raw.apply(create_calc_group_id, axis=1)

# ==========================================================
# الفلاتر - القائمة الجانبية (Sidebar Filters)
# ==========================================================
st.sidebar.header("🔍 Filters")

sales_filtered = sales_raw.copy()

# 1. فلتر السنة (قائمة منسدلة)
years = ["الكل"] + sorted(sales_filtered["Year"].unique().tolist())
year = st.sidebar.selectbox("السنة", years)
if year != "الكل":
    sales_filtered = sales_filtered[sales_filtered["Year"] == year]

# 2. فلتر الشهر (قائمة منسدلة)
months = ["الكل"] + sorted(sales_filtered["Month"].unique().tolist())
month = st.sidebar.selectbox("الشهر", months)
if month != "الكل":
    sales_filtered = sales_filtered[sales_filtered["Month"] == month]

# 3. فلتر المندوب (متعدد الاختيارات Multi-select)
salespersons_list = sorted(sales_filtered["Salesperson"].dropna().unique().tolist())
selected_sps = st.sidebar.multiselect("المندوبين", salespersons_list, default=[])
if selected_sps:
    sales_filtered = sales_filtered[sales_filtered["Salesperson"].isin(selected_sps)]

# 4. فلتر مجموعة المواد (متعدد الاختيارات Multi-select)
item_group_col = "ItemGroup" if "ItemGroup" in sales_filtered.columns else ("Item_Group" if "Item_Group" in sales_filtered.columns else None)
if item_group_col:
    groups_list = sorted(sales_filtered[item_group_col].dropna().unique().tolist())
    selected_groups = st.sidebar.multiselect("مجموعات المواد", groups_list, default=[])
    if selected_groups:
        sales_filtered = sales_filtered[sales_filtered[item_group_col].isin(selected_groups)]

# 5. فلتر اسم المادة (متعدد الاختيارات Multi-select)
item_desc_col = "ItemDescription"
if item_desc_col in sales_filtered.columns:
    items_list = sorted(sales_filtered[item_desc_col].dropna().unique().tolist())
    selected_items = st.sidebar.multiselect("أسماء المواد", items_list, default=[])
    if selected_items:
        sales_filtered = sales_filtered[sales_filtered[item_desc_col].isin(selected_items)]

# ==========================================================
# تهيئة كلاس المقاييس بناءً على البيانات المفلترة والمصححة
# ==========================================================
metrics = SalesMetrics(sales_filtered)

# ==========================================================
# المؤشرات الرئيسية المحدثة (KPIs)
# ==========================================================
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
    # معالجة قراءة الفواتير سواء كانت رقماً أو قائمة حركات
    invoices_count = 0
    if hasattr(metrics, 'invoices'):
        try:
            invoices_count = int(metrics.invoices())
        except Exception:
            invoices_count = len(metrics.invoices())
    st.metric("📄 Invoices", f"{invoices_count:,}")

with c4:
    # التعديل الجوهري: حساب عدد الكيانات الحقيقية بدقة بعد الدمج وعزل الشرطة (-)
    true_customers_count = sales_filtered["Calc_Group_ID"].nunique()
    st.metric("👥 Customers", f"{true_customers_count:,}")

with c5:
    st.metric(
        "🧾 Avg Invoice",
        f"{metrics.avg_invoice():,.3f}"
    )

st.divider()

# ==========================================================
# الرسوم البيانية والجداول (Charts & Dataframes)
# ==========================================================
# عرض الرسوم البيانية لتتأثر بالفلاتر الجديدة تلقائياً
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