import os
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ادارة الانتاج", page_icon="🏭", layout="wide")
st.title("🏭 ادارة الانتاج")
st.caption("تقارير الانتاج والكفاءة والتكاليف")

@st.cache_data
def load_orders():
    df = pd.read_csv(os.path.join('data', r'production_orders.csv'))
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], format="%m/%d/%Y", errors="coerce")
    df["Year"] = df["OrderDate"].dt.year
    df["Month"] = df["OrderDate"].dt.month
    df["YearMonth"] = df["OrderDate"].dt.to_period("M").astype(str)
    df["FinishedItemCode"] = df["FinishedItem"].astype(str)
    return df

@st.cache_data
def load_materials():
    df = pd.read_csv(os.path.join('data', r'production_materials.csv'))
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], format="%m/%d/%Y", errors="coerce")
    df["Year"] = df["OrderDate"].dt.year
    df["Month"] = df["OrderDate"].dt.month
    return df

@st.cache_data
def load_packaging():
    """Load packaging materials (raw_materials.csv)"""
    df = pd.read_csv(os.path.join('data', r'raw_materials.csv'))
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], format="%m/%d/%Y", errors="coerce")
    df["Year"] = df["OrderDate"].dt.year
    df["Month"] = df["OrderDate"].dt.month
    return df

orders_df = load_orders()
materials_df = load_materials()
packaging_df = load_packaging()

st.markdown("### الفلاتر")
fcol1, fcol2, fcol3 = st.columns(3)

with fcol1:
    available_years = sorted(orders_df["Year"].dropna().unique().tolist(), reverse=True)
    selected_year = st.selectbox("السنة", available_years, index=0, key="y")

with fcol2:
    month_names = ["يناير", "فبراير", "مارس", "ابريل", "مايو", "يونيو", "يوليو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "ديسمبر"]
    selected_month = st.selectbox("الشهر", ["الكل"] + month_names, index=0, key="m")

with fcol3:
    products_list = sorted(orders_df["FinishedItem"].dropna().unique().tolist())
    product_names = orders_df.drop_duplicates("FinishedItem").set_index("FinishedItem")["FinishedItemName"].to_dict()
    product_options = ["الكل"] + [str(c) + " - " + product_names.get(c, "") for c in products_list]
    sel_prod_opt = st.selectbox("الصنف", product_options, index=0, key="p")
    selected_product = None if sel_prod_opt == "الكل" else sel_prod_opt.split(" - ")[0]

st.divider()

def apply_filters(df):
    out = df[df["Year"] == selected_year].copy()
    if selected_month != "الكل":
        out = out[out["Month"] == month_names.index(selected_month) + 1]
    if selected_product and "FinishedItemCode" in out.columns:
        out = out[out["FinishedItemCode"].astype(str) == str(selected_product)]
    return out

filtered_orders = apply_filters(orders_df)
filtered_materials = apply_filters(materials_df)
filtered_packaging = apply_filters(packaging_df)

info_text = "السنة: " + str(selected_year)
if selected_month != "الكل":
    info_text = info_text + " | الشهر: " + selected_month
if selected_product:
    info_text = info_text + " | الصنف: " + product_names.get(selected_product, "")
st.info(info_text)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "1- انتاج شهري", "2- استهلاك مواد", "3- الهدر",
    "4- صنف محدد", "5- الكفاءة", "6- التكلفة", "7- مواد التعبئة"
])

