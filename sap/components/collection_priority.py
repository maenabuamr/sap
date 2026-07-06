import streamlit as st
import pandas as pd


def render_collection_priority(df: pd.DataFrame):

    st.subheader("📞 Collection Center")

    # ==========================================
    # Customers to collect
    # ==========================================

    collection = df[df["CollectionAmount"] > 0].copy()

    if collection.empty:

        st.success("لا يوجد عملاء بحاجة إلى متابعة اليوم.")

        return

    # ==========================================
    # Dashboard
    # ==========================================

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(

            "📞 يحتاج متابعة",

            len(collection)

        )

    with col2:

        st.metric(

            "💰 المطلوب تحصيله",

            f"{collection['CollectionAmount'].sum():,.3f}"

        )

    with col3:

        st.metric(

            "🔴 +90 يوم",

            f"{collection['Age_90_Plus'].sum():,.3f}"

        )

    st.divider()

    # ==========================================
    # Display Table
    # ==========================================

    display = pd.DataFrame({

        "العميل": collection["CustomerName"],

        "المندوب": collection["Salesperson"],

        "الرصيد الحالي": collection["CurrentBalance"],

        "غير المستحق": collection["NotDue"],

        "المستحق": collection["DueBalance"],

        "+90": collection["Age_90_Plus"],

        "الحالة": collection["Status"],

        "الإجراء": collection["Action"]

    })

    st.dataframe(

        display,

        use_container_width=True,

        hide_index=True

    )