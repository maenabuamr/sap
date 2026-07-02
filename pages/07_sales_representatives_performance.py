import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import streamlit.components.v1 as components

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="تقرير أداء المندوبين المجمع",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
@st.cache_data
def load_data():
    # المسار المباشر والمضمون في بيئة Codespaces
    file_path = "/workspaces/sap/data/sales_customer.csv"
    
    # تأكد أن الأسطر التالية تبدأ جميعها بنفس عدد المسافات (4 مسافات)
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    df["Amt"] = pd.to_numeric(df["Amt"], errors="coerce").fillna(0)
    df["QYT"] = pd.to_numeric(df["QYT"], errors="coerce").fillna(0)
    df["Month"] = df["Month"].astype(int)
    df["Year"] = df["Year"].astype(int)
    df["MonthName"] = df["Month"].map(MONTHS_AR)
    return df
df_all = load_data()

# ── Filter Options ────────────────────────────────────────────────────────────
all_years    = sorted(df_all["Year"].unique(), reverse=True)
all_months   = sorted(df_all["Month"].unique())
all_reps     = sorted([r for r in df_all["Salesperson"].unique()
                       if r not in ["-No Sales Employee-", "موظفين"]])
all_db       = sorted(df_all["DB"].unique())

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="report-header">
  <p class="report-title">📊 تقرير أداء المندوبين المجمع</p>
  <p class="report-subtitle">تقرير المبيعات حسب العائلة والمندوب</p>
</div>
""", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns([0.8, 1.4, 2.2, 1.2, 0.7])

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
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 مسح"):
        for k in ["sel_year","sel_months","sel_reps","sel_db"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

# ── Apply Filters ─────────────────────────────────────────────────────────────
if not sel_months_num: sel_months_num = all_months
if not sel_reps:       sel_reps       = all_reps
if not sel_db:         sel_db         = all_db

df = df_all[
    (df_all["Year"]       == sel_year) &
    (df_all["Month"].isin(sel_months_num)) &
    (df_all["Salesperson"].isin(sel_reps)) &
    (df_all["DB"].isin(sel_db))
].copy()

# Filter note
st.markdown("""
<div class="filter-note">
  ⚠️ <span>ملاحظة:</span> يتم احتساب الإجماليات بناءً على الفلاتر المحددة أعلاه —
  التقرير يشمل الفواتير والمرتجعات معاً
