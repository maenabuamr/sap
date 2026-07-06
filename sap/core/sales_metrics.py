import pandas as pd


class SalesMetrics:

    def __init__(self, sales: pd.DataFrame):

        self.df = sales.copy()

    # ==========================================
    # KPIs
    # ==========================================

    def total_sales(self):

        return self.df["Amt"].sum()

    def total_qty(self):

        return self.df["QYT"].sum()
    def quantity(self):
         return self.total_qty()

    def invoices(self):

        return self.df["DocNum"].nunique()

    def customers(self):

        return self.df["ReferenceNumber"].nunique()

    def avg_invoice(self):

        invoices = self.invoices()

        if invoices == 0:
            return 0

        return self.total_sales() / invoices

    # ==========================================
    # Charts
    # ==========================================

    def monthly_sales(self):

        return (

            self.df

            .groupby(

                ["Year", "Month"],

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

            .sort_values(

                ["Year", "Month"]

            )

        )

    def salespersons(self):

        return (

            self.df

            .groupby(

                "Salesperson",

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

            .sort_values(

                "Sales",

                ascending=False

            )

        )

    def item_groups(self):

        return (

            self.df

            .groupby(

                "ItemGroup",

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

            .sort_values(

                "Sales",

                ascending=False

            )

        )

    def top_customers(self, top=20):

        return (

            self.df

            .groupby(

                ["ReferenceNumber", "CustomerName"],

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

            .sort_values(

                "Sales",

                ascending=False

            )

            .head(top)

        )

    def top_items(self, top=20):

        return (

            self.df

            .groupby(

                ["ItemCode", "ItemDescription"],

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum"),

                Qty=("QYT", "sum")

            )

            .sort_values(

                "Sales",

                ascending=False

            )

            .head(top)

        )