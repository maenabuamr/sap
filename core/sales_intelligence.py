import pandas as pd

class SalesIntelligence:

    def __init__(self, sales: pd.DataFrame):
        self.df = sales.copy()

    # ======================================================
    # Month Growth
    # ======================================================
    def month_growth(self):
        if self.df.empty:
            return None

        # التأكد من وجود أعمدة التاريخ والمبيعات
        if "Year" not in self.df.columns or "Month" not in self.df.columns or "Amt" not in self.df.columns:
            return None

        monthly = (
            self.df
            .groupby(["Year", "Month"], as_index=False)
            .agg(Sales=("Amt", "sum"))
            .sort_values(["Year", "Month"])
        )

        if len(monthly) < 2:
            return None

        current = monthly.iloc[-1]["Sales"]
        previous = monthly.iloc[-2]["Sales"]

        if previous == 0:
            growth = 0
        else:
            growth = ((current - previous) / previous) * 100

        return {
            "current": current,
            "previous": previous,
            "growth": growth
        }

    # ======================================================
    # Top Salesperson
    # ======================================================
    def top_salesperson(self):
        if self.df.empty or "Salesperson" not in self.df.columns:
            return None

        result = (
            self.df.groupby("Salesperson", as_index=False)
            .agg(Sales=("Amt", "sum"))
            .sort_values("Sales", ascending=False)
        )
        
        return result.iloc[0] if not result.empty else None

    # ======================================================
    # Top Customer
    # ======================================================
    def top_customer(self):
        if self.df.empty or "CustomerName" not in self.df.columns:
            return None

        # تحديد الأعمدة المتاحة للمجموعات لتفادي خطأ عدم وجود ReferenceNumber
        groupby_cols = ["CustomerName"]
        if "ReferenceNumber" in self.df.columns:
            groupby_cols.insert(0, "ReferenceNumber")

        result = (
            self.df.groupby(groupby_cols, as_index=False)
            .agg(Sales=("Amt", "sum"))
            .sort_values("Sales", ascending=False)
        )
        
        return result.iloc[0] if not result.empty else None

    # ======================================================
    # Top Item Group
    # ======================================================
    def top_group(self):
        if self.df.empty:
            return None

        # مرونة في فحص اسم العمود للمجموعات
        group_col = "ItemGroup" if "ItemGroup" in self.df.columns else ("Item_Group" if "Item_Group" in self.df.columns else None)
        
        if not group_col:
            return None

        result = (
            self.df.groupby(group_col, as_index=False)
            .agg(Sales=("Amt", "sum"))
            .sort_values("Sales", ascending=False)
        )
        
        return result.iloc[0] if not result.empty else None

    # ======================================================
    # Top Item
    # ======================================================
    def top_item(self):
        if self.df.empty or "ItemDescription" not in self.df.columns:
            return None

        groupby_cols = ["ItemDescription"]
        if "ItemCode" in self.df.columns:
            groupby_cols.insert(0, "ItemCode")

        result = (
            self.df.groupby(groupby_cols, as_index=False)
            .agg(Sales=("Amt", "sum"))
            .sort_values("Sales", ascending=False)
        )
        
        return result.iloc[0] if not result.empty else None

    # ======================================================
    # Average Invoice
    # ======================================================
    def average_invoice(self):
        if self.df.empty or "Amt" not in self.df.columns:
            return 0
            
        # استخدام DocNum أو إحصاء السطور كبديل الفواتير الفريدة
        invoice_col = "DocNum" if "DocNum" in self.df.columns else None
        
        if invoice_col:
            invoices = self.df[invoice_col].nunique()
        else:
            invoices = len(self.df) # حماية في حال غياب عمود رقم الفاتورة

        if invoices == 0:
            return 0

        return self.df["Amt"].sum() / invoices

    # ======================================================
    # AI Summary
    # ======================================================
    def ai_summary(self):
        summary = []

        if self.df.empty:
            return ["لا توجد بيانات متاحة لتحليلها."]

        # 1. أفضل مندوب
        top_sp = self.top_salesperson()
        if top_sp is not None:
            summary.append(f"🏆 أفضل مندوب: {top_sp['Salesperson']} بمبيعات قيمتها {top_sp['Sales']:,.2f}")

        # 2. أفضل عميل
        top_cust = self.top_customer()
        if top_cust is not None:
            summary.append(f"👥 أفضل عميل: {top_cust['CustomerName']} بمشتريات قيمتها {top_cust['Sales']:,.2f}")

        # 3. أعلى مجموعة مواد
        top_grp = self.top_group()
        if top_grp is not None:
            # قراءة اسم الحقل ديناميكياً سواء كان ItemGroup أو Item_Group
            group_field = "ItemGroup" if "ItemGroup" in top_grp else "Item_Group"
            summary.append(f"📦 أعلى مجموعة: {top_grp[group_field]} بمبيعات قيمتها {top_grp['Sales']:,.2f}")

        # 4. متوسط الفاتورة
        summary.append(f"💵 متوسط الفاتورة: {self.average_invoice():,.3f}")

        return summary