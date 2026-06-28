import pandas as pd


def build_customer360(aging, sales, checks):

    df = aging.copy()

    # ==========================================
    # توحيد نوع المفتاح
    # ==========================================

    df["ReferenceNumber"] = df["ReferenceNumber"].astype(str).str.strip()

    if not sales.empty:

        sales = sales.copy()

        sales["ReferenceNumber"] = (
            sales["ReferenceNumber"]
            .astype(str)
            .str.strip()
        )

        sales_summary = (

            sales.groupby("ReferenceNumber")

            .agg(

                TotalSales=("Amt", "sum"),
                InvoiceCount=("DocNum", "nunique"),
                TotalQty=("QYT", "sum"),

            )

            .reset_index()

        )

        df = df.merge(
            sales_summary,
            on="ReferenceNumber",
            how="left"
        )

    # ==========================================
    # Checks
    # ==========================================

    if not checks.empty:

        checks = checks.copy()

        checks = checks.rename(
            columns={
                "Reference Number": "ReferenceNumber",
                "قيمة الشيك": "CheckAmount",
                "رقم الشيك": "CheckNumber",
            }
        )

        checks["ReferenceNumber"] = (
            checks["ReferenceNumber"]
            .astype(str)
            .str.strip()
        )

        checks_summary = (

            checks.groupby("ReferenceNumber")

            .agg(

                CheckAmount=("CheckAmount", "sum"),
                CheckNumber=("CheckNumber", "count"),

            )

            .reset_index()

        )

        df = df.merge(
            checks_summary,
            on="ReferenceNumber",
            how="left"
        )

    # ==========================================
    # Fill Nulls
    # ==========================================

    for col in [
        "TotalSales",
        "InvoiceCount",
        "TotalQty",
        "CheckAmount",
        "CheckNumber",
    ]:

        if col in df.columns:

            df[col] = df[col].fillna(0)

    return df