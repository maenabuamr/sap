import streamlit as st

from data_loader import load_sales, load_aging

st.set_page_config(
    page_title="Credit Management",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Credit Management")

# ==========================
# Load Data
# ==========================

sales = load_sales()
aging = load_aging()

# ==========================
# Information
# ==========================

col1, col2 = st.columns(2)

with col1:
    st.metric("Sales Records", len(sales))

with col2:
    st.metric("Aging Records", len(aging))

st.success("Data loaded successfully ✅")