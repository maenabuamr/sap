import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(layout="wide", page_title="إدارة المشتريات")
st.title("🛒 إدارة المشتريات")

PURCHASE_PATH = "data/purchase.csv"

if not os.path.exists(PURCHASE_PATH):
    st.error(f"الملف غير موجود: {PURCHASE_PATH}")
    st.stop()


@st.cache_data
def load_data():
    return pd.read_csv(PURCHASE_PATH)


df_raw = load_data()

if df_raw.empty:
    st.error("لا توجد بيانات")
    st.stop()

# ─── Filters Row 1 ────────────────────────────────
years = sorted(df_raw['Year'].dropna().unique().tolist(), reverse=True)
months = sorted(df_raw['Month'].dropna().unique().tolist())

db_values = (
    sorted(df_raw['DB'].dropna().astype(str).unique().tolist())
    if 'DB' in df_raw.columns else []
)

type_values = (
    sorted(df_raw['PurchaseType'].dropna().astype(str).unique().tolist())
    if 'PurchaseType' in df_raw.columns else []
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    selected_years = st.multiselect("📅 السنة:", years, default=years)
with col2:
    selected_months = st.multiselect("📅 الشهر:", months, default=months)
with col3:
    selected_dbs = st.multiselect("🏢 الشركة (DB):", db_values, default=db_values)
with col4:
    selected_types = st.multiselect("🛒 نوع الشراء:", type_values, default=type_values)

# ─── Filters Row 2 ────────────────────────────────
vendor_options = (
    sorted(df_raw['VendorName'].dropna().astype(str).unique().tolist())
    if 'VendorName' in df_raw.columns else []
)

item_options = (
    sorted(df_raw['ItemDescription'].dropna().astype(str).unique().tolist())
    if 'ItemDescription' in df_raw.columns else []
)

col5, col6 = st.columns(2)
with col5:
    selected_vendors = st.multiselect("🏭 المورد:", vendor_options, default=vendor_options)
with col6:
    selected_items = st.multiselect("📦 الصنف:", item_options, default=item_options)

# ─── Apply combined filter ────────────────────────────────
mask = (
    df_raw['Year'].isin(selected_years)
    & df_raw['Month'].isin(selected_months)
)
if 'DB' in df_raw.columns:
    mask &= df_raw['DB'].astype(str).isin(selected_dbs)
if 'PurchaseType' in df_raw.columns:
    mask &= df_raw['PurchaseType'].astype(str).isin(selected_types)
if 'VendorName' in df_raw.columns and vendor_options:
    mask &= df_raw['VendorName'].astype(str).isin(selected_vendors)
if 'ItemDescription' in df_raw.columns and item_options:
    mask &= df_raw['ItemDescription'].astype(str).isin(selected_items)

df = df_raw[mask].copy()

if df.empty:
    st.warning("لا توجد بيانات بعد الفلترة")
    st.stop()

df['سعر الوحدة'] = df.apply(
    lambda r: r['Amt'] / r['QYT'] if pd.notna(r['QYT']) and r['QYT'] > 0 else None,
    axis=1,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 إجمالي المبلغ", f"{df['Amt'].sum():,.2f}")
m2.metric("📦 إجمالي الكمية", f"{df['QYT'].sum():,.0f}")
m3.metric("🏭 عدد الموردين", df['VendorCode'].nunique())
m4.metric("📋 عدد الأصناف", df['ItemCode'].nunique())

st.divider()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏭 الموردين", "📦 الأصناف", "📅 الفترة الزمنية", "📊 التركيز", "📋 تقرير المواد", "🔍 تفاصيل الأصناف",
])

