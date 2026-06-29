"""
ERP AI Analytics
Unified Schema
"""

# ==========================================
# Customer
# ==========================================

REFERENCE = "ReferenceNumber"
CUSTOMER_CODE = "CustomerCode"
CUSTOMER_NAME = "CustomerName"
SALESPERSON = "Salesperson"

# ==========================================
# Sales
# ==========================================

SALES = "TotalSales"
QTY = "TotalQty"
INVOICES = "InvoiceCount"

# ==========================================
# Credit
# ==========================================

CURRENT_BALANCE = "CurrentBalance"
DUE_BALANCE = "DueBalance"
NOT_DUE = "NotDue"
OVERDUE = "Overdue"

# ==========================================
# Aging
# ==========================================

AGE_0_15 = "Age_0_15"
AGE_16_30 = "Age_16_30"
AGE_31_45 = "Age_31_45"
AGE_46_60 = "Age_46_60"
AGE_61_75 = "Age_61_75"
AGE_76_90 = "Age_76_90"
AGE_90 = "Age_90_Plus"

# ==========================================
# Checks
# ==========================================

CHECK_COUNT = "CheckNumber"
CHECK_VALUE = "CheckAmount"

# ==========================================
# Risk
# ==========================================

RISK = "Risk"
PRIORITY = "Priority"

# ==========================================
# Dates
# ==========================================

YEAR = "Year"
MONTH = "Month"

# ==========================================
# Items
# ==========================================

ITEM = "ItemDescription"
ITEM_CODE = "ItemCode"
ITEM_GROUP = "ItemGroup"