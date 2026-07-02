import streamlit as st

st.set_page_config(
    page_title="نظام الإدارة",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تعريف الصفحات
pages = {
    "المالية والمبيعات": [
        st.Page("pages/02_credit_management.py", title="إدارة الذمم", icon="💰"),
        st.Page("pages/04_account_statement.py", title="كشوفات الحساب", icon="📝"),
    ],
    "إدارة المبيعات": [
        st.Page("pages/03_sales_analytics.py", title="تحليل المبيعات", icon="📊"),
        st.Page("pages/03_sales_dashboard.py", title="لوحة المبيعات", icon="📈"),
        st.Page("pages/07_sales_representatives_performance.py", title="أداء المندوبين", icon="👥"),
    ],
    "إدارة المستودعات": [
        st.Page("pages/05_inventory_management.py", title="المستودعات", icon="📦"),
    ],
}

pg = st.navigation(pages)
pg.run()