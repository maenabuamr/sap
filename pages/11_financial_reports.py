import os
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="التقارير المالية", page_icon="💰", layout="wide")

st.title("💰 التقارير المالية")
st.caption("قائمة الدخل والذمم والمخزون - مفلترة بالسنة والشهر")

@st.cache_data
def load_sales():
    df = pd.read_csv(os.path.join('data', r'sales_customer.csv'))
    # Normalize columns
    df["Amt"] = pd.to_numeric(df["Amt"], errors="coerce").fillna(0)
    df["QYT"] = pd.to_numeric(df["QYT"], errors="coerce").fillna(0)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Month"] = pd.to_numeric(df["Month"], errors="coerce")
    return df

@st.cache_data
def load_aging():
    df = pd.read_csv(os.path.join('data', r'aging_report.csv'))
    for col in df.columns:
        cn = str(col)
        if any(kw in cn for kw in ["رصيد", "balance", "حركة"]):
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    return df

@st.cache_data
def load_production():
    return pd.read_csv(os.path.join('data', r'production_orders.csv'))

@st.cache_data
def load_inventory():
    return pd.read_csv(os.path.join('data', r'inventory.csv'))

@st.cache_data
def load_expenses():
    """Load expenses data"""
    df = pd.read_csv(os.path.join('data', r'expenses.csv'), encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    # Parse date
    df["Date"] = pd.to_datetime(df["التاريخ"], format="%m/%d/%Y", errors="coerce")
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Amount"] = pd.to_numeric(df["المبلغ"], errors="coerce").fillna(0)
    return df

sales_df = load_sales()
aging_df = load_aging()
production_df = load_production()
inventory_df = load_inventory()
expenses_df = load_expenses()

st.markdown("### الفلاتر")
fcol1, fcol2 = st.columns(2)
with fcol1:
    available_years = sorted(sales_df["Year"].dropna().unique().tolist(), reverse=True)
    selected_year = st.selectbox("السنة", available_years, index=0, key="fin_year")
with fcol2:
    month_names = ["يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو", "يوليو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "ديسمبر"]
    selected_month = st.selectbox("الشهر", ["الكل"] + month_names, index=0, key="fin_month")

st.divider()

# Filter sales
filtered_sales = sales_df[sales_df["Year"] == selected_year].copy()
if selected_month != "الكل":
    filtered_sales = filtered_sales[filtered_sales["Month"] == month_names.index(selected_month) + 1]

# Calculate P&L KPIs
# Revenue: positive Amt only (sales, not returns)
revenue_sales = filtered_sales[filtered_sales["Amt"] > 0]["Amt"].sum()
revenue_returns = filtered_sales[filtered_sales["Amt"] < 0]["Amt"].sum()  # negative
net_revenue = revenue_sales + revenue_returns

# COGS: sum of production cost in this period
prod_year = production_df[production_df["OrderDate"].astype(str).str.contains(str(int(selected_year)))]
if selected_month != "الكل":
    prod_filtered = prod_year[prod_year["OrderDate"].astype(str).str.contains(f"/{month_names.index(selected_month) + 1}/")]
else:
    prod_filtered = prod_year
cogs = prod_filtered["TotalProductionCost"].sum() if "TotalProductionCost" in prod_filtered.columns else 0

gross_profit = net_revenue - cogs
gross_margin = (gross_profit / net_revenue * 100) if net_revenue > 0 else 0

# AR total
ar_total = aging_df["الرصيد الحالي"].sum() if "الرصيد الحالي" in aging_df.columns else aging_df["CurrentBalance"].sum()

# KPIs
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("صافي المبيعات", f"{net_revenue:,.0f}")
k2.metric("تكلفة الإنتاج", f"{cogs:,.0f}")
k3.metric("الربح الإجمالي", f"{gross_profit:,.0f}")
k4.metric("هامش الربح", f"{gross_margin:.1f}%")
k5.metric("إجمالي الذمم", f"{ar_total:,.0f}")

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1- قائمة الدخل", "2- الذمم المدينة", "3- المخزون", "4- أكبر المدينين", "5- الاتجاه الشهري", "6- المصروفات"
])

