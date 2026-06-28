import pandas as pd


def build_customer360(
    aging: pd.DataFrame,
    sales: pd.DataFrame,
    checks: pd.DataFrame,
):

    df = aging.copy()

    # ==========================================
    # SALES
    # ==========================================

    if not sales.empty:

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
    # CHECKS
    # ==========================================

    if not checks.empty:

        checks = checks.rename(

            columns={

                "Reference Number": "ReferenceNumber",

                "قيمة الشيك": "CheckAmount",

                "رقم الشيك": "CheckNumber"

            }

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

    numeric = [

        "TotalSales",

        "InvoiceCount",

        "TotalQty",

        "CheckAmount",

        "CheckNumber",

    ]

    for c in numeric:

        if c in df.columns:

            df[c] = df[c].fillna(0)

    return df