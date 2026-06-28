import pandas as pd


def build_collection_list(df: pd.DataFrame) -> pd.DataFrame:
    """
    تجهيز قائمة التحصيل اليومية.
    """

    result = df.copy()

    # ==========================================
    # المبلغ المستحق
    # ==========================================

    result["CollectionAmount"] = (
        result["Age_61_75"]
        + result["Age_76_90"]
        + result["Age_90_Plus"]
    )

    # ==========================================
    # حالة الحساب
    # ==========================================

    def account_status(row):

        if row["Age_90_Plus"] > 0:
            return "🔴 متأخر أكثر من 90 يوم"

        elif (
            row["Age_61_75"] > 0
            or row["Age_76_90"] > 0
        ):
            return "🟠 متأخر 61-90 يوم"

        elif row["DueBalance"] > 0:
            return "🟡 يوجد ذمم مستحقة"

        else:
            return "🟢 ضمن فترة السداد"

    result["Status"] = result.apply(
        account_status,
        axis=1
    )

    # ==========================================
    # الإجراء المقترح
    # ==========================================

    def action(row):

        if row["Age_90_Plus"] > 0:
            return "📞 اتصال فوري"

        elif (
            row["Age_61_75"] > 0
            or row["Age_76_90"] > 0
        ):
            return "☎ متابعة"

        elif row["DueBalance"] > 0:
            return "📅 متابعة لاحقاً"

        return "✅ لا يوجد"

    result["Action"] = result.apply(
        action,
        axis=1
    )

    # ==========================================
    # ترتيب الأولوية
    # ==========================================

    result = result.sort_values(

        by=[
            "Priority",
            "Age_90_Plus",
            "CollectionAmount",
            "CurrentBalance"
        ],

        ascending=[
            True,
            False,
            False,
            False
        ]

    )

    return result