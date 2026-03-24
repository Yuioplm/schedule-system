import streamlit as st

st.title("外来スケジュール管理")

st.write("メニュー")

st.page_link("pages/1_枠管理.py", label="枠管理")
st.page_link("pages/2_予定検索.py", label="予定検索")
st.page_link("pages/3_予定変更入力.py", label="予定変更入力")
st.page_link("pages/5_帳票2.py", label="帳票出力2")
st.page_link("pages/6_帳票3.py", label="帳票出力3")
st.page_link("pages/7_帳票4.py", label="帳票出力4")
st.page_link("pages/8_帳票5.py", label="帳票出力5")

st.set_page_config(layout="wide")