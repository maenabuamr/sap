import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Financial Reports", page_icon="M", layout="wide")
st.title("M - Financial Reports")
st.caption("P&L with company filter")

@st.cache_data
def load_sales():
    # Try UTF-8 first (works for our sales file)
    df = None
    for enc in ["utf-8-sig", "utf-8", "cp1256", "latin1"]:
        try:
            df = pd.read_csv("data/sales_customer.csv", encoding=enc)
            if "DB" in df.columns and len(df["DB"].dropna()) > 0:
                sample = str(df["DB"].dropna().iloc[0])
                if any("\u0600" <= c <= "\u06ff" for c in sample):
                    break
        except Exception:
            continue
    if df is None:
        return pd.DataFrame()
    df["Amt"] = pd.to_numeric(df["Amt"], errors="coerce").fillna(0)
    df["QYT"] = pd.to_numeric(df["QYT"], errors="coerce").fillna(0)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Month"] = pd.to_numeric(df["Month"], errors="coerce")
    df = df.rename(columns={"DB": "Company"})
    return df

@st.cache_data
def load_journal():
    df = None
    for enc in ["utf-16", "utf-16-le", "utf-8-sig", "cp1256", "latin1"]:
        for sep in ["\t", ",", ";"]:
            try:
                df = pd.read_csv("data/journal_entries.csv", encoding=enc, sep=sep, on_bad_lines="skip", engine="python")
                if len(df.columns) >= 4 and len(df) > 0:
                    break
            except Exception:
                continue
        if df is not None and len(df.columns) >= 4:
            break
    if df is None or len(df.columns) < 4:
        return None
    expected = ["Company", "AccountCode", "AccountName", "Date", "DocNum", "DocType", "Description", "Amount"]
    if len(df.columns) == len(expected):
        df.columns = expected
    else:
        cols = list(df.columns)
        df.columns = expected[:len(cols)]
    if "Amount" in df.columns:
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    if "Date" in df.columns:
        date_parsed = False
        for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"]:
            try:
                df["Date"] = pd.to_datetime(df["Date"], format=fmt, errors="coerce")
                if df["Date"].notna().sum() > 0:
                    date_parsed = True
                    break
            except Exception:
                continue
        if not date_parsed:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df["Year"] = df["Date"].dt.year.fillna(0).astype(int)
        df["Month"] = df["Date"].dt.month.fillna(0).astype(int)
    return df

@st.cache_data
def load_production():
    df = pd.read_csv("data/production_orders.csv")
    df["OrderDate"] = pd.to_datetime(df["OrderDate"], format="%m/%d/%Y", errors="coerce")
    df["Year"] = df["OrderDate"].dt.year
    df["Month"] = df["OrderDate"].dt.month
    return df

sales_df = load_sales()
journal_df = load_journal()
production_df = load_production()

if journal_df is None:
    st.error("Cannot load journal entries")
    st.stop()

# Map: display name -> (sales_value, journal_value)
COMPANY_MAP = {
    "التجارية": ("\u0627\u0644\u0634\u0631\u0643\u0629 \u0627\u0644\u062a\u062c\u0627\u0631\u064a\u0629", "\u0627\u0644\u0634\u0631\u0643\u0629 \u0627\u0644\u062a\u062c\u0627\u0631\u064a\u0629"),
    "\u0627\u0644\u0645\u0648\u0642\u0631": ("\u0627\u0644\u0645\u0648\u0642\u0631", "\u0627\u0644\u0645 Orr"),
}

st.markdown("### Filters")
fcol1, fcol2, fcol3 = st.columns(3)
with fcol1:
    selected_display = st.selectbox("\u0627\u0644\u0634\u0631\u0643\u0629", ["\u0627\u0644\u0643\u0644"] + list(COMPANY_MAP.keys()), index=0, key="company")
with fcol2:
    all_years = sorted(set(list(sales_df["Year"].dropna().unique()) + list(journal_df["Year"].dropna().unique())), reverse=True)
    if not all_years:
        all_years = [2026]
    selected_year = st.selectbox("\u0627\u0644\u0633\u0646\u0629", all_years, index=0, key="fin_year")
with fcol3:
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_month = st.selectbox("\u0627\u0644\u0634\u0647\u0631", ["\u0627\u0644\u0643\u0644"] + month_names, index=0, key="fin_month")

