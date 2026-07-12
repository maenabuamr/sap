import pandas as pd
import streamlit as st


import os
import pandas as pd
@st.cache_data
def load_sales():
    return pd.read_csv(os.path.join('/workspaces/sap/data', 'sales_customer.csv'))


@st.cache_data
def load_aging():
    """Load aging report from /workspaces/sap/data/"""
    import os
    import pandas as pd
    fp = os.path.join('/workspaces/sap/data', 'aging_report.csv')
    if os.path.exists(fp) and os.path.getsize(fp) > 0:
        return pd.read_csv(fp, encoding='utf-8-sig')
    return None


def load_checks():
    """Load postdated checks from /workspaces/sap/data/"""
    import os
    import pandas as pd
    fp = os.path.join('/workspaces/sap/data', 'postdated_checks.csv')
    if os.path.exists(fp) and os.path.getsize(fp) > 0:
        return pd.read_csv(fp, encoding='utf-8-sig')
    return pd.DataFrame(columns=['CustomerName', 'CheckNumber', 'Amount', 'DueDate', 'Status'])

