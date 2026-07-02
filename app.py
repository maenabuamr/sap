import streamlit as st
import json, os
from config import PAGE_CONFIG

if "user_info" not in st.session_state: st.session_state.user_info = None
st.set_page_config(layout="wide", page_title="نظام الإدارة الموحد")

# منطق تسجيل الدخول
if st.session_state.user_info is None:
    st.markdown("<style>[data-testid='stSidebar'] { display: none; }</style>", unsafe_allow_html=True)
    st.title("🔐 تسجيل الدخول")
    user = st.text_input("اسم المستخدم")
    pw = st.text_input("كلمة السر", type="password")
    if st.button("دخول"):
        if os.path.exists("data/users.json"):
            with open("data/users.json", "r", encoding='utf-8') as f:
                users = json.load(f)
            if user in users and users[user]["password"] == pw:
                st.session_state.user_info = {"username": user, **users[user]}
                st.rerun()
            else:
                st.error("خطأ في البيانات")
    st.stop()

# بناء الملاحة بناءً على الصلاحيات
role = st.session_state.user_info.get("role")
allowed = st.session_state.user_info.get("allowed_pages", [])
nav_structure = {}

if role == "admin":
    for group, pages in PAGE_CONFIG.items():
        nav_structure[group] = [st.Page(f"pages/{p[0]}", title=p[1], icon=p[2]) for p in pages]
    nav_structure["إدارة النظام"] = [st.Page("pages/08_admin_users.py", title="إدارة المستخدمين", icon="⚙️")]
else:
    for group, pages in PAGE_CONFIG.items():
        filtered = [st.Page(f"pages/{p[0]}", title=p[1], icon=p[2]) for p in pages if p[0] in allowed]
        if filtered: nav_structure[group] = filtered

# القائمة الجانبية
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