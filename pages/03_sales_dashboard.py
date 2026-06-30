import streamlit as st
import pandas as pd
from data_loader import load_sales
from core.sales_metrics import SalesMetrics
from core.sales_intelligence import SalesIntelligence

# إعدادات الصفحة
st.set_page_config(page_title="Sales Analytics", page_icon="📈", layout="wide")
st.title("📈 Sales Analytics")

# تحميل البيانات وتجهيزها
sales_raw = load_sales()
sales_raw["CustomerName"] = sales_raw["CustomerName"].fillna("عميل غير معروف")
sales_raw["ReferenceNumber"] = sales_raw["ReferenceNumber"].astype(str).str.strip().fillna("-")

def create_calc_group_id(row):
    val = str(row["ReferenceNumber"]).strip()
    if val == "" or val == "-":
        return f"UNLINKED_{row['CustomerName']}"
    return val

sales_raw["Calc_Group_ID"] = sales_raw.apply(create_calc_group_id, axis=1)

# الفلاتر
st.sidebar.header("🔍 Filters")
sales_filtered = sales_raw.copy()

year = st.sidebar.selectbox("السنة", ["الكل"] + sorted(sales_raw["Year"].unique().tolist()))
if year != "الكل": sales_filtered = sales_filtered[sales_filtered["Year"] == year]

month = st.sidebar.selectbox("الشهر", ["الكل"] + sorted(sales_filtered["Month"].unique().tolist()))
if month != "الكل": sales_filtered = sales_filtered[sales_filtered["Month"] == month]

# إضافة فلتر نوع الحركة (DocType)
if "DocType" in sales_filtered.columns:
    doctype_list = sorted(sales_filtered["DocType"].dropna().unique().tolist())
    selected_doctype = st.sidebar.multiselect("نوع الحركة", doctype_list)
    if selected_doctype: sales_filtered = sales_filtered[sales_filtered["DocType"].isin(selected_doctype)]

# إضافة فلتر العملاء
customers_list = sorted(sales_filtered["CustomerName"].unique().tolist())
selected_customers = st.sidebar.multiselect("العملاء", customers_list)
if selected_customers: sales_filtered = sales_filtered[sales_filtered["CustomerName"].isin(selected_customers)]

selected_sps = st.sidebar.multiselect("المندوبين", sorted(sales_filtered["Salesperson"].dropna().unique().tolist()))
if selected_sps: sales_filtered = sales_filtered[sales_filtered["Salesperson"].isin(selected_sps)]

item_group_col = "ItemGroup" if "ItemGroup" in sales_filtered.columns else "Item_Group"
groups_list = sorted(sales_filtered[item_group_col].dropna().unique().tolist()) if item_group_col in sales_filtered.columns else []
selected_groups = st.sidebar.multiselect("مجموعات المواد", groups_list)
if selected_groups: sales_filtered = sales_filtered[sales_filtered[item_group_col].isin(selected_groups)]

item_desc_col = "ItemDescription"
items_list = sorted(sales_filtered[item_desc_col].dropna().unique().tolist()) if item_desc_col in sales_filtered.columns else []
selected_items = st.sidebar.multiselect("أسماء المواد", items_list)
if selected_items: sales_filtered = sales_filtered[sales_filtered[item_desc_col].isin(selected_items)]

# تهيئة الكلاسات
metrics = SalesMetrics(sales_filtered)
intel = SalesIntelligence(sales_filtered)

# Insights
st.subheader("🤖 AI Sales Insights")
for line in intel.ai_summary(): st.info(line)
st.divider()

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 إجمالي المبيعات", f"{metrics.total_sales():,.3f}")

inv_data = metrics.invoices()
inv_count = len(inv_data) if hasattr(inv_data, '__len__') and not isinstance(inv_data, int) else (inv_data if isinstance(inv_data, int) else 0)
c2.metric("📄 عدد الفواتير", f"{inv_count:,}")

c3.metric("📦 الكمية", f"{metrics.quantity():,.2f}")
c4.metric("👥 العملاء", f"{sales_filtered['Calc_Group_ID'].nunique():,}")

st.divider()