st.divider()

def filter_sales(df):
    year_data = df[df["Year"] == selected_year]
    out = year_data.copy() if len(year_data) > 0 else df.copy()
    if selected_month != "\u0627\u0644\u0643\u0644":
        out = out[out["Month"] == month_names.index(selected_month) + 1]
    if selected_display != "\u0627\u0644\u0643\u0644":
        sales_val, _ = COMPANY_MAP[selected_display]
        out = out[out["Company"] == sales_val]
    return out

def filter_journal(df):
    year_data = df[df["Year"] == selected_year]
    out = year_data.copy() if len(year_data) > 0 else df.copy()
    if selected_month != "\u0627\u0644\u0643\u0644":
        out = out[out["Month"] == month_names.index(selected_month) + 1]
    if selected_display != "\u0627\u0644\u0643\u0644":
        _, journal_val = COMPANY_MAP[selected_display]
        out = out[out["Company"] == journal_val]
    return out

filtered_sales = filter_sales(sales_df)
filtered_journal = filter_journal(journal_df)
filtered_production = production_df[production_df["Year"] == selected_year]
if selected_month != "\u0627\u0644\u0643\u0644":
    filtered_production = filtered_production[filtered_production["Month"] == month_names.index(selected_month) + 1]

sales_amt = filtered_sales[filtered_sales["Amt"] > 0]["Amt"].sum()
returns_amt = filtered_sales[filtered_sales["Amt"] < 0]["Amt"].sum()
net_revenue = sales_amt + returns_amt

prod = production_df.copy()
prod["FinishedItem"] = prod["FinishedItem"].astype(str).str.strip()
prod["FinishedItemName"] = prod["FinishedItemName"].astype(str).str.strip()
prod_costs_by_code = prod.groupby("FinishedItem")["UnitProductionCost"].mean()
prod_costs_by_name = prod.groupby("FinishedItemName")["UnitProductionCost"].mean()

# Calculate GLOBAL cost ratio from all sales (so numbers add up across companies)
all_sales = sales_df.copy()
all_sales["ItemCode"] = all_sales["ItemCode"].astype(str).str.strip()
all_sales["ItemDescription"] = all_sales["ItemDescription"].astype(str).str.strip()
all_sales["UnitProductionCost"] = all_sales["ItemCode"].map(prod_costs_by_code)
mask_missing_all = all_sales["UnitProductionCost"].isna()
all_sales.loc[mask_missing_all, "UnitProductionCost"] = all_sales.loc[mask_missing_all, "ItemDescription"].map(prod_costs_by_name)
all_sales["CostOfSale"] = (all_sales["QYT"].abs() * all_sales["UnitProductionCost"]).fillna(0)
matched_cogs_all = all_sales[(all_sales["UnitProductionCost"].notna()) & (all_sales["Amt"] > 0)]["CostOfSale"].sum()
matched_revenue_all = all_sales[(all_sales["UnitProductionCost"].notna()) & (all_sales["Amt"] > 0)]["Amt"].sum()
GLOBAL_COST_RATIO = matched_cogs_all / matched_revenue_all if matched_revenue_all > 0 else 0.7

fs = filtered_sales.copy()
fs["ItemCode"] = fs["ItemCode"].astype(str).str.strip()
fs["ItemDescription"] = fs["ItemDescription"].astype(str).str.strip()
fs["UnitProductionCost"] = fs["ItemCode"].map(prod_costs_by_code)
mask_missing = fs["UnitProductionCost"].isna()
fs.loc[mask_missing, "UnitProductionCost"] = fs.loc[mask_missing, "ItemDescription"].map(prod_costs_by_name)

# Use GLOBAL cost ratio for unmatched items - ensures numbers add up
fs["CostOfSale"] = (fs["QYT"].abs() * fs["UnitProductionCost"]).fillna(0)
matched_cogs_f = fs[(fs["UnitProductionCost"].notna()) & (fs["Amt"] > 0)]["CostOfSale"].sum()
unmatched_revenue_f = fs[(fs["UnitProductionCost"].isna()) & (fs["Amt"] > 0)]["Amt"].sum()
cogs = matched_cogs_f + (unmatched_revenue_f * GLOBAL_COST_RATIO)

