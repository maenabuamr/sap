import streamlit as st
import pandas as pd
import os
import io

# إعداد الصفحة
st.set_page_config(layout="wide", page_title="تقرير أداء المندوبين")

# دالة تحميل البيانات مع تحسينات الاستقرار
@st.cache_data
def load_sales_data():
    # التأكد من المسار، الملف موجود في المجلد الرئيسي حسب المرفقات
    file_path = "sales_customer.csv"
    
    if not os.path.exists(file_path):
        return None
    try:
        # قراءة الملف مع التأكد من معالجة الأعمدة والترميز
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        # تنظيف عمود المندوب والارقام
        if 'Salesperson' in df.columns:
            df['Salesperson'] = df['Salesperson'].astype(str).str.strip()
        return df
    except Exception:
        return None

# تحميل البيانات
df = load_sales_data()

st.title("👤 تقرير أداء المندوبين والمبيعات")

if df is None:
    st.error("تعذر العثور على ملف 'sales_customer.csv' في المجلد الرئيسي.")
elif df.empty:
    st.warning("الملف فارغ ولا يحتوي على بيانات.")
else:
    st.sidebar.header("تصفية البيانات")
    
    # اختيار المندوب (Salesperson) مع معالجة القيم المفقودة
    if 'Salesperson' in df.columns:
        reps = sorted(df['Salesperson'].dropna().unique().tolist())
        selected_reps = st.sidebar.multiselect("اختر المندوب:", reps, default=reps)
        filtered_df = df[df['Salesperson'].isin(selected_reps)]
    else:
        filtered_df = df
        st.sidebar.warning("لم يتم العثور على عمود 'Salesperson'.")

    # عرض مؤشرات الأداء
    st.subheader("ملخص مؤشرات الأداء")
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي العمليات", len(filtered_df))
    
    # معالجة الأرقام قبل الجمع لتجنب الأخطاء
    if 'Amt' in filtered_df.columns:
        filtered_df['Amt'] = pd.to_numeric(filtered_df['Amt'], errors='coerce').fillna(0)
    if 'QYT' in filtered_df.columns:
        filtered_df['QYT'] = pd.to_numeric(filtered_df['QYT'], errors='coerce').fillna(0)
    
    total_amt = filtered_df['Amt'].sum() if 'Amt' in filtered_df.columns else 0
    total_qyt = filtered_df['QYT'].sum() if 'QYT' in filtered_df.columns else 0
    
    col2.metric("إجمالي قيمة المبيعات", f"{total_amt:,.2f}")
    col3.metric("إجمالي الكميات المباعة", f"{total_qyt:,.2f}")
    
    # عرض البيانات التفصيلية
    st.subheader("سجل المبيعات التفصيلي")
    st.dataframe(filtered_df, use_container_width=True)

    # التصدير إلى Excel
    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False)
        st.download_button("📥 تحميل تقرير الأداء (Excel)", buffer.getvalue(), "sales_customer_performance.xlsx", "application/vnd.ms-excel")
    except Exception as e:
        st.error(f"خطأ أثناء تصدير الملف: {e}")