import streamlit as st
import pandas as pd


def render_executive_charts(customer360, sales):

    st.subheader("📊 Executive Analytics")

    # =====================================================
    # Monthly Sales
    # =====================================================

    if not sales.empty:

        monthly = (

            sales.groupby(

                ["Year", "Month"],

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

        )

        monthly["Period"] = (

            monthly["Year"].astype(str)

            + "-"

            + monthly["Month"].astype(str)

        )

        st.markdown("### 📈 Monthly Sales")

        st.line_chart(

            monthly.set_index("Period")["Sales"],

            use_container_width=True

        )

    st.divider()

    # =====================================================
    # Sales by Salesperson
    # =====================================================

    if not sales.empty:

        salesperson = (

            sales.groupby(

                "Salesperson",

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

            .sort_values(

                "Sales",

                ascending=False

            )

            .head(10)

        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### 👨‍💼 Top Salespersons")

            st.bar_chart(

                salesperson.set_index("Salesperson")["Sales"],

                use_container_width=True

            )

    # =====================================================
    # Sales by Item Group
    # =====================================================

        groups = (

            sales.groupby(

                "ItemGroup",

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

            .sort_values(

                "Sales",

                ascending=False

            )

        )

        with col2:

            st.markdown("### 📦 Item Groups")

            st.bar_chart(

                groups.set_index("ItemGroup")["Sales"],

                use_container_width=True

            )

    st.divider()

    # =====================================================
    # Credit Distribution
    # =====================================================

    aging = pd.DataFrame({

        "Period": [

            "0-15",

            "16-30",

            "31-45",

            "46-60",

            "61-75",

            "76-90",

            "+90"

        ],

        "Amount": [

            customer360["Age_0_15"].sum(),

            customer360["Age_16_30"].sum(),

            customer360["Age_31_45"].sum(),

            customer360["Age_46_60"].sum(),

            customer360["Age_61_75"].sum(),

            customer360["Age_76_90"].sum(),

            customer360["Age_90_Plus"].sum(),

        ]

    })

    st.markdown("### 💳 Aging Distribution")

    st.bar_chart(

        aging.set_index("Period")["Amount"],

        use_container_width=True

    )