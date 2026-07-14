import bcrypt
import streamlit as st
import json, os, sys
sys.path.append(os.getcwd()) # لضمان رؤية config.py
from config import PAGE_CONFIG

if st.session_state.get("user_info", {}).get("role") != "admin":
    st.error("غير مصرح لك"); st.stop()

DATA_FILE = "data/users.json"

def load_users():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r", encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

users = load_users()
st.title("⚙️ إدارة المستخدمين")

# تجميع الملفات من المرجع المركزي
all_files = [p[0] for group in PAGE_CONFIG.values() for p in group]

# إضافة مستخدم
with st.expander("➕ إضافة مستخدم جديد"):
    new_user = st.text_input("اسم المستخدم الجديد")
    new_pass = st.text_input("كلمة السر", type="password")
    if st.button("حفظ المستخدم"):
        users[new_user] = {"password": new_pass, "role": "user", "allowed_pages": []}
        with open(DATA_FILE, "w", encoding='utf-8') as f: json.dump(users, f, indent=4)
        st.rerun()

# إدارة المستخدمين
st.subheader("المستخدمون المسجلون")
for username in list(users.keys()):
    with st.expander(f"👤 {username}"):
        new_pw = st.text_input(f"كلمة سر لـ {username}", key=f"pw_{username}")
        current_perms = users[username].get('allowed_pages', [])
        valid_perms = [p for p in current_perms if p in all_files or p == 'all']
        if 'all' in current_perms:
            valid_perms = list(all_files)
        new_perms = st.multiselect("الصلاحيات", all_files, default=valid_perms, key=f"perm_{username}")
        
        c1, c2 = st.columns(2)
        if c1.button("تحديث", key=f"upd_{username}"):
            if new_pw:
                    users[username]["password_hash"] = bcrypt.hashpw(new_pw.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
                users[username]["allowed_pages"] = new_perms
            with open(DATA_FILE, "w", encoding='utf-8') as f: json.dump(users, f, indent=4)
            st.rerun()
        if c2.button("حذف", key=f"del_{username}"):
            del users[username]
            with open(DATA_FILE, "w", encoding='utf-8') as f: json.dump(users, f, indent=4)
            st.rerun()