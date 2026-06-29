import streamlit as st
import pandas as pd

def render_customer_card(df: pd.DataFrame):

    st.subheader("👤 Customer 360")

    customers = sorted(df["CustomerName"].dropna().unique())

    customer = st.selectbox(
        "اختر العميل",
        customers
    )

    row = df[df["CustomerName"] == customer].iloc[0]

    st.divider()

    # =====================================================
    # KPIs
    # =====================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "الرصيد الحالي",
            f"{row['CurrentBalance']:,.3f}"
        )

    with c2:
        st.metric(
            "الرصيد المستحق",
            f"{row['DueBalance']:,.3f}"
        )

    with c3:
        st.metric(
            "+90 يوم",
            f"{row['Age_90_Plus']:,.3f}"
        )

    with c4:
        st.metric(
            "عدد الشيكات",
            int(row.get("CheckNumber", 0))
        )

    st.divider()
    
    st.metric(
        "⭐ Customer Score",
        f"{int(row.get('CustomerScore', 100))}/100"
    )

    # =====================================================
    # Customer Health
    # =====================================================

    st.markdown("### ❤️ Customer Health")

    score = int(row.get("CustomerScore", 100))

    st.progress(score / 100)

    if score >= 90:
        st.success("🟢 عميل ممتاز")
    elif score >= 70:
        st.info("🔵 عميل جيد")
    elif score >= 50:
        st.warning("🟡 يحتاج متابعة")
    else:
        st.error("🔴 عميل عالي الخطورة")
    
    st.divider()

    # =====================================================
    # بيانات العميل وملخص المبيعات
    # =====================================================

    left, right = st.columns(2)

    with left:
        st.markdown("### 📋 معلومات العميل")
        st.write(f"**Reference Number :** {row['ReferenceNumber']}")
        st.write(f"**المندوب :** {row['Salesperson']}")
        st.write(f"**فترة السداد :** {row['PaymentTerm']}")
        st.write(f"**الخطورة :** {row['Risk']}")
        st.write(f"**عدد الفواتير :** {int(row.get('InvoiceCount', 0))}")
        st.write(f"**آخر فاتورة :** {row.get('LastInvoiceNo', '-')}")
        st.write(f"**أفضل صنف :** {row.get('TopItem','-')}")
        st.write(f"**أفضل مجموعة :** {row.get('TopGroup','-')}")

    with right:
        st.markdown("### 💰 ملخص المبيعات")
        st.metric(
            "إجمالي المبيعات",
            f"{row.get('TotalSales', 0):,.3f}"
        )
        st.metric(
            "متوسط الفاتورة",
            f"{row.get('AvgInvoice', 0):,.3f}"
        )
        st.metric(
            "عدد الفواتير",
            int(row.get('InvoiceCount', 0))
        )
        st.metric(
            "إجمالي الكمية",
            f"{row.get('TotalQty', 0):,.2f}"
        )
        st.metric(
            "قيمة الشيكات",
            f"{row.get('CheckAmount', 0):,.3f}"
        )

    st.divider()

    # =====================================================
    # Aging
    # =====================================================

    st.markdown("### 📊 أعمار الذمم")

    aging = pd.DataFrame({
        "الفترة": [
            "0-15",
            "16-30",
            "31-45",
            "46-60",
            "61-75",
            "76-90",
            "+90"
        ],
        "القيمة": [
            row["Age_0_15"],
            row["Age_16_30"],
            row["Age_31_45"],
            row["Age_46_60"],
            row["Age_61_75"],
            row["Age_76_90"],
            row["Age_90_Plus"]
        ]
    })

    st.bar_chart(
        aging.set_index("الفترة"),
        use_container_width=True
    )

    st.divider()

    # =====================================================
    # AI Recommendation
    # =====================================================

    st.markdown("### 🤖 توصية النظام")

    if row["Age_90_Plus"] > 0:
        st.error(
            "يوصى بإيقاف البيع مؤقتًا والمتابعة الفورية مع العميل."
        )
    elif row["DueBalance"] > 0:
        st.warning(
            "يوصى بمتابعة العميل لتحصيل الذمم قبل إصدار مبيعات جديدة."
        )
    else:
        st.success(
            "وضع العميل ممتاز ولا توجد إجراءات مطلوبة."
        )