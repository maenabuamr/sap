import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="كشف الحساب الموحد")

# 1. تحميل البيانات من المجلد الصحيح
@st.cache_data
def load_data():
    file_path = os.path.join("data", "combined_statements.csv")
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        st.error(f"الملف غير موجود في المسار: {file_path}")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    st.title("📊 كشف الحساب الموحد")

    # 2. الفلاتر
    col1, col2 = st.columns(2)
    
    with col1:
        # السماح باختيار شركة واحدة أو أكثر
        companies = sorted(df['Company'].unique().tolist())
        selected_companies = st.multiselect("اختر الشركة (أو الشركات):", companies, default=companies)

    # تصفية أولية حسب الشركة
    temp_df = df[df['Company'].isin(selected_companies)]

    with col2:
        # قائمة العملاء بناءً على الشركات المختارة
        customers = ["الكل"] + sorted(temp_df['CustomerName'].unique().tolist())
        selected_customer = st.selectbox("اختر العميل:", customers)

    # 3. المنطق الذكي لدمج الشركتين (استخدام الرقم المرجعي)
    if selected_customer != "الكل":
        # إيجاد الرقم المرجعي للعميل المختار لربط الشركتين
        ref_numbers = df[df['CustomerName'] == selected_customer]['ReferenceNumber'].unique()
        # عرض كل البيانات التي تخص هذا العميل (في أي شركة)
        final_df = df[df['ReferenceNumber'].isin(ref_numbers) | (df['CustomerName'] == selected_customer)]
    else:
        final_df = temp_df

    # 4. عرض الإحصائيات (Metrics)
    st.subheader("ملخص الحساب")
    m1, m2, m3 = st.columns(3)
    m1.metric("إجمالي المدين", f"{final_df['DebitAmount'].sum():,.2f}")
    m2.metric("إجمالي الدائن", f"{final_df['CreditAmount'].sum():,.2f}")
    m3.metric("الرصيد المتبقي", f"{final_df['RunningBalance'].iloc[-1] if not final_df.empty else 0:,.2f}")

    # 5. الجدول
    st.dataframe(final_df[['Company', 'CustomerName', 'PostingDate', 'Details', 'DebitAmount', 'CreditAmount', 'RunningBalance']], use_container_width=True)

else:
    st.warning("يرجى التأكد من وجود ملف البيانات في المجلد الصحيح.")