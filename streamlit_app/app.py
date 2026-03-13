import streamlit as st

st.title("外来スケジュール管理")

st.write("メニュー")

st.page_link("pages/1_枠管理.py", label="枠管理")
st.page_link("pages/2_予定検索.py", label="予定検索")
st.page_link("pages/4_帳票出力.py", label="帳票出力")