with tab1:
    st.subheader("تقرير الانتاج الشهري")
    if filtered_orders.empty:
        st.warning("لا توجد بيانات")
    else:
        c1, c2, c3, c4 = st.columns(4)
        tp = filtered_orders["ProducedQty"].sum()
        pl = filtered_orders["PlannedQtyFinished"].sum()
        ef = (tp / pl * 100) if pl > 0 else 0
        c1.metric("الاوامر", len(filtered_orders))
        c2.metric("المنتج", str(round(tp)))
        c3.metric("المخطط", str(round(pl)))
        c4.metric("الكفاءة", str(round(ef, 1)) + "%")
        st.divider()
        st.subheader("تفصيل حسب المنتج")
        by_product = filtered_orders.groupby(["FinishedItemCode", "FinishedItemName"]).agg(
            Orders=("ProductionOrder", "count"),
            Planned=("PlannedQtyFinished", "sum"),
            Produced=("ProducedQty", "sum"),
            TotalCost=("TotalProductionCost", "sum"),
        ).reset_index().sort_values("Produced", ascending=False)
        by_product["AvgUnitCost"] = (by_product["TotalCost"] / by_product["Produced"]).round(4)
        st.dataframe(by_product, use_container_width=True, hide_index=True)
        st.subheader("ملخص شهري")
        if selected_month == "الكل":
            monthly = filtered_orders.groupby("Month").agg(
                Orders=("ProductionOrder", "count"),
                Planned=("PlannedQtyFinished", "sum"),
                Produced=("ProducedQty", "sum"),
                Cost=("TotalProductionCost", "sum"),
            ).reset_index()
            monthly["MonthName"] = monthly["Month"].apply(lambda m: month_names[m-1])
            monthly["Eff"] = (monthly["Produced"] / monthly["Planned"] * 100).round(1)
            fig = px.bar(monthly, x="MonthName", y=["Planned", "Produced"], barmode="group", title="المخطط vs المنتج")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(monthly, use_container_width=True, hide_index=True)
        else:
            daily = filtered_orders.groupby(filtered_orders["OrderDate"].dt.day).agg(
                Orders=("ProductionOrder", "count"),
                Produced=("ProducedQty", "sum"),
                Cost=("TotalProductionCost", "sum"),
            ).reset_index()
            daily.columns = ["Day", "Orders", "Produced", "Cost"]
            st.dataframe(daily, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("استهلاك المواد الاولية")
    if filtered_materials.empty:
        if selected_product:
            st.warning("لا توجد بيانات مواد أولية لهذا الصنف")
            st.info("💡 اختر 'الكل' من فلتر الصنف لعرض جميع المواد")
        else:
            st.warning("لا توجد بيانات لهذه الفترة")
    else:
        top_mat = filtered_materials.groupby(["RawMaterialCode", "RawMaterialName"]).agg(
            TotalQty=("ActualConsumedQty", "sum"),
            TotalCost=("TotalMaterialCost", "sum"),
        ).reset_index().sort_values("TotalCost", ascending=False).head(20)
        c1, c2 = st.columns(2)
        c1.metric("عدد المواد", filtered_materials["RawMaterialCode"].nunique())
        c2.metric("اجمالي التكلفة", str(round(filtered_materials["TotalMaterialCost"].sum(), 2)))
        fig = px.bar(top_mat, x="TotalCost", y="RawMaterialName", orientation="h", color="TotalCost", color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(top_mat, use_container_width=True, hide_index=True)
        st.subheader("المواد حسب المنتج النهائي")
        by_product = filtered_materials.groupby("FinishedItemName").agg(
            Materials=("RawMaterialCode", "nunique"),
            TotalQty=("ActualConsumedQty", "sum"),
            TotalCost=("TotalMaterialCost", "sum"),
        ).reset_index().sort_values("TotalCost", ascending=False)
        st.dataframe(by_product, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("تقرير الهدر")
    if filtered_orders.empty:
        st.warning("لا توجد بيانات")
    else:
        tw = filtered_orders["TotalWasteCost"].sum()
        tc = filtered_orders["TotalProductionCost"].sum()
        wp = (tw / tc * 100) if tc > 0 else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("تكلفة الهدر", str(round(tw, 2)))
        c2.metric("تكلفة الانتاج", str(round(tc, 2)))
        c3.metric("نسبة الهدر", str(round(wp, 2)) + "%")
        st.divider()
        wbp = filtered_orders.groupby(["FinishedItem", "FinishedItemName"]).agg(
            WasteCost=("TotalWasteCost", "sum"),
            Produced=("ProducedQty", "sum"),
        ).reset_index().sort_values("WasteCost", ascending=False).head(15)
        wbp["WastePerUnit"] = (wbp["WasteCost"] / wbp["Produced"]).round(4)
        fig = px.bar(wbp, x="WasteCost", y="FinishedItemName", orientation="h", color="WasteCost", color_continuous_scale="OrRd")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(wbp, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("تقرير انتاج صنف محدد")
    if selected_product:
        st.info("الصنف: " + product_names.get(selected_product, "") + " (" + selected_product + ")")
        if filtered_orders.empty:
            st.warning("لا توجد بيانات")
        else:
            dd = filtered_orders[["ProductionOrder", "OrderDate", "PlannedQtyFinished", "ProducedQty", "TotalProductionCost"]].copy()
            dd["Efficiency"] = (dd["ProducedQty"] / dd["PlannedQtyFinished"] * 100).round(1)
            c1, c2, c3 = st.columns(3)
            c1.metric("الاوامر", len(filtered_orders))
            c2.metric("المنتج", str(round(filtered_orders["ProducedQty"].sum())))
            c3.metric("متوسط الكفاءة", str(round(dd["Efficiency"].mean(), 1)) + "%")
            st.dataframe(dd, use_container_width=True, hide_index=True)
            tr = filtered_orders.groupby("YearMonth").agg(Produced=("ProducedQty", "sum"), Planned=("PlannedQtyFinished", "sum")).reset_index()
            fig = px.line(tr, x="YearMonth", y=["Planned", "Produced"], markers=True)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("اختر صنف من الفلاتر بالاعلى")

with tab5:
    st.subheader("تقرير الكفاءة")
    if filtered_orders.empty:
        st.warning("لا توجد بيانات")
    else:
        edf = filtered_orders.copy()
        edf["Eff"] = (edf["ProducedQty"] / edf["PlannedQtyFinished"] * 100).round(2)
        c1, c2, c3 = st.columns(3)
        c1.metric("متوسط", str(round(edf["Eff"].mean(), 1)) + "%")
        c2.metric("اعلى", str(round(edf["Eff"].max(), 1)) + "%")
        c3.metric("اقل", str(round(edf["Eff"].min(), 1)) + "%")
        st.divider()
        ebp = edf.groupby(["FinishedItem", "FinishedItemName"]).agg(AvgEff=("Eff", "mean"), Orders=("ProductionOrder", "count")).reset_index().sort_values("AvgEff", ascending=False).head(20)
        fig = px.bar(ebp, x="AvgEff", y="FinishedItemName", orientation="h", color="AvgEff", color_continuous_scale="RdYlGn")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(ebp, use_container_width=True, hide_index=True)

with tab6:
    st.subheader("تقرير تكلفة الانتاج")
    if filtered_orders.empty:
        st.warning("لا توجد بيانات")
    else:
        tc = filtered_orders["TotalProductionCost"].sum()
        tu = filtered_orders["ProducedQty"].sum()
        au = (tc / tu) if tu > 0 else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("التكلفة", str(round(tc, 2)))
        c2.metric("الوحدات", str(round(tu)))
        c3.metric("تكلفة الوحدة", str(round(au, 4)))
        c4.metric("الهدر", str(round(filtered_orders["TotalWasteCost"].sum(), 2)))
        st.divider()
        cbp = filtered_orders.groupby(["FinishedItem", "FinishedItemName"]).agg(
            TotalCost=("TotalProductionCost", "sum"),
            TotalUnits=("ProducedQty", "sum"),
            AvgUnit=("UnitProductionCost", "mean"),
        ).reset_index().sort_values("TotalCost", ascending=False).head(20)
        fig = px.bar(cbp, x="TotalCost", y="FinishedItemName", orientation="h", color="TotalCost", color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(cbp, use_container_width=True, hide_index=True)
        st.subheader("توزيع التكاليف")
        cb = pd.DataFrame({"Item": ["انتاج", "هدر"], "Cost": [tc - filtered_orders["TotalWasteCost"].sum(), filtered_orders["TotalWasteCost"].sum()]})
        fig2 = px.pie(cb, values="Cost", names="Item", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

with tab7:
    st.subheader("تقرير استهلاك مواد التعبئة والتغليف")
    if packaging_df.empty:
        st.warning("لا توجد بيانات في raw_materials.csv")
    else:
        if filtered_packaging.empty:
            st.warning("لا توجد بيانات تعبئة لهذه الفترة")
            st.info("💡 جرب سنة/شهر/صنف ثاني")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("عدد مواد التعبئة", filtered_packaging["RawMaterialCode"].nunique())
            c2.metric("اجمالي الكمية", f"{filtered_packaging['ActualConsumedQty'].sum():,.0f}")
            c3.metric("اجمالي التكلفة", f"{filtered_packaging['TotalMaterialCost'].sum():,.2f}")
            c4.metric("عدد أوامر الإنتاج", filtered_packaging["ProductionOrderNo"].nunique())
            st.divider()
            st.subheader("أعلى مواد التعبئة بالتكلفة")
            top_pkg = filtered_packaging.groupby(["RawMaterialCode", "RawMaterialName"]).agg(
                TotalQty=("ActualConsumedQty", "sum"),
                TotalCost=("TotalMaterialCost", "sum"),
                AvgUnitPrice=("UnitPrice", "mean"),
            ).reset_index().sort_values("TotalCost", ascending=False).head(20)
            top_pkg["AvgUnitPrice"] = top_pkg["AvgUnitPrice"].round(4)
            top_pkg["TotalQty"] = top_pkg["TotalQty"].round(0)
            top_pkg["TotalCost"] = top_pkg["TotalCost"].round(2)
            fig = px.bar(top_pkg, x="TotalCost", y="RawMaterialName", orientation="h",
                         color="TotalCost", color_continuous_scale="Oranges",
                         title="أعلى 20 مادة تعبئة بالتكلفة")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(top_pkg, use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("مواد التعبئة لكل منتج نهائي")
            by_finished = filtered_packaging.groupby("FinishedItemName").agg(
                PackagingItems=("RawMaterialCode", "nunique"),
                TotalQty=("ActualConsumedQty", "sum"),
                TotalCost=("TotalMaterialCost", "sum"),
            ).reset_index().sort_values("TotalCost", ascending=False)
            by_finished["TotalCost"] = by_finished["TotalCost"].round(2)
            by_finished["TotalQty"] = by_finished["TotalQty"].round(0)
            fig2 = px.bar(by_finished, x="TotalCost", y="FinishedItemName", orientation="h",
                          color="TotalCost", color_continuous_scale="Greens",
                          title="تكلفة التعبئة لكل منتج")
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(by_finished, use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("حسب المستودع المصدر")
            by_warehouse = filtered_packaging.groupby("FromWarehouse").agg(
                Materials=("RawMaterialCode", "nunique"),
                TotalQty=("ActualConsumedQty", "sum"),
                TotalCost=("TotalMaterialCost", "sum"),
            ).reset_index().sort_values("TotalCost", ascending=False)
            by_warehouse["TotalCost"] = by_warehouse["TotalCost"].round(2)
            by_warehouse["TotalQty"] = by_warehouse["TotalQty"].round(0)
            st.dataframe(by_warehouse, use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("التوزيع الشهري")
            if selected_month == "الكل":
                monthly_pkg = filtered_packaging.groupby("Month").agg(
                    Orders=("ProductionOrderNo", "nunique"),
                    TotalQty=("ActualConsumedQty", "sum"),
                    TotalCost=("TotalMaterialCost", "sum"),
                ).reset_index()
                monthly_pkg["MonthName"] = monthly_pkg["Month"].apply(lambda m: month_names[m-1])
                monthly_pkg["TotalCost"] = monthly_pkg["TotalCost"].round(2)
                monthly_pkg["TotalQty"] = monthly_pkg["TotalQty"].round(0)
                fig3 = px.line(monthly_pkg, x="MonthName", y="TotalCost", markers=True,
                               title="تكلفة التعبئة الشهرية")
                st.plotly_chart(fig3, use_container_width=True)
                st.dataframe(monthly_pkg, use_container_width=True, hide_index=True)
            st.divider()
            st.subheader("تفاصيل مواد التعبئة")
            detail_cols = ["ProductionOrderNo", "OrderDate", "FinishedItemName",
                           "RawMaterialCode", "RawMaterialName", "ActualConsumedQty",
                           "UnitPrice", "TotalMaterialCost", "FromWarehouse"]
            available_cols = [c for c in detail_cols if c in filtered_packaging.columns]
            detail_df = filtered_packaging[available_cols].sort_values("TotalMaterialCost", ascending=False).head(100)
            detail_df["TotalMaterialCost"] = detail_df["TotalMaterialCost"].round(2)
            detail_df["UnitPrice"] = detail_df["UnitPrice"].round(4)
            st.dataframe(detail_df, use_container_width=True, hide_index=True)

st.divider()
st.caption("ERP AI Analytics | Production V2.0")