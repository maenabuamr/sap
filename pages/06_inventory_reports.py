import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide", page_title="تقارير المخزون")
st.title("📈 تقارير حركة ودوران المواد")

# ─── مسارات الملفات ───────────────────────────────────────────
TRANSFERS_PATH = os.path.join('data', r'Items_Transfers.csv')
INVENTORY_PATH = os.path.join('data', r'inventory.csv')

if not os.path.exists(TRANSFERS_PATH):
    st.error(f"الملف غير موجود: {TRANSFERS_PATH}")
    st.stop()
if not os.path.exists(INVENTORY_PATH):
    st.error(f"الملف غير موجود: {INVENTORY_PATH}")
    st.stop()


@st.cache_data
def load_data():
    df_t = pd.read_csv(TRANSFERS_PATH)
    df_i = pd.read_csv(INVENTORY_PATH)
    df_t['تاريخ القيد'] = pd.to_datetime(df_t['تاريخ القيد'], errors='coerce')
    return df_t, df_i


df_transfers, df_inventory = load_data()

if df_transfers.empty:
    st.error("لا توجد بيانات حركات")
    st.stop()

# ─── تجميع المخزون حسب الصنف (تجميع عبر كل المستودعات) ──────
inv_summary = (
    df_inventory.groupby('الوصف')
    .agg({
        'الرصيد': 'sum',
        'قيمة المخزون': 'sum',
        'كلفة الوحدة': 'first',
    })
    .reset_index()
)

# ─── تجميع الحركات حسب الصنف ────────────────────────────────
df_t = df_transfers.copy()
df_t['sign'] = df_t['الكمية'].apply(
    lambda x: 'IN' if x > 0 else 'OUT' if x < 0 else 'NEUTRAL'
)

mov_summary = (
    df_t.groupby('الوصف')
    .agg(
        total_in=('الكمية', lambda x: x[x > 0].sum()),
        total_out=('الكمية', lambda x: abs(x[x < 0].sum())),
        last_movement=('تاريخ القيد', 'max'),
        first_movement=('تاريخ القيد', 'min'),
        movement_count=('الكمية', 'count'),
    )
    .reset_index()
)

# ─── Dataframe موحد للتحليلات ────────────────────────────────
date_min = df_t['تاريخ القيد'].min()
date_max = df_t['تاريخ القيد'].max()
period_days = max((date_max - date_min).days, 1) if pd.notna(date_min) and pd.notna(date_max) else 1

df = mov_summary.merge(
    inv_summary, on='الوصف', how='left'
).fillna({'الرصيد': 0, 'قيمة المخزون': 0, 'كلفة الوحدة': 0})

df['avg_daily_out'] = df['total_out'] / period_days
df['turnover_ratio'] = df.apply(
    lambda r: r['total_out'] / r['الرصيد'] if r['الرصيد'] > 0 else 0, axis=1
)
df['dio'] = df.apply(
    lambda r: (r['الرصيد'] / r['avg_daily_out']) if r['avg_daily_out'] > 0 else None,
    axis=1,
)
df['days_since_last_movement'] = (date_max - df['last_movement']).dt.days
df['days_until_stockout'] = df.apply(
    lambda r: r['الرصيد'] / r['avg_daily_out'] if r['avg_daily_out'] > 0 else None,
    axis=1,
)

# ─── ملخص أعلى الصفحة ────────────────────────────────────────
st.caption(
    f"📅 فترة البيانات: من {date_min:%Y-%m-%d} إلى {date_max:%Y-%m-%d} "
    f"({period_days} يوم) — عدد الأصناف: {len(df)}"
)

# ─── التبويبات ────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 تفاصيل الحركة",
    "🔄 دوران المخزون",
    "🧊 الأصناف الراكدة",
    "📊 ABC Analysis",
    "⏰ توقع النفاد",
])

