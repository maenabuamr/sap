import streamlit as st
# PWA Configuration
st.markdown("""
<link rel="manifest" href="./static/manifest.json">
<meta name="theme-color" content="#1a2332">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="SAP">
<link rel="apple-touch-icon" href="./static/icon-192.png">
<script>if("serviceWorker"in navigator){navigator.serviceWorker.register("./static/sw.js")}</script>
""", unsafe_allow_html=True)











import streamlit as st
import os

from config import PAGE_CONFIG
from auth import verify_credentials

# Simple PIN login — set APP_PIN env var to change.

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
    username = st.text_input("اسم المستخدم", key="login_user")
    password = st.text_input("كلمة المرور", type="password", key="login_pass")
    if st.button("دخول"):
        ok, role, allowed_pages = verify_credentials(username, password)
        if ok:
            st.session_state.user_info = {
                "username": username,
                "role": role or "user",
                "allowed_pages": allowed_pages,
            }
            st.rerun()
        else:
            st.error("اسم المستخدم أو كلمة المرور خاطئة")
        st.stop()
    st.stop()

# ─── Post-login — full navigation ───
role = st.session_state.user_info.get("role")
allowed = st.session_state.user_info.get("allowed_pages", [])
is_full_admin = role == "admin" and (not allowed or allowed == ["all"])
nav_structure = {}
if is_full_admin:
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