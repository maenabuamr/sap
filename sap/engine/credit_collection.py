import pandas as pd


def build_collection_list(df: pd.DataFrame) -> pd.DataFrame:
    """
    تجهيز قائمة التحصيل اليومية المفلترة والموحدة.
    تضمن مطابقة أرقام المندوبين عبر التبويبات بنسبة 100%.
    """
    if df.empty:
        return df

    result = df.copy()

    # ==========================================
    # فحص وتوحيد مسميات الأعمدة لضمان التوافق (عربي / إنجليزي)
    # ==========================================
    age_90 = "Age_90_Plus" if "Age_90_Plus" in result.columns else ("90+" if "90+" in result.columns else None)
    age_76_90 = "Age_76_90" if "Age_76_90" in result.columns else None
    age_61_75 = "Age_61_75" if "Age_61_75" in result.columns else None
    
    due_balance = "DueBalance" if "DueBalance" in result.columns else ("المستحق" if "المستحق" in result.columns else ("Overdue" if "Overdue" in result.columns else None))
    curr_balance = "CurrentBalance" if "CurrentBalance" in result.columns else ("الرصيد الحالي" if "الرصيد الحالي" in result.columns else None)

    # ==========================================
    # 1. حساب مبلغ التحصيل (CollectionAmount) بناءً على الأعمدة المتاحة
    # ==========================================
    result["CollectionAmount"] = 0.0
    
    if age_61_75 and age_76_90 and age_90:
        result["CollectionAmount"] = (
            result[age_61_75].fillna(0)
            + result[age_76_90].fillna(0)
            + result[age_90].fillna(0)
        )
    elif age_90 and due_balance:
        result["CollectionAmount"] = result[due_balance].fillna(0)
    elif due_balance:
        result["CollectionAmount"] = result[due_balance].fillna(0)

    # ==========================================
    # 2. حالة الحساب (Account Status)
    # ==========================================
    def account_status(row):
        val_90 = row[age_90] if age_90 else 0
        val_76 = row[age_76_90] if age_76_90 else 0
        val_61 = row[age_61_75] if age_61_75 else 0
        val_due = row[due_balance] if due_balance else 0

        if val_90 > 0:
            return "🔴 متأخر أكثر من 90 يوم"
        elif val_76 > 0 or val_61 > 0:
            return "🟠 متأخر 61-90 يوم"
        elif val_due > 0:
            return "🟡 يوجد ذمم مستحقة"
        else:
            return "🟢 ضمن فترة السداد"

    result["Status"] = result.apply(account_status, axis=1)

    # ==========================================
    # 3. الإجراء المقترح (Action)
    # ==========================================
    def action(row):
        val_90 = row[age_90] if age_90 else 0
        val_76 = row[age_76_90] if age_76_90 else 0
        val_61 = row[age_61_75] if age_61_75 else 0
        val_due = row[due_balance] if due_balance else 0

        if val_90 > 0:
            return "📞 اتصال فوري"
        elif val_76 > 0 or val_61 > 0:
            return "☎ متابعة"
        elif val_due > 0:
            return "📅 متابعة لاحقاً"
        return "✅ لا يوجد"

    result["Action"] = result.apply(action, axis=1)

    # ==========================================
    # 4. التعديل الجوهري: تصفية واستبعاد الحسابات السليمة لمنع تضارب الأعداد
    # ==========================================
    # هنا يتم فقط الإبقاء على العملاء الذين يتطلبون إجراءات تحصيل فعلية
    result = result[result["Action"] != "✅ لا يوجد"].copy()

    # ==========================================
    # 5. ترتيب الأولوية والفرز
    # ==========================================
    # التحقق من وجود الأعمدة قبل محاولة الفرز لتفادي أخطاء الـ Key Error
    sort_by_columns = []
    ascending_rules = []

    if "Priority" in result.columns:
        sort_by_columns.append("Priority")
        ascending_rules.append(True)

    if age_90:
        sort_by_columns.append(age_90)
        ascending_rules.append(False)

    sort_by_columns.append("CollectionAmount")
    ascending_rules.append(False)

    if curr_balance:
        sort_by_columns.append(curr_balance)
        ascending_rules.append(False)

    if sort_by_columns:
        result = result.sort_values(by=sort_by_columns, ascending=ascending_rules)

    return result