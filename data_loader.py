import streamlit as st
import os
import pandas as pd

@st.cache_data
def load_sales():
    """Load sales customer report using relative path"""
    # المسار النسبي: المجلد 'data' يجب أن يكون في نفس مستوى ملف الكود الرئيسي
    fp = os.path.join('data', 'sales_customer.csv')
    if os.path.exists(fp) and os.path.getsize(fp) > 0:
        return pd.read_csv(fp, encoding='utf-8-sig')
    return pd.DataFrame() # إرجاع داتا فريم فارغ في حال عدم وجود الملف

@st.cache_data
def load_aging():
    """Load aging report using relative path"""
    fp = os.path.join('data', 'aging_report.csv')
    if os.path.exists(fp) and os.path.getsize(fp) > 0:
        return pd.read_csv(fp, encoding='utf-8-sig')
    return None

@st.cache_data
def load_checks():
    """Load postdated checks using relative path"""
    fp = os.path.join('data', 'postdated_checks.csv')
    if os.path.exists(fp) and os.path.getsize(fp) > 0:
        return pd.read_csv(fp, encoding='utf-8-sig')
    return pd.DataFrame(columns=['CustomerName', 'CheckNumber', 'Amount', 'DueDate', 'Status'])