with tab1:
    st.subheader("قائمة الدخل")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### الإيرادات")
        st.metric("إجمالي المبيعات", f"{revenue_sales:,.0f}")
        st.metric("مرتجعات", f"{revenue_returns:,.0f}")
        st.metric("صافي الإيرادات", f"{net_revenue:,.0f}")
        
        st.markdown("#### التكاليف")
        st.metric("تكلفة الإنتاج", f"{cogs:,.0f}")
        
        st.markdown("#### الربح")
        st.metric("الربح الإجمالي", f"{gross_profit:,.0f}", delta=f"{gross_margin:.1f}%")
    
    with col2:
        # Pie chart of cost vs revenue vs profit
        pl_data = pd.DataFrame({
            "Item": ["تكلفة الإنتاج", "الربح الإجمالي"],
            "Amount": [cogs, max(gross_profit, 0)]
        })
        if pl_data["Amount"].sum() > 0:
            fig = px.pie(pl_data, values="Amount", names="Item", title="توزيع الإيرادات",
                        color_discrete_sequence=["#ef553b", "#00cc96"], hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
    
    # Revenue by item group
    st.subheader("الإيرادات حسب مجموعة الأصناف")
    by_group = filtered_sales.groupby("ItemGroup")["Amt"].sum().reset_index().sort_values("Amt", ascending=False).head(10)
    if not by_group.empty:
        fig = px.bar(by_group, x="Amt", y="ItemGroup", orientation="h",
                    color="Amt", color_continuous_scale="Greens")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(by_group, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("تقرير الذمم المدينة (AR Aging)")
    
    # Find bucket columns
    bucket_cols = [c for c in aging_df.columns if any(kw in c for kw in ["يوم", "يوم)"])]
    if not bucket_cols:
        bucket_cols = [c for c in aging_df.columns if "يوم" in str(c)]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if "الرصيد الحالي" in aging_df.columns:
        current = aging_df["الرصيد الحالي"].sum()
    else:
        current = 0
    
    col1.metric("إجمالي الذمم", f"{current:,.0f}")
    
    # Try to get bucket sums
    bucket_data = {}
    for col in bucket_cols:
        bucket_data[col] = aging_df[col].sum() if col in aging_df.columns else 0
    
    if bucket_data:
        bucket_df = pd.DataFrame(list(bucket_data.items()), columns=["Bucket", "Amount"])
        bucket_df = bucket_df[bucket_df["Amount"] > 0]
        
        col2, col3, col4 = st.columns(3)
        if len(bucket_df) >= 3:
            col2.metric(bucket_df.iloc[0]["Bucket"], f"{bucket_df.iloc[0]['Amount']:,.0f}")
            col3.metric(bucket_df.iloc[1]["Bucket"], f"{bucket_df.iloc[1]['Amount']:,.0f}")
            col4.metric(bucket_df.iloc[2]["Bucket"], f"{bucket_df.iloc[2]['Amount']:,.0f}")
        
        if not bucket_df.empty:
            fig = px.bar(bucket_df, x="Bucket", y="Amount", color="Amount",
                        color_continuous_scale="Reds", title="توزيع الذمم حسب الأعمار")
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("تقييم المخزون")
    
    if not inventory_df.empty:
        # Find value column
        value_cols = [c for c in inventory_df.columns if any(kw in c.lower() for kw in ["value", "price", "cost", "قيمة", "سعر"])]
        qty_cols = [c for c in inventory_df.columns if any(kw in c.lower() for kw in ["qty", "quantity", "كمية", "stock"])]
        
        st.info(f"عدد الأصناف: {len(inventory_df)}")
        
        if value_cols and qty_cols:
            value_col = value_cols[0]
            qty_col = qty_cols[0]
            inventory_df["TotalValue"] = pd.to_numeric(inventory_df[qty_col], errors="coerce").fillna(0) * pd.to_numeric(inventory_df[value_col], errors="coerce").fillna(0)
            total_value = inventory_df["TotalValue"].sum()
            
            st.metric("إجمالي قيمة المخزون", f"{total_value:,.0f}")
            
            top_items = inventory_df.nlargest(20, "TotalValue")[["ItemCode", "ItemName", qty_col, value_col, "TotalValue"]].copy()
            st.dataframe(top_items, use_container_width=True, hide_index=True)
        else:
            st.warning("ما في أعمدة قيمة أو كمية في المخزون")
            st.dataframe(inventory_df.head(20), use_container_width=True, hide_index=True)
    else:
        st.warning("لا توجد بيانات مخزون")

with tab4:
    st.subheader("أكبر المدينين")
    
    name_col = next((c for c in aging_df.columns if "اسم العميل" in str(c) or "CustomerName" in str(c)), None)
    balance_col = "الرصيد الحالي" if "الرصيد الحالي" in aging_df.columns else None
    
    if name_col and balance_col:
        top_debtors = aging_df.nlargest(20, balance_col)[[name_col, balance_col, "رصيد متأخر"]].copy()
        top_debtors.columns = ["العميل", "الرصيد", "متأخر"]
        top_debtors["نسبة التأخير"] = (top_debtors["متأخر"] / top_debtors["الرصيد"] * 100).round(1)
        top_debtors = top_debtors[top_debtors["الرصيد"] > 0]
        
        fig = px.bar(top_debtors.head(15), x="الرصيد", y="العميل", orientation="h",
                    color="نسبة التأخير", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(top_debtors, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("الاتجاه الشهري")
    
    monthly_sales = sales_df.groupby(["Year", "Month"])["Amt"].sum().reset_index()
    monthly_sales = monthly_sales[monthly_sales["Amt"] > 0]  # only sales, not returns
    
    # Filter to selected year
    monthly_year = monthly_sales[monthly_sales["Year"] == selected_year].copy()
    monthly_year["MonthName"] = monthly_year["Month"].apply(
        lambda m: month_names[int(m)-1] if pd.notna(m) else "Unknown"
    )
    
    if not monthly_year.empty:
        fig = px.line(monthly_year, x="MonthName", y="Amt", markers=True,
                     title=f"المبيعات الشهرية {int(selected_year)}")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(monthly_year[["MonthName", "Amt"]], use_container_width=True, hide_index=True)
    
    # Compare with previous year
    prev_year = selected_year - 1 if isinstance(selected_year, (int, float)) else None
    if prev_year:
        prev_data = monthly_sales[monthly_sales["Year"] == prev_year].copy()
        prev_data["MonthName"] = prev_data["Month"].apply(
            lambda m: month_names[int(m)-1] if pd.notna(m) else "Unknown"
        )
        if not prev_data.empty:
            prev_data["Year"] = int(prev_year)
            monthly_year["Year"] = int(selected_year)
            combined = pd.concat([monthly_year, prev_data])
            fig2 = px.line(combined, x="MonthName", y="Amt", color="Year",
                          markers=True, title=f"مقارنة {int(prev_year)} vs {int(selected_year)}")
            st.plotly_chart(fig2, use_container_width=True)

with tab6:
    st.subheader("تقرير المصروفات")
    if expenses_df.empty:
        st.warning("لا توجد بيانات مصروفات")
    else:
        # فلاتر خاصة
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            companies = sorted(expenses_df["الشركة"].dropna().unique().tolist())
            sel_company = st.multiselect("الشركة:", companies, default=companies, key="exp_co")
        with fcol2:
            exp_years = sorted(expenses_df["Year"].dropna().unique().tolist(), reverse=True)
            sel_exp_year = st.selectbox("السنة:", exp_years, index=0, key="exp_yr")
        with fcol3:
            exp_months_list = ["الكل"] + month_names
            sel_exp_month = st.selectbox("الشهر:", exp_months_list, index=0, key="exp_mo")
        with fcol4:
            exp_accounts = sorted(expenses_df["اسم الحساب"].dropna().unique().tolist())
            sel_exp_types = st.multiselect("نوع المصروف (اسم الحساب):", exp_accounts, default=exp_accounts, key="exp_ac")

        # تطبيق الفلاتر
        exp_filtered = expenses_df[expenses_df["الشركة"].isin(sel_company)].copy()
        exp_filtered = exp_filtered[exp_filtered["Year"] == sel_exp_year].copy()
        if sel_exp_month != "الكل":
            exp_filtered = exp_filtered[exp_filtered["Month"] == month_names.index(sel_exp_month) + 1]
        if sel_exp_accounts:
            exp_filtered = exp_filtered[exp_filtered["اسم الحساب"].isin(sel_exp_accounts)]

        if exp_filtered.empty:
            st.warning("لا توجد بيانات للفترة المختارة")
        else:
            # KPIs
            total_exp = exp_filtered["Amount"].sum()
            count_exp = len(exp_filtered)
            avg_exp = total_exp / count_exp if count_exp > 0 else 0
            top_exp = exp_filtered.nlargest(1, "Amount")
            top_amount = top_exp["Amount"].iloc[0] if not top_exp.empty else 0

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("اجمالي المصروفات", f"{total_exp:,.2f}")
            k2.metric("عدد السجلات", f"{count_exp:,}")
            k3.metric("متوسط المصروف", f"{avg_exp:,.2f}")
            k4.metric("اكبر مصروف", f"{top_amount:,.2f}")

            st.divider()

            # Top 10 حسابات
            st.subheader("أعلى 10 حسابات مصروف")
            by_account = exp_filtered.groupby(["رقم الحساب", "اسم الحساب"]).agg(
                Total=("Amount", "sum"),
                Count=("Amount", "count"),
            ).reset_index().sort_values("Total", ascending=False).head(10)
            by_account["Total"] = by_account["Total"].round(2)
            fig1 = px.bar(by_account, x="Total", y="اسم الحساب", orientation="h",
                          color="Total", color_continuous_scale="Reds",
                          title="أعلى 10 حسابات")
            st.plotly_chart(fig1, use_container_width=True)
            st.dataframe(by_account, use_container_width=True, hide_index=True)

            st.divider()

            # شهري
            st.subheader("المصروفات الشهرية")
            if selected_month == "الكل":
                monthly_exp = exp_filtered.groupby("Month").agg(
                    Total=("Amount", "sum"),
                    Count=("Amount", "count")
                ).reset_index()
                monthly_exp["MonthName"] = monthly_exp["Month"].apply(lambda m: month_names[int(m)-1])
                fig2 = px.line(monthly_exp, x="MonthName", y="Total", markers=True,
                               title=f"المصروفات الشهرية {int(sel_exp_year)}")
                st.plotly_chart(fig2, use_container_width=True)
                st.dataframe(monthly_exp, use_container_width=True, hide_index=True)

            st.divider()

            # حسب نوع المستند
            st.subheader("حسب نوع المستند")
            by_type = exp_filtered.groupby("نوع المستند").agg(
                Total=("Amount", "sum"),
                Count=("Amount", "count")
            ).reset_index().sort_values("Total", ascending=False)
            if not by_type.empty:
                fig3 = px.pie(by_type, values="Total", names="نوع المستند", hole=0.4)
                st.plotly_chart(fig3, use_container_width=True)
                st.dataframe(by_type, use_container_width=True, hide_index=True)

            st.divider()

            # تفاصيل
            st.subheader("التفاصيل الكاملة")
            detail_cols = ["الشركة", "التاريخ", "رقم الحساب", "اسم الحساب",
                           "رقم السند", "نوع المستند", "البيان/الشرح", "المبلغ"]
            avail = [c for c in detail_cols if c in exp_filtered.columns]
            det = exp_filtered[avail].sort_values("المبلغ", ascending=False)
            st.dataframe(det, use_container_width=True, hide_index=True)
            st.download_button(
                "تحميل CSV",
                det.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                "expenses.csv", "text/csv"
            )

st.divider()
st.caption("ERP AI Analytics | Financial Reports V2.0")
