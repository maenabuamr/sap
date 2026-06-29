import pandas as pd


def build_customer360(
    aging: pd.DataFrame,
    sales: pd.DataFrame,
    checks: pd.DataFrame,
):

    df = aging.copy()

    # =====================================================
    # Normalize Reference Number
    # =====================================================

    df["ReferenceNumber"] = (
        df["ReferenceNumber"]
        .astype(str)
        .str.strip()
    )

    # =====================================================
    # SALES
    # =====================================================

    if not sales.empty:

        sales = sales.copy()

        sales["ReferenceNumber"] = (
            sales["ReferenceNumber"]
            .astype(str)
            .str.strip()
        )

        # ----------------------------
        # Sales Summary
        # ----------------------------

        sales_summary = (

            sales.groupby("ReferenceNumber", as_index=False)

            .agg(

                TotalSales=("Amt", "sum"),

                InvoiceCount=("DocNum", "nunique"),

                TotalQty=("QYT", "sum"),

                AvgInvoice=("Amt", "mean"),

                LastInvoiceNo=("DocNum", "max"),

            )

        )

        # ----------------------------
        # Top Item
        # ----------------------------

        top_item = (

            sales.groupby(
                ["ReferenceNumber", "ItemDescription"],
                as_index=False
            )

            .agg(
                Sales=("Amt", "sum")
            )

            .sort_values(
                ["ReferenceNumber", "Sales"],
                ascending=[True, False]
            )

            .drop_duplicates("ReferenceNumber")

            [["ReferenceNumber", "ItemDescription"]]

            .rename(
                columns={
                    "ItemDescription": "TopItem"
                }
            )

        )

        # ----------------------------
        # Top Item Group
        # ----------------------------

        top_group = (

            sales.groupby(
                ["ReferenceNumber", "ItemGroup"],
                as_index=False
            )

            .agg(
                Sales=("Amt", "sum")
            )

            .sort_values(
                ["ReferenceNumber", "Sales"],
                ascending=[True, False]
            )

            .drop_duplicates("ReferenceNumber")

            [["ReferenceNumber", "ItemGroup"]]

            .rename(
                columns={
                    "ItemGroup": "TopGroup"
                }
            )

        )

        df = df.merge(
            sales_summary,
            on="ReferenceNumber",
            how="left"
        )

        df = df.merge(
            top_item,
            on="ReferenceNumber",
            how="left"
        )

        df = df.merge(
            top_group,
            on="ReferenceNumber",
            how="left"
        )

    # =====================================================
    # CHECKS
    # =====================================================

    if not checks.empty:

        checks = checks.copy()

        checks = checks.rename(
            columns={
                "Reference Number": "ReferenceNumber",
                "قيمة الشيك": "CheckAmount",
                "رقم الشيك": "CheckNumber",
                "تاريخ الاستحقاق": "DueDate",
            }
        )

        checks["ReferenceNumber"] = (
            checks["ReferenceNumber"]
            .astype(str)
            .str.strip()
        )

        checks_summary = (

            checks.groupby("ReferenceNumber", as_index=False)

            .agg(

                CheckAmount=("CheckAmount", "sum"),

                CheckNumber=("CheckNumber", "count"),

            )

        )

        df = df.merge(
            checks_summary,
            on="ReferenceNumber",
            how="left"
        )

    # =====================================================
    # Fill Numeric
    # =====================================================

    numeric_cols = [

        "TotalSales",

        "InvoiceCount",

        "TotalQty",

        "AvgInvoice",

        "CheckAmount",

        "CheckNumber",

    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = df[col].fillna(0)

    # =====================================================
    # Customer Score
    # =====================================================

    df["CustomerScore"] = 100

    if "Age_90_Plus" in df.columns:

        df.loc[df["Age_90_Plus"] > 0, "CustomerScore"] -= 40

    if "Overdue" in df.columns:

        df.loc[df["Overdue"] > 0, "CustomerScore"] -= 20

    if "TotalSales" in df.columns:

        df.loc[df["TotalSales"] > 10000, "CustomerScore"] += 10

    df["CustomerScore"] = df["CustomerScore"].clip(0, 100)

    # =====================================================
    # Recommendation
    # =====================================================

    df["Recommendation"] = "🟢 عميل ممتاز"

    if "Age_90_Plus" in df.columns:

        df.loc[
            df["Age_90_Plus"] > 0,
            "Recommendation"
        ] = "🔴 إيقاف البيع والمتابعة"

    if "Overdue" in df.columns:

        mask = (
            (df["Overdue"] > 0)
            &
            (df["Age_90_Plus"] <= 0)
        )

        df.loc[
            mask,
            "Recommendation"
        ] = "🟡 متابعة التحصيل"

    return df