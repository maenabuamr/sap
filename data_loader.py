import pandas as pd
import os
import streamlit as st

@st.cache_data
def load_checks():
    # 1. تحديد المسار المطلق لمجلد العمل الحالي
    # بالنظر إلى مسار الخطأ، الملف يعمل من /workspaces/sap/sap/
    # المجلد المطلوب هو /workspaces/sap/sap/data/
    
    # الحصول على مسار الملف الحالي
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # بناء مسار الملف باستخدام الانضمام لضمان التوافق
    # سنستخدم المسار المباشر للمجلد 'data' الموجود بجانب 'data_loader.py'
    file_path = os.path.join(current_dir, "data", "postdated_checks.csv")
    
    # للتشخيص: إذا فشل، سيخبرنا الكود أين يبحث بالضبط
    if not os.path.exists(file_path):
        st.error(f"❌ لم يتم العثور على الملف في المسار: {file_path}")
        return None
        
    return pd.read_csv(file_path)