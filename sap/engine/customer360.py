import pandas as pd


def build_customer360(
    aging: pd.DataFrame,
    sales: pd.DataFrame,
    checks: pd.DataFrame,
):
    if aging.empty:
        return pd.DataFrame()

    df = aging.copy()

    # 1. تحديد اسم مفتاح الربط المتاح في جدول أعمار الديون وتحويله فوراً لنص محمي
    join_key = "Calc_Group_ID" if "Calc_Group_ID" in df.columns else "ReferenceNumber"
    df[join_key] = df[join_key].astype(str).str.strip()

    # =====================================================
    # SALES
    # =====================================================
    if not sales.empty:
        sales = sales.copy()
        sales_key = "Calc_Group_ID" if "Calc_Group_ID" in sales.columns else "ReferenceNumber"
        
        # تحويل مفتاح الربط في جدول المبيعات لنصوص لمنع خطأ الـ ValueError
        sales[sales_key] = sales[sales_key].astype(str).str.strip()

        # ----------------------------
        # Sales Summary
        # ----------------------------
        sales_summary = (
            sales.groupby(sales_key, as_index=False)
            .agg(
                TotalSales=("Amt", "sum"),
                InvoiceCount=("DocNum", "nunique"),
                TotalQty=("QYT", "sum") if "QYT" in sales.columns else (("Qty", "sum") if "Qty" in sales.columns else ("Quantity", "sum")),
                AvgInvoice=("Amt", "mean"),
                LastInvoiceNo=("DocNum", "max"),
            )
        )
        # توحيد اسم العمود ونوعه بدقة
        sales_summary = sales_summary.rename(columns={sales_key: join_key})
        sales_summary[join_key] = sales_summary[join_key].astype(str).str.strip()

        # ----------------------------
        # Top Item
        # ----------------------------
        top_item = (
            sales.groupby([sales_key, "ItemDescription"], as_index=False)
            .agg(Sales=("Amt", "sum"))
            .sort_values([sales_key, "Sales"], ascending=[True, False])
            .drop_duplicates(sales_key)
            [[sales_key, "ItemDescription"]]
            .rename(columns={sales_key: join_key, "ItemDescription": "TopItem"})
        )
        top_item[join_key] = top_item[join_key].astype(str).str.strip()

        # ----------------------------
        # Top Item Group
        # ----------------------------
        group_field = "ItemGroup" if "ItemGroup" in sales.columns else ("Item_Group" if "Item_Group" in sales.columns else None)
        if group_field:
            top_group = (
                sales.groupby([sales_key, group_field], as_index=False)
                .agg(Sales=("Amt", "sum"))
                .sort_values([sales_key, "Sales"], ascending=[True, False])
                .drop_duplicates(sales_key)
                [[sales_key, group_field]]
                .rename(columns={sales_key: join_key, group_field: "TopGroup"})
            )
            top_group[join_key] = top_group[join_key].astype(str).str.strip()
        else:
            top_group = pd.DataFrame(columns=[join_key, "TopGroup"])

        # الاندماج الآمن الآن بعد تطابق الأنواع 100% كـ str
        df = df.merge(sales_summary, on=join_key, how="left")
        df = df.merge(top_item, on=join_key, how="left")
        df = df.merge(top_group, on=join_key, how="left")

    # =====================================================
    # CHECKS
    # =====================================================
    if not checks.empty:
        checks = checks.copy()
        checks_key = "Calc_Group_ID" if "Calc_Group_ID" in checks.columns else "ReferenceNumber"

        checks = checks.rename(
            columns={
                "Reference Number": "ReferenceNumber",
                "قيمة الشيك": "CheckAmount",
                "رقم الشيك": "CheckNumber",
                "تاريخ الاستحقاق": "DueDate",
            }
        )
        
        # تحويل مفتاح الربط في الشيكات لنصوص
        checks[checks_key] = checks[checks_key].astype(str).str.strip()

        chk_amt_col = "CheckAmount" if "CheckAmount" in checks.columns else ("Amount" if "Amount" in checks.columns else None)
        chk_num_col = "CheckNumber" if "CheckNumber" in checks.columns else ("DocNum" if "DocNum" in checks.columns else None)

        if chk_amt_col and chk_num_col:
            checks_summary = (
                checks.groupby(checks_key, as_index=False)
                .agg(
                    CheckAmount=(chk_amt_col, "sum"),
                    CheckNumber=(chk_num_col, "count"),
                )
            )
            checks_summary = checks_summary.rename(columns={checks_key: join_key})
            checks_summary[join_key] = checks_summary[join_key].astype(str).str.strip()

            df = df.merge(checks_summary, on=join_key, how="left")

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

    age_90_col = "Age_90_Plus" if "Age_90_Plus" in df.columns else ("90+" if "90+" in df.columns else None)
    overdue_col = "Overdue" if "Overdue" in df.columns else ("المستحق" if "المستحق" in df.columns else None)

    if age_90_col:
        df.loc[df[age_90_col] > 0, "CustomerScore"] -= 40

    if overdue_col:
        df.loc[df[overdue_col] > 0, "CustomerScore"] -= 20

    if "TotalSales" in df.columns:
        df.loc[df["TotalSales"] > 10000, "CustomerScore"] += 10

    df["CustomerScore"] = df["CustomerScore"].clip(0, 100)

    # =====================================================
    # Recommendation
    # =====================================================
    df["Recommendation"] = "🟢 عميل ممتاز"

    if age_90_col:
        df.loc[df[age_90_col] > 0, "Recommendation"] = "🔴 إيقاف البيع والمتابعة"

    if overdue_col and age_90_col:
        mask = (df[overdue_col] > 0) & (df[age_90_col] <= 0)
        df.loc[mask, "Recommendation"] = "🟡 متابعة التحصيل"

    return df