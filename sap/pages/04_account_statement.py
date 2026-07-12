import streamlit as st
import pandas as pd
import os
import io
from utils import display_header
from data_loader import load_aging, load_checks

# 1. الترويسة الثابتة
display_header()

# 2. تحميل البيانات الأساسية
@st.cache_data
def load_main_data():
    file_path = os.path.join("data", "combined_statements.csv")
    if not os.path.exists(file_path):
        return None, f"الملف غير موجود في: {file_path}"
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig', sep=None, engine='python')
        df.columns = df.columns.str.strip()
        return df, None
    except Exception as e:
        return None, str(e)

df, error = load_main_data()

if error:
    st.error(f"خطأ في تحميل الملف: {error}")
else:
    st.title("📊 كشف الحساب الموحد")

    # تنظيف الأعمدة الرقمية
    cols_to_numeric = ['DebitAmount', 'CreditAmount', 'RunningBalance']
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    # 3. الفلاتر الأساسية
    col1, col2 = st.columns(2)
    with col1:
        # تأكد من أن اسم العمود هنا يطابق ملف combined_statements.csv
        companies = sorted(df['Company'].dropna().unique().tolist())
        selected_companies = st.multiselect("اختر الشركة:", companies, default=companies)
        temp_df = df[df['Company'].isin(selected_companies)]
    
    with col2:
        customers = ["الكل"] + sorted(temp_df['CustomerName'].dropna().unique().tolist())
        selected_customer = st.selectbox("اختر العميل:", customers)

    final_df = temp_df if selected_customer == "الكل" else temp_df[temp_df['CustomerName'] == selected_customer]

    # عرض الملخص
    m1, m2, m3 = st.columns(3)
    m1.metric("إجمالي المدين", f"{final_df['DebitAmount'].sum():,.2f}")
    m2.metric("إجمالي الدائن", f"{final_df['CreditAmount'].sum():,.2f}")
    last_balance = final_df['RunningBalance'].iloc[-1] if not final_df.empty else 0
    m3.metric("الرصيد المتبقي", f"{last_balance:,.2f}")

    st.dataframe(final_df, use_container_width=True)

    # 4. قسم الإضافات
    if selected_customer != "الكل":
        st.divider()
        st.subheader(f"بيانات إضافية للعميل: {selected_customer}")
        
        tab1, tab2 = st.tabs(["🕒 أعمار الذمم", "🏦 الشيكات"])

        with tab1:
            aging_df = load_aging()
            if aging_df is not None:
                # نستخدم 'اسم العميل' كما ظهر في صورتك
                if 'اسم العميل' in aging_df.columns:
                    cust_aging = aging_df[aging_df['اسم العميل'] == selected_customer]
                    st.dataframe(cust_aging, use_container_width=True)
                else:
                    st.error(f"يجب أن يحتوي ملف الأعمار على عمود باسم 'اسم العميل'. الأعمدة الحالية: {list(aging_df.columns)}")

        with tab2:
            checks_df = load_checks()
            if checks_df is not None:
                # نستخدم 'اسم العميل' كما ظهر في صورتك
                if 'اسم العميل' in checks_df.columns:
                    cust_checks = checks_df[checks_df['اسم العميل'] == selected_customer]
                    # عرض كل شيكات العميل المختار مباشرة
                    st.dataframe(cust_checks, use_container_width=True)
                else:
                    st.error(f"يجب أن يحتوي ملف الشيكات على عمود باسم 'اسم العميل'. الأعمدة الحالية: {list(checks_df.columns)}")

    # 5. التصدير
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False, sheet_name='Statement')
    st.download_button(
        "📥 تحميل كشف الحساب (Excel)",
        buffer.getvalue(),
        "account_statement.xlsx",
        "application/vnd.ms-excel"
    )

    # PDF Section
    st.divider()
    st.subheader("📄 تحميل PDF")
    aging_for_pdf = None
    checks_for_pdf = None
    try:
        if "aging_df" in dir() and aging_df is not None:
            col_a = "اسم العميل" if "اسم العميل" in aging_df.columns else "CustomerName"
            aging_for_pdf = aging_df[aging_df[col_a] == selected_customer]
    except: pass
    try:
        if "checks_df" in dir() and checks_df is not None:
            col_c = "اسم العميل" if "اسم العميل" in checks_df.columns else "CustomerName"
            checks_for_pdf = checks_df[checks_df[col_c] == selected_customer]
    except: pass

    if st.button("📄 إنشاء PDF", key="gen_pdf"):
        try:
            from pdf_generator import generate_account_statement_pdf
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
                f"statement_{selected_customer[:20]}.pdf",
                "application/pdf",
                key="dl_pdf_btn"
            )
        except Exception as e:
            st.error(f"❌ خطأ: {e}")

st.divider()
st.subheader("📄 تحميل PDF")
aging_for_pdf = None
checks_for_pdf = None
try:
    if "aging_df" in dir() and aging_df is not None:
        col_a = "اسم العميل" if "اسم العميل" in aging_df.columns else "CustomerName"
        aging_for_pdf = aging_df[aging_df[col_a] == selected_customer]
except: pass
try:
    if "checks_df" in dir() and checks_df is not None:
        col_c = "اسم العميل" if "اسم العميل" in checks_df.columns else "CustomerName"
        checks_for_pdf = checks_df[checks_df[col_c] == selected_customer]
except: pass

if st.button("📄 إنشاء PDF", key="gen_pdf"):
    try:
        from pdf_generator import generate_account_statement_pdf
        pdf_buffer = generate_account_statement_pdf(
            customer_name=selected_customer,
            company_name=", ".join(selected_companies) if selected_companies else "All",
            ref_number=str(ref_numbers[0]) if len(ref_numbers) > 0 else "",
            statement_df=final_df,
            aging_data=aging_for_pdf,
            checks_data=checks_for_pdf
        )
        st.download_button("📥 حمّل PDF", pdf_buffer.getvalue(), f"statement.pdf", "application/pdf", key="dl_pdf")
    except Exception as e:
        st.error(f"❌ خطأ: {e}"), "account_statement.xlsx", "application/vnd.ms-excel")