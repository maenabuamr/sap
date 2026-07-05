import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ميزان المراجعة", page_icon="S", layout="wide")
st.title("S - ميزان المراجعة")
st.caption("مقارنة بين الشركات - Trial Balance Analysis")

@st.cache_data
def load_trial_balance(file_path, company_label):
    df = None
    last_error = "All attempts failed"
    for enc in ["utf-8-sig", "utf-8", "cp1256", "latin1"]:
        for sep in [",", ";", "\t", "|"]:
            try:
                test_df = pd.read_csv(file_path, encoding=enc, sep=sep, nrows=2, engine="python", on_bad_lines="skip", quoting=3)
                if len(test_df.columns) >= 3:
                    df = pd.read_csv(file_path, encoding=enc, sep=sep, engine="python", on_bad_lines="skip", quoting=3)
                    last_error = None
                    break
            except Exception as e:
                last_error = f"{enc}/{sep}: {e}"
                continue
        if df is not None and len(df.columns) >= 3:
            break

    if df is None or len(df.columns) < 3:
        try:
            import csv as csv_module
            import io as io_module
            with open(file_path, "rb") as f:
                raw = f.read()
            text = None
            for enc in ["utf-8-sig", "utf-8", "cp1256", "latin1", "utf-16"]:
                try:
                    text = raw.decode(enc)
                    if len(text) > 100:
                        break
                except:
                    continue
            if text is None:
                return None, "Cannot decode file"
            sample = text[:5000]
            try:
                dialect = csv_module.Sniffer().sniff(sample, delimiters=",;\t|")
            except Exception:
                dialect = csv_module.excel
            reader = csv_module.reader(io_module.StringIO(text), dialect=dialect)
            rows = list(reader)
            if len(rows) < 2:
                return None, f"Only {len(rows)} rows"
            df = pd.DataFrame(rows[1:], columns=[str(c).strip() for c in rows[0]])
            last_error = None
        except Exception as e:
            return None, f"csv parse error: {e}"

    if df is None:
        return None, f"Failed: {last_error}"
    if len(df.columns) < 3:
        return None, f"Got only {len(df.columns)} cols"

    df.columns = [str(c).strip() for c in df.columns]

    code_col = name_col = balance_col = debit_col = credit_col = ob_col = None
    for col in df.columns:
        cl = str(col).lower()
        if code_col is None and ("code" in cl or "acct" in cl or "bp" in cl or "كود" in col or "حساب" in col):
            code_col = col
        elif name_col is None and ("name" in cl or "اسم" in col):
            name_col = col
        elif balance_col is None and ("balance" in cl or "الرصيد" in col):
            balance_col = col
        elif debit_col is None and ("debit" in cl or "مدين" in col):
            debit_col = col
        elif credit_col is None and ("credit" in cl or "دائن" in col):
            credit_col = col
        elif ob_col is None and ("ob" in cl or "opening" in cl or "افتتاحي" in col):
            ob_col = col

    if code_col is None and len(df.columns) > 0:
        code_col = df.columns[0]
    if name_col is None and len(df.columns) > 1:
        name_col = df.columns[1]

    result = pd.DataFrame()
    result["Code"] = df[code_col].astype(str).str.strip() if code_col else ""
    result["Name"] = df[name_col].astype(str).str.strip() if name_col else ""

    def to_num(s):
        return pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce").fillna(0)

    result["OB"] = to_num(df[ob_col]) if ob_col else 0
    result["Debit"] = to_num(df[debit_col]) if debit_col else 0
    result["Credit"] = to_num(df[credit_col]) if credit_col else 0
    if balance_col:
        result["Balance"] = to_num(df[balance_col])
    else:
        result["Balance"] = result["OB"] + result["Debit"] - result["Credit"]

    result["Company"] = company_label
    result = result[result["Code"].str.len() > 0]
    result = result[result["Code"] != "nan"]
    return result, None


@st.cache_data
def load_all():
    c, e1 = load_trial_balance("data/trial_balance_commercial.csv", "التجارية")
    m, e2 = load_trial_balance("data/trial_balance_muqawwar.csv", "شركة الم Orr")
    return {"commercial": c, "muqawwar": m, "errors": [e1, e2]}