with tab1:
    st.subheader("تحليل الموردين")
    by_vendor = df.groupby(['VendorCode', 'VendorName']).agg(
        total_amount=('Amt', 'sum'),
        total_qty=('QYT', 'sum'),
        doc_count=('DocNum', 'nunique'),
        item_count=('ItemCode', 'nunique'),
    ).reset_index().sort_values('total_amount', ascending=False)
    st.markdown("**🏆 أعلى 20 مورد حسب المبلغ:**")
    st.dataframe(by_vendor.head(20), use_container_width=True)
    st.divider()
    by_type = df.groupby('PurchaseType').agg(
        total_amount=('Amt', 'sum'),
        vendor_count=('VendorCode', 'nunique'),
    ).reset_index().sort_values('total_amount', ascending=False)
    st.dataframe(by_type, use_container_width=True)
    st.plotly_chart(
        px.pie(by_type, values='total_amount', names='PurchaseType',
               title='توزيع المبلغ حسب نوع الشراء'),
        use_container_width=True,
    )

with tab2:
    st.subheader("📋 كل الأصناف")
    st.caption("جدول بكل صنف: الاسم، إجمالي الكمية، متوسط السعر، إجمالي السعر")
    all_items = df.groupby(['ItemCode', 'ItemDescription', 'ItemGroup']).agg(
        total_qty=('QYT', 'sum'),
        total_amount=('Amt', 'sum'),
    ).reset_index()
    all_items['avg_price'] = all_items.apply(
        lambda r: r['total_amount'] / r['total_qty'] if r['total_qty'] > 0 else 0,
        axis=1,
    )
    sort_opts_t2 = {
        'total_amount': 'إجمالي السعر',
        'total_qty': 'إجمالي الكمية',
        'avg_price': 'متوسط السعر',
    }
    sort_by_t2 = st.selectbox(
        "ترتيب:",
        options=list(sort_opts_t2.keys()),
        format_func=lambda x: sort_opts_t2[x],
    )
    st.caption(f"إجمالي {len(all_items)} صنف")
    st.dataframe(
        all_items.sort_values(sort_by_t2, ascending=False),
        use_container_width=True,
        column_config={
            'total_qty': st.column_config.NumberColumn('إجمالي كمية الشراء', format="%.2f"),
            'avg_price': st.column_config.NumberColumn('متوسط السعر', format="%.4f"),
            'total_amount': st.column_config.NumberColumn('إجمالي السعر', format="%.2f"),
        },
        column_order=['ItemCode', 'ItemDescription', 'ItemGroup', 'total_qty', 'avg_price', 'total_amount'],
        hide_index=True,
    )
    st.download_button(
        "📥 تنزيل كل الأصناف كـ CSV",
        data=all_items.to_csv(index=False).encode('utf-8-sig'),
        file_name="all_items.csv",
        mime="text/csv",
        key='dl_all_items',
    )

with tab3:
    st.subheader("تحليل الفترة الزمنية")
    monthly = df.groupby(['Year', 'Month']).agg(
        total_amount=('Amt', 'sum'),
        doc_count=('DocNum', 'nunique'),
    ).reset_index()
    monthly['period'] = (
        monthly['Year'].astype(int).astype(str)
        + '-'
        + monthly['Month'].astype(int).astype(str).str.zfill(2)
    )
    monthly = monthly.sort_values('period')
    st.plotly_chart(
        px.line(monthly, x='period', y='total_amount', markers=True,
                title='اتجاه المبلغ الإجمالي شهرياً'),
        use_container_width=True,
    )
    st.divider()
    yearly = df.groupby('Year').agg(
        total_amount=('Amt', 'sum'),
        doc_count=('DocNum', 'nunique'),
    ).reset_index().sort_values('Year')
    yearly['growth_pct'] = yearly['total_amount'].pct_change() * 100
    st.dataframe(yearly, use_container_width=True)
    st.plotly_chart(
        px.bar(yearly, x='Year', y='total_amount', title='إجمالي المشتريات سنوياً'),
        use_container_width=True,
    )

