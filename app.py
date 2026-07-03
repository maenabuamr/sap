import streamlit as st
import os

from config import PAGE_CONFIG

# Simple PIN login — set APP_PIN env var to change.
APP_PIN = os.environ.get("APP_PIN", "1234")

if "user_info" not in st.session_state:
    st.session_state.user_info = None

st.set_page_config(layout="wide", page_title="نظام الإدارة الموحد")

if st.session_state.user_info is None:
    # Hide sidebar visually on the login screen via CSS.
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none}"
        "[data-testid='stSidebarNav']{display:none}</style>",
        unsafe_allow_html=True,
    )
    st.title("🔐 تسجيل الدخول")
    pin = st.text_input("رمز الدخول", type="password")
    if st.button("دخول"):
        if pin == APP_PIN:
            st.session_state.user_info = {
                "username": "user",
                "role": "admin",
                "allowed_pages": [],
            }
            st.rerun()
        else:
            st.error("رمز خاطئ")
        st.stop()
    st.stop()

# ─── Post-login — full navigation ───
role = st.session_state.user_info.get("role")
allowed = st.session_state.user_info.get("allowed_pages", [])
nav_structure = {}
if role == "admin":
    for group, pages in PAGE_CONFIG.items():
        nav_structure[group] = [st.Page(f"pages/{p[0]}", title=p[1], icon=p[2]) for p in pages]
    nav_structure["إدارة النظام"] = [
        st.Page("pages/08_admin_users.py", title="إدارة المستخدمين", icon="⚙️")
    ]
else:
    for group, pages in PAGE_CONFIG.items():
        filtered = [
            st.Page(f"pages/{p[0]}", title=p[1], icon=p[2])
            for p in pages if p[0] in allowed
        ]
        if filtered:
            nav_structure[group] = filtered

with st.sidebar:
    st.write(f"👤 {st.session_state.user_info['username']}")
    if st.button("🚪 تسجيل خروج"):
        st.session_state.user_info = None
        st.rerun()

if nav_structure:
    pg = st.navigation(nav_structure)
    pg.run()
else:
    st.error("ليس لديك صلاحية الوصول لأي صفحة.")