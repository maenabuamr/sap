import streamlit as st
import pandas as pd

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
# LOAD & CLEAN DATA
# ==========================================================
# الحفاظ على ثبات البيانات الخام في الـ Session لمنع أي توليد عشوائي أثناء التنقل
if 'raw_aging' not in st.session_state:
    st.session_state.raw_aging = load_aging()
    st.session_state.raw_sales = load_sales()
    st.session_state.raw_checks = load_checks()

aging = st.session_state.raw_aging.copy()
sales = st.session_state.raw_sales.copy()
checks = st.session_state.raw_checks.copy()

# دالة المعرف الذكي: تعزل الـ (-) وتوحد الحسابات بناءً على الرقم المرجعي
def apply_smart_grouping(df, customer_name_col="CustomerName"):
    if "ReferenceNumber" in df.columns:
        df["ReferenceNumber"] = df["ReferenceNumber"].astype(str).str.strip().fillna("-")
        df["CustomerName"] = df[customer_name_col].fillna("غير معروف")
        df["Calc_Group_ID"] = df.apply(
            lambda r: f"UNLINKED_{r['CustomerName']}" if r["ReferenceNumber"] in ["", "-"] else str(r["ReferenceNumber"]),
            axis=1
        )
    return df

# تطبيق منطق فصل الـ (-) المعتمد على الكيان قبل التمرير للموديل لتوحيد المفاتيح
aging = apply_smart_grouping(aging)
sales = apply_smart_grouping(sales)
checks = apply_smart_grouping(checks, customer_name_col="CardName" if "CardName" in checks.columns else "CustomerName")

aging = map_aging_columns(aging)
aging = classify_risk(aging)


# ==========================================================
# 🌟 التعديل الجوهري: استثناء الكيانات ذات المبالغ الأقل من 1 صحيح
# ==========================================================
# فحص أعمدة الأرصدة المتوفرة (بالعربي أو الإنجليزي) وتصفيتها لحذف الفروقات والكسور الصفرية
balance_col = "CurrentBalance" if "CurrentBalance" in aging.columns else ("الرصيد الحالي" if "الرصيد الحالي" in aging.columns else None)
due_col = "DueBalance" if "DueBalance" in aging.columns else ("المستحق" if "المستحق" in aging.columns else ("Overdue" if "Overdue" in aging.columns else None))

if balance_col:
    # استبعاد أي حساب قيمته المطلقة بين -1 و +1 دينار لتطهير لوحة التحكم من الحسابات المقفلة دفترياً
    aging = aging[aging[balance_col].abs() >= 1.0].copy()
elif due_col:
    aging = aging[aging[due_col].abs() >= 1.0].copy()


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

# تطبيق الفلاتر المختارة من الـ Sidebar مباشرة على الموديل
model.apply_filters(
    company=filters["company"],
    year=filters["year"],
    month=filters["month"],
    salesperson=filters["salesperson"],
    customer=filters["customer"],
)


# ==========================================================
# CREDIT ENGINE (توحيد المنبع لمنع تضارب أرقام المندوبين)
# ==========================================================
# بناء السجل الشامل للأعمدة المفلترة الحالية داخل الموديل مباشرة
customer360 = build_customer360(
    model.aging,
    model.sales,
    model.checks,
)

# هذا المتغير "filtered" هو المرجع النهائي والوحيد لكافة التبويبات بالأسفل
filtered = customer360.copy()

# اشتقاق التحصيل والـ KPIs والتنبيهات من نفس المتغير تماماً لضمان التطابق الحسابي
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
# 1. DASHBOARD
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
# 2. COLLECTION CENTER (تبويب التحصيل)
# ==========================================================
with tab2:
    st.subheader("📋 قائمة أولويات المتابعة والتحصيل الفوري")
    # نمرر القائمة المحدثة المشتقة مباشرة لتعرض نفس أعداد المندوبين
    render_collection_priority(collection)


# ==========================================================
# 3. CUSTOMERS (تبويب جدول العملاء)
# ==========================================================
with tab3:
    st.subheader("👥 السجل الائتماني الموحد لكيانات العملاء")
    # التمرير المباشر لجدول filtered الموحد ليتطابق مع الفلتر الجانبي 100%
    render_credit_table(filtered)


# ==========================================================
# 4. CUSTOMER 360
# ==========================================================
with tab4:
    st.subheader("👤 ملف العميل الشامل (Customer 360° Profile)")
    
    if not filtered.empty:
        # صندوق اختيار ديناميكي يستعرض فقط أسماء العملاء المتاحين حالياً في الفلترة
        customer_options = sorted(filtered["CustomerName"].unique().tolist())
        selected_c360_name = st.selectbox("اختر العميل لعرض ملفه الائتماني وحركاته:", customer_options)
        
        single_customer_data = filtered[filtered["CustomerName"] == selected_c360_name]
        render_customer_card(single_customer_data)
    else:
        st.info("لا توجد بيانات متاحة بناءً على الفلاتر الحالية.")


# ==========================================================
# FOOTER
# ==========================================================
st.divider()
st.caption("ERP AI Analytics | Credit Management V3.0")