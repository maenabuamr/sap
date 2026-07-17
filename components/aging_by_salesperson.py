"""
Aging Report by Salesperson Component
======================================
يعرض تقرير أعمار الذمم مفصّل حسب المندوب:
    - اختيار مندوب من القائمة
    - KPIs ملخص لأداء المندوب
    - رسم بياني لتوزيع أعمار الذمم
    - جدول تفصيلي لكل عميل
    - تصدير Excel / CSV

الاستخدام:
    from components.aging_by_salesperson import render_aging_by_salesperson
    render_aging_by_salesperson(filtered_df)
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# ──────────────────────────────────────────────────────────
# تعريف الأعمدة (يقبل عربي / إنجليزي + كشف ذكي)
# ──────────────────────────────────────────────────────────
import re

# قائمة بكل الأسماء المحتملة لشرائح الأعمار (عربي + إنجليزي + نظام Age_X_Y)
AGING_BUCKETS = [
    # عربي
    "0-15 يوم", "16-30 يوم", "31-45 يوم", "46-60 يوم",
    "61-75 يوم", "76-90 يوم", "اكثر من 90 يوم",
    "أكثر من 90 يوم", "0-30 يوم", "31-60 يوم", "61-90 يوم",
    # إنجليزي (نظام SAP B1 + أنظمة أخرى)
    "0-30 Days", "1-30 Days", "31-60 Days", "61-90 Days", "90+ Days",
    "Current", "1-30", "31-60", "61-90", "Over 90",
    "0-30", "31-60", "61-90", "90+",
    "Bucket1", "Bucket2", "Bucket3", "Bucket4", "Bucket5",
    # نظام Age_X_Y (اللي عندك في الداتا!)
    "Age_0_15", "Age_16_30", "Age_31_45", "Age_46_60",
    "Age_61_75", "Age_76_90", "Age_90_Plus",
]

SALES_COL_CANDIDATES   = [
    "Salesperson", "SlpName", "SalesPersonName", "SalesPersonCode",
    "SlpCode", "المندوب", "اسم المندوب",
]
CUSTOMER_COL_CANDIDATES = [
    "CustomerName", "CardName", "اسم العميل", "Customer", "CardCode",
]
BALANCE_COL_CANDIDATES  = [
    "CurrentBalance", "الرصيد الحالي", "الرصيد",
    "Balance", "DueBalance", "TotalBalance",
]
RISK_COL_CANDIDATES     = [
    "RiskCategory", "RiskLevel", "فئة المخاطر", "التصنيف", "Risk",
]

# Regex لكشف أعمدة الأعمار تلقائياً من أي DataFrame
# يدعم الأنماط: 1-30 Days, 90+ Days, Age_0_15, Age_90_Plus, اكثر من 90 يوم
_AGING_PATTERN = re.compile(
    r'(\d+\s*[-+]\s*\d+\s*(يوم|Days?|days?))'
    r'|(\d+\+\s*(يوم|Days?|days?))'
    r'|(Age[_-]?\d+[_-]\d+(_?Plus)?)'
    r'|(Age[_-]?\d+[_+]\d*)'
    r'|(اكثر\s*من\s*\d+|أكثر\s*من\s*\d+|Over\s*\d+)'
    r'|^Age$|^(Current|Bucket\d+)$',
    re.IGNORECASE
)


def _detect_aging_columns(df: pd.DataFrame) -> list[str]:
    """كشف تلقائي لأعمدة أعمار الذمم الموجودة فعلياً في الـ DataFrame"""
    found = []
    for col in df.columns:
        if _AGING_PATTERN.search(str(col)):
            found.append(col)
    return found

# ألوان متدرجة من الأخضر → الأحمر (لشرائح الأعمار)
BUCKET_COLORS = ["#48bb78", "#84cc16", "#ecc94b", "#ed8936", "#e53e3e", "#c53030", "#742a2a"]


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────
def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """يرجع أول عمود موجود فعلاً في الـ DataFrame من قائمة المرشحين"""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _fmt_num(val) -> str:
    """تنسيق الأرقام بفاصلة الآلاف"""
    try:
        if pd.isna(val):
            return "0.00"
        return f"{float(val):,.2f}"
    except Exception:
        return "0.00"


def _kpi_card(title: str, value: str, sub: str | None = None, color: str = "#1a2332") -> None:
    """KPI card بنفس ستايل التطبيق الأساسي"""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
            color: white;
            padding: 16px 18px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.10);
            min-height: 90px;
        ">
            <div style="font-size: 12px; opacity: 0.9; margin-bottom: 4px;">{title}</div>
            <div style="font-size: 24px; font-weight: bold; margin: 4px 0;">{value}</div>
            {f'<div style="font-size: 11px; opacity: 0.8; margin-top: 4px;">{sub}</div>' if sub else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────
# Renderers
# ──────────────────────────────────────────────────────────
def render_aging_by_salesperson(filtered: pd.DataFrame) -> None:
    """نقطة الدخول الرئيسية للمكون"""
    st.markdown("### 👤 تقرير أعمار الذمم حسب المندوب")
    st.caption("اختر مندوب لعرض ملخص أعمار الذمم لجميع العملاء المرتبطين به.")

    # ── فحص الأعمدة ──
    sp_col   = _pick_col(filtered, SALES_COL_CANDIDATES)
    cust_col = _pick_col(filtered, CUSTOMER_COL_CANDIDATES)
    bal_col  = _pick_col(filtered, BALANCE_COL_CANDIDATES)

    if not sp_col or not cust_col:
        st.error("⚠️ بيانات المندوبين أو العملاء غير متوفرة في البيانات الحالية.")
        st.caption(f"الأعمدة الموجودة: {list(filtered.columns)}")
        return

    # ── قائمة المندوبين بعد تطبيق الفلاتر العالمية ──
    salespersons = sorted(
        filtered[sp_col].dropna().astype(str).str.strip().unique().tolist()
    )
    salespersons = [s for s in salespersons if s]  # حذف القيم الفارغة

    if not salespersons:
        st.info("لا يوجد مندوبين في البيانات المفلترة حالياً. جرّب تعديل الفلاتر الجانبية.")
        return

    # ── شريط الاختيار ──
    sel_col, info_col = st.columns([3, 7])
    with sel_col:
        selected_sp = st.selectbox(
            "🎯 اختر المندوب:",
            options=salespersons,
            key="aging_sp_select",
        )

    sp_subset = filtered[filtered[sp_col].astype(str).str.strip() == selected_sp]
    customer_count = sp_subset[cust_col].nunique() if not sp_subset.empty else 0

    with info_col:
        st.markdown(
            f"""
            <div style="background: #f8f9fa; padding: 14px 18px; border-radius: 8px;
                        border-right: 4px solid #d4af37; margin-top: 26px;">
                <div style="font-size: 13px; color: #444;">
                    <b>المندوب المختار:</b> {selected_sp} &nbsp;|&nbsp;
                    <b>عدد العملاء المرتبطين:</b> {customer_count}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if sp_subset.empty:
        st.warning(f"لا توجد بيانات للمندوب: {selected_sp}")
        return

    st.divider()

    # ── كشف تلقائي لأعمدة الأعمار الموجودة فعلاً ──
    detected_buckets = _detect_aging_columns(sp_subset)
    if not detected_buckets:
        st.warning("⚠️ لم يتم العثور على أعمدة أعمار ذمم في البيانات.")
        st.caption(f"الأعمدة الموجودة: {list(sp_subset.columns)}")
        return

    # ── KPIs ──
    _render_sp_kpis(sp_subset, bal_col, detected_buckets)

    st.divider()

    # ── رسم بياني + أعلى 5 عملاء ──
    chart_col, top_col = st.columns([6, 4])
    with chart_col:
        _render_aging_distribution_chart(sp_subset, detected_buckets)
    with top_col:
        _render_top_customers(sp_subset, cust_col, bal_col)

    st.divider()

    # ── جدول تفصيلي لكل عميل ──
    with st.expander("📋 تفاصيل أعمار الذمم لكل عميل (جدول كامل)", expanded=True):
        _render_detailed_aging_table(sp_subset, cust_col, bal_col, detected_buckets)

    st.divider()

    # ── Export Buttons ──
    _render_export_buttons(sp_subset, selected_sp, cust_col, bal_col, detected_buckets)


