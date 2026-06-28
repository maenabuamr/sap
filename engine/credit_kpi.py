import pandas as pd


def calculate_kpis(df: pd.DataFrame) -> dict:
    """
    حساب مؤشرات الأداء الخاصة بإدارة الذمم.
    """

    return {

        # ==========================
        # Customers
        # ==========================

        "customers": len(df),

        # ==========================
        # Balances
        # ==========================

        "current_balance": df["CurrentBalance"].sum(),

        "overdue": df["Overdue"].sum(),

        "not_due": df["NotDue"].sum(),

        "due_balance": df["DueBalance"].sum(),

        # ==========================
        # Checks
        # ==========================

        "checks_count": df["ChecksCount"].sum(),

        "checks_value": df["ChecksValue"].sum(),

        # ==========================
        # Risk
        # ==========================

        "high_risk_customers": len(
            df[df["Priority"] == 1]
        ),

        "medium_risk_customers": len(
            df[df["Priority"] == 2]
        ),

        "low_risk_customers": len(
            df[df["Priority"] == 3]
        ),

        "normal_customers": len(
            df[df["Priority"] == 4]
        ),

        # ==========================
        # Aging
        # ==========================

        "age_0_15": df["Age_0_15"].sum(),

        "age_16_30": df["Age_16_30"].sum(),

        "age_31_45": df["Age_31_45"].sum(),

        "age_46_60": df["Age_46_60"].sum(),

        "age_61_75": df["Age_61_75"].sum(),

        "age_76_90": df["Age_76_90"].sum(),

        "age_90_plus": df["Age_90_Plus"].sum()

    }