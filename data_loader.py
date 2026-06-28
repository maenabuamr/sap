import pandas as pd
import streamlit as st


@st.cache_data
def load_sales():
    return pd.read_csv("data/sales_customer.csv")


@st.cache_data
def load_aging():
    return pd.read_csv("data/aging_report.csv")


@st.cache_data
def load_checks():
    return pd.read_csv("data/postdated_checks.csv")