with tab4:
    st.subheader("تحليل التركيز (Pareto)")
    st.caption("قاعدة 80/20")
    grand_total = df['Amt'].sum()
    by_vendor_p = df.groupby(['VendorCode', 'VendorName'])['Amt'].sum().reset_index().sort_values('Amt', ascending=False)
    by_vendor_p['cum_pct'] = by_vendor_p['Amt'].cumsum() / by_vendor_p['Amt'].sum() * 100
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🏭 تركّز الموردين**")
        top5_v = by_vendor_p.head(5)['Amt'].sum()
        st.metric("أعلى 5 موردين", f"{top5_v/grand_total*100:.1f}%", f"{top5_v:,.2f}")
        v_80 = (by_vendor_p['cum_pct'] <= 80).sum() + 1
        st.metric("موردين لـ 80%", f"{v_80}")
    with col2:
        st.markdown("**📦 تركّز الأصناف**")
        by_item_p = df.groupby(['ItemCode', 'ItemDescription'])['Amt'].sum().reset_index().sort_values('Amt', ascending=False)
        by_item_p['cum_pct'] = by_item_p['Amt'].cumsum() / by_item_p['Amt'].sum() * 100
        top10_i = by_item_p.head(10)['Amt'].sum()
        st.metric("أعلى 10 أصناف", f"{top10_i/grand_total*100:.1f}%", f"{top10_i:,.2f}")
        i_80 = (by_item_p['cum_pct'] <= 80).sum() + 1
        st.metric("أصناف لـ 80%", f"{i_80}")
    st.divider()
    pareto_data = by_vendor_p.head(50).copy()
    pareto_data['rank'] = range(1, len(pareto_data) + 1)
    fig = px.line(pareto_data, x='rank', y='cum_pct', markers=True, title='تراكمي % للموردين')
    fig.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="80%")
    st.plotly_chart(fig, use_container_width=True)
    st.divider()
    st.dataframe(by_vendor_p.head(30), use_container_width=True)

with tab5:
    st.subheader("📋 تقرير شامل بالمواد (بالتفاصيل)")
    st.caption("كل صنف مع المورد الأعلى والأدنى سعر")
    detailed = df.groupby(['ItemCode', 'ItemDescription', 'ItemGroup']).agg(
        total_qty=('QYT', 'sum'),
        total_amount=('Amt', 'sum'),
        avg_price=('سعر الوحدة', 'mean'),
        min_price=('سعر الوحدة', 'min'),
        max_price=('سعر الوحدة', 'max'),
        vendor_count=('VendorCode', 'nunique'),
        purchase_count=('DocNum', 'count'),
    ).reset_index()
    valid_prices = df.dropna(subset=['سعر الوحدة'])
    if not valid_prices.empty:
        min_max_vendors = valid_prices.groupby('ItemCode').apply(
            lambda g: pd.Series({
                'min_vendor': g.loc[g['سعر الوحدة'].idxmin(), 'VendorName'],
                'max_vendor': g.loc[g['سعر الوحدة'].idxmax(), 'VendorName'],
            })
        ).reset_index()
    else:
        min_max_vendors = pd.DataFrame(columns=['ItemCode', 'min_vendor', 'max_vendor'])
    detailed = detailed.merge(min_max_vendors, on='ItemCode', how='left')
    detailed['price_spread_pct'] = (
        (detailed['max_price'] - detailed['min_price'])
        / detailed['min_price'].replace(0, float('nan'))
        * 100
    ).round(2).fillna(0)
    col_search, col_sort = st.columns([2, 1])
    with col_search:
        search_term = st.text_input("🔍 ابحث:", "")
    with col_sort:
        sort_opts_t5 = {
            'total_amount': 'إجمالي المبلغ',
            'avg_price': 'متوسط السعر',
            'min_price': 'أدنى سعر',
            'max_price': 'أعلى سعر',
            'price_spread_pct': 'فرق السعر %',
            'vendor_count': 'عدد الموردين',
        }
        sort_col_t5 = st.selectbox("ترتيب:", list(sort_opts_t5.keys()),
                                   format_func=lambda x: sort_opts_t5[x])
    display = detailed.copy()
    if search_term:
        mask_search = (
            display['ItemCode'].astype(str).str.contains(search_term, case=False, na=False)
            | display['ItemDescription'].astype(str).str.contains(search_term, case=False, na=False)
            | display['ItemGroup'].astype(str).str.contains(search_term, case=False, na=False)
            | display['min_vendor'].astype(str).str.contains(search_term, case=False, na=False)
            | display['max_vendor'].astype(str).str.contains(search_term, case=False, na=False)
        )
        display = display[mask_search]
    st.caption(f"عدد الأصناف المعروضة: {len(display)} من {len(detailed)}")
    st.dataframe(
        display.sort_values(sort_col_t5, ascending=False),
        use_container_width=True,
        column_config={
            'avg_price': st.column_config.NumberColumn('متوسط السعر', format="%.4f"),
            'min_price': st.column_config.NumberColumn('أدنى سعر', format="%.4f"),
            'max_price': st.column_config.NumberColumn('أعلى سعر', format="%.4f"),
            'total_amount': st.column_config.NumberColumn('إجمالي المبلغ', format="%.2f"),
            'price_spread_pct': st.column_config.NumberColumn('فرق السعر %', format="%.1f%%"),
            'vendor_count': st.column_config.NumberColumn('عدد الموردين'),
            'purchase_count': st.column_config.NumberColumn('عدد مرات الشراء'),
        },
        column_order=[
            'ItemCode', 'ItemDescription', 'ItemGroup', 'vendor_count',
            'total_qty', 'total_amount', 'purchase_count',
            'avg_price', 'min_price', 'min_vendor', 'max_price', 'max_vendor',
            'price_spread_pct',
        ],
        hide_index=True,
    )
    csv_data = detailed.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "📥 تنزيل التقرير كـ CSV",
        data=csv_data,
        file_name="material_report.csv",
        mime="text/csv",
    )


