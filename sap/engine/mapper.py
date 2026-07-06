import pandas as pd


AGING_COLUMN_MAP = {
    "Reference Number": "ReferenceNumber",
    "رقم العميل الشركة التجارية": "CustomerCode",
    "اسم العميل": "CustomerName",
    "اسم المندوب": "Salesperson",
    "فترة السداد": "PaymentTerm",
    "الرصيد الافتتاحي": "OpeningBalance",
    "حركات جارية": "Transactions",
    "الرصيد الحالي": "CurrentBalance",
    "رصيد متأخر": "Overdue",
    "رصيد غير مستحق": "NotDue",
    "0-15 يوم": "Age_0_15",
    "16-30 يوم": "Age_16_30",
    "31-45 يوم": "Age_31_45",
    "46-60 يوم": "Age_46_60",
    "61-75 يوم": "Age_61_75",
    "76-90 يوم": "Age_76_90",
    "اكثر من 90 يوم": "Age_90_Plus",
    "عدد الشيكات": "ChecksCount",
    "مجموع قيم الشيكات": "ChecksValue",
    "تواريخ الشيكات غير المستحقة": "ChecksDates",
}


def map_aging_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename aging report columns to internal project names.
    """
    df = df.copy()
    df.rename(columns=AGING_COLUMN_MAP, inplace=True)
    return df