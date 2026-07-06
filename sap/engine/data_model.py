import pandas as pd


class ERPDataModel:

    def __init__(self, aging, sales, checks):
        # الاحتفاظ بنسخة أصلية خام (دائمة) لا تتأثر بالفلترة لضمان إعادة الفلترة بشكل صحيح
        self.aging_orig = aging.copy()
        self.sales_orig = sales.copy()
        self.checks_orig = checks.copy()

        # الجداول النشطة التي تقرأ منها الواجهة والـ Engines
        self.sales = sales.copy()
        self.aging = aging.copy()
        self.checks = checks.copy()

    # =====================================================
    # Filters
    # =====================================================

    def apply_filters(
        self,
        company=None,
        year=None,
        month=None,
        salesperson=None,  # يتوقع الآن قائمة عناصر (List) بسبب الـ multiselect
        customer=None,
    ):
        # في كل مرة يتم استدعاء الفلاتر، نبدأ من النسخ الأصلية الخام
        sales = self.sales_orig.copy()
        aging = self.aging_orig.copy()
        checks = self.checks_orig.copy()

        # ---------------- Sales ----------------
        if company not in [None, "الكل", []] and "DB" in sales.columns:
            sales = sales[sales["DB"] == company]

        if year not in [None, "الكل", []] and "Year" in sales.columns:
            sales = sales[sales["Year"] == year]

        if month not in [None, "الكل", []] and "Month" in sales.columns:
            sales = sales[sales["Month"] == month]

        # دعم الفلترة متعددة الاختيارات للمندوبين
        if salesperson not in [None, "الكل", []] and "Salesperson" in sales.columns:
            if isinstance(salesperson, list):
                sales = sales[sales["Salesperson"].isin(salesperson)]
            else:
                sales = sales[sales["Salesperson"] == salesperson]

        if customer and customer != "الكل":
            sales = sales[
                sales["CustomerName"].str.contains(
                    customer, case=False, na=False
                )
            ]

        self.sales = sales

        # ---------------- Aging ----------------
        if company not in [None, "الكل", []] and "DB" in aging.columns:
            aging = aging[aging["DB"] == company]

        # دعم الفلترة متعددة الاختيارات للمندوبين
        if salesperson not in [None, "الكل", []] and "Salesperson" in aging.columns:
            if isinstance(salesperson, list):
                aging = aging[aging["Salesperson"].isin(salesperson)]
            else:
                aging = aging[aging["Salesperson"] == salesperson]

        if customer and customer != "الكل":
            aging = aging[
                aging["CustomerName"].str.contains(
                    customer, case=False, na=False
                )
            ]

        self.aging = aging

        # ---------------- Checks ----------------
        if company not in [None, "الكل", []] and "DB" in checks.columns:
            checks = checks[checks["DB"] == company]

        # التحقق من اسم العمود الموحد للمندوب في الشيكات (Salesperson أو اسم المندوب)
        check_sp_col = (
            "Salesperson"
            if "Salesperson" in checks.columns
            else ("اسم المندوب" if "اسم المندوب" in checks.columns else None)
        )

        if salesperson not in [None, "الكل", []] and check_sp_col:
            if isinstance(salesperson, list):
                checks = checks[checks[check_sp_col].isin(salesperson)]
            else:
                checks = checks[checks[check_sp_col] == salesperson]

        if customer and customer != "الكل":
            check_cust_col = (
                "CustomerName"
                if "CustomerName" in checks.columns
                else ("CardName" if "CardName" in checks.columns else None)
            )
            if check_cust_col:
                checks = checks[
                    checks[check_cust_col].str.contains(
                        customer, case=False, na=False
                    )
                ]

        self.checks = checks

        return self