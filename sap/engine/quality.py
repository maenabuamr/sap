import pandas as pd

MIN_RISK_AMOUNT = 1.0


# ==========================================================
# Risk Classification
# ==========================================================

def classify_risk(df: pd.DataFrame) -> pd.DataFrame:

    result = df.copy()

    result["Risk"] = "⚪ لا يوجد تأخير"
    result["Priority"] = 4
    result["Action"] = "لا يحتاج متابعة"

    # ------------------------------------------------------
    # منخفض (0-60)
    # ------------------------------------------------------

    low = (
        (result["Age_0_15"] >= MIN_RISK_AMOUNT) |
        (result["Age_16_30"] >= MIN_RISK_AMOUNT) |
        (result["Age_31_45"] >= MIN_RISK_AMOUNT) |
        (result["Age_46_60"] >= MIN_RISK_AMOUNT)
    )

    result.loc[low, "Risk"] = "🟢 منخفض"
    result.loc[low, "Priority"] = 3
    result.loc[low, "Action"] = "متابعة"

    # ------------------------------------------------------
    # متوسط (61-90)
    # ------------------------------------------------------

    medium = (
        (result["Age_61_75"] >= MIN_RISK_AMOUNT) |
        (result["Age_76_90"] >= MIN_RISK_AMOUNT)
    )

    result.loc[medium, "Risk"] = "🟡 متوسط"
    result.loc[medium, "Priority"] = 2
    result.loc[medium, "Action"] = "متابعة عاجلة"

    # ------------------------------------------------------
    # مرتفع (+90)
    # ------------------------------------------------------

    high = (
        result["Age_90_Plus"] >= MIN_RISK_AMOUNT
    )

    result.loc[high, "Risk"] = "🔴 مرتفع"
    result.loc[high, "Priority"] = 1
    result.loc[high, "Action"] = "اتصال فوري"

    return result


# ==========================================================
# KPI
# ==========================================================

def calculate_credit_kpis(df: pd.DataFrame):

    return {

        "customers": len(df),

        "current_balance": df["CurrentBalance"].sum(),

        "overdue": df["Overdue"].sum(),

        "not_due": df["NotDue"].sum(),

        "checks_count": df["ChecksCount"].sum(),

        "checks_value": df["ChecksValue"].sum(),

        "high_risk_customers": len(
            df[df["Priority"] == 1]
        ),

        "medium_risk_customers": len(
            df[df["Priority"] == 2]
        ),

        "low_risk_customers": len(
            df[df["Priority"] == 3]
        ),

        "no_delay_customers": len(
            df[df["Priority"] == 4]
        )

    }


# ==========================================================
# Collection Priority
# ==========================================================

def collection_priority(df: pd.DataFrame):

    result = df.copy()

    return result.sort_values(

        by=[
            "Priority",
            "Age_90_Plus",
            "Age_76_90",
            "Age_61_75",
            "CurrentBalance"
        ],

        ascending=[
            True,
            False,
            False,
            False,
            False
        ]

    )


# ==========================================================
# Top High Risk
# ==========================================================

def top_high_risk(df: pd.DataFrame, top=10):

    return (

        collection_priority(df)

        .head(top)

    )


# ==========================================================
# Alerts
# ==========================================================

def generate_alerts(df: pd.DataFrame):

    alerts = []

    high = len(df[df["Priority"] == 1])

    medium = len(df[df["Priority"] == 2])

    if high > 0:

        alerts.append(

            f"🔴 يوجد {high} عميل لديهم ذمم أكثر من 90 يوم."

        )

    if medium > 0:

        alerts.append(

            f"🟡 يوجد {medium} عميل لديهم ذمم بين 61 و90 يوم."

        )

    return alerts