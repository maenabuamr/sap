import streamlit as st


def render_global_filters(aging, sales):

    st.sidebar.header("🔍 الفلاتر")

    filters = {}

    # ==========================================
    # Company (الشركة - خيار مفرد)
    # ==========================================
    companies = ["الكل"]
    if "DB" in aging.columns:
        companies += sorted(
            aging["DB"].dropna().unique().tolist()
        )

    filters["company"] = st.sidebar.selectbox(
        "🏢 الشركة",
        companies
    )

    # ==========================================
    # Year (السنة - خيار مفرد)
    # ==========================================
    years = ["الكل"]
    if "Year" in sales.columns:
        years += sorted(
            sales["Year"].dropna().unique().tolist()
        )

    filters["year"] = st.sidebar.selectbox(
        "📅 السنة",
        years
    )

    # ==========================================
    # Month (الشهر - خيار مفرد)
    # ==========================================
    months = ["الكل"]
    if "Month" in sales.columns:
        months += sorted(
            sales["Month"].dropna().unique().tolist()
        )

    filters["month"] = st.sidebar.selectbox(
        "📆 الشهر",
        months
    )

    # ==========================================
    # Salesperson (المندوب - تحسين إلى اختيار متعدد Multi-select)
    # ==========================================
    # نقوم باستخراج الأسماء فقط بدون كلمة "الكل" لأن القائمة الفارغة تعني الكل في الـ multiselect
    salespersons_list = []
    if "Salesperson" in aging.columns:
        salespersons_list = sorted(
            aging["Salesperson"].dropna().unique().tolist()
        )

    # استخدام multiselect بدلاً من selectbox لدعم اختيار مندوب أو أكثر بشكل مرن
    selected_salespersons = st.sidebar.multiselect(
        "👨‍💼 المندوبين",
        options=salespersons_list,
        default=[]  # افتراضياً فارغة تعني عدم تصفية أي مندوب (عرض الكل)
    )
    
    # تمرير القائمة مباشرة لتتوافق مع دالة .isin() داخل الـ data_model
    filters["salesperson"] = selected_salespersons if selected_salespersons else "الكل"

    # ==========================================
    # Customer (العميل - تحسين الاختيار والبحث)
    # ==========================================
    customers_list = ["الكل"]
    if "CustomerName" in aging.columns:
        customers_list += sorted(
            aging["CustomerName"].dropna().unique().tolist()
        )

    # تحويله إلى selectbox بدلاً من text_input لتسهيل البحث بالاسم الصحيح مباشرة
    filters["customer"] = st.sidebar.selectbox(
        "👤 العميل",
        customers_list
    )

    return filters