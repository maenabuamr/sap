import streamlit as st
import pandas as pd
from utils import display_header
from data_loader import load_sales, load_aging
from core.sales_metrics import SalesMetrics
from core.sales_intelligence import SalesIntelligence

# استدعاء الترويسة الثابتة
display_header()

# ==========================================================
# ملاحظة: تم إزالة st.set_page_config لأنها موجودة في app.py
# ==========================================================
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

# ==========================================================
# 💳 ملخص التزام العملاء بالدفع
# ==========================================================
st.divider()
st.subheader("💳 ملخص التزام العملاء بالدفع")
st.caption("تصنيف العملاء حسب التزامهم بالسداد — مربوط بـ ReferenceNumber الموحد")

@st.cache_data
def get_payment_compliance():
    try:
        from data_loader import load_aging
    except ImportError:
        import sys
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        from data_loader import load_aging
    
    try:
        from engine.mapper import map_aging_columns
        from engine.credit_risk import classify_risk
    except ImportError:
        import sys
        if '.' not in sys.path:
            sys.path.insert(0, '.')
        from engine.mapper import map_aging_columns
        from engine.credit_risk import classify_risk
    
    aging = load_aging()
    
    name_col = next((c for c in aging.columns if "اسم العميل" in str(c) or "CustomerName" in str(c) or "CardName" in str(c)), None)
    
    if name_col:
        aging[name_col] = aging[name_col].fillna("غير معروف")
    
    # ✅ ReferenceNumber هو الرقم الموحد بين الشركتين (per user instruction)
    ref_col = None
    for c in aging.columns:
        cn = str(c).strip()
        if cn == "Reference Number" or cn == "ReferenceNumber" or "ReferenceNumber" in cn:
            ref_col = c
            break
    
    if ref_col:
        aging["RefCode"] = aging[ref_col].astype(str).str.strip().fillna("-")
        # UNLINKED fallback للعملاء بدون ReferenceNumber
        if name_col and name_col in aging.columns:
            mask = aging["RefCode"].isin(["", "-", "nan", "None"])
            if mask.any():
                aging.loc[mask, "RefCode"] = "UNLINKED_" + aging.loc[mask, name_col].astype(str)
    elif name_col:
        aging["RefCode"] = aging[name_col]
    else:
        aging["RefCode"] = aging.index.astype(str)
    
    aging = map_aging_columns(aging)
    aging = classify_risk(aging)
    return aging

aging_with_risk = get_payment_compliance()

with st.expander("🔧 التشخيص"):
    st.write(f"عدد الصفوف: {len(aging_with_risk)}")
    if "RefCode" in aging_with_risk.columns:
        n_unique = aging_with_risk["RefCode"].nunique()
        st.write(f"عدد العملاء (RefCode): {n_unique}")
        st.write(f"عينة RefCode من aging: {aging_with_risk['RefCode'].head(5).tolist()}")
        unlinked = aging_with_risk[aging_with_risk['RefCode'].str.startswith('UNLINKED_', na=False)]
        st.write(f"UNLINKED (بدون ReferenceNumber): {len(unlinked)} صف")
    if "Risk" in aging_with_risk.columns:
        st.write(f"توزيع المخاطر:\n{aging_with_risk['Risk'].value_counts().to_string()}")
    if "summary" in dir() and isinstance(summary, pd.DataFrame):
        st.write(f"\\nSummary columns: {list(summary.columns)}")
        if "Calc_Group_ID" in summary.columns:
            st.write(f"Summary Calc_Group_ID samples: {summary['Calc_Group_ID'].astype(str).head(5).tolist()}")