# ─── Tab 1: تفاصيل الحركة ────────────────────────────────────
with tab1:
    st.subheader("سجل الحركة التفصيلي")
    item_options = df_transfers['الوصف'].dropna().unique()
    if len(item_options) == 0:
        st.info("لا توجد أصناف")
    else:
        selected_item = st.selectbox("اختر الصنف:", item_options)
        df_item = (
            df_transfers[df_transfers['الوصف'] == selected_item]
            .sort_values(by='تاريخ القيد')
        )
        if not df_item.empty:
            st.dataframe(
                df_item[['تاريخ القيد', 'نوع الحركة', 'الكمية', 'الرصيد']],
                use_container_width=True,
            )
            st.plotly_chart(
                px.line(
                    df_item,
                    x='تاريخ القيد', y='الرصيد',
                    title=f"تطور رصيد: {selected_item}",
                ),
                use_container_width=True,
            )

    st.divider()
    st.subheader("توزيع الحركات حسب النوع")
    movement_types = df_transfers['نوع الحركة'].value_counts().reset_index()
    movement_types.columns = ['نوع الحركة', 'count']
    st.plotly_chart(
        px.pie(
            movement_types, values='count', names='نوع الحركة',
            title="توزيع الحركات",
        ),
        use_container_width=True,
    )

# ─── Tab 2: دوران المخزون ─────────────────────────────────────
with tab2:
    st.subheader("معدل دوران المخزون وعدد أيام التخزين (DIO)")
    st.caption(
        "**Turnover Ratio** = إجمالي الخروج ÷ الرصيد الحالي — كلما زاد، الصنف أسرع دورانًا.\n\n"
        "**DIO** = كم يوم المخزون الحالي بيكفي — كلما قل، أحسن."
    )

    top_turnover = df.sort_values('turnover_ratio', ascending=False).head(20)
    st.dataframe(
        top_turnover[['الوصف', 'الرصيد', 'total_out', 'turnover_ratio', 'dio']],
        use_container_width=True,
        column_config={
            'turnover_ratio': st.column_config.NumberColumn('معدل الدوران', format="%.2f"),
            'dio': st.column_config.NumberColumn('DIO (يوم)', format="%.1f"),
        },
    )

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🏆 أعلى 10 أصناف دوراناً**")
        top10 = df.sort_values('turnover_ratio', ascending=False).head(10)
        st.dataframe(
            top10[['الوصف', 'turnover_ratio']],
            use_container_width=True,
            column_config={'turnover_ratio': st.column_config.NumberColumn(format="%.2f")},
        )
    with col2:
        st.markdown("**🐌 أبطأ 10 أصناف دوراناً**")
        bot10 = df[df['الرصيد'] > 0].sort_values('turnover_ratio').head(10)
        st.dataframe(
            bot10[['الوصف', 'turnover_ratio']],
            use_container_width=True,
            column_config={'turnover_ratio': st.column_config.NumberColumn(format="%.2f")},
        )

# ─── Tab 3: الأصناف الراكدة ───────────────────────────────────
with tab3:
    st.subheader("الأصناف الراكدة وغير المتحركة")
    slow_threshold_days = st.slider(
        "حد الأصناف الراكدة (أيام بدون حركة):",
        min_value=30, max_value=365, value=90, step=30,
    )

    df_active = df[df['الرصيد'] > 0]
    slow_moving = df_active[df_active['days_since_last_movement'] >= slow_threshold_days]
    non_moving = df_active[df_active['movement_count'] == 0]

    col1, col2, col3 = st.columns(3)
    col1.metric("🧊 راكد (≥ الأيام المختارة)", len(slow_moving))
    col2.metric("⛔ غير متحرك إطلاقاً", len(non_moving))
    col3.metric(
        "💰 قيمة المخزون الراكد",
        f"{slow_moving['قيمة المخزون'].sum():,.2f}",
    )

    st.divider()
    st.markdown(f"**🧊 الأصناف الراكدة ({len(slow_moving)} صنف)**")
    st.dataframe(
        slow_moving[['الوصف', 'الرصيد', 'قيمة المخزون', 'days_since_last_movement', 'last_movement']]
        .sort_values('قيمة المخزون', ascending=False),
        use_container_width=True,
        column_config={
            'days_since_last_movement': st.column_config.NumberColumn('أيام بدون حركة', format="%d"),
        },
    )

    st.divider()
    st.markdown(f"**⛔ الأصناف غير المتحركة ({len(non_moving)} صنف)**")
    if len(non_moving):
        st.dataframe(
            non_moving[['الوصف', 'الرصيد', 'قيمة المخزون']],
            use_container_width=True,
        )
    else:
        st.success("كل الأصناف فيها حركة ✅")