# ──────────────────────────────────────────────────────────
def _is_late_bucket(col_name: str) -> bool:
    """هل هذه الشريحة >= 31 يوم (متأخرة)؟"""
    name = str(col_name).lower()
    # نمط: 31-45 / 31-60 / 31-90 / 3X-YY
    if re.search(r'\b(3[1-9]|[4-9]\d|\d{3,})\s*[-+]', name):
        return True
    # نمط: Age_31_45 / Age_46_60 (الرقم الأول >= 31)
    if re.search(r'age[_-]?(3[1-9]|[4-9]\d|\d{3,})[_-]\d+', name):
        return True
    if 'اكتر' in name or 'أكثر' in name or 'over' in name or '_plus' in name:
        return True
    return False


def _is_critical_bucket(col_name: str) -> bool:
    """هل هذه الشريحة > 90 يوم (حرجة)؟"""
    name = str(col_name).lower()
    if re.search(r'(9[1-9]|\d{3,})\s*\+', name):
        return True
    if 'اكتر من 90' in name or 'أكثر من 90' in name or 'over 90' in name:
        return True
    if re.search(r'90\s*\+', name) or re.search(r'90\+', name):
        return True
    # نمط: Age_90_Plus / age_9X_YY
    if re.search(r'age[_-]?(9[1-9]|\d{3,})[_-]\d+', name):
        return True
    if 'age_90_plus' in name or 'age-90-plus' in name:
        return True
    return False


