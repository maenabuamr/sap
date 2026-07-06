import pandas as pd


class Metrics:

    def __init__(self, customer360: pd.DataFrame):

        self.df = customer360.copy()

    # =====================================================
    # Customers
    # =====================================================

    def customers(self):

        return len(self.df)

    # =====================================================
    # Credit
    # =====================================================

    def current_balance(self):

        return self.df["CurrentBalance"].sum()

    def due_balance(self):

        return self.df["DueBalance"].sum()

    def overdue_90(self):

        return self.df["Age_90_Plus"].sum()

    def overdue_total(self):

        return self.df["Overdue"].sum()

    # =====================================================
    # Sales
    # =====================================================

    def total_sales(self):

        if "TotalSales" not in self.df.columns:
            return 0

        return self.df["TotalSales"].sum()

    def invoices(self):

        if "InvoiceCount" not in self.df.columns:
            return 0

        return int(self.df["InvoiceCount"].sum())

    def quantity(self):

        if "TotalQty" not in self.df.columns:
            return 0

        return self.df["TotalQty"].sum()

    # =====================================================
    # Checks
    # =====================================================

    def checks_value(self):

        if "CheckAmount" not in self.df.columns:
            return 0

        return self.df["CheckAmount"].sum()

    def checks_count(self):

        if "CheckNumber" not in self.df.columns:
            return 0

        return int(self.df["CheckNumber"].sum())

    # =====================================================
    # Risk
    # =====================================================

    def high_risk(self):

        return len(

            self.df[

                self.df["Priority"] == 1

            ]

        )

    def medium_risk(self):

        return len(

            self.df[

                self.df["Priority"] == 2

            ]

        )

    def low_risk(self):

        return len(

            self.df[

                self.df["Priority"] == 3

            ]

        )

    # =====================================================
    # Top Customers
    # =====================================================

    def top_customers(self, n=10):

        return (

            self.df

            .sort_values(

                "TotalSales",

                ascending=False

            )

            .head(n)

        )

    # =====================================================
    # Top Risk
    # =====================================================

    def top_risk(self, n=10):

        return (

            self.df

            .sort_values(

                [

                    "Age_90_Plus",

                    "DueBalance"

                ],

                ascending=False

            )

            .head(n)

        )