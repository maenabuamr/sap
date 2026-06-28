import pandas as pd


class SalesMetrics:

    def __init__(self, sales: pd.DataFrame):

        self.df = sales.copy()

    # ==========================================
    # KPIs
    # ==========================================

    def total_sales(self):

        return self.df["Amt"].sum()

    def invoices(self):

        return self.df["DocNum"].nunique()

    def quantity(self):

        return self.df["QYT"].sum()

    def customers(self):

        return self.df["ReferenceNumber"].nunique()

    def salespersons(self):

        return self.df["Salesperson"].nunique()

    def items(self):

        return self.df["ItemCode"].nunique()

    def item_groups(self):

        return self.df["ItemGroup"].nunique()

    def average_invoice(self):

        invoices = self.invoices()

        if invoices == 0:
            return 0

        return self.total_sales() / invoices

    # ==========================================
    # Top Customers
    # ==========================================

    def top_customers(self, top=10):

        return (

            self.df

            .groupby("CustomerName", as_index=False)

            .agg(

                Sales=("Amt", "sum"),

                Qty=("QYT", "sum"),

                Invoices=("DocNum", "nunique"),

            )

            .sort_values(

                "Sales",

                ascending=False

            )

            .head(top)

        )

    # ==========================================
    # Top Items
    # ==========================================

    def top_items(self, top=10):

        return (

            self.df

            .groupby("ItemDescription", as_index=False)

            .agg(

                Sales=("Amt", "sum"),

                Qty=("QYT", "sum"),

            )

            .sort_values(

                "Sales",

                ascending=False

            )

            .head(top)

        )

    # ==========================================
    # Top Item Groups
    # ==========================================

    def top_groups(self):

        return (

            self.df

            .groupby("ItemGroup", as_index=False)

            .agg(

                Sales=("Amt", "sum"),

            )

            .sort_values(

                "Sales",

                ascending=False

            )

        )

    # ==========================================
    # Monthly Sales
    # ==========================================

    def monthly_sales(self):

        return (

            self.df

            .groupby(

                ["Year", "Month"],

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum"),

            )

            .sort_values(

                ["Year", "Month"]

            )

        )