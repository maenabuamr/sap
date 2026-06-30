import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(layout="wide", page_title="كشف الحساب الموحد")

@st.cache_data
def load_data():
    file_path = os.path.join("data", "combined_statements.csv")
    if not os.path.exists(file_path):
        return None, f"الملف غير موجود في: {file_path}"
    
    try:
        # قراءة الملف مع الكشف التلقائي عن الفاصل
        df = pd.read_csv(file_path, encoding='utf-8-sig', sep=None, engine='python')
        return df, None
    except Exception as e:
        return None, str(e)

df, error = load_data()

if error:
    st.error(f"خطأ في تحميل الملف: {error}")
    st.info("تأكد أن الملف موجود في مجلد 'data' على GitHub وأن اسمه `combined_statements.csv`")
elif not df.empty:
    st.title("📊 كشف الحساب الموحد")

    # تنظيف أسماء الأعمدة من المسافات
    df.columns = df.columns.str.strip()

    # تحويل الأعمدة الرقمية وتنظيفها من الفواصل
    cols_to_numeric = ['DebitAmount', 'CreditAmount', 'RunningBalance']
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    # 2. الفلاتر
    col1, col2 = st.columns(2)
    with col1:
        if 'Company' in df.columns:
            companies = sorted(df['Company'].dropna().unique().tolist())
            selected_companies = st.multiselect("اختر الشركة:", companies, default=companies)
            temp_df = df[df['Company'].isin(selected_companies)]
        else:
            st.error("عمود 'Company' غير موجود في الملف!")
            temp_df = df

    with col2:
        if 'CustomerName' in temp_df.columns:
            customers = ["الكل"] + sorted(temp_df['CustomerName'].dropna().unique().tolist())
            selected_customer = st.selectbox("اختر العميل:", customers)
        else:
            selected_customer = "الكل"

    # 3. المنطق
    if selected_customer != "الكل":
        final_df = temp_df[temp_df['CustomerName'] == selected_customer]
    else:
        final_df = temp_df

    # 4. عرض
    st.subheader("ملخص الحساب")
    m1, m2, m3 = st.columns(3)
    m1.metric("إجمالي المدين", f"{final_df['DebitAmount'].sum():,.2f}")
    m2.metric("إجمالي الدائن", f"{final_df['CreditAmount'].sum():,.2f}")
    last_balance = final_df['RunningBalance'].iloc[-1] if not final_df.empty else 0
    m3.metric("الرصيد المتبقي", f"{last_balance:,.2f}")

    # 5. التصدير إلى Excel
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False, sheet_name='Statement')
        st.download_button("📥 تحميل كشف الحساب (Excel)", buffer.getvalue(), "account_statement.xlsx", "application/vnd.ms-excel")
    except ImportError:
        st.warning("مكتبة 'xlsxwriter' غير مثبتة. يرجى إضافتها في ملف requirements.txt لتفعيل التصدير.")

    st.dataframe(final_df, use_container_width=True)

else:
    st.warning("الملف فارغ أو تعذر قراءته.")