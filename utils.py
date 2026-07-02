import streamlit as st
import os

def display_header():
    # تصميم ترويسة موحدة لكل صفحات النظام
    col1, col2 = st.columns([1, 8])
    
    with col1:
        # التأكد من وجود الشعار في المجلد الرئيسي
        if os.path.exists("LOGO.jpeg"):
            st.image("LOGO.jpeg", width=70)
        else:
            # عرض أيقونة افتراضية في حال عدم وجود الشعار
            st.markdown("<h2 style='text-align: center; margin: 0;'>🏢</h2>", unsafe_allow_html=True)
            
    with col2:
        # اسم الشركة الموحد
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