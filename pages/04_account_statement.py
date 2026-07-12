import streamlit as st
import pandas as pd
import io
from data_loader import load_checks, load_statements

st.set_page_config(layout="wide")
st.title("📊 كشف الحساب الموحد")

# تحميل البيانات
df = load_statements()
checks_df = load_checks()

if df is not None:
    # الفلاتر
    col1, col2 = st.columns(2)
    with col1:
        companies = sorted(df['Company'].dropna().unique().tolist())
        selected_companies = st.multiselect("اختر الشركة:", companies, default=companies)
    with col2:
        temp_df = df[df['Company'].isin(selected_companies)]
        customers = sorted(temp_df['CustomerName'].dropna().unique().tolist())
        selected_customer = st.selectbox("اختر العميل:", customers)

    # معالجة كشف الحساب
    final_df = df[(df['CustomerName'] == selected_customer) & (df['Company'].isin(selected_companies))].copy()
    final_df = final_df.sort_values(by='PostingDate')
    final_df['RunningBalance'] = (final_df['DebitAmount'] - final_df['CreditAmount']).cumsum()

    st.subheader(f"كشف حساب: {selected_customer}")
    st.dataframe(final_df, use_container_width=True)

    # عرض الشيكات
    st.subheader("🏦 الشيكات المستقبلية")
    if checks_df is not None and 'CustomerCode' in final_df.columns:
        cust_id = final_df['CustomerCode'].iloc[0]
        filtered_checks = checks_df[checks_df['رقم العميل'].astype(str) == str(cust_id)].copy()
        
        if not filtered_checks.empty:
            st.dataframe(filtered_checks, use_container_width=True)
        else:
            st.info("لا توجد شيكات مستقبلية لهذا العميل.")
    
    # التصدير
    if st.button("📥 تحميل التقرير (Excel)"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            final_df.to_excel(writer, sheet_name='Statement', index=False)
            if 'filtered_checks' in locals() and not filtered_checks.empty:
                filtered_checks.to_excel(writer, sheet_name='Checks', index=False)
        st.download_button("حفظ الملف الآن", buffer.getvalue(), "statement.xlsx")