gross = net_revenue - cogs
gross_margin = (gross / net_revenue * 100) if net_revenue > 0 else 0
opex_filtered = filtered_journal[filtered_journal["AccountCode"].astype(str).str.startswith("6", na=False)]["Amount"].sum()
if opex_filtered == 0 and len(filtered_journal) == 0 and selected_display != "الكل":
    total_opex_all = journal_df[journal_df["AccountCode"].astype(str).str.startswith("6", na=False)]["Amount"].sum()
    if len(sales_df) > 0:
        total_sales_all = sales_df[sales_df["Amt"] > 0]["Amt"].sum()
        sales_share = sales_amt / total_sales_all if total_sales_all > 0 else 0
        opex = total_opex_all * sales_share
    else:
        opex = total_opex_all
else:
    opex = opex_filtered
net = gross - opex
net_margin = (net / net_revenue * 100) if net_revenue > 0 else 0

st.subheader("\u0645\u0644\u062e\u0635 \u0627\u0644\u0641\u062a\u0631\u0629")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("\u0635\u0627\u0641\u064a \u0627\u0644\u0625\u064a\u0631\u0627\u062f\u0627\u062a", format(round(net_revenue), ","))
k2.metric("COGS (\u0627\u0644\u062a\u0643\u0644\u0641\u0629)", format(round(cogs), ","))
k3.metric("\u0627\u0644\u0631\u0628\u062d \u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a", format(round(gross), ","), delta=format(round(gross_margin), ",") + "%")
k4.metric("\u0627\u0644\u0645\u0635\u0627\u0631\u064a\u0641 \u0627\u0644\u062a\u0634\u063a\u064a\u0644\u064a\u0629", format(round(opex), ","))
k5.metric("\u0635\u0627\u0641\u064a \u0627\u0644\u0631\u0628\u062d", format(round(net), ","), delta=format(round(net_margin), ",") + "%")

st.divider()

with st.expander("\u0645\u0639\u0644\u0648\u0645\u0627\u062a \u0627\u0644\u0628\u064a\u0627\u0646\u0627\u062a"):
    st.write(f"\u0639\u062f\u062f \u0635\u0641\u0648\u0641 \u0627\u0644\u0645\u0628\u064a\u0639\u0627\u062a: {len(filtered_sales)}")
    st.write(f"\u0639\u062f\u062f \u0635\u0641\u0648\u0641 \u0627\u0644\u0642\u0648\u0627\u0626\u0645: {len(filtered_journal)}")
    st.write(f"\u0639\u062f\u062f \u0635\u0641\u0648\u0641 \u0627\u0644\u0625\u0646\u062a\u0627\u062c: {len(filtered_production)}")
    st.write(f"\u0642\u064a\u0645 \u0634\u0631\u0643\u0627\u062a \u0627\u0644\u0645\u0628\u064a\u0639\u0627\u062a: {sales_df['Company'].unique().tolist() if 'Company' in sales_df.columns else 'N/A'}")
    st.write(f"\u0642\u064a\u0645 \u0634\u0631\u0643\u0627\u062a \u0627\u0644\u0642\u0648\u0627\u0626\u0645: {journal_df['Company'].unique().tolist() if 'Company' in journal_df.columns else 'N/A'}")

tab1, tab2, tab3 = st.tabs(["1- \u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u062f\u062e\u0644", "2- \u062a\u0641\u0635\u064a\u0644 \u0627\u0644\u0645\u0635\u0627\u0631\u064a\u0641", "3- \u0645\u0642\u0627\u0631\u0646\u0629 \u0627\u0644\u0623\u0634\u0647\u0631"])

