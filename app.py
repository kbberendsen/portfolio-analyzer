import streamlit as st

pg = st.navigation([st.Page("app_pages/dashboard.py"),
                    st.Page("app_pages/stock_split.py"),
                    st.Page("app_pages/ticker_mapping.py"),
                    st.Page("app_pages/analysis.py"),
                    st.Page("app_pages/type_split.py"),],
                    position="top")

pg.run()