def classify_account(code):
    code_str = str(code).strip()
    if not code_str or code_str == "nan":
        return "غير محدد"
    first = code_str[0]
    mapping = {"1": "أصول", "2": "خصوم", "3": "حقوق ملكية", "4": "إيرادات", "5": "مصروفات"}
    return mapping.get(first, "أخرى")


data = load_all()
commercial_df = data["commercial"]
muqawwar_df = data["muqawwar"]

with st.expander("Load info"):
    if commercial_df is not None:
        st.write(f"التجارية: {len(commercial_df)} صف")
    else:
        st.error(f"التجارية: {data['errors'][0]}")
    if muqawwar_df is not None:
        st.write(f"شركة الم Orr: {len(muqawwar_df)} صف")
    else:
        st.error(f"الم Orr: {data['errors'][1]}")

if commercial_df is None or muqawwar_df is None:
    st.warning("Cannot load trial balance files")
    st.stop()

c_dr = commercial_df["Debit"].sum()
c_cr = commercial_df["Credit"].sum()
c_diff = c_dr - c_cr
m_dr = muqawwar_df["Debit"].sum()
m_cr = muqawwar_df["Credit"].sum()
m_diff = m_dr - m_cr

st.markdown("### Summary - المدين / الدائن / الفرق")

st.markdown("#### الشركة التجارية")
sc1, sc2, sc3, sc4 = st.columns(4)
sc1.metric("عدد الحسابات", f"{len(commercial_df):,}")
sc2.metric("إجمالي المدين", f"{c_dr:,.0f}")
sc3.metric("إجمالي الدائن", f"{c_cr:,.0f}")
sc4.metric("الفرق", f"{c_diff:,.0f}")

st.markdown("#### شركة الم Orr")
sm1, sm2, sm3, sm4 = st.columns(4)
sm1.metric("عدد الحسابات", f"{len(muqawwar_df):,}")
sm2.metric("إجمالي المدين", f"{m_dr:,.0f}")
sm3.metric("إجمالي الدائن", f"{m_cr:,.0f}")
sm4.metric("الفرق", f"{m_diff:,.0f}")

total_diff = c_diff + m_diff
st.divider()
combined1, combined2, combined3 = st.columns(3)
combined1.metric("مجموع المدين", f"{c_dr + m_dr:,.0f}")
combined2.metric("مجموع الدائن", f"{c_cr + m_cr:,.0f}")
combined3.metric("مجموع الفرق", f"{total_diff:,.0f}", delta="متوازن" if abs(total_diff) < 1 else "غير متوازن")

st.divider()


def show_table(df, key):
    txt = st.text_input("بحث بالاسم أو الكود", "", key=key)
    out = df.copy()
    if txt:
        m = out["Name"].astype(str).str.contains(txt, na=False) | out["Code"].astype(str).str.contains(txt, na=False)
        out = out[m]
    if "Company" in out.columns and out["Company"].nunique() == 1:
        out = out.drop(columns=["Company"])
    col_config = {
        "Code": st.column_config.TextColumn("Code", width="small"),
        "Name": st.column_config.TextColumn("Name", width="large"),
    }
    for cn in ["OB", "Debit", "Credit", "Balance", "Commercial", "Muqawwar", "Diff"]:
        if cn in out.columns:
            col_config[cn] = st.column_config.NumberColumn(cn, format="%.2f", width="medium")
    st.dataframe(out, use_container_width=True, hide_index=True, height=700, column_config=col_config)
    parts = []
    for cn, label in [("OB", "OB"), ("Debit", "Dr"), ("Credit", "Cr"), ("Balance", "Bal"),
                       ("Commercial", "التجاري"), ("Muqawwar", "الم Orr"), ("Diff", "الفرق")]:
        if cn in out.columns:
            parts.append(f"{label}={out[cn].sum():,.0f}")
    if parts:
        st.write(" | ".join(parts))
    st.caption(f"عدد الصفوف: {len(out):,}")
    return out


tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "1- ميزان التجارية",
    "2- ميزان شركة الم Orr",
    "3- المقارنة",
    "4- الفروقات",
    "5- تصنيف الحسابات",
    "6- أكبر الأرصدة",
    "7- الأرصدة المخالفة",
    "8- ملخص حسب النوع"
])

with tab1:
    st.subheader("ميزان الشركة التجارية")
    show_table(commercial_df, "f1")

with tab2:
    st.subheader("ميزان شركة الم Orr")
    show_table(muqawwar_df, "f2")

with tab3:
    st.subheader("المقارنة بين الميزانين")
    merged = pd.merge(
        commercial_df[["Code", "Name", "Balance"]].rename(columns={"Balance": "Commercial"}),
        muqawwar_df[["Code", "Name", "Balance"]].rename(columns={"Balance": "Muqawwar", "Name": "Name_M"}),
        on="Code", how="outer"
    )
    merged["Name"] = merged["Name"].fillna(merged["Name_M"]).fillna("")
    merged["Commercial"] = merged["Commercial"].fillna(0)
    merged["Muqawwar"] = merged["Muqawwar"].fillna(0)
    merged["Diff"] = merged["Commercial"] - merged["Muqawwar"]
    merged = merged[["Code", "Name", "Commercial", "Muqawwar", "Diff"]]
    show_table(merged, "f3")

with tab4:
    st.subheader("الفروقات بين الشركتين")
    threshold = st.number_input("الحد الأدنى للفرق", value=1000.0, step=1000.0)
    merged = pd.merge(
        commercial_df[["Code", "Name", "Balance"]].rename(columns={"Balance": "Commercial"}),
        muqawwar_df[["Code", "Name", "Balance"]].rename(columns={"Balance": "Muqawwar", "Name": "Name_M"}),
        on="Code", how="outer"
    )
    merged["Name"] = merged["Name"].fillna(merged["Name_M"]).fillna("")
    merged["Commercial"] = merged["Commercial"].fillna(0)
    merged["Muqawwar"] = merged["Muqawwar"].fillna(0)
    merged["Diff"] = (merged["Commercial"] - merged["Muqawwar"]).abs()
    diffs = merged[merged["Diff"] >= threshold].sort_values("Diff", ascending=False)
    st.write(f"عدد الحسابات بفرق أكبر من {threshold:,.0f}: {len(diffs)}")
    st.dataframe(diffs[["Code", "Name", "Commercial", "Muqawwar", "Diff"]], use_container_width=True, hide_index=True, height=600)


with tab5:
    st.subheader("تصنيف الحسابات حسب النوع")
    company_choice = st.radio("اختر الشركة", ["التجارية", "شركة الم Orr"], key="classify_co", horizontal=True)
    df_class = commercial_df if company_choice == "التجارية" else muqawwar_df
    if len(df_class) > 0:
        df_class = df_class.copy()
        df_class["النوع"] = df_class["Code"].apply(classify_account)
        type_summary = df_class.groupby("النوع").agg(
            عدد=("Code", "count"),
            مدين=("Debit", "sum"),
            دائن=("Credit", "sum"),
            رصيد=("Balance", "sum")
        ).reset_index()
        type_summary = type_summary.sort_values("رصيد", ascending=False)
        st.dataframe(type_summary, use_container_width=True, hide_index=True)
        for type_name in ["أصول", "خصوم", "حقوق ملكية", "إيرادات", "مصروفات"]:
            type_df = df_class[df_class["النوع"] == type_name]
            if len(type_df) > 0:
                with st.expander(f"{type_name} ({len(type_df)} حساب) - إجمالي: {type_df['Balance'].sum():,.0f}"):
                    st.dataframe(type_df[["Code", "Name", "Debit", "Credit", "Balance"]], use_container_width=True, hide_index=True, height=400)


