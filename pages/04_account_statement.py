import streamlit as st
import pandas as pd
import os
import io
from utils import display_header
from data_loader import load_aging, load_checks

# 1. الترويسة الثابتة
display_header()

@st.cache_data
def load_main_data():
    file_path = os.path.join('/workspaces/sap/data', "combined_statements.csv")
    if not os.path.exists(file_path):
        return None, f"الملف غير موجود في: {file_path}"
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig', sep=None, engine='python')
        df.columns = df.columns.str.strip()
        for col in ['DebitAmount', 'CreditAmount']:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        if 'ReferenceNumber' in df.columns:
            df['ReferenceNumber'] = df['ReferenceNumber'].astype(str).str.strip()
        df['PostingDate'] = pd.to_numeric(df['PostingDate'], errors='coerce')
        return df, None
    except Exception as e:
        return None, str(e)

df, error = load_main_data()

if error:
    st.error(f"خطأ في تحميل الملف: {error}")
    st.stop()

st.title("📊 كشف الحساب الموحد (معدل الأرصدة)")

# الفلاتر
col1, col2 = st.columns(2)
with col1:
    companies = sorted(df['Company'].dropna().unique().tolist())
    selected_companies = st.multiselect("اختر الشركة:", companies, default=companies)

with col2:
    temp_df = df[df['Company'].isin(selected_companies)]
    customers = sorted(temp_df['CustomerName'].dropna().unique().tolist())
    selected_customer = st.selectbox("اختر العميل:", customers)

# المنطق المدمج
ref_numbers = df[df['CustomerName'] == selected_customer]['ReferenceNumber'].unique()
final_df = df[
    (df['ReferenceNumber'].isin(ref_numbers)) &
    (df['Company'].isin(selected_companies))
].copy()
final_df = final_df.sort_values(by='PostingDate')
final_df['RunningBalance'] = (final_df['DebitAmount'] - final_df['CreditAmount']).cumsum()

# المؤشرات
m1, m2, m3 = st.columns(3)
m1.metric("إجمالي المدين", f"{final_df['DebitAmount'].sum():,.2f}")
m2.metric("إجمالي الدائن", f"{final_df['CreditAmount'].sum():,.2f}")
last_balance = final_df['RunningBalance'].iloc[-1] if not final_df.empty else 0
m3.metric("الرصيد المتبقي", f"{last_balance:,.2f}")

st.dataframe(final_df, use_container_width=True)

# الإضافات
aging_df = None
checks_df = None
if not final_df.empty:
    st.divider()
    st.subheader(f"بيانات إضافية للعميل: {selected_customer}")
    tab1, tab2 = st.tabs(["🕒 أعمار الذمم", "🏦 الشيكات"])
    with tab1:
        aging_df = load_aging()
        if aging_df is not None:
            col_name = 'اسم العميل' if 'اسم العميل' in aging_df.columns else 'CustomerName'
            st.dataframe(aging_df[aging_df[col_name] == selected_customer], use_container_width=True)
    with tab2:
        checks_df = load_checks()
        if checks_df is not None:
            col_name = 'اسم العميل' if 'اسم العميل' in checks_df.columns else 'CustomerName'
            st.dataframe(checks_df[checks_df[col_name] == selected_customer], use_container_width=True)

# ====== التصدير ======
st.divider()
st.subheader("📥 تحميل التقرير")

col1, col2 = st.columns(2)

# Excel
with col1:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False, sheet_name='Statement')
    st.download_button(
        "📊 تحميل Excel",
        buffer.getvalue(),
        "account_statement.xlsx",
        "application/vnd.ms-excel",
        use_container_width=True
    )

# PDF
with col2:
    if st.button("📄 إنشاء وتحميل PDF", use_container_width=True):
        try:
            from pdf_generator import generate_account_statement_pdf
            aging_for_pdf = None
            checks_for_pdf = None
            if aging_df is not None:
                col_name = 'اسم العميل' if 'اسم العميل' in aging_df.columns else 'CustomerName'
                aging_for_pdf = aging_df[aging_df[col_name] == selected_customer]
            if checks_df is not None:
                col_name = 'اسم العميل' if 'اسم العميل' in checks_df.columns else 'CustomerName'
                checks_for_pdf = checks_df[checks_df[col_name] == selected_customer]
            pdf_buffer = generate_account_statement_pdf(
                customer_name=selected_customer,
                company_name=", ".join(selected_companies) if selected_companies else "All",
                ref_number=str(ref_numbers[0]) if len(ref_numbers) > 0 else "",
                statement_df=final_df,
                aging_data=aging_for_pdf,
                checks_data=checks_for_pdf
            )
            st.download_button(
                "📥 حمّل PDF",
                pdf_buffer.getvalue(),
                f"statement_{str(selected_customer)[:20]}.pdf",
                "application/pdf",
                key="dl_pdf_final"
            )
        except Exception as e:
            st.error(f"❌ خطأ: {e}")