# ──────────────────────────────────────────────────────────
def _render_sp_kpis(sp_data: pd.DataFrame, bal_col: str | None, detected_buckets: list) -> None:
    """KPIs ملخص المندوب"""
    total_customers = sp_data["CustomerName"].nunique() if "CustomerName" in sp_data.columns else len(sp_data)
    total_balance = sp_data[bal_col].sum() if bal_col and bal_col in sp_data.columns else 0.0

    # شرائح "متأخرة" بناءً على الكشف التلقائي
    late_buckets = [b for b in detected_buckets if _is_late_bucket(b)]
    overdue_balance = float(sp_data[late_buckets].sum().sum()) if late_buckets else 0.0

    # شرائح "حرجة" بناءً على الكشف التلقائي
    critical_buckets = [b for b in detected_buckets if _is_critical_bucket(b)]
    critical_balance = float(sp_data[critical_buckets].sum().sum()) if critical_buckets else 0.0

    overdue_pct = (overdue_balance / total_balance * 100) if total_balance > 0 else 0.0
    critical_pct = (critical_balance / total_balance * 100) if total_balance > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _kpi_card("👥 عدد العملاء", f"{int(total_customers):,}", color="#1a2332")
    with c2:
        _kpi_card("💰 إجمالي الرصيد", _fmt_num(total_balance), "دينار", color="#2c5282")
    with c3:
        _kpi_card(
            "⚠️ رصيد متأخر (>30 يوم)",
            _fmt_num(overdue_balance),
            f"{overdue_pct:.1f}% من الإجمالي",
            color="#c53030",
        )
    with c4:
        _kpi_card(
            "🚨 رصيد حرج (>90 يوم)",
            _fmt_num(critical_balance),
            f"{critical_pct:.1f}% من الإجمالي",
            color="#742a2a",
        )


