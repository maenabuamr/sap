import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.header("⚖️ كشف الحساب الموحد")

# المسار الصحيح للملف
file_path = "data/combined_statements.csv"

try:
    df = pd.read_csv(file_path)
    
    # تحويل التاريخ بشكل صحيح لمنع ظهور 1970
    df["PostingDate"] = pd.to_datetime(df["PostingDate"], errors='coerce')
    df = df.dropna(subset=['PostingDate'])
    df["DisplayDate"] = df["PostingDate"].dt.strftime('%Y-%m-%d')
    
    # إنشاء الاسم المدمج
    df["CustomerLabel"] = df["ReferenceNumber"].astype(str) + " - " + df["CustomerName"]
    
    # 1. فلتر اختيار العميل
    selected_customer = st.selectbox("🔍 اختر العميل:", sorted(df["CustomerLabel"].dropna().unique()))
    
    if selected_customer:
        df_c = df[df["CustomerLabel"] == selected_customer].sort_values("PostingDate").copy()
        
        # 2. فلتر اختيار الشركة (الذي كان مفقوداً)
        company_options = ["الكل"] + df_c["Company"].unique().tolist()
        selected_company = st.radio("🏢 حدد نطاق عرض كشف الحساب:", company_options, horizontal=True)
        
        if selected_company != "الكل":
            df_c = df_c[df_c["Company"] == selected_company].copy()
            
        # حساب الرصيد التراكمي
        bal = 0
        bals = []
        for _, r in df_c.iterrows():
            debit = float(r["DebitAmount"]) if pd.notnull(r["DebitAmount"]) else 0
            credit = float(r["CreditAmount"]) if pd.notnull(r["CreditAmount"]) else 0
            bal += (debit - credit)
            bals.append(bal)
        df_c["الرصيد"] = bals
        
        # 3. الملخص المالي (الذي كان مفقوداً)
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي المدين", f"{df_c['DebitAmount'].sum():,.2f} JOD")
        col2.metric("إجمالي الدائن", f"{df_c['CreditAmount'].sum():,.2f} JOD")
        col3.metric("الرصيد النهائي", f"{bals[-1] if bals else 0:,.2f} JOD")
        
        # عرض الجدول بالأعمدة المختصرة
        display_df = df_c[["Company", "ReferenceNumber", "CustomerName", "DisplayDate", "Details", "DebitAmount", "CreditAmount", "الرصيد"]]
        display_df.columns = ["الشركة", "رقم الحساب", "العميل", "التاريخ", "التفاصيل", "مدين", "دائن", "الرصيد"]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
except Exception as e:
    st.error(f"⚠️ خطأ في تحميل البيانات: {e}")