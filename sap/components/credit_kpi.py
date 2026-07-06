import streamlit as st


def render_credit_kpis(kpis: dict):

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "إجمالي العملاء",
            f"{kpis['customers']:,}"
        )

    with col2:
        st.metric(
            "الرصيد الحالي",
            f"{kpis['current_balance']:,.3f}"
        )

    with col3:
        st.metric(
            "الرصيد المستحق",
            f"{kpis['due_balance']:,.3f}"
        )

    with col4:
        st.metric(
            "أكثر من 90 يوم",
            f"{kpis['age_90_plus']:,.3f}"
        )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🔴 مرتفع",
            kpis["high_risk_customers"]
        )

    with col2:
        st.metric(
            "🟠 متوسط",
            kpis["medium_risk_customers"]
        )

    with col3:
        st.metric(
            "🟢 منخفض",
            kpis["low_risk_customers"]
        )

    with col4:
        st.metric(
            "⚪ ضمن الفترة",
            kpis["normal_customers"]
        )