if "RefCode" in aging_with_risk.columns and "Risk" in aging_with_risk.columns:
    def aggregate_worst(grp):
        worst_idx = grp["Priority"].idxmin() if "Priority" in grp.columns else 0
        return pd.Series({"Risk": grp.loc[worst_idx, "Risk"]})
    
    # ✅ تجميع حسب RefCode (= ReferenceNumber الموحد)
    customer_risk = aging_with_risk.groupby("RefCode").apply(aggregate_worst).reset_index()
    
    # اسم العميل للعرض
    if "CustomerName" in aging_with_risk.columns:
        first_names = aging_with_risk.groupby("RefCode")["CustomerName"].first().reset_index()
        customer_risk = customer_risk.merge(first_names, on="RefCode", how="left")
    
    risk_label_map = {
        "🟢 منخفض": "ملتزم 🟢",
        "🟡 متوسط": "متوسط 🟡",
        "🔴 مرتفع": "متعثر 🔴",
        "⚪ ضمن فترة السداد": "ضمن السداد ⚪",
    }
    customer_risk["تصنيف الالتزام"] = customer_risk["Risk"].map(risk_label_map).fillna(customer_risk["Risk"])
    
    cp1, cp2, cp3, cp4 = st.columns(4)
    risk_counts = customer_risk["تصنيف الالتزام"].value_counts()
    cp1.metric("ملتزم 🟢", risk_counts.get("ملتزم 🟢", 0))
    cp2.metric("متوسط 🟡", risk_counts.get("متوسط 🟡", 0))
    cp3.metric("ضمن السداد ⚪", risk_counts.get("ضمن السداد ⚪", 0))
    cp4.metric("متعثر 🔴", risk_counts.get("متعثر 🔴", 0))
    
    st.divider()
    st.subheader("🔗 التصنيفين معاً: الولاء + الالتزام")
    
    if "summary" in dir() and isinstance(summary, pd.DataFrame):
        # ✅ الربط الأساسي: Calc_Group_ID ↔ RefCode (= ReferenceNumber)
        if "Calc_Group_ID" in summary.columns:
            summary["_key"] = summary["Calc_Group_ID"].astype(str).str.strip()
            customer_risk["_key"] = customer_risk["RefCode"].astype(str).str.strip()
            shared = set(summary["_key"].dropna()) & set(customer_risk["_key"].dropna())
            
            if shared:
                combined = summary.merge(
                    customer_risk[["_key", "تصنيف الالتزام"]],
                    on="_key",
                    how="left"
                )
                combined.drop(columns=["_key"], inplace=True, errors="ignore")
                st.caption(f"✅ Link by ReferenceNumber: {len(shared)} matches")
                
                # Fallback: للـ UNLINKED_ entries، نربط بالاسم
                unlinked_keys = customer_risk[customer_risk["RefCode"].str.startswith("UNLINKED_", na=False)]
                if not unlinked_keys.empty and "CustomerName" in unlinked_keys.columns:
                    name_col_summary = "Name" if "Name" in summary.columns else None
                    if name_col_summary:
                        # Normalize names for fallback
                        def normalize_arabic(s):
                            if pd.isna(s): return ""
                            s = str(s).strip().lower()
                            s = s.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
                            s = s.replace('ة', 'ه').replace('ى', 'ي')
                            return ' '.join(s.split())
                        
                        unlinked_keys = unlinked_keys.copy()
                        unlinked_keys["_norm"] = unlinked_keys["CustomerName"].apply(normalize_arabic)
                        combined["_norm"] = combined[name_col_summary].apply(normalize_arabic)
                        
                        name_map = dict(zip(unlinked_keys["_norm"], unlinked_keys["تصنيف الالتزام"]))
                        combined["_name_match"] = combined["_norm"].map(name_map)
                        # Fill NaN values for payment classification
                        combined["تصنيف الالتزام"] = combined["تصنيف الالتزام"].fillna(combined["_name_match"])
                        combined.drop(columns=["_norm", "_name_match"], inplace=True, errors="ignore")
                
                combined["تصنيف الالتزام"] = combined["تصنيف الالتزام"].fillna("—")
                
                if "Name" in combined.columns:
                    combined_display = pd.DataFrame({
                        "العميل": combined["Name"],
                        "الأشهر النشطة": combined["True_Active"].astype(str) + f"/{total_months}" if "True_Active" in combined.columns else "—",
                        "الانتظام %": combined["الانتظام"].astype(str) + "%" if "الانتظام" in combined.columns else "—",
                        "تصنيف الولاء": combined["التصنيف"] if "التصنيف" in combined.columns else "—",
                        "تصنيف الالتزام": combined["تصنيف الالتزام"],
                    })
                    st.dataframe(combined_display, use_container_width=True, hide_index=True)
                else:
                    st.dataframe(combined.head(20), use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ ما في ReferenceNumber مشترك")
                with st.expander("🔍 قارن المفاتيح"):
                    st.write("Summary Calc_Group_ID samples:", sorted(set(summary["Calc_Group_ID"].astype(str)))[:10])
                    st.write("Aging RefCode samples:", sorted(set(customer_risk["RefCode"]))[:10])
        else:
            st.warning("⚠️ ما في Calc_Group_ID في summary")
    else:
        st.warning("ما في summary dataframe")
else:
    st.warning("⚠️ ما في RefCode أو Risk")
