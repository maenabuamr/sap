import streamlit as st
import pandas as pd
from data_loader import load_sales
from core.sales_metrics import SalesMetrics
from core.sales_intelligence import SalesIntelligence

# ==========================================================
# إعدادات الصفحة
# ==========================================================
st.set_page_config(
    page_title="Sales Analytics",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Sales Analytics")

# ==========================================================
# تحميل البيانات وتنظيفها وتجهيز معرفات الكيانات
# ==========================================================
sales_raw = load_sales()

# تنظيف وتعبئة القيم المفقودة لضمان دقة العمليات الحسابية والتجميعية
sales_raw["CustomerName"] = sales_raw["CustomerName"].fillna("عميل غير معروف")
sales_raw["ReferenceNumber"] = sales_raw["ReferenceNumber"].astype(str).str.strip().fillna("-")

# بناء دالة المعرف الذكي لمعالجة استثناء الشرطة (-) لعدم دمج العملاء غير المرتبطين برقم مرجعي موحد
def create_calc_group_id(row):
    val = str(row["ReferenceNumber"]).strip()
    if val == "" or val == "-":
        return f"UNLINKED_{row['CustomerName']}"
    return val

# تطبيق المعرف الموحد على البيانات الخام مباشرة لضمان مطابقة الإحصائيات العلوية مع الجدول السفلي
sales_raw["Calc_Group_ID"] = sales_raw.apply(create_calc_group_id, axis=1)

# ==========================================================
# الفلاتر - القائمة الجانبية (Filters - Sidebar)
# ==========================================================
st.sidebar.header("🔍 Filters")

sales_filtered = sales_raw.copy()

# 1. فلتر السنة
years = ["الكل"] + sorted(sales_filtered["Year"].unique().tolist())
year = st.sidebar.selectbox("السنة", years)

if year != "الكل":
    sales_filtered = sales_filtered[sales_filtered["Year"] == year]

# 2. فلتر الشهر
months = ["الكل"] + sorted(sales_filtered["Month"].unique().tolist())
month = st.sidebar.selectbox("الشهر", months)

if month != "الكل":
    sales_filtered = sales_filtered[sales_filtered["Month"] == month]

# 3. فلتر المندوب (متعدد الاختيارات Multi-select)
salespersons_list = sorted(sales_filtered["Salesperson"].dropna().unique().tolist())
selected_sps = st.sidebar.multiselect("المندوبين", salespersons_list, default=[])

if selected_sps:
    sales_filtered = sales_filtered[sales_filtered["Salesperson"].isin(selected_sps)]

# 4. فلتر اسم العميل (CustomerName)
customer_col = "CustomerName"
if customer_col in sales_filtered.columns:
    customers_list = ["الكل"] + sorted(sales_filtered[customer_col].dropna().unique().tolist())
    selected_customer = st.sidebar.selectbox("اسم العميل", customers_list)
    
    if selected_customer != "الكل":
        sales_filtered = sales_filtered[sales_filtered[customer_col] == selected_customer]

# 5. فلتر مجموعة المواد (متعدد الاختيارات Multi-select)
item_group_col = "ItemGroup" if "ItemGroup" in sales_filtered.columns else ("Item_Group" if "Item_Group" in sales_filtered.columns else None)

if item_group_col:
    groups_list = sorted(sales_filtered[item_group_col].dropna().unique().tolist())
    selected_groups = st.sidebar.multiselect("مجموعات المواد", groups_list, default=[])
    
    if selected_groups:
        sales_filtered = sales_filtered[sales_filtered[item_group_col].isin(selected_groups)]

# 6. فلتر اسم المادة (متعدد الاختيارات Multi-select)
item_desc_col = "ItemDescription"
if item_desc_col in sales_filtered.columns:
    items_list = sorted(sales_filtered[item_desc_col].dropna().unique().tolist())
    selected_items = st.sidebar.multiselect("أسماء المواد", items_list, default=[])
    
    if selected_items:
        sales_filtered = sales_filtered[sales_filtered[item_desc_col].isin(selected_items)]


# تهيئة كلاس المقاييس والذكاء الاصطناعي بناءً على البيانات المفلترة للعمليات الجانبية
metrics = SalesMetrics(sales_filtered)
intel = SalesIntelligence(sales_filtered)

# ==========================================================
# AI Sales Insights
# ==========================================================
st.subheader("🤖 AI Sales Insights")

for line in intel.ai_summary():
    st.info(line)

st.divider()

# ==========================================================
# المؤشرات الرئيسية (KPIs) - السطر الأول المحدث
# ==========================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    total_sales_val = metrics.total_sales() if hasattr(metrics, 'total_sales') else 0.0
    st.metric("💰 إجمالي المبيعات", f"{total_sales_val:,.3f}")

with c2:
    invoices_count = 0
    if hasattr(metrics, 'invoices'):
        try:
            invoices_count = int(metrics.invoices())
        except Exception:
            invoices_count = len(metrics.invoices())
    st.metric("📄 عدد الفواتير", f"{invoices_count:,}")

with c3:
    qty_val = metrics.quantity() if hasattr(metrics, 'quantity') else 0.0
    st.metric("📦 الكمية", f"{qty_val:,.2f}")

with c4:
    # تعديل جوهري: حساب عدد الكيانات الحقيقية (المدمجة والمفصولة للشرطة) ليتطابق تماماً مع مجموع كروت التقرير
    true_customers_count = sales_filtered["Calc_Group_ID"].nunique()
    st.metric("👥 العملاء", f"{true_customers_count:,}")

st.divider()

# ==========================================================
# التقرير المتكامل القائم على حساب الكيانات والأرقام المرجعية
# ==========================================================
st.subheader("🔄 تقرير انتظام وقوة العملاء البيعية (Reference-Based Comprehensive Analytics)")

ref_col = "ReferenceNumber"

if ref_col in sales_raw.columns and "Month" in sales_filtered.columns:
    
    # 1. تحديد قاعدة البيانات المرجعية للسنة كاملة للشركة بدون تأثير الفلاتر العشوائية
    if year != "الكل":
        base_data_for_retention = sales_raw[sales_raw["Year"] == year]
    else:
        base_data_for_retention = sales_raw
        
    total_available_months = base_data_for_retention["Month"].nunique()
    if total_available_months == 0:
        total_available_months = 1
        
    # 2. حساب عدد الشهور النشطة وعلاقة الولاء بناءً على المعرف الحامي للشرطة (Calc_Group_ID)
    global_customer_months = base_data_for_retention.groupby("Calc_Group_ID").agg(
        True_Active_Months=("Month", "nunique"),
        Customer_Display_Name=("CustomerName", "first"),
        Actual_Ref_Num=(ref_col, "first")
    ).reset_index()

    # 3. تحديد الأعمدة المالية وأرقام الفواتير بشكل ديناميكي ذكي
    sales_col = "Amt" if "Amt" in sales_filtered.columns else ("Sales" if "Sales" in sales_filtered.columns else "LineTotal")
    invoice_id_col = "DocNum" if "DocNum" in sales_filtered.columns else ("InvoiceID" if "InvoiceID" in sales_filtered.columns else "Month")

    # 4. حساب المقاييس المالية المفلترة مجمعة أيضاً حسب المعرف الجديد
    filtered_customer_perf = sales_filtered.groupby("Calc_Group_ID").agg(
        Total_Sales_Amount=(sales_col, "sum"),
        Total_Invoices_Count=(invoice_id_col, "nunique")
    ).reset_index()
    
    # 5. الدمج الكامل بين جدول الولاء التراكمي للرقم المرجعي والأداء المالي الحالي
    customer_summary = pd.merge(filtered_customer_perf, global_customer_months, on="Calc_Group_ID", how="left")
    
    # 6. حساب العمليات الحسابية ونسب الانتظام للكيان الموحد
    customer_summary["الانتظام"] = (customer_summary["True_Active_Months"] / total_available_months * 100).round(0)
    customer_summary["الأشهر"] = customer_summary["True_Active_Months"].astype(str) + f"/{total_available_months}"
    customer_summary["متوسط الفاتورة"] = customer_summary["Total_Sales_Amount"] / customer_summary["Total_Invoices_Count"]
    
    # 7. دالة التصنيف الملون المعتمد على الـ Calc_Group_ID الموحد
    def assign_classification(row):
        pct = row["الانتظام"]
        months = row["True_Active_Months"]
        
        if pct >= 90 or months == total_available_months:
            return "Loyal 🟢"
        elif pct >= 70:
            return "Very Active 🟡"
        elif months == 1:
            return "One-Time 🔴"
        else:
            return "Regular 🔵"
            
    customer_summary["التصنيف"] = customer_summary.apply(assign_classification, axis=1)
    
    # 8. الترتيب حسب عدد الشهور النشطة أولاً ثم الأعلى مبيعات ليعطي الأولوية لانتظام العميل وعمقه البيعي
    customer_summary_sorted = customer_summary.sort_values(by=["True_Active_Months", "Total_Sales_Amount"], ascending=[False, False])
    
    # 9. صياغة الجدول النهائي بالتصميم والترتيب والمسميات المطلوبة تماماً
    final_table = pd.DataFrame({
        "الرقم المرجعي": customer_summary_sorted["Actual_Ref_Num"],
        "العميل": customer_summary_sorted["Customer_Display_Name"],
        "الأشهر": customer_summary_sorted["الأشهر"],
        "الانتظام": customer_summary_sorted["الانتظام"].astype(int).astype(str) + "%",
        "المبيعات": customer_summary_sorted["Total_Sales_Amount"].map("{:,.3f}".format),
        "الفواتير": customer_summary_sorted["Total_Invoices_Count"].astype(int),
        "متوسط الفاتورة": customer_summary_sorted["متوسط الفاتورة"].map("{:,.3f}".format),
        "التصنيف": customer_summary_sorted["التصنيف"]
    })
    
    # كروت الملخص المدمجة أسفل العنوان ومطابقتها التامة للواقع
    summary_counts = customer_summary_sorted["التصنيف"].value_counts()
    c_loyal, c_vactive, c_reg, c_onetime = st.columns(4)
    c_loyal.metric("Loyal 🟢", f"{summary_counts.get('Loyal 🟢', 0)} كيان")
    c_vactive.metric("Very Active 🟡", f"{summary_counts.get('Very Active 🟡', 0)} كيان")
    c_reg.metric("Regular 🔵", f"{summary_counts.get('Regular 🔵', 0)} كيان")
    c_onetime.metric("One-Time 🔴", f"{summary_counts.get('One-Time 🔴', 0)} كيان")
    
    st.write("")
    
    st.dataframe(
        final_table,
        use_container_width=True,
        hide_index=True
    )

else:
    st.error(f"تأكد من وجود عمود '{ref_col}' و 'Month' في ملف البيانات لتشغيل التقرير المدمج الاستثنائي.")

st.divider()
st.caption("ERP AI Analytics | Sales Dashboard V1")