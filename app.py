import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt

# =========================
# 📥 Load Data
# =========================
def load_data():

    mowaqer = pd.read_excel("data/mowaqer.xlsx")
    tijari = pd.read_excel("data/tijari.xlsx")

    df = pd.concat([mowaqer, tijari], ignore_index=True)

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")

    return df


# =========================
# 👥 Customer Analysis
# =========================
def build_customer_ai(df):

    customer_ai = df.groupby("U_ST_Ref").agg(
        Total_Sales=("Amount", "sum"),
        Invoices=("DocNum", "count"),
        Companies=("Company", "nunique")
    ).reset_index()

    return customer_ai.sort_values("Total_Sales", ascending=False)


# =========================
# 🚀 APP START
# =========================
st.set_page_config(page_title="ERP AI Dashboard", layout="wide")

st.title("🏭 ERP AI Dashboard - Release 1.0")

# Load data
df = load_data()
customer_ai = build_customer_ai(df)

# =========================
# 🔍 FILTERS
# =========================
st.sidebar.header("🔍 Filters")

company_filter = st.sidebar.selectbox(
    "Select Company",
    ["All"] + list(df["Company"].dropna().unique())
)

if company_filter != "All":
    df = df[df["Company"] == company_filter]
    customer_ai = build_customer_ai(df)


# =========================
# 📊 METRICS
# =========================
st.subheader("📊 Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Customers", customer_ai.shape[0])
col2.metric("Total Sales", round(customer_ai["Total_Sales"].sum(), 2))
col3.metric("Avg Sales", round(customer_ai["Total_Sales"].mean(), 2))


# =========================
# 🏆 TOP CUSTOMERS
# =========================
top_customers = customer_ai.head(10)

st.subheader("🏆 Top 10 Customers")
st.dataframe(top_customers, use_container_width=True)


# =========================
# ⚠️ BOTTOM CUSTOMERS
# =========================
bottom_customers = customer_ai.tail(10)

st.subheader("⚠️ Bottom 10 Customers")
st.dataframe(bottom_customers, use_container_width=True)


# =========================
# 📈 CHART - Distribution
# =========================
st.subheader("📈 Sales Distribution")

fig, ax = plt.subplots()
ax.hist(customer_ai["Total_Sales"], bins=20)
st.pyplot(fig)


# =========================
# 📊 CHART - Top 10
# =========================
st.subheader("📊 Top Customers Chart")

fig2, ax2 = plt.subplots()

top_customers.set_index("U_ST_Ref")["Total_Sales"].plot(
    kind="bar",
    ax=ax2
)

st.pyplot(fig2)


# =========================
# 📤 EXPORT EXCEL
# =========================
st.subheader("📤 Export Report")

output = io.BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:

    customer_ai.to_excel(writer, index=False, sheet_name="Customers")
    top_customers.to_excel(writer, index=False, sheet_name="Top")
    bottom_customers.to_excel(writer, index=False, sheet_name="Bottom")

output.seek(0)

st.download_button(
    label="📥 Download Excel Report",
    data=output,
    file_name="ERP_AI_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)