</div>
""", unsafe_allow_html=True)

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

def build_pivot_data(data, sel_reps_list):
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
    fam = fam.reset_index().sort_values("a_tot", ascending=False)

    # Item-level pivot per family
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
        items[grp] = rows.reset_index().sort_values("a_tot", ascending=False)

    return fam, items, reps

fam_df, items_dict, reps_in_data = build_pivot_data(df, sel_reps)

# ── Export ────────────────────────────────────────────────────────────────────
ex1, ex2, _sp = st.columns([1, 1, 5])
if not fam_df.empty:
    export_rows = []
    for _, frow in fam_df.iterrows():
        grp = frow["ItemGroup"]
        base = {"العائلة": grp, "الصنف": ""}
        for r in reps_in_data:
            base[f"{r} - Amt"] = frow.get(f"a_{r}", 0)
            base[f"{r} - QTY"] = frow.get(f"q_{r}", 0)
        base["الإجمالي - Amt"] = frow["a_tot"]
        base["الإجمالي - QTY"] = frow["q_tot"]
        export_rows.append(base)
        for _, irow in items_dict.get(grp, pd.DataFrame()).iterrows():
            ir = {"العائلة": grp, "الصنف": irow["ItemDescription"]}
            for r in reps_in_data:
                ir[f"{r} - Amt"] = irow.get(f"a_{r}", 0)
                ir[f"{r} - QTY"] = irow.get(f"q_{r}", 0)
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

def build_tree_html(fam_df, items_dict, reps):
    COLORS = ["#e3f2fd","#fce4ec","#f3e5f5","#e8f5e9","#fff8e1",
              "#fbe9e7","#e0f7fa","#f9fbe7","#ede7f6","#fff3e0"]

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

  /* Sticky first column on the RIGHT (LTR) */
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
  .grand-row td { background:#1a2332 !important; color:#fff !important;
      font-weight:900; font-size:12px; }
  .grand-row td:first-child { background:#1a2332 !important; }
  .num { text-align:left !important; }
</style>"""

    # ── header ──
    # حساب إجمالي مبيعات كل مندوب
    total_all = float(fam_df["a_tot"].sum()) if "a_tot" in fam_df else 0
    rep_totals = {r: float(fam_df[f"a_{r}"].sum()) if f"a_{r}" in fam_df else 0
                  for r in reps}

    # صف 1: أسماء المجموعات (العائلة / الإجمالي / المندوبين)
    row1 = '<th rowspan="3">العائلة / الصنف</th>'
    row1 += '<th colspan="2">الإجمالي</th>'
    for rep in reps:
        row1 += f'<th colspan="2">{rep}</th>'

    # صف 2: إجمالي مبيعات كل مندوب (Amt فقط)
    row2 = f'<th colspan="2" class="rep-total">{fmt_n(total_all)}</th>'
    for rep in reps:
        row2 += f'<th colspan="2" class="rep-total">{fmt_n(rep_totals[rep])}</th>'

    # صف 3: Amt / QTY لكل عمود
    row3 = "<th>Amt</th><th>QTY</th>"
    for _ in reps:
        row3 += "<th>Amt</th><th>QTY</th>"

    head = f"""
<thead>
  <tr>{row1}</tr>
  <tr>{row2}</tr>
  <tr>{row3}</tr>
</thead>"""

    # ── rows ──
    body_rows = []
    grand_amt = grand_qty = 0.0

    for idx, (_, frow) in enumerate(fam_df.iterrows()):
        grp    = frow["ItemGroup"]
        g_amt  = float(frow["a_tot"])
        g_qty  = float(frow["q_tot"])
        grand_amt += g_amt
        grand_qty += g_qty
        gid    = f"g{idx}"
        color  = COLORS[idx % len(COLORS)]

        # الإجمالي أولاً ثم المندوبين
        rep_cells = (f'<td class="num total-col">{fmt_n(g_amt)}</td>'
                     f'<td class="num total-col">{fmt_n(g_qty,0)}</td>')
        for r in reps:
            rep_cells += (f'<td class="num">{fmt_n(frow.get(f"a_{r}",0))}</td>'
                          f'<td class="num">{fmt_n(frow.get(f"q_{r}",0),0)}</td>')

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
            item_rep_cells = (f'<td class="num total-col">{fmt_n(irow["a_tot"])}</td>'
                              f'<td class="num total-col">{fmt_n(irow["q_tot"],0)}</td>')
            for r in reps:
                item_rep_cells += (f'<td class="num">{fmt_n(irow.get(f"a_{r}",0))}</td>'
                                   f'<td class="num">{fmt_n(irow.get(f"q_{r}",0),0)}</td>')
            body_rows.append(
                f'<tr class="item-row" data-group="{gid}" style="display:none">'
                f'<td>{item}</td>{item_rep_cells}</tr>'
            )

    # Grand Total row
    gt_tot_cells = (f'<td class="num">{fmt_n(grand_amt)}</td>'
                    f'<td class="num">{fmt_n(grand_qty,0)}</td>')
    gt_rep_cells = ""
    for r in reps:
        a = float(fam_df[f"a_{r}"].sum()) if f"a_{r}" in fam_df else 0
        q = float(fam_df[f"q_{r}"].sum()) if f"q_{r}" in fam_df else 0
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
    html_table = build_tree_html(fam_df, items_dict, reps_in_data)
    # estimate height: ~28px per family row + some buffer
    est_height = max(500, len(fam_df) * 30 + 120)
    components.html(html_table, height=est_height, scrolling=True)

    st.markdown(f"""
    <div style='font-size:12px;color:#888;margin-top:4px;text-align:center;'>
      عدد العائلات: {len(fam_df)} &nbsp;|&nbsp;
      الفترة: {", ".join(sel_months_ar) if sel_months_ar else "الكل"} {sel_year}
    </div>""", unsafe_allow_html=True)
else:
    st.info("لا توجد بيانات تطابق الفلاتر المحددة")

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
    # Merge small families into "أخرى"
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
  • المبالغ بالدينار الأردني &nbsp;|&nbsp; المصدر: SAP Business One
</div>
""", unsafe_allow_html=True)
