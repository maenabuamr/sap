import pandas as pd


class ExecutiveMetrics:

    def __init__(self, customer360: pd.DataFrame):

        self.df = customer360.copy()

    # ======================================================
    # SALES
    # ======================================================

    def total_sales(self):

        if "TotalSales" not in self.df.columns:
            return 0

        return self.df["TotalSales"].sum()

    # ======================================================
    # CREDIT
    # ======================================================

    def current_balance(self):

        return self.df["CurrentBalance"].sum()

    def due_balance(self):

        return self.df["DueBalance"].sum()

    def overdue(self):

        return self.df["Overdue"].sum()

    def overdue90(self):

        return self.df["Age_90_Plus"].sum()

    # ======================================================
    # CUSTOMERS
    # ======================================================

    def customers(self):

        return len(self.df)

    # ======================================================
    # CHECKS
    # ======================================================

    def checks_value(self):

        if "CheckAmount" not in self.df.columns:
            return 0

        return self.df["CheckAmount"].sum()

    def checks_count(self):

        if "CheckNumber" not in self.df.columns:
            return 0

        return int(self.df["CheckNumber"].sum())

    # ======================================================
    # SALES
    # ======================================================

    def invoices(self):

        if "InvoiceCount" not in self.df.columns:
            return 0

        return int(self.df["InvoiceCount"].sum())

    def qty(self):

        if "TotalQty" not in self.df.columns:
            return 0

        return self.df["TotalQty"].sum()

    # ======================================================
    # TOP CUSTOMERS
    # ======================================================

    def top_customers(self, top=10):

        return (

            self.df

            .sort_values(

                "TotalSales",

                ascending=False

            )

            .head(top)

        )

    # ======================================================
    # TOP DEBTORS
    # ======================================================

    def top_debtors(self, top=10):

        return (

            self.df

            .sort_values(

                "CurrentBalance",

                ascending=False

            )

            .head(top)

        )

    # ======================================================
    # TOP RISK
    # ======================================================

    def top_risk(self, top=10):

        return (

            self.df

            .sort_values(

                "Age_90_Plus",

                ascending=False

            )

            .head(top)

        )

    # ======================================================
    # COLLECTION %
    # ======================================================

    def collection_ratio(self):

        current = self.current_balance()

        overdue = self.overdue()

        if current == 0:

            return 0

        return round((overdue / current) * 100, 2)