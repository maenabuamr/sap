import streamlit as st
import pandas as pd


def render_credit_table(df: pd.DataFrame):

    st.subheader("👥 جميع العملاء")

    # ==========================================
    # Smart Search
    # ==========================================

    search = st.text_input(
        "🔍 بحث (اسم العميل / رقم المرجع / المندوب)",
        placeholder="اكتب للبحث..."
    )

    data = df.copy()

    if search:

        search = search.strip().lower()

        data = data[

            data["CustomerName"].astype(str).str.lower().str.contains(search)

            |

            data["ReferenceNumber"].astype(str).str.contains(search)

            |

            data["Salesperson"].astype(str).str.lower().str.contains(search)

        ]

    # ==========================================
    # ترتيب حسب الأولوية
    # ==========================================

    data = data.sort_values(

        by=[

            "Priority",
            "Age_90_Plus",
            "DueBalance",
            "CurrentBalance"

        ],

        ascending=[

            True,
            False,
            False,
            False

        ]

    )

    # ==========================================
    # عرض الجدول
    # ==========================================

    display = pd.DataFrame({

        "Reference": data["ReferenceNumber"],

        "العميل": data["CustomerName"],

        "المندوب": data["Salesperson"],

        "فترة السداد": data["PaymentTerm"],

        "الرصيد الحالي": data["CurrentBalance"],

        "المستحق": data["DueBalance"],

        "+90": data["Age_90_Plus"],

        "الخطورة": data["Risk"],

        "الإجراء": data["Action"]

    })

    st.dataframe(

        display,

        use_container_width=True,

        hide_index=True

    )

    # ==========================================
    # Export
    # ==========================================

    csv = display.to_csv(index=False).encode("utf-8-sig")

    st.download_button(

        "📥 تصدير Excel (CSV)",

        csv,

        "customers.csv",

        "text/csv"

    )