import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide")
st.title("📈 تقارير حركة ودوران المواد")

# المسار المحدث للملف
FILE_PATH = "data/Itemes_Transfers.csv"

if not os.path.exists(FILE_PATH):
    st.error(f"الملف غير موجود في المسار: {FILE_PATH}. يرجى التأكد من وجوده داخل مجلد data.")
    st.stop()

@st.cache_data
def load_data():
    df = pd.read_csv(FILE_PATH)
    # تحويل التاريخ للتأكد من صحة التنسيق
    df['تاريخ القيد'] = pd.to_datetime(df['تاريخ القيد'], errors='coerce')
    return df

df_raw = load_data()
tab1, tab2, tab3 = st.tabs(["📋 حركة المادة التفصيلية", "🔄 معدل دوران المواد", "📊 تحليل حركات المستودعات"])

with tab1:
    st.subheader("سجل الحركة التفصيلي")
    item_options = df_raw['الوصف'].dropna().unique()
    selected_item = st.selectbox("اختر الصنف:", item_options)
    df_item = df_raw[df_raw['الوصف'] == selected_item].sort_values(by='تاريخ القيد')
    if not df_item.empty:
        st.dataframe(df_item[['تاريخ القيد', 'نوع الحركة', 'الكمية', 'الرصيد']], use_container_width=True)
        st.plotly_chart(px.line(df_item, x='تاريخ القيد', y='الرصيد', title="تطور الرصيد"), use_container_width=True)

with tab2:
    st.subheader("معدل دوران المواد")
    summary = df_raw.groupby(['الوصف']).agg(الخروج=('الكمية', lambda x: abs(x[x < 0].sum()))).sort_values(by='الخروج', ascending=False)
    st.dataframe(summary.head(10), use_container_width=True)

with tab3:
    st.subheader("توزيع الحركات")
    movement_types = df_raw['نوع الحركة'].value_counts().reset_index()
    st.plotly_chart(px.pie(movement_types, values='count', names='نوع الحركة', title="توزيع الحركات"), use_container_width=True)