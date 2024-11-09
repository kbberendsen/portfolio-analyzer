import streamlit as st

pg = st.navigation([st.Page("dashboard.py"), st.Page("stock_split.py")])
pg.run()