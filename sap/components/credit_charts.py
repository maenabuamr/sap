import streamlit as st
import pandas as pd


def render_credit_charts(df: pd.DataFrame):

    st.subheader("📊 تحليل أعمار الذمم")

    aging = pd.DataFrame(
        {
            "الفترة": [
                "0-15",
                "16-30",
                "31-45",
                "46-60",
                "61-75",
                "76-90",
                "+90",
            ],
            "القيمة": [
                df["Age_0_15"].sum(),
                df["Age_16_30"].sum(),
                df["Age_31_45"].sum(),
                df["Age_46_60"].sum(),
                df["Age_61_75"].sum(),
                df["Age_76_90"].sum(),
                df["Age_90_Plus"].sum(),
            ],
        }
    )

    col1, col2 = st.columns(2)

    # ==========================================
    # جدول ملخص
    # ==========================================

    with col1:

        st.markdown("### توزيع الذمم")

        st.dataframe(
            aging,
            use_container_width=True,
            hide_index=True
        )

    # ==========================================
    # Bar Chart
    # ==========================================

    with col2:

        st.markdown("### الرسم البياني")

        chart = aging.set_index("الفترة")

        st.bar_chart(
            chart,
            use_container_width=True
        )