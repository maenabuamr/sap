import pandas as pd
import streamlit as st


@st.cache_data
def load_sales():
    return pd.read_csv("data/sales_customer.csv")


@st.cache_data
def load_aging():
    """Load aging report - searches /workspaces/sap/data/ first"""
    import os
    import pandas as pd
    paths = [
        '/workspaces/sap/data/aging_report.csv',
        'data/aging_report.csv',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'aging_report.csv'),
    ]
    for p in paths:
        try:
            if os.path.exists(p) and os.path.getsize(p) > 0:
                return pd.read_csv(p, encoding='utf-8-sig')
        except Exception:
            continue
    return None


def load_checks():
    """Load postdated checks - searches /workspaces/sap/data/ first"""
    import os
    import pandas as pd
    paths = [
        '/workspaces/sap/data/postdated_checks.csv',
        'data/postdated_checks.csv',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'postdated_checks.csv'),
    ]
    for p in paths:
        try:
            if os.path.exists(p) and os.path.getsize(p) > 0:
                return pd.read_csv(p, encoding='utf-8-sig')
        except Exception:
            continue
    return pd.DataFrame(columns=['CustomerName', 'CheckNumber', 'Amount', 'DueDate', 'Status'])

