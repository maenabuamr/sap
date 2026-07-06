import streamlit as st


def render_ai_insights(insights):

    st.subheader("🤖 AI Insights")

    if len(insights) == 0:

        st.success("لا توجد تنبيهات حالياً.")

        return

    for item in insights:

        st.info(item)