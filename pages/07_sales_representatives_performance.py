import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide", page_title="تقرير أداء المندوبين")

@st.cache_data
def load_data():
    file = os.path.join("data", "sales_customer.csv")
    df = pd.read_csv(file, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df["Amt"] = pd.to_numeric(df["Amt"], errors="coerce").fillna(0)
    df["QYT"] = pd.to_numeric(df["QYT"], errors="coerce").fillna(0)
    return df

df = load_data()

st.title("📊 تقرير أداء المندوبين المجمع")

# الفلاتر
col1, col2, col3 = st.columns(3)
with col1: year = st.selectbox("السنة", sorted(df["Year"].unique()))
with col2: month = st.multiselect("الشهر", sorted(df["Month"].unique()), default=sorted(df["Month"].unique()))
with col3: rep = st.multiselect("المندوب", sorted(df["Salesperson"].unique()), default=sorted(df["Salesperson"].unique()))

# الفلترة
filtered_df = df[(df["Year"] == year) & (df["Month"].isin(month)) & (df["Salesperson"].isin(rep))]

# إنشاء Pivot Table مع أعمدة هرمية (المندوب -> Amt, QYT)
pivot = filtered_df.pivot_table(
    index=["ItemGroup", "ItemDescription"],
    columns="Salesperson",
    values=["Amt", "QYT"],
    aggfunc="sum",
    fill_value=0
)

# ترتيب الأعمدة لتظهر مرتبة حسب المندوبين ثم (Amt ثم QYT لكل مندوب)
pivot = pivot.swaplevel(0, 1, axis=1).sort_index(axis=1)

# عرض النتائج
for group in pivot.index.get_level_values("ItemGroup").unique():
    group_df = pivot.xs(group, level="ItemGroup")
    
    # حساب الإجمالي لكل مجموعة
    total_row = group_df.sum()
    total_df = pd.DataFrame([total_row], columns=group_df.columns, index=["🔵 إجمالي العائلة"])
    
    # دمج البيانات
    display_df = pd.concat([total_df, group_df])

    # التنسيق الشرطي لكل عمود
    def get_styled_table(df_to_style):
        # إنشاء قاموس التنسيق
        format_dict = {}
        for col in df_to_style.columns:
            if col[1] == 'Amt':
                format_dict[col] = "{:,.2f}"
            else:
                format_dict[col] = "{:,.0f}"
        # تطبيق التنسيق على الـ Styler
        return df_to_style.style.format(format_dict)

    with st.expander(f"📂 {group}", expanded=False):
        st.dataframe(get_styled_table(display_df), use_container_width=True)

st.divider()