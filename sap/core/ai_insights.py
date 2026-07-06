import pandas as pd


class AIInsights:

    def __init__(self, customer360: pd.DataFrame):

        self.df = customer360.copy()

    # =====================================================
    # Generate Insights
    # =====================================================

    def generate(self):

        insights = []

        # -----------------------------------------
        # High Risk Customers
        # -----------------------------------------

        high = self.df[self.df["Age_90_Plus"] > 0]

        if not high.empty:

            insights.append(
                f"🔴 يوجد {len(high)} عميل لديهم ذمم تتجاوز 90 يوم."
            )

            insights.append(
                f"💰 إجمالي الذمم (+90) = {high['Age_90_Plus'].sum():,.3f}"
            )

        # -----------------------------------------
        # Collection Ratio
        # -----------------------------------------

        if "CurrentBalance" in self.df.columns:

            ratio = 0

            total = self.df["CurrentBalance"].sum()

            overdue = self.df["Overdue"].sum()

            if total > 0:

                ratio = overdue / total * 100

            insights.append(
                f"📊 نسبة الذمم المستحقة من إجمالي الذمم = {ratio:.1f}%"
            )

        # -----------------------------------------
        # Top Customer
        # -----------------------------------------

        if "TotalSales" in self.df.columns:

            top = self.df.sort_values(
                "TotalSales",
                ascending=False
            ).head(1)

            if len(top):

                r = top.iloc[0]

                insights.append(
                    f"🏆 أعلى عميل مبيعاً: {r['CustomerName']} ({r['TotalSales']:,.3f})"
                )

        # -----------------------------------------
        # Biggest Balance
        # -----------------------------------------

        top_balance = self.df.sort_values(
            "CurrentBalance",
            ascending=False
        ).head(1)

        if len(top_balance):

            r = top_balance.iloc[0]

            insights.append(
                f"💳 أعلى رصيد على عميل: {r['CustomerName']} ({r['CurrentBalance']:,.3f})"
            )

        return insights