import streamlit as st

st.set_page_config(page_title="منظومة الإدارة الموحدة", layout="wide")

# القائمة الجانبية الموحدة
with st.sidebar:
    st.title("💼 شيخ الكار")
    st.subheader("منظومة إدارة البيانات الموحدة")
    st.divider()

# واجهة ترحيبية بسيطة
st.title("مرحباً بك في منظومة شيخ الكار")
st.write("استخدم القائمة الجانبية للتنقل إلى تقارير كشف الحساب.")