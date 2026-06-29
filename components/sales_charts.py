import streamlit as st


def render_sales_charts(metrics):

    # ==========================================
    # Monthly Sales
    # ==========================================

    st.subheader("📈 Monthly Sales")

    monthly = metrics.monthly_sales()

    if not monthly.empty:

        monthly["Period"] = (
            monthly["Year"].astype(str)
            + "-"
            + monthly["Month"].astype(str)
        )

        st.line_chart(
            monthly.set_index("Period")["Sales"],
            use_container_width=True
        )

    st.divider()

    # ==========================================
    # Salesperson
    # ==========================================

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("👨‍💼 Sales by Salesperson")

        st.bar_chart(
            metrics.salespersons().set_index("Salesperson")["Sales"],
            use_container_width=True
        )

    with col2:

        st.subheader("📦 Sales by Item Group")

        st.bar_chart(
            metrics.item_groups().set_index("ItemGroup")["Sales"],
            use_container_width=True
        )