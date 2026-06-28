import streamlit as st

from components.credit_kpi import render_credit_kpis
from components.credit_charts import render_credit_charts


def render_dashboard(df, kpis, alerts):

    st.header("📊 لوحة التحكم")

    # ======================================
    # KPIs
    # ======================================

    render_credit_kpis(kpis)

    # ======================================
    # Alerts
    # ======================================

    if alerts:

        st.subheader("🚨 مركز التنبيهات")

        for alert in alerts:
            st.warning(alert)

    st.divider()

    # ======================================
    # Charts
    # ======================================

    render_credit_charts(df)