# ─── Tab 4: ABC Analysis ──────────────────────────────────────
with tab4:
    st.subheader("ABC Analysis — تصنيف الأصناف حسب قيمة المخزون")
    st.caption(
        "**A** = أهم 70% من القيمة (عادةً 20% من الأصناف)\n\n"
        "**B** = الـ 20% التالية\n\n"
        "**C** = الـ 10% الأخيرة (الأقل قيمة)"
    )

    df_abc = (
        df[df['قيمة المخزون'] > 0]
        .copy()
        .sort_values('قيمة المخزون', ascending=False)
        .reset_index(drop=True)
    )
    grand_total = df_abc['قيمة المخزون'].sum()
    df_abc['cumulative_pct'] = df_abc['قيمة المخزون'].cumsum() / grand_total * 100

    def classify(pct: float) -> str:
        if pct <= 70:
            return 'A'
        if pct <= 90:
            return 'B'
        return 'C'

    df_abc['category'] = df_abc['cumulative_pct'].apply(classify)

    col1, col2, col3 = st.columns(3)
    for cat, col in zip(['A', 'B', 'C'], [col1, col2, col3]):
        cat_df = df_abc[df_abc['category'] == cat]
        col.metric(
            f"الفئة {cat}",
            f"{len(cat_df)} صنف",
            f"{cat_df['قيمة المخزون'].sum():,.0f}",
        )

    st.divider()
    st.dataframe(
        df_abc[['الوصف', 'الرصيد', 'قيمة المخزون', 'cumulative_pct', 'category']],
        use_container_width=True,
        column_config={
            'cumulative_pct': st.column_config.NumberColumn('% تراكمي', format="%.1f%%"),
        },
    )

    st.plotly_chart(
        px.bar(
            df_abc.head(50),
            x='الوصف', y='قيمة المخزون', color='category',
            title='توزيع ABC (أول 50 صنف حسب القيمة)',
        ),
        use_container_width=True,
    )

# ─── Tab 5: توقع النفاد ───────────────────────────────────────
with tab5:
    st.subheader("التوقع المتوقع لنفاد المخزون")
    st.caption(
        "بناءً على معدل الخروج اليومي، بنحسب كم يوم بيكفي الرصيد الحالي. "
        "الأرقام الصغيرة = أولوية للطلب."
    )

    forecast = df[df['الرصيد'] > 0].copy().sort_values('days_until_stockout', na_position='last')

    col1, col2 = st.columns([1, 1])
    with col1:
        critical_threshold = st.number_input(
            "حد التنبيه (يوم):",
            min_value=1, max_value=180, value=14, step=1,
        )

    critical = forecast[
        forecast['days_until_stockout'].notna()
        & (forecast['days_until_stockout'] <= critical_threshold)
    ]

    col_a, col_b = st.columns(2)
    col_a.metric(f"⚠️ أولوية (≤ {int(critical_threshold)} يوم)", len(critical))
    col_b.metric("✅ مخزون كافي", int((forecast['days_until_stockout'] > critical_threshold).sum()))

    st.divider()
    st.markdown(f"**⚠️ أصناف رصيدها رايح ينخلص قريباً:**")
    if len(critical):
        st.dataframe(
            critical[['الوصف', 'الرصيد', 'avg_daily_out', 'days_until_stockout']].head(30),
            use_container_width=True,
            column_config={
                'avg_daily_out': st.column_config.NumberColumn('متوسط الخروج اليومي', format="%.2f"),
                'days_until_stockout': st.column_config.NumberColumn('يوم متبقي', format="%.1f"),
            },
        )
    else:
        st.success("مفيش أصناف حرجة ✅")

    st.divider()
    st.markdown("**📋 كل الأصناف مرتبة حسب المتبقي (أول 100):**")
    st.dataframe(
        forecast[['الوصف', 'الرصيد', 'avg_daily_out', 'days_until_stockout']].head(100),
        use_container_width=True,
        column_config={
            'avg_daily_out': st.column_config.NumberColumn('متوسط الخروج اليومي', format="%.2f"),
            'days_until_stockout': st.column_config.NumberColumn('يوم متبقي', format="%.1f"),
        },
    )