# ──────────────────────────────────────────────────────────
def _render_aging_distribution_chart(sp_data: pd.DataFrame, detected_buckets: list) -> None:
    """رسم بياني أفقي لتوزيع أعمار الذمم"""
    st.markdown("#### 📊 توزيع أعمار الذمم")

    if not detected_buckets:
        st.info("لا توجد بيانات أعمار ذمم متاحة.")
        return

    bucket_totals = {b: float(sp_data[b].sum()) for b in detected_buckets if b in sp_data.columns}
    bucket_totals = {k: v for k, v in bucket_totals.items() if v > 0}

    if not bucket_totals:
        st.info("✅ لا توجد أرصدة في شرائح الأعمار — جميع العملاء بحالة جيدة.")
        return

    df_chart = pd.DataFrame({
        "الفترة": list(bucket_totals.keys()),
        "المبلغ": list(bucket_totals.values()),
    })

    fig = px.bar(
        df_chart,
        x="المبلغ",
        y="الفترة",
        orientation="h",
        color="الفترة",
        color_discrete_sequence=BUCKET_COLORS[:len(df_chart)],
        text="المبلغ",
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(
        showlegend=False,
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis={"categoryorder": "array", "categoryarray": df_chart["الفترة"].tolist()},
        xaxis_title="المبلغ (دينار)",
        yaxis_title=None,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)


# ──────────────────────────────────────────────────────────
def _render_top_customers(sp_data: pd.DataFrame, cust_col: str, bal_col: str | None) -> None:
    """أعلى 5 عملاء من حيث الرصيد"""
    st.markdown("#### 🏆 أعلى 5 عملاء (حسب الرصيد)")

    if not bal_col or bal_col not in sp_data.columns:
        st.info("بيانات الرصيد غير متوفرة.")
        return

    top5 = (
        sp_data.groupby(cust_col)[bal_col]
        .sum()
        .reset_index()
        .sort_values(bal_col, ascending=False)
        .head(5)
    )
    top5.columns = ["العميل", "الرصيد"]
    top5["الرصيد"] = top5["الرصيد"].apply(_fmt_num)
    top5.insert(0, "#", range(1, len(top5) + 1))

    st.dataframe(top5, use_container_width=True, hide_index=True, height=300)


# ──────────────────────────────────────────────────────────
def _classify_risk(row, bal_col, late_buckets, critical_buckets):
    """تصنيف مستوى خطر العميل حسب نسبة التأخر"""
    if not bal_col or bal_col not in row.index:
        return "✅ منخفض", "#22543d", 0

    try:
        total = float(row[bal_col]) if not pd.isna(row[bal_col]) else 0.0
    except Exception:
        return "✅ منخفض", "#22543d", 0

    if total <= 0:
        return "✅ غير مديون", "#22543d", 0

    overdue = 0.0
    for b in late_buckets:
        if b in row.index and not pd.isna(row[b]):
            try:
                overdue += float(row[b])
            except Exception:
                pass

    critical = 0.0
    for b in critical_buckets:
        if b in row.index and not pd.isna(row[b]):
            try:
                critical += float(row[b])
            except Exception:
                pass

    overdue_pct = (overdue / total * 100) if total > 0 else 0
    critical_pct = (critical / total * 100) if total > 0 else 0

    if critical_pct >= 50 or overdue_pct >= 80:
        return "🚨 حرج", "#c53030", 4
    elif overdue_pct >= 50:
        return "⚠️ مرتفع", "#dd6b20", 3
    elif overdue_pct >= 20:
        return "⚡ متوسط", "#d69e2e", 2
    elif overdue_pct > 0:
        return "👀 منخفض", "#38a169", 1
    else:
        return "✅ جيد", "#22543d", 0


def _bucket_emoji(col_name):
    """إضافة رمز بصري بجانب اسم الشريحة الحرجة"""
    if _is_critical_bucket(col_name):
        return f"🔻 {col_name}"
    elif _is_late_bucket(col_name):
        return f"⏰ {col_name}"
    return col_name


# ──────────────────────────────────────────────────────────
def _render_detailed_aging_table(sp_data: pd.DataFrame, cust_col: str, bal_col: str | None, detected_buckets: list) -> None:
    """جدول تفصيلي لكل عميل (كل الشرائح) - مع التصوير البصري"""
    available_buckets = [b for b in detected_buckets if b in sp_data.columns]
    if not available_buckets:
        st.info("لا توجد بيانات تفصيلية متاحة.")
        return

    # تجميع حسب العميل
    agg_dict: dict = {b: "sum" for b in available_buckets}
    if bal_col and bal_col not in available_buckets and bal_col in sp_data.columns:
        agg_dict[bal_col] = "sum"

    detailed = sp_data.groupby(cust_col).agg(agg_dict).reset_index()

    # تصنيف الخطر (قبل التنسيق ليبقى رقمي)
    late_buckets = [b for b in available_buckets if _is_late_bucket(b)]
    critical_buckets = [b for b in available_buckets if _is_critical_bucket(b)]
    risk_data = detailed.apply(
        lambda r: _classify_risk(r, bal_col, late_buckets, critical_buckets),
        axis=1, result_type="expand"
    )
    risk_data.columns = ["تصنيف الخطر", "_color", "_sort"]
    detailed = pd.concat([detailed, risk_data], axis=1)

    # ترتيب حسب تصنيف الخطر (الأعلى أولاً) ثم الرصيد
    sort_cols = ["_sort"]
    if bal_col and bal_col in detailed.columns:
        sort_cols.append(bal_col)
    detailed = detailed.sort_values(sort_cols, ascending=[False, False]).reset_index(drop=True)

    # نسخة العرض (ترتيب الأعمدة فقط - التنسيق رح يتطبّق عبر Styler)
    display_df = detailed.drop(columns=["_color", "_sort"]).copy()

    # ترتيب الأعمدة: العميل، الخطر، ثم الباقي
    cols_order = [cust_col, "تصنيف الخطر"]
    cols_order += [c for c in available_buckets if c in display_df.columns]
    if bal_col and bal_col in display_df.columns:
        cols_order.append(bal_col)
    display_df = display_df[cols_order]

    # ⚠️ لا نطبّق تنسيق الأرقام هنا — Styler رح يطبّقها (الرقام تبقى رقمية)

    # شريط البحث
    search = st.text_input("🔍 بحث في الجدول (اسم العميل):", "", key="aging_sp_search")
    if search:
        mask = display_df[cust_col].astype(str).str.contains(search, case=False, na=False)
        display_df = display_df[mask]

    # ملخص سريع للألوان
    risk_counts = detailed["تصنيف الخطر"].value_counts()
    summary_cols = st.columns(5)
    risk_styles = [
        ("🚨 حرج", "#c53030"),
        ("⚠️ مرتفع", "#dd6b20"),
        ("⚡ متوسط", "#d69e2e"),
        ("👀 منخفض", "#38a169"),
        ("✅ جيد", "#22543d"),
    ]
    for i, (label, color) in enumerate(risk_styles):
        with summary_cols[i]:
            count = risk_counts.get(label, 0)
            st.markdown(
                f'<div style="background:{color}; color:white; padding:8px 12px; '
                f'border-radius:6px; text-align:center; font-size:13px;">'
                f'<div style="font-size:18px; font-weight:bold;">{count}</div>'
                f'<div style="font-size:11px;">{label}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ==== عرض الجدول بألوان ====
    def _color_cells(val, col_name):
        """تلوين الخلية حسب قيمتها ونوع العمود"""
        # val قد يكون رقم أو نص (لـ na_rep="-")
        try:
            if pd.isna(val):
                return ""
            num = float(val)
        except (ValueError, TypeError):
            return ""

        if num == 0:
            return "color: #999; background: #fafafa"

        if _is_critical_bucket(col_name):
            return "background-color: #fed7d7; color: #742a2a; font-weight: bold"
        elif _is_late_bucket(col_name):
            return "background-color: #fef5e7; color: #7b341e; font-weight: 600"
        else:
            return "background-color: #f0fff4; color: #22543d"

    def _color_risk(val):
        """تلوين خلية تصنيف الخطر"""
        color_map = {
            "🚨 حرج": "background-color: #c53030; color: white; font-weight: bold; text-align: center",
            "⚠️ مرتفع": "background-color: #dd6b20; color: white; font-weight: bold; text-align: center",
            "⚡ متوسط": "background-color: #d69e2e; color: white; font-weight: bold; text-align: center",
            "👀 منخفض": "background-color: #38a169; color: white; text-align: center",
            "✅ جيد": "background-color: #c6f6d5; color: #22543d; text-align: center",
            "✅ غير مديون": "background-color: #e6fffa; color: #234e52; text-align: center",
        }
        return color_map.get(str(val), "")

    def _color_negative(val):
        """تلوين القيم السالبة بالأحمر"""
        try:
            if pd.isna(val):
                return ""
            num = float(val)
        except (ValueError, TypeError):
            return ""
        if num < 0:
            return "color: #c53030; font-weight: bold"
        return ""

    # تطبيق التنسيق
    styled = display_df.style

    # تلوين أعمدة الأعمار
    for col in available_buckets:
        if col in display_df.columns:
            styled = styled.map(lambda v, c=col: _color_cells(v, c), subset=[col])

    # تلوين الرصيد الحالي
    if bal_col and bal_col in display_df.columns:
        styled = styled.map(_color_negative, subset=[bal_col])

    # تلوين تصنيف الخطر
    if "تصنيف الخطر" in display_df.columns:
        styled = styled.map(_color_risk, subset=["تصنيف الخطر"])

    # تنسيق الأرقام (3 منازل عشرية كما في الصورة الأصلية)
    fmt_dict = {}
    for col in available_buckets + ([bal_col] if bal_col and bal_col in display_df.columns else []):
        if col in display_df.columns:
            fmt_dict[col] = "{:,.2f}"
    if fmt_dict:
        styled = styled.format(fmt_dict, na_rep="-")

    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    # مفتاح الألوان
    with st.expander("🎨 مفتاح الألوان", expanded=False):
        st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 13px;">
            <div>🔴 <span style="background:#fed7d7; padding:2px 8px; border-radius:4px;">خلفية حمراء</span> — شريحة حرجة (>90 يوم)</div>
            <div>🟠 <span style="background:#fef5e7; padding:2px 8px; border-radius:4px;">خلفية برتقالية</span> — شريحة متأخرة (31-90 يوم)</div>
            <div>🟢 <span style="background:#f0fff4; padding:2px 8px; border-radius:4px;">خلفية خضراء</span> — شريحة حديثة (0-30 يوم)</div>
            <div>⚪ <span style="background:#fafafa; padding:2px 8px; border-radius:4px;">خلفية رمادية</span> — قيمة صفر</div>
        </div>
        """, unsafe_allow_html=True)

    st.caption(f"📊 إجمالي السجلات: {len(display_df)} عميل | مرتّبين حسب مستوى الخطر (الأعلى أولاً)")


# ──────────────────────────────────────────────────────────
def _render_export_buttons(sp_data: pd.DataFrame, selected_sp: str,
                            cust_col: str, bal_col: str | None, detected_buckets: list) -> None:
    """أزرار التصدير (Excel / CSV)"""
    st.markdown("#### 📤 تصدير التقرير")

    available_buckets = [b for b in detected_buckets if b in sp_data.columns]
    agg_dict: dict = {b: "sum" for b in available_buckets}
    if bal_col and bal_col in sp_data.columns and bal_col not in agg_dict:
        agg_dict[bal_col] = "sum"

    export_df = sp_data.groupby(cust_col).agg(agg_dict).reset_index() if agg_dict else sp_data.copy()

    # إضافة صف الإجمالي
    if not export_df.empty:
        total_row = {cust_col: "الإجمالي"}
        for col in export_df.columns:
            if col != cust_col:
                total_row[col] = export_df[col].sum()
        export_df = pd.concat([export_df, pd.DataFrame([total_row])], ignore_index=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    safe_sp = "".join(c for c in selected_sp if c.isalnum() or c in ("-", "_"))[:30]

    col1, col2, col3 = st.columns([1, 1, 6])

    with col1:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, sheet_name=f"Aging_{safe_sp}", index=False)
        st.download_button(
            label="📊 Excel",
            data=buffer.getvalue(),
            file_name=f"aging_{safe_sp}_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col2:
        csv = export_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📄 CSV",
            data=csv,
            file_name=f"aging_{safe_sp}_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )
