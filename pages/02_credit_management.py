import streamlit as st
from data_loader import load_sales, load_aging, load_checks

st.set_page_config(
    page_title="Credit Management",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Credit Management")

sales = load_sales()
aging = load_aging()
checks = load_checks()

col1, col2, col3 = st.columns(3)

col1.metric("Sales Records", len(sales))
col2.metric("Aging Records", len(aging))
col3.metric("Checks Records", len(checks))

st.success("Data loaded successfully ✅")