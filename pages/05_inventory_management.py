import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(layout="wide", page_title="إدارة المستودعات")

# تحميل البيانات من ملف inventory.csv الموجود في مجلد data
@st.cache_data
def load_inventory_data():
    file_path = os.path.join("data", "inventory.csv")
    if os.path.exists(file_path):
        # استخدام ترميز utf-8-sig للتعامل الصحيح مع اللغة العربية
        return pd.read_csv(file_path, encoding='utf-8-sig')
    else:
        st.error("ملف البيانات غير موجود في المسار: data/inventory.csv")
        return pd.DataFrame()

inv_df = load_inventory_data()

if not inv_df.empty:
    # تصفية البيانات لاستبعاد الأصناف التي رصيدها أقل من 1
    inv_df = inv_df[inv_df['الرصيد'] >= 1].copy()

    st.title("📦 إدارة المستودعات والمخزون")

    # 1. إحصائيات سريعة
    st.subheader("نظرة عامة على المخزون")
    m1, m2, m3 = st.columns(3)
    m1.metric("إجمالي الأصناف", int(inv_df['الصنف'].nunique()))
    m2.metric("إجمالي قيمة المخزون", f"{inv_df['قيمة المخزون'].sum():,.2f} JOD")
    m3.metric("عدد المستودعات", int(inv_df['اسم المستودع'].nunique()))

    # 2. الفلاتر المحدثة
    st.divider()
    c1, c2 = st.columns(2)
    
    with c1:
        warehouses = sorted(inv_df['اسم المستودع'].unique().tolist())
        selected_wh = st.multiselect("تصفية حسب المستودع:", options=warehouses, default=warehouses)
    
    with c2:
        # الفلتر يعتمد على الوصف (اسم المادة)
        descriptions = sorted(inv_df['الوصف'].unique().astype(str).tolist())
        selected_desc = st.multiselect("تصفية حسب اسم المادة:", options=descriptions, default=descriptions)

    # تطبيق الفلترة
    filtered_df = inv_df[
        (inv_df['اسم المستودع'].isin(selected_wh)) & 
        (inv_df['الوصف'].astype(str).isin(selected_desc))
    ]

    # 3. عرض ملخص القيمة حسب المستودع
    st.subheader("ملخص القيمة حسب المستودع")
    wh_summary = filtered_df.groupby('اسم المستودع')['قيمة المخزون'].sum().reset_index()
    st.dataframe(wh_summary, use_container_width=True)

    # 4. تفاصيل الأصناف (تم إضافة الأعمدة الجديدة)
    st.subheader("تفاصيل الأصناف")
    st.dataframe(filtered_df[['الشركة', 'الصنف', 'الوصف', 'اسم المستودع', 'الرصيد', 'قيمة المخزون', 'كلفة الوحدة', 'سعر البيع', 'الربح', 'هامش الربح']], use_container_width=True)

    # 5. التصدير إلى Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Inventory')
    
    st.download_button(
        label="📥 تحميل تقرير المستودع (Excel)",
        data=buffer.getvalue(),
        file_name="inventory_report.xlsx",
        mime="application/vnd.ms-excel"
    )

else:
    st.warning("يرجى التأكد من أن ملف البيانات يحتوي على المعلومات المطلوبة.")