# حساب بيانات الولاء للجميع
base = sales_raw[sales_raw["Year"] == year] if year != "الكل" else sales_raw
total_months = base["Month"].nunique() or 1
summary = sales_filtered.groupby("Calc_Group_ID").agg(
    True_Active=("Month", "nunique"),
    Name=("CustomerName", "first")
).reset_index()
summary["الانتظام"] = (summary["True_Active"] / total_months * 100).round(0)
summary["التصنيف"] = summary.apply(lambda x: "Loyal 🟢" if x["الانتظام"]>=90 else ("Very Active 🟡" if x["الانتظام"]>=70 else ("One-Time 🔴" if x["True_Active"]==1 else "Regular 🔵")), axis=1)

# إضافة الملخص التفاعلي للعملاء
st.subheader("📊 ملخص تصنيف العملاء")
c_l, c_va, c_r, c_ot = st.columns(4)
stats = summary["التصنيف"].value_counts()
c_l.metric("Loyal 🟢", stats.get("Loyal 🟢", 0))
c_va.metric("Very Active 🟡", stats.get("Very Active 🟡", 0))
c_r.metric("Regular 🔵", stats.get("Regular 🔵", 0))
c_ot.metric("One-Time 🔴", stats.get("One-Time 🔴", 0))
st.divider()

# 1. التقرير التفصيلي
if len(selected_customers) > 0 or len(selected_items) > 0 or len(selected_groups) > 0:
    st.subheader("🔍 كشف مشتريات المواد التفصيلي")
    sales_col = "Amt" if "Amt" in sales_filtered.columns else "Sales"
    possible_qty_cols = ["QYT", "Qty", "Quantity", "QuantityOrdered", "OrderedQty"]
    qty_col = next((col for col in possible_qty_cols if col in sales_filtered.columns), None)
    
    agg_dict = {sales_col: "sum"}
    if qty_col: 
        agg_dict[qty_col] = "sum"
    
    drilldown = sales_filtered.groupby(["Calc_Group_ID", "CustomerName", item_desc_col]).agg(agg_dict).reset_index()
    
    drilldown = drilldown.merge(summary[["Calc_Group_ID", "التصنيف"]], on="Calc_Group_ID", how="left")
    
    rename_dict = {"CustomerName": "العميل", item_desc_col: "المادة", "التصنيف": "تصنيف الولاء"}
    if qty_col: rename_dict[qty_col] = "الكمية"
    rename_dict[sales_col] = "القيمة"
    
    drilldown = drilldown.rename(columns=rename_dict)
    
    # التنسيق
    if "الكمية" in drilldown.columns: drilldown["الكمية"] = drilldown["الكمية"].map("{:,.2f}".format)
    drilldown["القيمة"] = drilldown["القيمة"].map("{:,.3f}".format)
    
    cols_order = [c for c in ["العميل", "المادة", "الكمية", "القيمة", "تصنيف الولاء"] if c in drilldown.columns]
    st.dataframe(drilldown[cols_order], use_container_width=True, hide_index=True)
    st.divider()

# 2. تقرير الولاء العام
st.subheader("🔄 تقرير انتظام وقوة العملاء البيعية")
sales_col = "Amt" if "Amt" in sales_filtered.columns else "Sales"

summary_table = sales_filtered.groupby("Calc_Group_ID").agg(
    Total_Sales=(sales_col, "sum"),
    Total_Invoices=("DocNum", "nunique"),
    True_Active=("Month", "nunique"),
    Name=("CustomerName", "first")
).reset_index()

summary_table["الانتظام"] = (summary_table["True_Active"] / total_months * 100).round(0)
summary_table["التصنيف"] = summary_table.apply(lambda x: "Loyal 🟢" if x["الانتظام"]>=90 else ("Very Active 🟡" if x["الانتظام"]>=70 else ("One-Time 🔴" if x["True_Active"]==1 else "Regular 🔵")), axis=1)

final_table = pd.DataFrame({
    "العميل": summary_table["Name"], 
    "الأشهر": summary_table["True_Active"].astype(str) + f"/{total_months}",
    "الانتظام": summary_table["الانتظام"].astype(str) + "%", 
    "المبيعات": summary_table["Total_Sales"].map("{:,.3f}".format),
    "التصنيف": summary_table["التصنيف"]
})
st.dataframe(final_table, use_container_width=True, hide_index=True)

st.caption("ERP AI Analytics | Sales Dashboard V1")