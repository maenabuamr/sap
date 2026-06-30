import streamlit as st
import pandas as pd
import os
import io
from fpdf import FPDF

st.set_page_config(layout="wide", page_title="كشف الحساب الموحد")

# 1. تحميل البيانات
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
        companies = sorted(df['Company'].unique().tolist())
        selected_companies = st.multiselect("اختر الشركة:", companies, default=companies)

    temp_df = df[df['Company'].isin(selected_companies)]

    with col2:
        customers = ["الكل"] + sorted(temp_df['CustomerName'].unique().tolist())
        selected_customer = st.selectbox("اختر العميل:", customers)

    # 3. المنطق الذكي
    if selected_customer != "الكل":
        ref_numbers = df[df['CustomerName'] == selected_customer]['ReferenceNumber'].unique()
        final_df = df[df['ReferenceNumber'].isin(ref_numbers) | (df['CustomerName'] == selected_customer)]
    else:
        final_df = temp_df

    # 4. ملخص الحساب
    st.subheader("ملخص الحساب")
    m1, m2, m3 = st.columns(3)
    m1.metric("إجمالي المدين", f"{final_df['DebitAmount'].sum():,.2f}")
    m2.metric("إجمالي الدائن", f"{final_df['CreditAmount'].sum():,.2f}")
    m3.metric("الرصيد المتبقي", f"{final_df['RunningBalance'].iloc[-1] if not final_df.empty else 0:,.2f}")

    # 5. أزرار التصدير
    col_exp1, col_exp2 = st.columns([1, 6])
    
    # تصدير Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False, sheet_name='Statement')
    
    col_exp1.download_button(
        label="📥 تحميل Excel",
        data=buffer.getvalue(),
        file_name="account_statement.xlsx",
        mime="application/vnd.ms-excel"
    )

    # 6. عرض الجدول
    st.dataframe(final_df[['Company', 'CustomerName', 'PostingDate', 'Details', 'DebitAmount', 'CreditAmount', 'RunningBalance']], use_container_width=True)

else:
    st.warning("يرجى التأكد من وجود ملف البيانات في المجلد الصحيح.")