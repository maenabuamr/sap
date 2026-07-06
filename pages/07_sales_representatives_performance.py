import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import streamlit.components.v1 as components
from utils import display_header  # إضافة الاستيراد

# استدعاء الترويسة الثابتة
display_header()

# ── Page config (تم حذف st.set_page_config لأنها في app.py) ──

# ── Styling (LTR) ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* تحويل الاتجاه إلى اليسار لليمين */
html, body, [class*="css"] { direction: ltr; font-family: sans-serif; }
.stApp { background-color: #f5f7fa; }

.report-header { background:white; padding:14px 22px; border-bottom:2px solid #e8ecf0;
  margin-bottom:16px; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,.05); }
.report-title  { font-size:24px; font-weight:900; color:#1a2332; margin:0; }
.report-subtitle { font-size:13px; color:#6b7a8d; margin:2px 0 0 0; }

.kpi-card { background:white; border-radius:12px; padding:18px 14px; text-align:center;
  box-shadow:0 2px 8px rgba(0,0,0,.07); border:1px solid #eef0f3; }
.kpi-icon  { font-size:26px; margin-bottom:4px; }
.kpi-value { font-size:26px; font-weight:900; color:#1a2332; line-height:1.1; }
.kpi-label { font-size:12px; color:#6b7a8d; margin-top:4px; font-weight:600; }
.kpi-unit  { font-size:11px; color:#a0aab4; margin-top:2px; }

.filter-note { background:#fff8e1; border:1px solid #ffe082; border-radius:6px;
  padding:7px 14px; font-size:12px; color:#795548; margin-bottom:12px; }
.filter-note span { font-weight:700; color:#e65100; }

.footer-note { background:#f8f9fa; border:1px solid #dee2e6; border-radius:6px;
  padding:12px 16px; font-size:12px; color:#6b7a8d; margin-top:12px; line-height:1.9; }

div[data-testid="stHorizontalBlock"] { gap:10px; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
MONTHS_AR = {1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",
             7:"يوليو",8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}

# ── Load Data ─────────────────────────────────────────────────────────────────
import os

@st.cache_data
def load_data():
    file_path = os.path.join("data", "sales_customer.csv")
    if not os.path.exists(file_path):
        st.error(f"الملف غير موجود في المسار: {os.path.abspath(file_path)}")
        return pd.DataFrame()
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df["Amt"] = pd.to_numeric(df["Amt"], errors="coerce").fillna(0)
    df["QYT"] = pd.to_numeric(df["QYT"], errors="coerce").fillna(0)
    df["Month"] = df["Month"].astype(int)
    df["Year"] = df["Year"].astype(int)
    df["MonthName"] = df["Month"].map(MONTHS_AR)
    return df

def _norm_name(s):
    """تطبيع الاسم: إزالة المسافات الزائدة والتشكيل."""
    import re
    s = str(s).strip()
    s = re.sub(r'[\u064B-\u065F]', '', s)   # إزالة التشكيل
    s = re.sub(r'\s+', ' ', s)              # مسافة واحدة
    return s.lower()

def _best_name_match(target_name, sales_names):
    """أفضل مطابقة بين اسم من ملف التارجت وقائمة أسماء المبيعات."""
    tn = _norm_name(target_name)
    # مطابقة تامة
    for s in sales_names:
        if _norm_name(s) == tn:
            return s
    # مطابقة جزئية: الاسم الأول والثاني
    tn_words = set(tn.split())
    best, best_score = None, 0
    for s in sales_names:
        sn_words = set(_norm_name(s).split())
        score = len(tn_words & sn_words)
        if score > best_score:
            best_score, best = score, s
    return best if best_score >= 1 else None

@st.cache_data
def load_targets_v2():
    """
    قراءة مباشرة لملف التارجت:
    - البحث عن صف 'Target qty'
    - الحصول على أسماء المندوبين من الصف الأول (row 0) عند العمود tc-1
    - تخطي أول عمود Target qty (الإجمالي عند col 3)
    - قراءة قيمة Target qty لكل مندوب ولكل صنف مباشرة من العمود tc
    """
    target_paths = ["data/salesperson_targets.csv", "salesperson_targets.csv"]
    target_path  = None
    for p in target_paths:
        if os.path.exists(p):
            target_path = p
            break
    if not target_path:
        return None, "Target file not found"

    # جرّب كل المحددات والترميزات واحتفظ بأكثرها أعمدة
    df = None
    for enc in ["utf-8-sig", "cp1256", "utf-8", "latin1"]:
        for sep in ["\t", ",", ";"]:
            try:
                tmp = pd.read_csv(target_path, encoding=enc, sep=sep,
                                  header=None, dtype=str)
                if df is None or tmp.shape[1] > df.shape[1]:
                    df = tmp
            except Exception:
                continue
    if df is None or df.shape[1] < 4:
        return None, f"Failed to load target file (best shape: {df.shape if df is not None else 'None'})"

    # ── 1. إيجاد صف "Target qty" ─────────────────────────────────────────────
    sub_row_idx = None
    for ri in range(min(10, len(df))):
        if any("target qty" in str(v).lower()
               for v in df.iloc[ri].fillna("").astype(str)):
            sub_row_idx = ri
            break
    if sub_row_idx is None:
        return None, "Could not find 'Target qty' row in target file"

    subheader = df.iloc[sub_row_idx].fillna("").astype(str)

    # ── 2. مواضع كل عمود "Target qty" ────────────────────────────────────────
    all_tq_cols = [i for i, v in enumerate(subheader) if "target qty" in v.lower()]
    if not all_tq_cols:
        return None, "No 'Target qty' columns found"

    # أول عمود هو الإجمالي (col 3) → نتخطاه، نأخذ الباقي
    rep_tq_cols = all_tq_cols[1:]

    # ── 3. أسماء المندوبين من الصف الأول عند العمود tc-1 ─────────────────────
    row0 = df.iloc[0].fillna("").astype(str)

    rep_col_map = {}  # {rep_name: target_qty_col_index}
    seen_names  = set()
    for tc in rep_tq_cols:
        name = ""
        # أسماء المندوبين في الصف الأول عند tc-1 (الخانة الفارغة في subheader)
        for pos in [tc - 1, tc, tc - 2, tc + 1]:
            if 0 <= pos < len(row0):
                cand = row0.iloc[pos].strip()
                if (cand and cand.lower() not in ("nan", "")
                        and not cand.replace(".", "").replace("-", "").replace(",", "").isdigit()):
                    name = cand
                    break
        if name and name not in seen_names:
            rep_col_map[name] = tc
            seen_names.add(name)

    if not rep_col_map:
        return None, "No rep names found in row 0"

    # ── 4. قراءة بيانات كل صنف ────────────────────────────────────────────────
    per_item_targets = {}
    rep_totals       = {r: 0.0 for r in rep_col_map}

    for _, row in df.iloc[sub_row_idx + 1:].iterrows():
        item_code = str(row.iloc[0]).strip()
        if not item_code or item_code.lower() == "nan":
            continue
        item_d = {}
        for rep, tc in rep_col_map.items():
            try:
                raw = row.iloc[tc] if tc < len(row) else ""
                val = pd.to_numeric(str(raw).replace(",", ""), errors="coerce")
                tgt = float(val) if pd.notna(val) else 0.0
            except Exception:
                tgt = 0.0
            item_d[rep] = tgt
            rep_totals[rep] += tgt
        per_item_targets[item_code] = item_d

    return {
        "totals":            rep_totals,
        "per_item":          per_item_targets,
        "rep_names_in_file": list(rep_col_map.keys()),
        "_raw_row0":         list(row0),          # للتشخيص فقط
        "_sub_row_idx":      sub_row_idx,
        "_rep_tq_cols":      rep_tq_cols,
    }, None


df_all = load_data()

# ── تحميل بيانات التارجت مبكراً ──────────────────────────────────────────────
target_data_v2, target_err_v2 = load_targets_v2()

# ── قسم التشخيص (افتحه لمعرفة ما يُقرأ من ملف التارجت) ──────────────────────
with st.expander("🔍 تشخيص ملف التارجت"):
    if target_err_v2:
        st.error(f"خطأ: {target_err_v2}")
    elif target_data_v2:
        file_names  = target_data_v2.get("rep_names_in_file", [])
        totals      = target_data_v2.get("totals", {})
        per_item    = target_data_v2.get("per_item", {})
        raw_row0    = target_data_v2.get("_raw_row0", [])
        sub_ri      = target_data_v2.get("_sub_row_idx", "?")
        rep_tq_cols = target_data_v2.get("_rep_tq_cols", [])
        sales_reps  = sorted([r for r in df_all["Salesperson"].unique()
                              if r not in ["-No Sales Employee-", "موظفين"]])

        st.markdown(f"**صف 'Target qty' محدد عند الصف رقم:** `{sub_ri}`")
        st.markdown(f"**أعمدة Target qty للمندوبين (بعد تخطي الإجمالي):** `{rep_tq_cols}`")

        st.markdown("**الصف الأول من الملف (row 0) — هنا يجب أن تظهر أسماء المندوبين:**")
        row0_df = pd.DataFrame([raw_row0], columns=range(len(raw_row0)))
        st.dataframe(row0_df, hide_index=True)

        st.markdown("**أسماء المندوبين التي استخرجها الكود من row0:**")
        st.write(file_names if file_names else "⚠️ لم يُعثر على أسماء!")

        st.markdown("**إجمالي التارجت لكل مندوب:**")
        st.dataframe(pd.DataFrame(list(totals.items()), columns=["المندوب (ملف التارجت)", "إجمالي Target"]),
                     hide_index=True)

        st.markdown("**مطابقة الأسماء → أسماء ملف المبيعات:**")
        mapping_rows = []
        for fn in file_names:
            match = _best_name_match(fn, sales_reps)
            mapping_rows.append({"اسم في التارجت": fn,
                                  "أفضل مطابقة في المبيعات": match or "❌ لا تطابق",
                                  "حالة": "✅" if match else "❌"})
        st.dataframe(pd.DataFrame(mapping_rows), hide_index=True)

        st.markdown(f"**عدد الأصناف في ملف التارجت:** `{len(per_item)}`")
        if per_item:
            sample_key = next(iter(per_item))
            st.markdown(f"**مثال — صنف `{sample_key}`:**")
            st.write(per_item[sample_key])
    else:
        st.warning("لا توجد بيانات تارجت")

# ── Filter Options ────────────────────────────────────────────────────────────
all_years    = sorted(df_all["Year"].unique(), reverse=True)
all_months   = sorted(df_all["Month"].unique())
all_reps     = sorted([r for r in df_all["Salesperson"].unique()
                       if r not in ["-No Sales Employee-", "موظفين"]])
all_db       = sorted(df_all["DB"].unique())
all_groups = sorted(df_all["ItemGroup"].dropna().unique().tolist())

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="report-header">
  <p class="report-title">📊 تقرير أداء المندوبين المجمع</p>
  <p class="report-subtitle">تقرير المبيعات حسب العائلة والمندوب</p>
</div>
""", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns([0.8, 1.4, 2.2, 1.2, 1.2, 0.7])

with c1:
    st.markdown("<label style='font-size:13px;font-weight:700;color:#444'>السنة</label>", unsafe_allow_html=True)
    sel_year = st.selectbox("", all_years, label_visibility="collapsed", key="sel_year")

with c2:
    st.markdown("<label style='font-size:13px;font-weight:700;color:#444'>الشهر</label>", unsafe_allow_html=True)
    month_options = [MONTHS_AR[m] for m in all_months]
    sel_months_ar = st.multiselect("", month_options, default=month_options,
                                    label_visibility="collapsed", key="sel_months")
    sel_months_num = [k for k, v in MONTHS_AR.items() if v in sel_months_ar]

with c3:
    st.markdown("<label style='font-size:13px;font-weight:700;color:#444'>المندوب</label>", unsafe_allow_html=True)
    sel_reps = st.multiselect("", all_reps, default=all_reps,
                               label_visibility="collapsed", key="sel_reps")

with c4:
    st.markdown("<label style='font-size:13px;font-weight:700;color:#444'>الشركة</label>", unsafe_allow_html=True)
    sel_db = st.multiselect("", all_db, default=all_db,
                             label_visibility="collapsed", key="sel_db")

with c5:
    st.markdown("<label style='font-size:13px;font-weight:700;color:#444'>العائلة</label>", unsafe_allow_html=True)
    sel_groups = st.multiselect("", all_groups, default=all_groups,
                                label_visibility="collapsed", key="sel_groups")

with c6:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 مسح"):
        for k in ["sel_year", "sel_months", "sel_reps", "sel_db", "sel_groups"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# ── Apply Filters ─────────────────────────────────────────────────────────────
if not sel_months_num: sel_months_num = all_months
if not sel_reps:       sel_reps       = all_reps
if not sel_db:         sel_db         = all_db
if not sel_groups:     sel_groups     = all_groups

try:
    df = df_all[
        (df_all["Year"] == sel_year) &
        (df_all["Month"].isin(sel_months_num)) &
        (df_all["Salesperson"].isin(sel_reps)) &
        (df_all["DB"].isin(sel_db)) &
        (df_all["ItemGroup"].isin(sel_groups))
    ].copy()
except Exception as e:
    st.error(f"حدث خطأ أثناء تطبيق الفلاتر: {e}")
    df = df_all.copy()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
total_sales    = df["Amt"].sum()
total_qty      = df["QYT"].sum()
num_reps       = df["Salesperson"].nunique()
num_families   = df["ItemGroup"].nunique()
num_invoices   = df[df["DocType"]=="فاتورة"]["DocNum"].nunique()

k1,k2,k3,k4,k5 = st.columns(5)
def kpi(col, icon, val, label, unit=""):
    with col:
        st.markdown(f"""<div class="kpi-card">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-unit">{unit}</div>
        </div>""", unsafe_allow_html=True)

kpi(k1, "👥", f"{num_reps:,}",         "عدد المندوبين",  "مندوب")
kpi(k2, "📦", f"{num_families:,}",     "عدد العائلات",   "عائلة")
kpi(k3, "🧾", f"{num_invoices:,}",     "عدد الفواتير",   "فاتورة")
kpi(k4, "🔢", f"{total_qty:,.0f}",     "إجمالي الكمية",  "قطعة")
kpi(k5, "💰", f"{total_sales:,.2f}",   "إجمالي المبيعات","دينار")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── Pivot Table: Tree HTML (ItemGroup → ItemDescription) ──────────────────────
st.markdown("### 📋 تفصيل المبيعات حسب العائلة والمندوب")

def build_pivot_data(data, sel_reps_list, target_data=None):
    """Return (family_df, items_dict, reps) for the tree table."""
    required = {"Salesperson", "Amt", "QYT", "ItemGroup", "ItemDescription"}
    if not required.issubset(data.columns) or data.empty:
        return pd.DataFrame(), {}, []

    reps_avail = [r for r in sel_reps_list if r in data["Salesperson"].values]

    # Family-level pivot
    fam_amt = data.pivot_table(index="ItemGroup", columns="Salesperson",
                               values="Amt", aggfunc="sum", fill_value=0)
    fam_qty = data.pivot_table(index="ItemGroup", columns="Salesperson",
                               values="QYT", aggfunc="sum", fill_value=0)
    reps = [r for r in reps_avail if r in fam_amt.columns]

    fam = pd.DataFrame(index=fam_amt.index)
    for r in reps:
        fam[f"a_{r}"] = fam_amt[r]
        fam[f"q_{r}"] = fam_qty[r]
    fam["a_tot"] = fam_amt[reps].sum(axis=1)
    fam["q_tot"] = fam_qty[reps].sum(axis=1)

    # ── حساب التارجت لكل مندوب ────────────────────────────────────────────────
    raw_totals  = target_data.get("totals", {})   if target_data else {}
    per_item    = target_data.get("per_item", {}) if target_data else {}
    file_names  = target_data.get("rep_names_in_file", list(raw_totals.keys())) if target_data else []

    # بناء جدول تحويل: اسم المندوب في ملف المبيعات → اسم المندوب في ملف التارجت
    name_map = {}   # sales_name → file_name
    for r in reps:
        match = _best_name_match(r, file_names)
        if match:
            name_map[r] = match

    # إعادة بناء rep_totals_dict بمفاتيح أسماء المبيعات
    rep_totals_dict = {r: raw_totals.get(name_map[r], 0) for r in reps if r in name_map}

    # إعادة بناء per_item بأسماء المبيعات (لاستخدامها في DataFrame)
    per_item_mapped = {}
    for item_code, rep_tgts in per_item.items():
        per_item_mapped[item_code] = {}
        for r in reps:
            fn = name_map.get(r)
            per_item_mapped[item_code][r] = rep_tgts.get(fn, 0) if fn else 0

    # محاولة المطابقة بـ ItemCode أولاً ثم بـ ItemDescription
    target_item_df = pd.DataFrame()
    matched_col = None

    if per_item_mapped:
        for try_col in (["ItemCode", "ItemDescription"] if "ItemCode" in data.columns
                        else ["ItemDescription"]):
            item_target_rows = []
            for key_val, rep_tgts in per_item_mapped.items():
                row_dict = {try_col: key_val}
                row_dict.update(rep_tgts)
                item_target_rows.append(row_dict)
            tdf = pd.DataFrame(item_target_rows).fillna(0)
            tdf[try_col] = tdf[try_col].astype(str).str.strip()

            # دائماً نجلب ItemDescription في نتيجة الـ merge حتى نستخدمها لاحقاً
            dk_cols = [try_col, "ItemGroup"]
            if try_col != "ItemDescription" and "ItemDescription" in data.columns:
                dk_cols.append("ItemDescription")
            dk = data[dk_cols].drop_duplicates().copy()
            dk[try_col] = dk[try_col].astype(str).str.strip()

            merged = tdf.merge(dk, on=try_col, how="left")
            if merged["ItemGroup"].notna().sum() > 0:
                target_item_df = merged
                matched_col = try_col
                break

    use_per_item = not target_item_df.empty and matched_col is not None

    # ── تارجت على مستوى العائلة ───────────────────────────────────────────────
    if use_per_item:
        fam_target_cols = [r for r in reps if r in target_item_df.columns]
        fam_tgt = target_item_df.groupby("ItemGroup")[fam_target_cols].sum()
        for r in reps:
            if r in fam_tgt.columns:
                fam[f"t_{r}"] = fam_tgt[r].reindex(fam.index, fill_value=0)
            else:
                fam[f"t_{r}"] = 0
    else:
        # Fallback: توزيع التارجت الإجمالي تناسباً مع الكمية المباعة
        for r in reps:
            total_tgt = rep_totals_dict.get(r, 0)
            total_qty_rep = fam[f"q_{r}"].sum() if f"q_{r}" in fam else 0
            if total_qty_rep > 0:
                fam[f"t_{r}"] = (fam[f"q_{r}"] / total_qty_rep * total_tgt).fillna(0)
            else:
                fam[f"t_{r}"] = 0

    # تصفير NaN المتبقية
    for r in reps:
        fam[f"t_{r}"] = pd.to_numeric(fam.get(f"t_{r}", 0), errors="coerce").fillna(0)

    fam["t_tot"] = sum(fam[f"t_{r}"] for r in reps)
    fam = fam.reset_index().sort_values("a_tot", ascending=False)

    # ── Item-level pivot per family ───────────────────────────────────────────
    items = {}
    for grp, grp_df in data.groupby("ItemGroup"):
        ia = grp_df.pivot_table(index="ItemDescription", columns="Salesperson",
                                values="Amt", aggfunc="sum", fill_value=0)
        iq = grp_df.pivot_table(index="ItemDescription", columns="Salesperson",
                                values="QYT", aggfunc="sum", fill_value=0)
        rows = pd.DataFrame(index=ia.index)
        for r in reps:
            rows[f"a_{r}"] = ia.get(r, 0)
            rows[f"q_{r}"] = iq.get(r, 0)
        rows["a_tot"] = ia[[c for c in reps if c in ia.columns]].sum(axis=1)
        rows["q_tot"] = iq[[c for c in reps if c in iq.columns]].sum(axis=1)

        # تارجت على مستوى الصنف
        if use_per_item:
            # المفتاح الصحيح للبحث هو ItemDescription دائماً (rows.index = ItemDescription)
            # إذا كانت المطابقة تمت بـ ItemCode نحتاج عمود ItemDescription في target_item_df
            lookup_col = ("ItemDescription"
                          if matched_col != "ItemDescription" and "ItemDescription" in target_item_df.columns
                          else matched_col)
            for r in reps:
                if r in target_item_df.columns:
                    tdf_r = target_item_df[[lookup_col, r]].dropna(subset=[lookup_col])
                    tdf_r = tdf_r.groupby(lookup_col)[r].sum()
                    tgt_map = tdf_r.to_dict()
                    rows[f"t_{r}"] = rows.index.map(
                        lambda x, m=tgt_map: m.get(str(x).strip(), 0))
                else:
                    rows[f"t_{r}"] = 0
        else:
            # توزيع تناسبي من تارجت العائلة
            fam_row = fam[fam["ItemGroup"] == grp]
            for r in reps:
                fam_tgt_r = float(fam_row[f"t_{r}"].iloc[0]) if (
                    not fam_row.empty and f"t_{r}" in fam_row.columns) else 0
                total_qty_grp = rows[f"q_{r}"].sum()
                if total_qty_grp > 0:
                    rows[f"t_{r}"] = (rows[f"q_{r}"] / total_qty_grp * fam_tgt_r).fillna(0)
                else:
                    rows[f"t_{r}"] = 0

        for r in reps:
            rows[f"t_{r}"] = pd.to_numeric(rows.get(f"t_{r}", 0), errors="coerce").fillna(0)

        rows["t_tot"] = sum(rows[f"t_{r}"] for r in reps)
        items[grp] = rows.reset_index().sort_values("a_tot", ascending=False)

    return fam, items, reps


fam_df, items_dict, reps_in_data = build_pivot_data(df, sel_reps, target_data=target_data_v2)

# ── Export ────────────────────────────────────────────────────────────────────
ex1, ex2, _sp = st.columns([1, 1, 5])
if not fam_df.empty:
    export_rows = []
    for _, frow in fam_df.iterrows():
        grp = frow["ItemGroup"]
        base = {"العائلة": grp, "الصنف": ""}
        for r in reps_in_data:
            base[f"{r} - QTY"]    = frow.get(f"q_{r}", 0)
            base[f"{r} - Amt"]    = frow.get(f"a_{r}", 0)
            base[f"{r} - Target"] = frow.get(f"t_{r}", 0)
            tgt = frow.get(f"t_{r}", 0)
            qty = frow.get(f"q_{r}", 0)
            base[f"{r} - %"]      = f"{qty/tgt*100:.1f}%" if tgt else "-"
        base["الإجمالي - Amt"] = frow["a_tot"]
        base["الإجمالي - QTY"] = frow["q_tot"]
        export_rows.append(base)
        for _, irow in items_dict.get(grp, pd.DataFrame()).iterrows():
            ir = {"العائلة": grp, "الصنف": irow["ItemDescription"]}
            for r in reps_in_data:
                ir[f"{r} - QTY"]    = irow.get(f"q_{r}", 0)
                ir[f"{r} - Amt"]    = irow.get(f"a_{r}", 0)
                ir[f"{r} - Target"] = irow.get(f"t_{r}", 0)
                tgt = irow.get(f"t_{r}", 0)
                qty = irow.get(f"q_{r}", 0)
                ir[f"{r} - %"]      = f"{qty/tgt*100:.1f}%" if tgt else "-"
            ir["الإجمالي - Amt"] = irow["a_tot"]
            ir["الإجمالي - QTY"] = irow["q_tot"]
            export_rows.append(ir)
    export_df = pd.DataFrame(export_rows)

    with ex1:
        st.download_button("📄 CSV",
            export_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            "تقرير_المندوبين.csv", "text/csv")
    with ex2:
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            export_df.to_excel(w, index=False, sheet_name="تقرير المندوبين")
        st.download_button("📊 Excel", buf.getvalue(),
            "تقرير_المندوبين.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ── Build HTML Tree Table ─────────────────────────────────────────────────────
def fmt_n(v, decimals=2):
    try:
        return f"{float(v):,.{decimals}f}"
    except Exception:
        return str(v)

def fmt_pct(qty, target):
    """احسب نسبة الإنجاز وأرجع نص ملوّن."""
    try:
        q = float(qty)
        t = float(target)
        if t <= 0:
            return '<span style="color:#aaa">-</span>'
        pct = q / t * 100
        if pct >= 100:
            color = "#2e7d32"   # أخضر
        elif pct >= 75:
            color = "#f57f17"   # برتقالي
        else:
            color = "#c62828"   # أحمر
        return f'<span style="color:{color};font-weight:700">{pct:.1f}%</span>'
    except Exception:
        return '<span style="color:#aaa">-</span>'

def build_tree_html(fam_df, items_dict, reps, target_data=None):
    COLORS = ["#e3f2fd","#fce4ec","#f3e5f5","#e8f5e9","#fff8e1",
              "#fbe9e7","#e0f7fa","#f9fbe7","#ede7f6","#fff3e0"]

    has_targets = target_data is not None

    # ── style ──
    css = """
<style>
  html, body { margin:0; padding:0; direction:LTR; }
  #tree-wrap { overflow-x: auto; direction: LTR; font-family: Cairo, sans-serif; font-size: 12px; }
  #tree-table { border-collapse: collapse; table-layout: auto; }
  #tree-table th, #tree-table td { border: 1px solid #dde3ec; padding: 5px 8px;
      white-space: nowrap; text-align: center; }
  #tree-table thead tr:first-child th { background:#1a2332; color:#fff;
      font-weight:700; font-size:12px; text-align:center; }
  #tree-table thead tr:nth-child(2) th { background:#1e3a5f; color:#fff;
      font-weight:600; font-size:11px; text-align:center; }
  #tree-table thead tr:last-child th  { background:#2d3e55; color:#eee;
      font-weight:600; font-size:11px; text-align:center; }
  .rep-total { font-size:12px !important; font-weight:800 !important;
      color:#ffd54f !important; letter-spacing:0.3px; }

  /* Sticky first column */
  #tree-table th:first-child,
  #tree-table td:first-child {
      position: sticky; right: 0; z-index: 3;
      min-width: 200px; max-width: 260px;
      text-align: center;
      box-shadow: -2px 0 5px rgba(0,0,0,0.08);
  }
  #tree-table thead tr:first-child th:first-child { background:#1a2332; }
  #tree-table thead tr:last-child  th:first-child { background:#2d3e55; }

  .fam-row td { background:#f0f4ff; font-weight:700; cursor:pointer; }
  .fam-row td:first-child { background:#f0f4ff; }
  .fam-row:hover td { background:#dde8ff; }
  .fam-row:hover td:first-child { background:#dde8ff; }
  .toggle-btn { display:inline-flex; align-items:center; justify-content:center;
      width:18px; height:18px; border-radius:3px; font-size:13px; font-weight:900;
      margin-left:6px; cursor:pointer; flex-shrink:0; }
  .item-row td { background:#fff; }
  .item-row td:first-child { background:#fff; padding-right: 36px; color:#444; }
  .item-row:hover td { background:#f8f9ff; }
  .item-row:hover td:first-child { background:#f8f9ff; }
  .total-col { background:#eef2ff !important; font-weight:700; }
  .tgt-col   { background:#fff8e1 !important; color:#5d4037; }
  .pct-col   { background:#f1f8e9 !important; }
  .grand-row td { background:#1a2332 !important; color:#fff !important;
      font-weight:900; font-size:12px; }
  .grand-row td:first-child { background:#1a2332 !important; }
  .num { text-align:left !important; }
</style>"""

    # ── header ──
    total_all  = float(fam_df["a_tot"].sum()) if "a_tot" in fam_df else 0
    total_qty_all = float(fam_df["q_tot"].sum()) if "q_tot" in fam_df else 0
    total_tgt_all = float(fam_df["t_tot"].sum()) if "t_tot" in fam_df else 0
    rep_totals = {r: float(fam_df[f"a_{r}"].sum()) if f"a_{r}" in fam_df else 0
                  for r in reps}
    rep_qty_totals = {r: float(fam_df[f"q_{r}"].sum()) if f"q_{r}" in fam_df else 0
                      for r in reps}
    rep_tgt_totals = {r: float(fam_df[f"t_{r}"].sum()) if f"t_{r}" in fam_df else 0
                      for r in reps}

    # عدد الأعمدة لكل مندوب
    rep_colspan = 4 if has_targets else 2

    # عدد أعمدة الإجمالي
    tot_colspan = 4 if has_targets else 2

    # صف 1: أسماء المجموعات
    row1 = '<th rowspan="3">العائلة / الصنف</th>'
    row1 += f'<th colspan="{tot_colspan}">الإجمالي</th>'
    for rep in reps:
        row1 += f'<th colspan="{rep_colspan}">{rep}</th>'

    # صف 2: إجمالي الكل + إجمالي كل مندوب (مبيعات + هدف + نسبة)
    if has_targets:
        tot_pct = f"{total_qty_all/total_tgt_all*100:.1f}%" if total_tgt_all > 0 else "-"
        row2 = (
            f'<th colspan="2" class="rep-total">{fmt_n(total_all)}</th>'
            f'<th class="rep-total" style="background:#2e5016;color:#c8e6c9">{fmt_n(total_tgt_all,0)}</th>'
            f'<th class="rep-total" style="background:#2e5016;color:#c8e6c9">{tot_pct}</th>'
        )
    else:
        row2 = f'<th colspan="2" class="rep-total">{fmt_n(total_all)}</th>'

    for rep in reps:
        if has_targets:
            t = rep_tgt_totals.get(rep, 0)
            q = rep_qty_totals.get(rep, 0)
            pct_hdr = f"{q/t*100:.1f}%" if t > 0 else "-"
            row2 += (
                f'<th colspan="2" class="rep-total">{fmt_n(rep_totals[rep])}</th>'
                f'<th class="rep-total" style="background:#2e5016;color:#c8e6c9">{fmt_n(t,0)}</th>'
                f'<th class="rep-total" style="background:#2e5016;color:#c8e6c9">{pct_hdr}</th>'
            )
        else:
            row2 += f'<th colspan="2" class="rep-total">{fmt_n(rep_totals[rep])}</th>'

    # صف 3: أسماء الأعمدة الفرعية
    if has_targets:
        row3 = "<th>Amt</th><th>QTY</th><th>Target</th><th>%</th>"
    else:
        row3 = "<th>Amt</th><th>QTY</th>"
    for _ in reps:
        if has_targets:
            row3 += "<th>QTY</th><th>Amt</th><th>Target</th><th>%</th>"
        else:
            row3 += "<th>Amt</th><th>QTY</th>"

    head = f"""
<thead>
  <tr>{row1}</tr>
  <tr>{row2}</tr>
  <tr>{row3}</tr>
</thead>"""

    # ── rows ──
    body_rows = []
    grand_amt = grand_qty = grand_tgt = 0.0

    for idx, (_, frow) in enumerate(fam_df.iterrows()):
        grp    = frow["ItemGroup"]
        g_amt  = float(frow["a_tot"])
        g_qty  = float(frow["q_tot"])
        g_tgt  = float(frow.get("t_tot", 0))
        grand_amt += g_amt
        grand_qty += g_qty
        grand_tgt += g_tgt
        gid    = f"g{idx}"
        color  = COLORS[idx % len(COLORS)]

        if has_targets:
            rep_cells = (f'<td class="num total-col">{fmt_n(g_amt)}</td>'
                         f'<td class="num total-col">{fmt_n(g_qty,0)}</td>'
                         f'<td class="num tgt-col">{fmt_n(g_tgt,0)}</td>'
                         f'<td class="num pct-col">{fmt_pct(g_qty, g_tgt)}</td>')
        else:
            rep_cells = (f'<td class="num total-col">{fmt_n(g_amt)}</td>'
                         f'<td class="num total-col">{fmt_n(g_qty,0)}</td>')
        for r in reps:
            r_qty = frow.get(f"q_{r}", 0)
            r_amt = frow.get(f"a_{r}", 0)
            r_tgt = frow.get(f"t_{r}", 0)
            if has_targets:
                rep_cells += (
                    f'<td class="num">{fmt_n(r_qty,0)}</td>'
                    f'<td class="num">{fmt_n(r_amt)}</td>'
                    f'<td class="num tgt-col">{fmt_n(r_tgt,0)}</td>'
                    f'<td class="num pct-col">{fmt_pct(r_qty, r_tgt)}</td>'
                )
            else:
                rep_cells += (f'<td class="num">{fmt_n(r_amt)}</td>'
                              f'<td class="num">{fmt_n(r_qty,0)}</td>')

        body_rows.append(
            f'<tr class="fam-row" onclick="toggle(\'{gid}\')">'
            f'<td><span class="toggle-btn" id="btn-{gid}" '
            f'style="background:{color};color:#333">⊕</span>{grp}</td>'
            f'{rep_cells}</tr>'
        )

        # item rows
        idf = items_dict.get(grp, pd.DataFrame())
        for _, irow in idf.iterrows():
            item = str(irow.get("ItemDescription", ""))
            i_tgt = float(irow.get("t_tot", 0))
            i_qty = float(irow.get("q_tot", 0))
            if has_targets:
                item_rep_cells = (f'<td class="num total-col">{fmt_n(irow["a_tot"])}</td>'
                                  f'<td class="num total-col">{fmt_n(i_qty,0)}</td>'
                                  f'<td class="num tgt-col">{fmt_n(i_tgt,0)}</td>'
                                  f'<td class="num pct-col">{fmt_pct(i_qty, i_tgt)}</td>')
            else:
                item_rep_cells = (f'<td class="num total-col">{fmt_n(irow["a_tot"])}</td>'
                                  f'<td class="num total-col">{fmt_n(i_qty,0)}</td>')
            for r in reps:
                r_qty = irow.get(f"q_{r}", 0)
                r_amt = irow.get(f"a_{r}", 0)
                r_tgt = irow.get(f"t_{r}", 0)
                if has_targets:
                    item_rep_cells += (
                        f'<td class="num">{fmt_n(r_qty,0)}</td>'
                        f'<td class="num">{fmt_n(r_amt)}</td>'
                        f'<td class="num tgt-col">{fmt_n(r_tgt,0)}</td>'
                        f'<td class="num pct-col">{fmt_pct(r_qty, r_tgt)}</td>'
                    )
                else:
                    item_rep_cells += (f'<td class="num">{fmt_n(r_amt)}</td>'
                                       f'<td class="num">{fmt_n(r_qty,0)}</td>')
            body_rows.append(
                f'<tr class="item-row" data-group="{gid}" style="display:none">'
                f'<td>{item}</td>{item_rep_cells}</tr>'
            )

    # Grand Total row
    if has_targets:
        gt_pct = f"{grand_qty/grand_tgt*100:.1f}%" if grand_tgt > 0 else "-"
        gt_tot_cells = (f'<td class="num">{fmt_n(grand_amt)}</td>'
                        f'<td class="num">{fmt_n(grand_qty,0)}</td>'
                        f'<td class="num">{fmt_n(grand_tgt,0)}</td>'
                        f'<td class="num">{gt_pct}</td>')
    else:
        gt_tot_cells = (f'<td class="num">{fmt_n(grand_amt)}</td>'
                        f'<td class="num">{fmt_n(grand_qty,0)}</td>')
    gt_rep_cells = ""
    for r in reps:
        a = float(fam_df[f"a_{r}"].sum()) if f"a_{r}" in fam_df else 0
        q = float(fam_df[f"q_{r}"].sum()) if f"q_{r}" in fam_df else 0
        t = rep_tgt_totals.get(r, 0)
        if has_targets:
            pct_val = f"{q/t*100:.1f}%" if t > 0 else "-"
            gt_rep_cells += (
                f'<td class="num">{fmt_n(q,0)}</td>'
                f'<td class="num">{fmt_n(a)}</td>'
                f'<td class="num">{fmt_n(t,0)}</td>'
                f'<td class="num">{pct_val}</td>'
            )
        else:
            gt_rep_cells += f'<td class="num">{fmt_n(a)}</td><td class="num">{fmt_n(q,0)}</td>'
    body_rows.append(
        f'<tr class="grand-row"><td>Grand Total</td>{gt_tot_cells}{gt_rep_cells}</tr>'
    )

    body = "<tbody>" + "\n".join(body_rows) + "</tbody>"

    # ── JS ──
    js = """
<script>
function toggle(gid){
  var btn = document.getElementById('btn-' + gid);
  var rows = document.querySelectorAll('[data-group="' + gid + '"]');
  var isOpen = btn.textContent === '⊖';
  rows.forEach(function(r){ r.style.display = isOpen ? 'none' : ''; });
  btn.textContent = isOpen ? '⊕' : '⊖';
}
</script>"""

    return css + f'<div id="tree-wrap"><table id="tree-table">{head}{body}</table></div>' + js


if not fam_df.empty:
    html_table = build_tree_html(fam_df, items_dict, reps_in_data, target_data=target_data_v2)
    est_height = max(500, len(fam_df) * 30 + 120)
    components.html(html_table, height=est_height, scrolling=True)

    st.markdown(f"""
    <div style='font-size:12px;color:#888;margin-top:4px;text-align:center;'>
      عدد العائلات: {len(fam_df)} &nbsp;|&nbsp;
      الفترة: {", ".join(sel_months_ar) if sel_months_ar else "الكل"} {sel_year}
    </div>""", unsafe_allow_html=True)
else:
    st.info("لا توجد بيانات تطابق الفلاتر المحددة")

if target_err_v2:
    st.warning(f"ملاحظة: ملف التارجت - {target_err_v2}")

st.markdown("---")

# ── Analytics ─────────────────────────────────────────────────────────────────
st.markdown("### 📈 تحليلات المبيعات")

ch1, ch2, ch3 = st.columns([1.4, 1.2, 1.4])

# Chart 1 – Top reps bar
with ch1:
    st.markdown("**🏆 أعلى المندوبين من حيث المبيعات**")
    rep_sales = (df.groupby("Salesperson")["Amt"].sum()
                   .reset_index()
                   .sort_values("Amt", ascending=True)
                   .tail(15))
    rep_sales.columns = ["المندوب", "المبيعات"]
    fig_bar = px.bar(rep_sales, x="المبيعات", y="المندوب", orientation="h",
                     color="المبيعات", color_continuous_scale="Blues", text="المبيعات")
    fig_bar.update_traces(texttemplate="%{x:,.0f}", textposition="outside")
    fig_bar.update_layout(
        margin=dict(l=0,r=30,t=10,b=10), coloraxis_showscale=False,
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Cairo",size=11),
        xaxis_title="المبيعات (دينار)", yaxis_title="", height=340)
    st.plotly_chart(fig_bar, width="stretch")

# Chart 2 – Family donut
with ch2:
    st.markdown("**🍩 توزيع المبيعات حسب العائلات**")
    fam_sales = (df.groupby("ItemGroup")["Amt"].sum()
                   .reset_index()
                   .sort_values("Amt", ascending=False))
    fam_sales.columns = ["العائلة", "المبيعات"]
    threshold = fam_sales["المبيعات"].sum() * 0.02
    fam_sales.loc[fam_sales["المبيعات"] < threshold, "العائلة"] = "أخرى"
    fam_sales = fam_sales.groupby("العائلة")["المبيعات"].sum().reset_index()
    fig_pie = px.pie(fam_sales, values="المبيعات", names="العائلة",
                     hole=0.38, color_discrete_sequence=px.colors.qualitative.Set3)
    fig_pie.update_traces(textposition="inside", textinfo="percent")
    fig_pie.update_layout(
        margin=dict(l=0,r=0,t=10,b=10),
        legend=dict(font=dict(size=10,family="Cairo"), orientation="v", x=1.0, y=0.5),
        font=dict(family="Cairo"), height=340)
    st.plotly_chart(fig_pie, width="stretch")

# Chart 3 – Monthly trend line
with ch3:
    st.markdown("**📅 تطور المبيعات حسب الأشهر**")
    monthly = (df.groupby("Month")["Amt"].sum().reset_index())
    monthly["الشهر"] = monthly["Month"].map(MONTHS_AR)
    monthly = monthly.sort_values("Month")
    monthly.columns = ["Month","المبيعات","الشهر"]
    fig_line = px.line(monthly, x="الشهر", y="المبيعات",
                       markers=True, line_shape="spline",
                       color_discrete_sequence=["#1565c0"])
    fig_line.update_traces(line_width=2.5, marker_size=8,
                           fill="tozeroy", fillcolor="rgba(21,101,192,0.08)")
    fig_line.update_layout(
        margin=dict(l=0,r=10,t=10,b=10),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Cairo",size=11),
        xaxis_title="الشهر", yaxis_title="المبيعات (دينار)", height=340)
    st.plotly_chart(fig_line, width="stretch")

# ── Footer Notes ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer-note">
  <strong>⚡ تنويه هام:</strong><br>
  • يتم احتساب الإجماليات بناءً على الفلاتر المحددة أعلاه<br>
  • التقرير يشمل جميع الفواتير (مبيعات + مرتجعات)<br>
  • المبالغ بالدينار الأردني &nbsp;|&nbsp; المصدر: SAP Business One<br>
  • نسبة الإنجاز: <span style="color:#2e7d32;font-weight:700">أخضر ≥100%</span> &nbsp;|&nbsp;
    <span style="color:#f57f17;font-weight:700">برتقالي ≥75%</span> &nbsp;|&nbsp;
    <span style="color:#c62828;font-weight:700">أحمر &lt;75%</span>
</div>
""", unsafe_allow_html=True)
