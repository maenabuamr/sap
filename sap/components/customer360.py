import pandas as pd


def build_customer360(
    aging: pd.DataFrame,
    sales: pd.DataFrame,
    checks: pd.DataFrame,
):

    df = aging.copy()

    # ==========================================
    # Normalize Keys
    # ==========================================

    df["ReferenceNumber"] = (
        df["ReferenceNumber"]
        .astype(str)
        .str.strip()
    )

    # ==========================================
    # SALES
    # ==========================================

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

                AvgInvoice=("Amt", "mean"),

                LastInvoiceDate=("DocDate", "max"),

            )

            .reset_index()

        )

        # ======================================
        # Last Invoice Number
        # ======================================

        last_invoice = (

            sales.sort_values("DocDate")

            .groupby("ReferenceNumber")

            .tail(1)[

                [

                    "ReferenceNumber",

                    "DocNum"

                ]

            ]

            .rename(

                columns={

                    "DocNum": "LastInvoiceNo"

                }

            )

        )

        # ======================================
        # Top Item
        # ======================================

        top_item = (

            sales.groupby(

                [

                    "ReferenceNumber",

                    "ItemDescription"

                ],

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

            .sort_values(

                "Sales",

                ascending=False

            )

            .drop_duplicates(

                "ReferenceNumber"

            )[

                [

                    "ReferenceNumber",

                    "ItemDescription"

                ]

            ]

            .rename(

                columns={

                    "ItemDescription": "TopItem"

                }

            )

        )

        # ======================================
        # Top Item Group
        # ======================================

        top_group = (

            sales.groupby(

                [

                    "ReferenceNumber",

                    "ItemGroup"

                ],

                as_index=False

            )

            .agg(

                Sales=("Amt", "sum")

            )

            .sort_values(

                "Sales",

                ascending=False

            )

            .drop_duplicates(

                "ReferenceNumber"

            )[

                [

                    "ReferenceNumber",

                    "ItemGroup"

                ]

            ]

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
            last_invoice,
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

    # ==========================================
    # CHECKS
    # ==========================================

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

            checks.groupby("ReferenceNumber")

            .agg(

                CheckAmount=("CheckAmount", "sum"),

                CheckNumber=("CheckNumber", "count"),

                LastCheckDate=("DueDate", "max"),

            )

            .reset_index()

        )

        df = df.merge(

            checks_summary,

            on="ReferenceNumber",

            how="left"

        )

    # ==========================================
    # Customer Score
    # ==========================================

    score = 100

    df["CustomerScore"] = score

    if "Age_90_Plus" in df.columns:

        df.loc[df["Age_90_Plus"] > 0, "CustomerScore"] -= 40

    if "Overdue" in df.columns:

        df.loc[df["Overdue"] > 0, "CustomerScore"] -= 20

    if "TotalSales" in df.columns:

        df.loc[df["TotalSales"] > 10000, "CustomerScore"] += 10

    df["CustomerScore"] = (

        df["CustomerScore"]

        .clip(0, 100)

    )

    # ==========================================
    # AI Recommendation
    # ==========================================

    df["Recommendation"] = "🟢 عميل ممتاز"

    if "Age_90_Plus" in df.columns:

        df.loc[

            df["Age_90_Plus"] > 0,

            "Recommendation"

        ] = "🔴 إيقاف البيع والمتابعة"

    elif "Overdue" in df.columns:

        df.loc[

            df["Overdue"] > 0,

            "Recommendation"

        ] = "🟡 متابعة التحصيل"

    # ==========================================
    # Fill Nulls
    # ==========================================

    numeric = [

        "TotalSales",

        "InvoiceCount",

        "TotalQty",

        "AvgInvoice",

        "CheckAmount",

        "CheckNumber",

    ]

    for c in numeric:

        if c in df.columns:

            df[c] = df[c].fillna(0)

    return df