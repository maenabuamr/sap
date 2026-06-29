import streamlit as st
import pandas as pd


def render_action_center(customer360: pd.DataFrame):

    st.subheader("🎯 Action Center")

    actions = []

    # =====================================================
    # High Risk Customers
    # =====================================================

    high = customer360[
        customer360["Age_90_Plus"] > 0
    ]

    if len(high):

        actions.append({

            "Priority": "🔴",

            "Action": "متابعة عاجلة",

            "Description": f"{len(high)} عميل لديهم ذمم تتجاوز 90 يوم."

        })

    # =====================================================
    # High Due Balance
    # =====================================================

    due = customer360[
        customer360["DueBalance"] > 1000
    ]

    if len(due):

        actions.append({

            "Priority": "🟠",

            "Action": "تحصيل",

            "Description": f"{len(due)} عميل لديهم ذمم مستحقة أكبر من 1000."

        })

    # =====================================================
    # Large Checks
    # =====================================================

    if "CheckAmount" in customer360.columns:

        checks = customer360[
            customer360["CheckAmount"] > 0
        ]

        if len(checks):

            actions.append({

                "Priority": "🟢",

                "Action": "مراجعة الشيكات",

                "Description": f"يوجد {len(checks)} عميل لديهم شيكات قائمة."

            })

    # =====================================================
    # No Actions
    # =====================================================

    if len(actions) == 0:

        st.success("✅ لا توجد إجراءات عاجلة اليوم.")

        return

    # =====================================================
    # Display
    # =====================================================

    actions = pd.DataFrame(actions)

    st.dataframe(

        actions,

        use_container_width=True,

        hide_index=True

    )