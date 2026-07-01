import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="تقرير أداء المندوبين")

@st.cache_data
def load_sales_data():
    # تصحيح المسار ليكون داخل مجلد data
    file_path = os.path.join("data", "sales_customer.csv")
    
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return None

df = load_sales_data()

st.title("👤 تقرير أداء المندوبين والمبيعات")

if df is None:
    st.error("تعذر العثور على ملف 'data/sales_customer.csv'. تأكد من وجود الملف داخل مجلد 'data'.")
elif df.empty:
    st.warning("الملف فارغ.")
else:
    # الفلترة حسب المندوب
    if 'Salesperson' in df.columns:
        reps = sorted(df['Salesperson'].dropna().unique().tolist())
        selected_reps = st.sidebar.multiselect("اختر المندوب:", reps, default=reps)
        filtered_df = df[df['Salesperson'].isin(selected_reps)]
    else:
        filtered_df = df

    # الإحصائيات
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي العمليات", len(filtered_df))
    
    # تحويل القيم لأرقام لضمان حسابها
    amt = pd.to_numeric(filtered_df['Amt'], errors='coerce').fillna(0)
    qyt = pd.to_numeric(filtered_df['QYT'], errors='coerce').fillna(0)
    
    col2.metric("إجمالي قيمة المبيعات", f"{amt.sum():,.2f}")
    col3.metric("إجمالي الكميات", f"{qyt.sum():,.2f}")
    
    st.dataframe(filtered_df, use_container_width=True)