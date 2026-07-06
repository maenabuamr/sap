import pandas as pd

MIN_AMOUNT = 1.0


def classify_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    تصنيف العملاء حسب أعمار الذمم.
    """

    result = df.copy()

    result["Risk"] = "⚪ ضمن فترة السداد"
    result["Priority"] = 4
    result["Action"] = "لا يوجد إجراء"

    # ------------------------------------
    # Low Risk (0-60)
    # ------------------------------------

    low = (
        (result["Age_0_15"] >= MIN_AMOUNT)
        | (result["Age_16_30"] >= MIN_AMOUNT)
        | (result["Age_31_45"] >= MIN_AMOUNT)
        | (result["Age_46_60"] >= MIN_AMOUNT)
    )

    result.loc[low, "Risk"] = "🟢 منخفض"
    result.loc[low, "Priority"] = 3
    result.loc[low, "Action"] = "متابعة دورية"

    # ------------------------------------
    # Medium Risk (61-90)
    # ------------------------------------

    medium = (
        (result["Age_61_75"] >= MIN_AMOUNT)
        | (result["Age_76_90"] >= MIN_AMOUNT)
    )

    result.loc[medium, "Risk"] = "🟡 متوسط"
    result.loc[medium, "Priority"] = 2
    result.loc[medium, "Action"] = "متابعة هذا الأسبوع"

    # ------------------------------------
    # High Risk (+90)
    # ------------------------------------

    high = result["Age_90_Plus"] >= MIN_AMOUNT

    result.loc[high, "Risk"] = "🔴 مرتفع"
    result.loc[high, "Priority"] = 1
    result.loc[high, "Action"] = "اتصال فوري"

    # ------------------------------------
    # Due Balance
    # ------------------------------------

    result["DueBalance"] = (
        result["CurrentBalance"]
        - result["NotDue"]
    ).clip(lower=0)

    return result