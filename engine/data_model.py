import pandas as pd


class ERPDataModel:

    def __init__(self, aging, sales, checks):

        self.aging = aging.copy()
        self.sales = sales.copy()
        self.checks = checks.copy()

    # =====================================================
    # Filters
    # =====================================================

    def apply_filters(

        self,

        company=None,

        year=None,

        month=None,

        salesperson=None,

        customer=None,

    ):

        # ---------------- Sales ----------------

        sales = self.sales.copy()

        if company not in [None, "الكل"] and "DB" in sales.columns:

            sales = sales[sales["DB"] == company]

        if year not in [None, "الكل"] and "Year" in sales.columns:

            sales = sales[sales["Year"] == year]

        if month not in [None, "الكل"] and "Month" in sales.columns:

            sales = sales[sales["Month"] == month]

        if salesperson not in [None, "الكل"] and "Salesperson" in sales.columns:

            sales = sales[sales["Salesperson"] == salesperson]

        if customer:

            sales = sales[
                sales["CustomerName"]
                .str.contains(customer, case=False, na=False)
            ]

        self.sales = sales

        # ---------------- Aging ----------------

        aging = self.aging.copy()

        if company not in [None, "الكل"] and "DB" in aging.columns:

            aging = aging[aging["DB"] == company]

        if salesperson not in [None, "الكل"] and "Salesperson" in aging.columns:

            aging = aging[aging["Salesperson"] == salesperson]

        if customer:

            aging = aging[
                aging["CustomerName"]
                .str.contains(customer, case=False, na=False)
            ]

        self.aging = aging

        # ---------------- Checks ----------------

        checks = self.checks.copy()

        if company not in [None, "الكل"] and "DB" in checks.columns:

            checks = checks[checks["DB"] == company]

        if salesperson not in [None, "الكل"] and "اسم المندوب" in checks.columns:

            checks = checks[
                checks["اسم المندوب"] == salesperson
            ]

        self.checks = checks

        return self