with tab6:
    st.subheader("أكبر الأرصدة")
    company_choice = st.radio("اختر الشركة", ["التجارية", "شركة الم Orr"], key="top_co", horizontal=True)
    df_top = commercial_df if company_choice == "التجارية" else muqawwar_df
    top_n = st.slider("عدد الحسابات", 5, 100, 20, key="top_n")
    if len(df_top) > 0:
        df_top = df_top.copy()
        df_top["النوع"] = df_top["Code"].apply(classify_account)
        df_top["AbsBalance"] = df_top["Balance"].abs()
        top_df = df_top.nlargest(top_n, "AbsBalance")
        st.dataframe(top_df[["Code", "Name", "النوع", "Debit", "Credit", "Balance"]], use_container_width=True, hide_index=True, height=600)
        total_top = top_df["Balance"].sum()
        total_all = df_top["Balance"].sum()
        pct = total_top / total_all * 100 if total_all != 0 else 0
        st.write(f"مجموع أكبر {top_n}: {total_top:,.0f} | الإجمالي: {total_all:,.0f} | النسبة: {pct:.1f}%")


with tab7:
    st.subheader("الأرصدة السالبة والمخالفة للطبيعة")
    company_choice = st.radio("اختر الشركة", ["التجارية", "شركة الم Orr"], key="neg_co", horizontal=True)
    df_neg = commercial_df if company_choice == "التجارية" else muqawwar_df
    if len(df_neg) > 0:
        df_neg = df_neg.copy()
        df_neg["النوع"] = df_neg["Code"].apply(classify_account)
        negative = df_neg[df_neg["Balance"] < 0].copy()
        abnormal = df_neg[
            ((df_neg["النوع"] == "أصول") & (df_neg["Balance"] < 0)) |
            ((df_neg["النوع"] == "خصوم") & (df_neg["Balance"] > 0)) |
            ((df_neg["النوع"] == "إيرادات") & (df_neg["Debit"] > df_neg["Credit"])) |
            ((df_neg["النوع"] == "مصروفات") & (df_neg["Credit"] > df_neg["Debit"]))
        ].copy()
        st.markdown(f"#### الأرصدة السالبة: {len(negative)} حساب")
        if len(negative) > 0:
            st.dataframe(negative[["Code", "Name", "النوع", "Debit", "Credit", "Balance"]], use_container_width=True, hide_index=True, height=400)
        else:
            st.info("لا توجد أرصدة سالبة")
        st.markdown(f"#### الأرصدة المخالفة للطبيعة: {len(abnormal)} حساب")
        if len(abnormal) > 0:
            st.dataframe(abnormal[["Code", "Name", "النوع", "Debit", "Credit", "Balance"]], use_container_width=True, hide_index=True, height=400)
        else:
            st.info("لا توجد أرصدة مخالفة")


with tab8:
    st.subheader("ملخص حسب النوع - مقارنة بين الشركتين")
    summary_data = []
    for type_name in ["أصول", "خصوم", "حقوق ملكية", "إيرادات", "مصروفات", "أخرى"]:
        c_sub = commercial_df.copy()
        c_sub["النوع"] = c_sub["Code"].apply(classify_account)
        c_filtered = c_sub[c_sub["النوع"] == type_name]
        m_sub = muqawwar_df.copy()
        m_sub["النوع"] = m_sub["Code"].apply(classify_account)
        m_filtered = m_sub[m_sub["النوع"] == type_name]
        summary_data.append({
            "النوع": type_name,
            "عدد التجاري": len(c_filtered),
            "رصيد التجاري": c_filtered["Balance"].sum(),
            "عدد الم Orr": len(m_filtered),
            "رصيد الم Orr": m_filtered["Balance"].sum(),
            "الفرق": c_filtered["Balance"].sum() - m_filtered["Balance"].sum()
        })
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    chart_data = summary_df[summary_df["النوع"].isin(["أصول", "خصوم", "حقوق ملكية", "إيرادات", "مصروفات"])]
    if len(chart_data) > 0:
        fig = px.bar(chart_data.melt(id_vars="النوع", value_vars=["رصيد التجاري", "رصيد الم Orr"]),
                     x="النوع", y="value", color="variable", barmode="group",
                     title="مقارنة الأرصدة حسب النوع")
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("ERP AI Analytics | Trial Balance V2.0")