with tab1:
    pl_data = pd.DataFrame({
        "\u0627\u0644\u0628\u0646\u062f": ["\u0625\u062c\u0645\u0627\u0644\u064a \u0627\u0644\u0645\u0628\u064a\u0639\u0627\u062a", "\u0627\u0644\u0645\u0631\u062a\u062c\u0639\u0627\u062a", "\u0635\u0627\u0641\u064a \u0627\u0644\u0625\u064a\u0631\u0627\u062f\u0627\u062a", "\u062a\u0643\u0644\u0641\u0629 \u0627\u0644\u0628\u0636\u0627\u0639\u0629 \u0627\u0644\u0645\u0628\u0627\u0639\u0629", "\u0627\u0644\u0631\u0628\u062d \u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a", "\u0647\u0627\u0645\u0634 \u0627\u0644\u0631\u0628\u062d \u0627\u0644\u0625\u062c\u0645\u0627\u0644\u064a", "\u0627\u0644\u0645\u0635\u0627\u0631\u064a\u0641 \u0627\u0644\u062a\u0634\u063a\u064a\u0644\u064a\u0629", "\u0635\u0627\u0641\u064a \u0627\u0644\u0631\u0628\u062d", "\u0647\u0627\u0645\u0634 \u0635\u0627\u0641\u064a \u0627\u0644\u0631\u0628\u062d"],
        "\u0627\u0644\u0645\u0628\u0644\u063a": [sales_amt, returns_amt, net_revenue, -cogs, gross, gross_margin, -opex, net, net_margin],
    })
    st.dataframe(pl_data, use_container_width=True, hide_index=True)

with tab2:
    if len(filtered_journal) > 0:
        exp = filtered_journal[filtered_journal["AccountCode"].astype(str).str.startswith("6", na=False)].copy()
        exp_detail = exp.groupby("AccountName")["Amount"].agg(["sum", "count"]).reset_index()
        exp_detail.columns = ["\u0627\u0644\u062d\u0633\u0627\u0628", "\u0627\u0644\u0645\u0628\u0644\u063a", "\u0639\u062f\u062f \u0627\u0644\u062d\u0631\u0643\u0627\u062a"]
        exp_detail = exp_detail.sort_values("\u0627\u0644\u0645\u0628\u0644\u063a", ascending=False)
        st.dataframe(exp_detail, use_container_width=True, hide_index=True)
        if not exp_detail.empty:
            fig = px.bar(exp_detail.head(15), x="\u0627\u0644\u062d\u0633\u0627\u0628", y="\u0627\u0644\u0645\u0628\u0644\u063a", title="\u0623\u0643\u0628\u0631 \u0627\u0644\u0645\u0635\u0627\u0631\u064a\u0641 \u0627\u0644\u062a\u0634\u063a\u064a\u0644\u064a\u0629")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("\u0644\u0627 \u062a\u0648\u062c\u062f \u0628\u064a\u0627\u0646\u0627\u062a")

with tab3:
    compare_data = []
    for display_name, (sales_val, journal_val) in COMPANY_MAP.items():
        fs = sales_df[(sales_df["Year"] == selected_year) & (sales_df["Company"] == sales_val)]
        fj = journal_df[(journal_df["Year"] == selected_year) & (journal_df["Company"] == journal_val)]
        rev = fs[fs["Amt"] > 0]["Amt"].sum() + fs[fs["Amt"] < 0]["Amt"].sum()
        opex_filtered_c = fj[fj["AccountCode"].astype(str).str.startswith("6", na=False)]["Amount"].sum()
        if opex_filtered_c == 0 and len(fj) == 0:
            total_opex = journal_df[journal_df["AccountCode"].astype(str).str.startswith("6", na=False)]["Amount"].sum()
            total_sales_all = sales_df[sales_df["Amt"] > 0]["Amt"].sum()
            sales_share = rev / total_sales_all if total_sales_all > 0 else 0
            opex = total_opex * sales_share
        else:
            opex = opex_filtered_c
        compare_data.append({
            "\u0627\u0644\u0634\u0631\u0643\u0629": display_name,
            "\u0627\u0644\u0625\u064a\u0631\u0627\u062f\u0627\u062a": rev,
            "\u0627\u0644\u0645\u0635\u0627\u0631\u064a\u0641": opex,
            "\u0627\u0644\u0635\u0627\u0641\u064a": rev - opex,
        })
    compare_df = pd.DataFrame(compare_data)
    st.dataframe(compare_df, use_container_width=True, hide_index=True)
    if not compare_df.empty:
        fig = px.bar(compare_df, x="\u0627\u0644\u0634\u0631\u0643\u0629", y=["\u0627\u0644\u0625\u064a\u0631\u0627\u062f\u0627\u062a", "\u0627\u0644\u0645\u0635\u0627\u0631\u064a\u0641", "\u0627\u0644\u0635\u0627\u0641\u064a"], barmode="group")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("ERP AI Analytics | Financial V4.2")