# ── Tab 6: تفاصيل مشتريات كل صنف ──────────────────────────────
with tab6:
    st.subheader("🔍 تاريخ مشتريات كل صنف")
    st.caption("اضغط على أي صنف لتوسيع تفاصيل مشترياته")

    item_codes_list = sorted(df['ItemCode'].dropna().astype(str).unique().tolist())

    for code_id in item_codes_list:
        rows = df[df['ItemCode'].astype(str) == code_id].sort_values(['Year', 'Month'])
        if rows.empty:
            continue
        item_info = rows.iloc[0]
        desc = str(item_info['ItemDescription']) if pd.notna(item_info['ItemDescription']) else code_id
        n_purchases = len(rows)
        total_amt = rows['Amt'].sum()
        total_qty = rows['QYT'].sum()

        with st.expander(f"📦 {code_id} — {desc[:60]}  ({n_purchases} مرة شراء، المجموع: {total_amt:,.2f})"):
            c1, c2, c3 = st.columns(3)
            c1.metric("📦 مرات الشراء", n_purchases)
            c2.metric("📊 إجمالي الكمية", f"{total_qty:,.2f}")
            c3.metric("💰 إجمالي المبلغ", f"{total_amt:,.2f}")

            display_rows = rows[['Year', 'Month', 'VendorName', 'QYT', 'Amt', 'سعر الوحدة']].copy()
            display_rows['period'] = (
                display_rows['Year'].astype(int).astype(str)
                + '-'
                + display_rows['Month'].astype(int).astype(str).str.zfill(2)
            )
            st.dataframe(
                display_rows[['period', 'VendorName', 'QYT', 'Amt', 'سعر الوحدة']],
                use_container_width=True,
                column_config={
                    'سعر الوحدة': st.column_config.NumberColumn(format="%.4f"),
                    'Amt': st.column_config.NumberColumn(format="%.2f"),
                },
                hide_index=True,
            )
