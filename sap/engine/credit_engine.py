import pandas as pd

MIN_AMOUNT = 1.0


class CreditEngine:

    def __init__(self, aging: pd.DataFrame):

        self.df = aging.copy()

    # =====================================================
    # Risk Classification
    # =====================================================

    def classify(self):

        df = self.df.copy()

        df["Risk"] = "⚪ ضمن فترة السداد"

        # منخفض (0-60)
        low = (
            (df["Age_0_15"] >= MIN_AMOUNT) |
            (df["Age_16_30"] >= MIN_AMOUNT) |
            (df["Age_31_45"] >= MIN_AMOUNT) |
            (df["Age_46_60"] >= MIN_AMOUNT)
        )

        df.loc[low, "Risk"] = "🟢 منخفض"

        # متوسط (61-90)
        medium = (
            (df["Age_61_75"] >= MIN_AMOUNT) |
            (df["Age_76_90"] >= MIN_AMOUNT)
        )

        df.loc[medium, "Risk"] = "🟡 متوسط"

        # مرتفع (+90)
        high = (
            df["Age_90_Plus"] >= MIN_AMOUNT
        )

        df.loc[high, "Risk"] = "🔴 مرتفع"

        self.df = df

        return df

    # =====================================================
    # Dashboard KPIs
    # =====================================================

    def dashboard(self):

        df = self.df

        return {

            "customers": len(df),

            "current_balance": df["CurrentBalance"].sum(),

            "overdue": df["Overdue"].sum(),

            "not_due": df["NotDue"].sum(),

            "checks_count": df["ChecksCount"].sum(),

            "checks_value": df["ChecksValue"].sum(),

            "high_risk_customers": len(
                df[df["Risk"] == "🔴 مرتفع"]
            ),

            "medium_risk_customers": len(
                df[df["Risk"] == "🟡 متوسط"]
            ),

            "low_risk_customers": len(
                df[df["Risk"] == "🟢 منخفض"]
            ),

            "no_delay_customers": len(
                df[df["Risk"] == "⚪ ضمن فترة السداد"]
            )

        }

    # =====================================================
    # Collection List
    # =====================================================

    def collection_list(self):

        df = self.df.copy()

        df = df.sort_values(

            by=[
                "Age_90_Plus",
                "Age_76_90",
                "Age_61_75",
                "CurrentBalance"
            ],

            ascending=[
                False,
                False,
                False,
                False
            ]

        )

        return df

    # =====================================================
    # Alerts
    # =====================================================

    def alerts(self):

        df = self.df

        alerts = []

        high = len(
            df[df["Age_90_Plus"] >= MIN_AMOUNT]
        )

        medium = len(
            df[
                (df["Age_61_75"] >= MIN_AMOUNT) |
                (df["Age_76_90"] >= MIN_AMOUNT)
            ]
        )

        high_amount = df["Age_90_Plus"].sum()

        if high > 0:
            alerts.append(
                f"🔴 يوجد {high} عميل لديهم ذمم أكثر من 90 يوم."
            )

        if medium > 0:
            alerts.append(
                f"🟡 يوجد {medium} عميل لديهم ذمم بين 61 و90 يوم."
            )

        if high_amount >= MIN_AMOUNT:
            alerts.append(
                f"💰 إجمالي الذمم أكثر من 90 يوم = {high_amount:,.3f}"
            )

        return alerts

    # =====================================================
    # Top High Risk
    # =====================================================

    def top_high_risk(self, top=10):

        df = self.collection_list()

        return df.head(top)