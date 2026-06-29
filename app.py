import streamlit as st
import os

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Credit Management",
    page_icon="💰",
    layout="wide",
)

# ==========================================================
# HEADER SECTION (اسم الشركة والشعار)
# ==========================================================
# إنشاء عمودين: عمود صغير للشعار وعمود للاسم ليظهرا بجانب بعضهما هندسياً
col1, col2 = st.columns([1, 8])

with col1:
    # تعديل الحروف لتصبح كابيتال LOGO.jpeg لتطابق اسم الملف في الـ Explorer تماماً
    if os.path.exists("LOGO.jpeg"):
        st.image("LOGO.jpeg", width=70)
    else:
        st.markdown("<h2 style='text-align: center; margin: 0;'>🏢</h2>", unsafe_allow_html=True)

with col2:
    # عرض اسم الشركة بخط متوسط، عريض، ومحاذى بشكل احترافي مع الشعار
    st.markdown(
        """
        <div style="display: flex; align-items: center; height: 70px;">
            <h3 style="margin: 0; font-weight: 700; color: #1E3A8A; font-size: 24px;">
                شركة بهاء الدين البستنجي وشركاه
            </h3>
        </div>
        """, 
        unsafe_allow_html=True
    )

st.divider()

# ==========================================================
# BODY
# ==========================================================
st.success("Done By : Ma'en A. Abu-Amr.")