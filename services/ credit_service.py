import pandas as pd


def build_credit_view(sales_df, aging_df, checks_df):
    """
    Build unified Credit View from:
    - Sales
    - Aging
    - Checks
    """

    # =====================================================
    # Sales Summary
    # =====================================================

    sales_summary = (
        sales_df
        .groupby(
            ["ReferenceNumber", "CustomerName", "Salesperson"],
            as_index=False
        )
        .agg(
            TotalSales=("Amt", "sum"),
            TotalQty=("QYT", "sum")
        )
    )

    # =====================================================
    # Aging
    # =====================================================

    aging = aging_df.copy()

    aging.rename(
        columns={
            "Reference Number": "ReferenceNumber",
            "الرصيد الحالي": "CurrentBalance",
            "رصيد متأخر": "Overdue",
            "رصيد غير مستحق": "NotDue"
        },
        inplace=True
    )

    # =====================================================
    # Checks
    # =====================================================

    checks = checks_df.copy()

    if "Reference Number" in checks.columns:
        checks.rename(
            columns={
                "Reference Number": "ReferenceNumber"
            },
            inplace=True
        )

    if "قيمة الشيك" in checks.columns:

        checks_summary = (
            checks.groupby(
                "ReferenceNumber",
                as_index=False
            )
            .agg(
                ChecksValue=("قيمة الشيك", "sum")
            )
        )

    else:

        checks_summary = pd.DataFrame(
            columns=[
                "ReferenceNumber",
                "ChecksValue"
            ]
        )

    # =====================================================
    # Merge Sales + Aging
    # =====================================================

    credit = sales_summary.merge(
        aging,
        on="ReferenceNumber",
        how="left"
    )

    # =====================================================
    # Merge Checks
    # =====================================================

    credit = credit.merge(
        checks_summary,
        on="ReferenceNumber",
        how="left"
    )

    # =====================================================
    # Fill Missing Values
    # =====================================================

    numeric_columns = [
        "CurrentBalance",
        "Overdue",
        "NotDue",
        "ChecksValue"
    ]

    for col in numeric_columns:

        if col in credit.columns:
            credit[col] = credit[col].fillna(0)

    # =====================================================
    # Risk
    # =====================================================

    credit["Risk"] = "Normal"

    if "Overdue" in credit.columns:

        credit.loc[
            credit["Overdue"] > 0,
            "Risk"
        ] = "High"

    return credit